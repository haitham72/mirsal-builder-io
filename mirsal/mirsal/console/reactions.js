/* Reaction effects (#/reactions, Create > + New): the ANIMATION PRESET LIBRARY (Haitham, 2026-10-14: "now it is not 1800+ emojis, it is 10-15
   animation presets, grouped by motion, each with a couple of inner presets"). docs/reaction/ section 13.
   - Animation presets: the presets side by side by motion (burst, fountain, vortex, rain, confetti), id `{motion}_{NN}`, each previewed on the
     sample emoji; Open (edit), JSON, ×, "+ Variation" per motion; Export all (.zip: `{motion}_{NN}.json` + manifest.json with every emoji's preset).
     A preset's Lottie has NO picture and NO base64: one external image asset `emoji` the chat app fills (engine/lottie.py slot export).
   - The editor: one preset on the sample emoji; Save | Save as new variation | JSON | Remove.
   - The wall: every bank emoji, 120 at a time (Load more), each HOLDING one preset (unassigned = its own motion's first variation); pointing at one
     plays its preset with it (Telegram-like, from its bottom-right); clicking opens its preset on it; Select (Shift-click ranges, Select all) and
     Assign one preset or a random variation of each emoji's own motion. Nothing is rendered per emoji: assigning is instant.
   Everything is the server's (flow/emoji_reactions.py): GET /api/particles/emoji-motions (the bank + start), POST emoji-preview (a looping WebP),
   /api/particles/reaction-presets (list, add, update, delete, assign, {id}.json, .zip). */
'use strict';

/* ---------- settings: [key, label, min, max, step, unit] ---------- */
const RXPRESETS=['burst','fountain','vortex','rain','confetti'];
const RXSIM=[['magnitude','Speed',0,3,.05,'×'],['gravity','Gravity',-2,3,.05,''],['vortex','Swirl',-2,2,.05,''],['spin','Rotation',0,3,.05,'×'],['count','Amount',4,80,1,''],['spread','Spread',10,360,5,'°']];
/* no Hue: a preset carries no picture, so the chat app's emoji is shown in its own colours */
const RXO=[['particle_size','Size',.25,3,.05,'×'],['size_var','Size variation',0,1,.05,'%'],['size_in_dur','Size in',0,1.5,.05,'s'],['size_out_dur','Size out',0,1.5,.05,'s']];
/* where a new variation starts; the server's EMOJI_START (GET emoji-motions `start`) replaces this copy as soon as the bank is read */
const RXSTART={magnitude:.7,gravity:1,vortex:0,spin:1,count:28,spread:360,particle_size:.3,size_var:.38,size_in_dur:.4,size_out_dur:.4};
const RXPX=256;                                  /* a preview loop's side */
const RXHOV=64;                                  /* the hover reaction's side */
const RXPAGE=120;                                /* wall tiles drawn at a time (Load more adds the next page) */

/* ---------- state ----------
   bank / rows: the emoji bank (server) and token -> row; start: the start look (server); lib: {presets, assign} (server); sample: the emoji the
   presets are previewed on; ek: the preset in the editor; hover: the emoji pointed at; pv / par: preview url and params per request; ppv: a card's
   preview; multi / sel / anchor: Select; apply: what Assign gives ('random' or a preset id); shown: wall tiles drawn. */
const RXQ={q:'',f:''};
const RXS={bank:null,rows:null,start:null,lib:null,sample:'happy',ek:null,hover:'',pv:{},par:{},ppv:{},hT:0,t:0,multi:false,sel:new Set(),anchor:'',apply:'random',shown:RXPAGE};
const rxStart=()=>RXS.start||RXSTART;

/* ---------- values ---------- */
const rxOpt=key=>RXSIM.find(o=>o[0]===key)||RXO.find(o=>o[0]===key);
const rxIsSim=key=>RXSIM.some(o=>o[0]===key);
function rxRow(t){if(!RXS.rows&&RXS.bank)RXS.rows=new Map(RXS.bank.map(m=>[m.token,m]));return (RXS.rows&&RXS.rows.get(t))||{token:t,emoji:'',preset:'',motion:''}}
const rxPresets=()=>(RXS.lib&&RXS.lib.presets)||[];
const rxPre=id=>rxPresets().find(p=>p.id===id);
/* the preset an emoji holds: its own, else its motion's first variation, else the first preset */
function rxPresetOf(t){
 const a=RXS.lib&&RXS.lib.assign[t];if(a&&rxPre(a))return a;
 const own=rxRow(t).preset,ps=rxPresets(),first=ps.find(p=>p.motion===own)||ps[0];return first?first.id:''}
/* a preview request: the emoji, the preset's motion and settings, no hue (a preset carries no colour change) */
const rxBodyOf=(t,s,motion)=>({token:t,...Object.fromEntries(Object.entries(s||{}).filter(([k,v])=>v!=null&&k!=='preset'&&k!=='hue_var').map(([k,v])=>[k,+v])),preset:motion,hue_var:0});
const rxKey=b=>JSON.stringify(b);
/* the editor: one preset (or a new variation of a motion) on one emoji */
function rxEdFrom(p,t,motion){const s={...rxStart(),...((p&&p.settings)||{})};
 return {id:p?p.id:'',name:p?p.name:'',motion:p?p.motion:motion,token:t,sim:Object.fromEntries(RXSIM.map(o=>[o[0],s[o[0]]])),
  particle_size:s.particle_size,size_var:s.size_var,size_in_dur:s.size_in_dur,size_out_dur:s.size_out_dur,own:null,shown:'',err:'',busy:false}}
const rxBody=k=>rxBodyOf(k.token,{...k.sim,particle_size:k.particle_size,size_var:k.size_var,size_in_dur:k.size_in_dur,size_out_dur:k.size_out_dur},k.motion);
const rxSettings=k=>{const b=rxBody(k);delete b.token;delete b.preset;delete b.hue_var;return b};
/* what an emoji plays: the editor's when it is open on it, else the preset it holds */
const rxFor=t=>{if(RXS.ek&&RXS.ek.token===t)return rxBody(RXS.ek);const p=rxPre(rxPresetOf(t));return rxBodyOf(t,p?p.settings:rxStart(),p?p.motion:(rxRow(t).preset||'burst'))};
function rxVal(k,o){const key=o[0];return rxIsSim(key)?(k.sim[key]!=null?k.sim[key]:k.own&&k.own[key]!=null?k.own[key]:null):k[key]}
const rxFmt=(o,v)=>v==null?'…':o[5]==='%'?Math.round(v*100)+'%':o[5]==='×'?'×'+(+v):(+v)+o[5];
const rxPlural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
function rxList(){
 const bank=RXS.bank||[],q=RXQ.q.trim().toLowerCase(),f=RXQ.f;
 return bank.filter(m=>(!q||(m.token+' '+m.emoji+' '+(m.motion||'')).toLowerCase().includes(q))&&(!f||rxPresetOf(m.token)===f))}
/* how many emojis hold each preset (one pass over the bank) */
function rxUse(){const n={};for(const m of RXS.bank||[]){const id=rxPresetOf(m.token);n[id]=(n[id]||0)+1}return n}

/* ---------- views ---------- */
/* the hover reaction plays as Telegram plays one: the burst's own origin sits on the sticker's bottom-right, 90% across and 90% down */
function rxFxStyle(par){const [ox,oy]=(par&&par.origin)||[.5,.5];return `width:${RXHOV}px;height:${RXHOV}px;left:calc(90% - ${Math.round(ox*RXHOV)}px);top:calc(90% - ${Math.round(oy*RXHOV)}px)`}
/* the hover's own preview: the whole burst scaled into its square (fit), never cut at its edges */
const rxHovKey=t=>rxKey(rxFor(t))+'|fit';
const rxStageHtml=(emoji,url,alt)=>`<span class=rx-ghost aria-hidden=true>${esc(emoji)}</span>${url?`<img src="${esc(url)}" alt="${esc(alt)}" loading=lazy>`:''}`;
function rxTile(m){
 const key=rxHovKey(m.token),ticked=RXS.multi&&RXS.sel.has(m.token),on=!RXS.multi&&!!RXS.ek&&RXS.ek.token===m.token,pid=rxPresetOf(m.token);
 const pv=RXS.hover===m.token&&!on?RXS.pv[key]:'';
 return `<button class="rx-e${on||ticked?' on':''}${pv?' play':''}" data-act=rxpick data-t="${esc(m.token)}" title="${esc(m.token)} · ${esc(pid)}" aria-label="${esc(m.token)}, ${esc(pid)}" aria-pressed=${on||ticked}>`+
  `<span class=rx-g>${esc(m.emoji||'?')}</span>${ticked?`<span class=rx-tick>${ic('check')}</span>`:''}${pv?`<img class=rx-fx src="${esc(pv)}" style="${rxFxStyle(RXS.par[key])}" alt="">`:''}</button>`}
function rxMoreHtml(n){const rest=n-Math.min(n,RXS.shown);
 return rest>0?`<div class=rx-more data-rxmore><button class="btn sm" data-act=rxmore>Load more</button><small class=mut>${Math.min(n,RXS.shown)} of ${n} shown · ${rest} more</small></div>`:'<div data-rxmore></div>'}
/* the preset library: one column per motion, its variations under it */
function rxCard(p,used){
 const url=RXS.ppv[p.id+'|'+RXS.sample]||'',open=RXS.ek&&RXS.ek.id===p.id;
 return `<article class="rx-card${open?' on':''}" data-rxcard=${esc(p.id)}><div class=rx-stage>${rxStageHtml(rxRow(RXS.sample).emoji,url,p.id)}${url?'':'<span class=spin></span>'}</div>
  <div class=rx-meta><span class=rx-mt><b>${esc(p.id)}</b><small class=mut>${esc(p.name)} · ${rxPlural(used||0,'emoji')}</small></span><button class=link data-act=rxpdel data-id="${esc(p.id)}" aria-label="Remove ${esc(p.id)}" title="Remove this preset (its emojis go back to their motion's first variation)">${ic('x')}</button></div>
  <div class=rx-acts><button class="btn sm${open?' pri':''}" data-act=rxpopen data-id="${esc(p.id)}">Open</button><button class="btn sm" data-act=rxdl data-id="${esc(p.id)}" title="${esc(p.id)}.json: the Lottie, no picture inside (the app fills the 'emoji' asset)">${ic('download')} JSON</button></div></article>`}
function rxLibHtml(){
 const ps=rxPresets();if(!RXS.lib)return `<section class=rx-made data-rxlib><div class=sh>Animation presets</div><span class=spin></span></section>`;
 const used=rxUse(),s=rxRow(RXS.sample);
 return `<section class=rx-made data-rxlib><div class=rx-ph><div class=sh>Animation presets <small class=mut>${ps.length}</small></div>`+
  `<small class=mut>Previewed on <b>${esc(s.emoji)} ${esc(s.token)}</b>: click any emoji below to preview on it</small><span class=sp></span>`+
  `<button class="btn sm" data-act=rxzip title="Every preset as {motion}_{NN}.json, plus manifest.json with the preset of every emoji">${ic('download')} Export all (.zip)</button></div>`+
  `<div class=rx-motions>${RXPRESETS.map(mo=>`<div class=rx-mcol><div class=rx-mh><b>${esc(mo)}</b><button class=link data-act=rxpadd data-m=${mo}>+ Variation</button></div>`+
   `${ps.filter(p=>p.motion===mo).map(p=>rxCard(p,used[p.id])).join('')||'<small class=mut>No variation yet</small>'}</div>`).join('')}</div></section>`}
function rxSlider(k,o){
 const v=rxVal(k,o);
 return `<label class=rx-sl><span class=mut>${o[1]}</span><input type=range min=${o[2]} max=${o[3]} step=${o[4]} value="${v??(o[2]+o[3])/2}" data-rxo=${o[0]} aria-label="${o[1]}"><output>${rxFmt(o,v)}</output></label>`}
function rxGroup(title,g,body){
 return `<div class=rx-grp><div class=rx-gh><b>${title}</b><button class=link data-act=rxreset data-g=${g}>Reset</button></div>${body}</div>`}
function rxStage(k){const url=RXS.pv[rxKey(rxBody(k))]||k.shown;return rxStageHtml(rxRow(k.token).emoji,url,(k.id||k.motion)+' preview')+(url||k.err?'':'<span class=spin></span>')}
function rxEditor(){
 const k=RXS.ek;if(!k)return '<div data-rxed></div>';const m=rxRow(k.token);
 return `<section class=rx-ed data-rxed><div class=rx-stage data-rxstage>${rxStage(k)}</div><div class=rx-ctl>
  <div class=rx-h><b>${esc(k.id||'new '+k.motion+' variation')}</b><span class=fx-chip>${esc(k.motion)}</span><small class=mut>${esc(k.name||'')} · on ${esc(m.emoji)} ${esc(m.token)}</small><button class=link data-act=rxclose aria-label="Close">${ic('x')}</button></div>
  <div class=rx-groups>
   ${rxGroup('Simulation','sim',RXSIM.map(o=>rxSlider(k,o)).join(''))}
   ${rxGroup('Shape','shape',RXO.map(o=>rxSlider(k,o)).join('')+'<small class=mut>The chat app shows the emoji in its own colours: a preset carries no picture.</small>')}
  </div>${k.err?`<span class=fx-warn>${esc(k.err)}</span>`:''}
  <div class=rx-foot>${k.id?`<button class="btn pri" data-act=rxsave ${k.busy?'disabled':''}>Save ${esc(k.id)}</button>`:''}<button class="btn${k.id?'':' pri'}" data-act=rxcreate ${k.busy?'disabled':''}>Save as new ${esc(k.motion)} variation</button>`+
  `${k.id?`<button class=btn data-act=rxdl data-id="${esc(k.id)}">${ic('download')} JSON</button><span class=sp></span><button class="btn dng" data-act=rxpdel data-id="${esc(k.id)}">Remove</button>`:''}</div></div></section>`}
/* the wall: every emoji with the preset it holds; Select + Assign */
function rxMany(){
 if(!RXS.multi)return '<div data-rxmany></div>';
 const n=RXS.sel.size,ps=rxPresets(),all=rxList().length;
 return `<div class=rx-many data-rxmany><span class=rx-many-sel>${n?`<b>${n}</b> selected`:'<span class=mut>Click to tick, Shift-click ticks the range</span>'}</span>`+
  `<button class=link data-act=rxselall>Select all (${all})</button>${n?'<button class=link data-act=rxclear>Clear</button>':''}`+
  `<label class=rx-pre><span class=mut>Give them</span><select data-rxapply aria-label="Preset to assign"><option value=random${RXS.apply==='random'?' selected':''}>a random variation of its own motion</option>`+
  `${ps.map(p=>`<option value="${esc(p.id)}"${p.id===RXS.apply?' selected':''}>${esc(p.id)} · ${esc(p.name)}</option>`).join('')}</select></label>`+
  `<button class="btn pri" data-act=rxmany ${n?'':'disabled'}>Assign to ${n||''}</button></div>`}
function rxPick(){
 const list=rxList(),total=(RXS.bank||[]).length,ps=rxPresets();
 return `<section class=rx-pick><div class=rx-top><input type=search data-rxq placeholder="Search ${total} emoji" value="${esc(RXQ.q)}" aria-label="Search the emoji bank">`+
  `<label class=rx-pre><span class=mut>Holding</span><select data-rxf aria-label="Show the emojis holding a preset"><option value="">any preset</option>${ps.map(p=>`<option value="${esc(p.id)}"${p.id===RXQ.f?' selected':''}>${esc(p.id)}</option>`).join('')}</select></label>`+
  `<span class=sp></span><button class="btn sm${RXS.multi?' pri':''}" data-act=rxmulti aria-pressed=${RXS.multi}>${ic('check')} Select</button></div>`+
  `<div class=rx-grid data-rxwall>${list.slice(0,RXS.shown).map(rxTile).join('')||'<span class=mut>No match.</span>'}</div>${rxMoreHtml(list.length)}${rxMany()}</section>`}
function rxHtml(){
 if(!RXS.bank)return `<div class="page rx"><div class=fx-job><span class=spin></span> <span class=mut>Reading the emoji bank…</span></div></div>`;
 return `<div class="page rx">${rxLibHtml()}${rxEditor()}${rxPick()}</div>`}

/* ---------- page updates: repaint only what changed ---------- */
function rxDraw(){
 const el=$('s-reactions');if(!el)return;
 const q=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.rxq!==undefined,
  w=el.querySelector&&el.querySelector('[data-rxwall]'),top=w?w.scrollTop:0;
 el.innerHTML=rxHtml();
 const w2=el.querySelector&&el.querySelector('[data-rxwall]');if(w2)w2.scrollTop=top;
 if(q){const i=el.querySelector('[data-rxq]');if(i){i.focus();try{i.setSelectionRange(i.value.length,i.value.length)}catch(e){}}}
 rxCardPreviews()}
const rxSwap=(sel,html)=>{const el=document.querySelector&&document.querySelector(sel);if(el)el.outerHTML=html;else rxDraw()};
function rxGridRedraw(){const w=document.querySelector&&document.querySelector('[data-rxwall]');if(!w)return;const list=rxList();
 w.innerHTML=list.slice(0,RXS.shown).map(rxTile).join('')||'<span class=mut>No match.</span>';rxSwap('[data-rxmore]',rxMoreHtml(list.length))}
function rxTileRedraw(t){const el=document.querySelector&&document.querySelector(`.rx-e[data-t="${t}"]`);if(el)el.outerHTML=rxTile(rxRow(t))}
function rxManyRedraw(){rxSwap('[data-rxmany]',rxMany())}
function rxEdRedraw(){if(RXS.ek)rxSwap('[data-rxed]',rxEditor());else rxDraw()}
function rxEdSync(){
 const k=RXS.ek,el=document.querySelector&&document.querySelector('[data-rxed]');if(!k||!el)return rxDraw();
 const st=el.querySelector('[data-rxstage]');if(st)st.innerHTML=rxStage(k);
 el.querySelectorAll('[data-rxo]').forEach(i=>{
  const o=rxOpt(i.dataset.rxo);if(!o||i===document.activeElement)return;
  const v=rxVal(k,o);if(v!=null)i.value=v;const out=i.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,v)})}

/* ---------- the server ---------- */
/* the editor's preview (the plain framing), or a hovered emoji's (fit) */
async function rxPlay(t){
 const ed=()=>RXS.ek&&RXS.ek.token===t;
 if(!ed()){if(await rxHovPreview(t)&&RXS.hover===t)rxTileRedraw(t);return}
 const b=rxBody(RXS.ek),key=rxKey(b);
 if(!RXS.pv[key]){
  const r=await post('/api/particles/emoji-preview',{...b,size:RXPX});
  if(!r.ok){if(ed()){RXS.ek.err=r.j.error||'The preview could not be made.';rxEdRedraw()}return}
  RXS.pv[key]=r.j.url;RXS.par[key]=r.j.params}
 if(ed()&&key===rxKey(rxBody(RXS.ek))){RXS.ek.own=RXS.par[key];RXS.ek.shown=RXS.pv[key];RXS.ek.err='';rxEdSync()}}
/* ---------- the same hover reaction anywhere else (a pack's sticker plays its emoji's preset when pointed at, the SAME effect as the wall) ---------- */
async function rxHovPreview(t){const key=rxHovKey(t);
 if(!RXS.pv[key]){const r=await post('/api/particles/emoji-preview',{...rxFor(t),size:RXPX,fit:true});if(!r.ok)return null;RXS.pv[key]=r.j.url;RXS.par[key]=r.j.params}
 return{url:RXS.pv[key],par:RXS.par[key]}}
async function rxBankEnsure(){
 if(!RXS.bank){const b=await api('/api/particles/emoji-motions');if(b.ok){RXS.bank=b.j.motions||[];RXS.rows=null;if(b.j.start)RXS.start=b.j.start}}
 if(!RXS.lib)await rxLoadLib(true);
 return RXS.bank||[]}
/* the bank emoji a sticker's emoji starts with (the longest match: 🧡 before ❤); '' when it is not a predefined emoji */
function rxTokenOf(glyph){const g=String(glyph||'').replace(/️/g,'');let best=null;
 if(g)for(const m of RXS.bank||[]){const e=String(m.emoji||'').replace(/️/g,'');if(e&&g.startsWith(e)&&(!best||e.length>best.e.length))best={t:m.token,e}}
 return best?best.t:''}
async function rxFxOn(host,glyph){host.dataset.rxon='1';await rxBankEnsure();const t=rxTokenOf(glyph);if(!t)return;
 const pv=await rxHovPreview(t);if(!pv||host.dataset.rxon!=='1')return;
 const old=host.querySelector(':scope > .rx-fx');if(old)old.remove();
 host.classList.add('rxon');host.insertAdjacentHTML('beforeend',`<img class=rx-fx src="${esc(pv.url)}" style="${rxFxStyle(pv.par)}" alt="">`)}
function rxFxOff(host){host.dataset.rxon='';host.classList.remove('rxon');const i=host.querySelector(':scope > .rx-fx');if(i)i.remove()}
async function rxLoadLib(quiet){const r=await api('/api/particles/reaction-presets');RXS.lib=r.ok?{presets:r.j.presets||[],assign:r.j.assign||{}}:{presets:[],assign:{}};if(!quiet&&route_==='reactions')rxDraw()}
/* each card shows its preset on the sample emoji, at its real size */
async function rxCardPreviews(){
 const t=RXS.sample;
 for(const p of rxPresets()){
  const k=p.id+'|'+t;if(RXS.ppv[k]!==undefined)continue;RXS.ppv[k]='';
  const r=await post('/api/particles/emoji-preview',{...rxBodyOf(t,p.settings,p.motion),size:RXPX});
  RXS.ppv[k]=r.ok?r.j.url:'';
  if(r.ok&&route_==='reactions'&&RXS.sample===t){const el=document.querySelector&&document.querySelector(`[data-rxcard="${p.id}"]`);if(el)el.outerHTML=rxCard(p,rxUse()[p.id])}}}
RENDER.reactions=async()=>{rxDraw();if(!RXS.bank||!RXS.lib){await rxBankEnsure();if(route_==='reactions')rxDraw()}};

/* ---------- events ---------- */
document.addEventListener('input',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxq!==undefined){RXQ.q=t.value;RXS.shown=RXPAGE;clearTimeout(RXS.t);RXS.t=setTimeout(rxGridRedraw,150);return}
 if(!t.dataset.rxo||!RXS.ek)return;
 const o=rxOpt(t.dataset.rxo);if(rxIsSim(o[0]))RXS.ek.sim[o[0]]=+t.value;else RXS.ek[o[0]]=+t.value;
 const out=t.parentNode&&t.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,t.value);
 clearTimeout(RXS.t);const tok=RXS.ek.token;RXS.t=setTimeout(()=>rxPlay(tok),300)});
document.addEventListener('change',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxapply!==undefined){RXS.apply=t.value||'random';return}
 if(t.dataset.rxf!==undefined){RXQ.f=t.value||'';RXS.shown=RXPAGE;rxGridRedraw();rxManyRedraw()}});
document.addEventListener('mouseover',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||route_!=='reactions')return;
 const t=b.dataset.t;if(RXS.hover===t)return;
 const was=RXS.hover;RXS.hover=t;if(was&&was!==t)rxTileRedraw(was);
 clearTimeout(RXS.hT);RXS.hT=setTimeout(()=>{if(RXS.hover===t)rxPlay(t)},220)});
document.addEventListener('mouseout',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||(ev.relatedTarget&&b.contains(ev.relatedTarget)))return;
 const t=b.dataset.t;if(RXS.hover!==t)return;RXS.hover='';clearTimeout(RXS.hT);rxTileRedraw(t)});

/* ---------- actions ---------- */
/* a click previews the presets on this emoji and opens the preset it holds; with Select on it ticks it (Shift: the whole range from the last tick) */
ACT.rxpick=(el,ev)=>{
 const t=el.dataset.t;
 if(RXS.multi){
  if(ev&&ev.shiftKey&&RXS.anchor&&RXS.anchor!==t){const ts=rxList().map(m=>m.token),a=ts.indexOf(RXS.anchor),b=ts.indexOf(t);
   if(a>=0&&b>=0){ts.slice(Math.min(a,b),Math.max(a,b)+1).forEach(x=>RXS.sel.add(x));RXS.anchor=t;rxGridRedraw();rxManyRedraw();return}}
  if(RXS.sel.has(t))RXS.sel.delete(t);else RXS.sel.add(t);RXS.anchor=t;rxTileRedraw(t);rxManyRedraw();return}
 RXS.sample=t;RXS.ek=rxEdFrom(rxPre(rxPresetOf(t)),t);RXS.hover='';rxDraw();rxPlay(t)};
ACT.rxmore=()=>{const list=rxList(),from=RXS.shown;RXS.shown+=RXPAGE;
 const w=document.querySelector&&document.querySelector('[data-rxwall]');if(w)w.insertAdjacentHTML('beforeend',list.slice(from,RXS.shown).map(rxTile).join(''));
 rxSwap('[data-rxmore]',rxMoreHtml(list.length))};
ACT.rxmulti=()=>{RXS.multi=!RXS.multi;RXS.sel.clear();RXS.anchor='';rxDraw()};
ACT.rxselall=()=>{rxList().forEach(m=>RXS.sel.add(m.token));rxGridRedraw();rxManyRedraw()};
ACT.rxclear=()=>{RXS.sel.clear();RXS.anchor='';rxDraw()};
/* Assign: the ticked emojis get one preset, or a random variation of each one's own motion (instant: nothing is rendered) */
ACT.rxmany=async()=>{
 const tokens=[...RXS.sel];if(!tokens.length)return;
 const r=await post('/api/particles/reaction-presets/assign',{tokens,preset_id:RXS.apply||'random'});
 if(!r.ok)return toast(r.j.error||'Could not assign',1);
 await rxLoadLib(true);RXS.sel.clear();RXS.multi=false;rxDraw();
 toast(`${rxPlural(r.j.assigned,'emoji')} now hold ${RXS.apply==='random'?'a variation of their own motion':RXS.apply}`)};
/* the library */
ACT.rxpopen=el=>{const p=rxPre(el.dataset.id);if(!p)return;RXS.ek=rxEdFrom(p,RXS.sample);rxDraw();rxPlay(RXS.sample);
 const ed=document.querySelector&&document.querySelector('[data-rxed]');if(ed&&ed.scrollIntoView)ed.scrollIntoView({block:'nearest',behavior:'smooth'})};
ACT.rxpadd=el=>{const mo=el.dataset.m,first=rxPresets().find(p=>p.motion===mo);
 RXS.ek={...rxEdFrom(first,RXS.sample,mo),id:'',name:''};rxDraw();rxPlay(RXS.sample)};
ACT.rxsave=async()=>{
 const k=RXS.ek;if(!k||!k.id||k.busy)return;k.busy=true;rxEdRedraw();
 const r=await post(`/api/particles/reaction-presets/${encodeURIComponent(k.id)}`,{settings:rxSettings(k)});k.busy=false;
 if(!r.ok){k.err=r.j.error||'Could not save it';return rxEdRedraw()}
 await rxLoadLib(true);Object.keys(RXS.ppv).filter(x=>x.startsWith(k.id+'|')).forEach(x=>delete RXS.ppv[x]);rxDraw();toast(`${k.id} saved`)};
ACT.rxcreate=async()=>{
 const k=RXS.ek;if(!k||k.busy)return;k.busy=true;rxEdRedraw();
 const r=await post('/api/particles/reaction-presets',{motion:k.motion,settings:rxSettings(k)});k.busy=false;
 if(!r.ok){k.err=r.j.error||'Could not add the variation';return rxEdRedraw()}
 await rxLoadLib(true);RXS.ek={...k,id:r.j.id,name:r.j.name};rxDraw();toast(`${r.j.id} added`)};
ACT.rxpdel=async el=>{
 const id=el.dataset.id;
 const r=await post(`/api/particles/reaction-presets/${encodeURIComponent(id)}/delete`,{});if(!r.ok)return toast(r.j.error||'Could not remove it',1);
 if(RXS.ek&&RXS.ek.id===id)RXS.ek=null;if(RXQ.f===id)RXQ.f='';if(RXS.apply===id)RXS.apply='random';
 await rxLoadLib(true);rxDraw();toast(`${id} removed${r.j.unassigned?`; ${rxPlural(r.j.unassigned,'emoji')} went back to their motion's first variation`:''}`)};
ACT.rxclose=()=>{RXS.ek=null;rxDraw()};
ACT.rxreset=el=>{const k=RXS.ek;if(!k)return;const s=rxEdFrom(null,k.token,k.motion);if(el.dataset.g==='sim')k.sim=s.sim;else RXO.forEach(o=>k[o[0]]=s[o[0]]);rxEdRedraw();rxPlay(k.token)};
const rxSave=(href,name)=>{const a=document.createElement('a');a.href=href;a.download=name;document.body.appendChild(a);a.click();a.remove()};
ACT.rxdl=el=>rxSave(`/api/particles/reaction-presets/${encodeURIComponent(el.dataset.id)}.json`,`${el.dataset.id}.json`);
ACT.rxzip=()=>rxSave('/api/particles/reaction-presets.zip','reaction-presets.zip');
