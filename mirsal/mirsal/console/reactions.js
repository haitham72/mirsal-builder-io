/* Reaction effects (#/reactions, Create > + New): the emoji bank ONLY. docs/reaction.md section 13, docs/design.md section 4 (Create's tabs).
   Its own screen and state (prefix rx); it shares nothing with effects.js / particles.js (the Studio's pack particles keep #/effects).
   Top to bottom: search + two rows of small emojis (pointing at one plays its reaction from its right edge, Telegram-like) -> the picked emoji in ONE
   editor card (Simulation: how they move; Shape: how each emoji looks; Create reaction | Save preset) -> Your reactions: only what was created, one card each.
   Select several: ticks emojis instead of opening one, then one bar applies each emoji's own look or a saved preset to all of them (one request).
   Everything is the server's (flow/emoji_reactions.py): GET /api/particles/emoji-motions (the bank), POST /api/particles/emoji-preview (a looping WebP),
   POST /api/particles/emoji-lottie (create: the Lottie + its loop), GET /api/particles/emoji-lottie (the created), /api/particles/emoji-presets (Save preset, list,
   delete), POST /api/particles/emoji-lottie/batch (many emojis, one preset). Nothing is decided in the browser. */
'use strict';

/* ---------- settings: [key, label, min, max, step, unit] ---------- */
const RXPRESETS=['burst','fountain','vortex','rain','confetti'];
const RXSIM=[['magnitude','Speed',0,3,.05,'×'],['gravity','Gravity',-2,3,.05,''],['vortex','Swirl',-2,2,.05,''],['spin','Rotation',0,3,.05,'×'],['count','Amount',4,80,1,''],['spread','Spread',10,360,5,'°']];
const RXO=[['particle_size','Size',.25,3,.05,'×'],['size_var','Size variation',0,1,.05,'%'],['size_in_dur','Size in',0,1.5,.05,'s'],['size_out_dur','Size out',0,1.5,.05,'s'],['hue_var','Hue',0,180,5,'°']];
const RXD={particle_size:1,size_var:null,size_in_dur:.4,size_out_dur:.4,hue_var:25};   /* Shape's defaults; size_var null = the motion's own range */
const RXPX=256;                                  /* a reaction loop's side: sharp at the 220 CSS px it is shown at */
const RXN=48;                                    /* tiles drawn; rxClip shows exactly two rows of them, whatever the width */
const RXHOV=64;                                  /* the hover reaction's side: 60% smaller than the 160 px it was (Haitham, 2026-10-13) */
const RXMANY=24;                                 /* emojis per Create (the server's MANY_MAX) */

/* ---------- state ----------
   bank: the emoji bank (server); made: the created reactions (server); ek: the picked emoji in the editor; hover: the emoji pointed at;
   pv / par: preview url and params per request (the server caches the files too); q: the search;
   multi: Select several is on; sel: the ticked emojis; presets: the saved presets (server); apply: the preset the bar applies ('' = each emoji's own). */
const RXQ={q:''};
const RXS={bank:null,made:null,ek:null,hover:'',pv:{},par:{},hT:0,t:0,multi:false,sel:new Set(),presets:null,apply:'',busyMany:false};
/* one picked emoji: its motion override, the Simulation keys the person moved (sim), the Shape values, and the server's last answer (own) */
const rxNew=(t,par)=>({token:t,preset:'',sim:{},...RXD,...(par||{}),own:null,shown:'',err:'',busy:false});

/* ---------- values ---------- */
const rxOpt=key=>RXSIM.find(o=>o[0]===key)||RXO.find(o=>o[0]===key);
const rxIsSim=key=>RXSIM.some(o=>o[0]===key);
const rxRow=t=>(RXS.bank||[]).find(m=>m.token===t)||{token:t,emoji:'',preset:'',motion:''};
function rxList(){
 const bank=RXS.bank||[],q=RXQ.q.trim().toLowerCase();
 return (q?bank.filter(m=>(m.token+' '+m.emoji+' '+(m.motion||'')).toLowerCase().includes(q)):bank).slice(0,RXN)}
/* the request: only the Simulation keys that were moved, the Shape values, size_var only once moved, the motion only when overridden */
function rxBody(k){
 const sim=Object.fromEntries(Object.entries(k.sim||{}).map(([a,v])=>[a,+v]));
 return {token:k.token,...sim,particle_size:+k.particle_size,...(k.size_var!=null?{size_var:+k.size_var}:{}),
  size_in_dur:+k.size_in_dur,size_out_dur:+k.size_out_dur,hue_var:+k.hue_var,...(k.preset?{preset:k.preset}:{})}}
const rxKey=b=>JSON.stringify(b);
const rxSettings=k=>{const b=rxBody(k);delete b.token;return b};
const rxFor=t=>RXS.ek&&RXS.ek.token===t?rxBody(RXS.ek):rxBody(rxNew(t));
/* a motion's own size variation, from its size range */
const rxOwnVar=p=>p&&p.size_max+p.size_min>0?Math.round((p.size_max-p.size_min)/(p.size_max+p.size_min)*1e4)/1e4:.35;
/* what a slider shows: what the person set, else what the motion has; null = not known until the server answers */
function rxVal(k,o){
 const key=o[0];
 if(rxIsSim(key))return k.sim[key]!=null?k.sim[key]:k.own&&k.own[key]!=null?k.own[key]:null;
 if(key==='size_var'&&k.size_var==null)return k.own?rxOwnVar(k.own):null;
 return k[key]}
const rxFmt=(o,v)=>v==null?'…':o[5]==='%'?Math.round(v*100)+'%':o[5]==='×'?'×'+(+v):(+v)+o[5];
function rxAgo(ts){
 const s=Math.max(0,Date.now()/1000-(+ts||0));
 if(!ts)return '';if(s<60)return 'just now';if(s<3600)return Math.floor(s/60)+' min ago';if(s<86400)return Math.floor(s/3600)+' h ago';
 return new Date(ts*1000).toLocaleDateString()}

/* ---------- views ---------- */
/* the hover reaction leaves from the tile's right edge, like Telegram's: the burst's own origin (a fountain starts low, rain at the top) sits on that edge */
function rxFxStyle(par){const [ox,oy]=(par&&par.origin)||[.5,.5];return `width:${RXHOV}px;height:${RXHOV}px;left:calc(100% - ${Math.round(ox*RXHOV)}px);top:calc(50% - ${Math.round(oy*RXHOV)}px)`}
/* the hover's own preview: the whole burst scaled into its square (fit), never cut at its edges (Haitham, 2026-10-14) */
const rxHovKey=t=>rxKey(rxFor(t))+'|fit';
function rxTile(m){
 const key=rxHovKey(m.token),ticked=RXS.multi&&RXS.sel.has(m.token),on=!RXS.multi&&!!RXS.ek&&RXS.ek.token===m.token;
 const pv=RXS.hover===m.token&&!on?RXS.pv[key]:'';
 return `<button class="rx-e${on||ticked?' on':''}${pv?' play':''}" data-act=rxpick data-t="${esc(m.token)}" title="${esc(m.token)}" aria-label="${esc(m.token)}" aria-pressed=${on||ticked}>`+
  `<span class=rx-g>${esc(m.emoji||'?')}</span>${ticked?`<span class=rx-tick>${ic('check')}</span>`:''}${pv?`<img class=rx-fx src="${esc(pv)}" style="${rxFxStyle(RXS.par[key])}" alt="">`:''}</button>`}
function rxPick(){
 const list=rxList();
 return `<section class=rx-pick><div class=rx-top><input type=search data-rxq placeholder="Search ${(RXS.bank||[]).length} emoji" value="${esc(RXQ.q)}" aria-label="Search the emoji bank">`+
  `<button class="btn sm${RXS.multi?' pri':''}" data-act=rxmulti aria-pressed=${RXS.multi}>${ic('check')} Select several</button>`+
  `<small class=mut>${RXS.multi?'Tick emojis, then create them all with one look.':'Pick an emoji: it flies as itself.'}</small></div>`+
  `<div class=rx-grid data-rxwall>${list.map(rxTile).join('')||'<span class=mut>No match.</span>'}</div>${rxMany()}</section>`}
/* Select several: the ticked emojis and one look for all of them (each emoji's own, or a saved preset) */
function rxMany(){
 if(!RXS.multi)return '';
 const n=RXS.sel.size,ps=RXS.presets||[],cur=ps.find(p=>p.id===RXS.apply);
 const glyphs=[...RXS.sel].map(t=>esc(rxRow(t).emoji)).join('');
 return `<div class=rx-many data-rxmany><span class=rx-many-sel>${n?`<b>${n}</b> <span class=rx-many-g>${glyphs}</span>`:'<span class=mut>Nothing ticked yet</span>'}</span>`+
  `<label class=rx-pre><span class=mut>Look</span><select data-rxapply aria-label="Look for the ticked emojis"><option value=""${RXS.apply?'':' selected'}>Each emoji's own</option>`+
  `${ps.map(p=>`<option value="${esc(p.id)}"${p.id===RXS.apply?' selected':''}>${esc(p.name)}</option>`).join('')}</select></label>`+
  `${cur?`<button class=link data-act=rxpdel data-id="${esc(cur.id)}">Delete ${esc(cur.name)}</button>`:''}`+
  `<button class="btn pri" data-act=rxmany ${n&&!RXS.busyMany?'':'disabled'}>${RXS.busyMany?'<span class=spin></span> Creating…':`Create ${n||''} reaction${n===1?'':'s'}`}</button>`+
  `${n?'<button class=link data-act=rxclear>Clear</button>':''}</div>`}
/* a stage: the emoji, faint, at the centre (a loop starts and ends empty) and its reaction looping over it */
const rxStageHtml=(emoji,url,alt)=>`<span class=rx-ghost aria-hidden=true>${esc(emoji)}</span>${url?`<img src="${esc(url)}" alt="${esc(alt)}" loading=lazy>`:''}`;
function rxStage(k){const url=RXS.pv[rxKey(rxBody(k))]||k.shown;return rxStageHtml(rxRow(k.token).emoji,url,k.token+' reaction')+(url||k.err?'':'<span class=spin></span>')}
function rxSlider(k,o){
 const v=rxVal(k,o);
 return `<label class=rx-sl><span class=mut>${o[1]}</span><input type=range min=${o[2]} max=${o[3]} step=${o[4]} value="${v??(o[2]+o[3])/2}" data-rxo=${o[0]} aria-label="${o[1]}"><output>${rxFmt(o,v)}</output></label>`}
function rxMotion(k,m){
 return `<label class=rx-sl><span class=mut>Motion</span><select data-rxpre aria-label="Motion"><option value=""${k.preset?'':' selected'}>its own · ${esc(m.preset||'')}</option>`+
  `${RXPRESETS.map(n=>`<option value=${n}${k.preset===n?' selected':''}>${n}</option>`).join('')}</select></label>`}
function rxGroup(title,g,resettable,body){
 return `<div class=rx-grp><div class=rx-gh><b>${title}</b><button class=link data-act=rxreset data-g=${g} ${resettable?'':'disabled'}>Reset</button></div>${body}</div>`}
function rxEditor(){
 const k=RXS.ek;if(!k)return '';const m=rxRow(k.token);
 return `<section class=rx-ed data-rxed><div class=rx-stage data-rxstage>${rxStage(k)}</div><div class=rx-ctl>
  <div class=rx-h><span class=rx-g>${esc(m.emoji)}</span><b>${esc(m.token)}</b><button class=link data-act=rxclose aria-label="Close">${ic('x')}</button></div>
  ${m.motion?`<small class=mut>${esc(m.motion)}</small>`:''}
  <div class=rx-groups>
   ${rxGroup('Simulation','sim',!!Object.keys(k.sim).length||!!k.preset,rxMotion(k,m)+RXSIM.map(o=>rxSlider(k,o)).join(''))}
   ${rxGroup('Shape','shape',true,RXO.map(o=>rxSlider(k,o)).join('')+'<small class=mut>Hue 0 keeps the emoji\'s own colours.</small>')}
  </div>${k.err?`<span class=fx-warn>${esc(k.err)}</span>`:''}
  <div class=rx-foot><button class="btn pri" data-act=rxcreate ${k.busy?'disabled':''}>${k.busy?'<span class=spin></span> Creating…':'Create reaction'}</button>`+
  `<button class=btn data-act=rxsave title="Keep these settings to apply them to many emojis (Select several)">Save preset</button></div></div></section>`}
function rxCard(r){
 return `<article class=rx-card title="${esc(r.id||'')}"><div class=rx-stage>${rxStageHtml(r.emoji,r.preview,r.token+' reaction')}</div>
  <div class=rx-meta><span class=rx-g>${esc(r.emoji)}</span><span class=rx-mt><b>${esc(r.token)}</b><small class=mut>${esc(r.preset||'')}${r.created?' · '+esc(rxAgo(r.created)):''}</small></span></div>
  <div class=rx-acts><button class="btn sm pri" data-act=rxdl data-u="${esc(r.url)}" data-n="${esc(r.token+' '+r.id)}">${ic('download')} Lottie</button>`+
  `<button class="btn sm" data-act=rxedit data-t="${esc(r.token)}" data-id="${esc(r.id)}">Edit</button></div></article>`}
function rxMade(){
 const m=RXS.made;
 if(m===null)return `<section class=rx-made><div class=sh>Your reactions</div><span class=spin></span></section>`;
 return `<section class=rx-made><div class=sh>Your reactions <small class=mut>${m.length||''}</small></div>`+
  `${m.length?`<div class=rx-cards>${m.map(rxCard).join('')}</div>`:'<div class=mut>Nothing created yet: pick an emoji above.</div>'}</section>`}
function rxHtml(){
 if(!RXS.bank)return `<div class="page rx"><div class=fx-job><span class=spin></span> <span class=mut>Reading the emoji bank…</span></div></div>`;
 return `<div class="page rx">${rxPick()}${rxEditor()}${rxMade()}</div>`}

/* ---------- page updates: repaint only what changed, so the search box, a dragged slider and the rest of the page never move ---------- */
function rxDraw(){
 const el=$('s-reactions');if(!el)return;
 const q=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.rxq!==undefined;
 el.innerHTML=rxHtml();rxClip();
 if(q){const i=el.querySelector('[data-rxq]');if(i){i.focus();try{i.setSelectionRange(i.value.length,i.value.length)}catch(e){}}}}
/* two rows only: the grid counts its own columns and every tile past the second row is hidden (a search narrows the rows instead) */
function rxClip(){
 const w=document.querySelector&&document.querySelector('[data-rxwall]');if(!w||!w.children)return;
 const cols=Math.max(1,String(getComputedStyle(w).gridTemplateColumns||'').split(' ').filter(Boolean).length);
 [...w.children].forEach((el,i)=>{el.style.display=i<2*cols?'':'none'})}
function rxGridRedraw(){const w=document.querySelector&&document.querySelector('[data-rxwall]');if(!w)return;w.innerHTML=rxList().map(rxTile).join('')||'<span class=mut>No match.</span>';rxClip()}
function rxTileRedraw(t){
 const el=document.querySelector&&document.querySelector(`.rx-e[data-t="${t}"]`);if(!el)return;
 const shown=el.style.display;el.outerHTML=rxTile(rxRow(t));
 const nu=document.querySelector(`.rx-e[data-t="${t}"]`);if(nu)nu.style.display=shown}
function rxManyRedraw(){const el=document.querySelector&&document.querySelector('[data-rxmany]');if(el)el.outerHTML=rxMany()}
function rxEdRedraw(){const el=document.querySelector&&document.querySelector('[data-rxed]');if(el&&RXS.ek)el.outerHTML=rxEditor();else rxDraw()}
/* a preview answer: swap the picture and the values nobody is touching; the slider being dragged stays as it is */
function rxEdSync(){
 const k=RXS.ek,el=document.querySelector&&document.querySelector('[data-rxed]');if(!k||!el)return rxDraw();
 const st=el.querySelector('[data-rxstage]');if(st)st.innerHTML=rxStage(k);
 el.querySelectorAll('[data-rxo]').forEach(i=>{
  const o=rxOpt(i.dataset.rxo);if(!o||i===document.activeElement)return;
  const v=rxVal(k,o);if(v!=null)i.value=v;const out=i.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,v)});
 const r=el.querySelector('[data-act=rxreset][data-g=sim]');if(r)r.disabled=!Object.keys(k.sim).length&&!k.preset}

/* ---------- the server ---------- */
async function rxPlay(t){
 const b=rxFor(t),ed=()=>RXS.ek&&RXS.ek.token===t,fit=!ed(),key=fit?rxHovKey(t):rxKey(b);
 if(!RXS.pv[key]){
  const r=await post('/api/particles/emoji-preview',{...b,size:RXPX,...(fit?{fit:true}:{})});
  if(!r.ok){if(ed()){RXS.ek.err=r.j.error||'The reaction could not be made.';rxEdRedraw()}return}
  RXS.pv[key]=r.j.url;RXS.par[key]=r.j.params}
 if(ed()){if(fit||key!==rxKey(rxBody(RXS.ek)))return;RXS.ek.own=RXS.par[key];RXS.ek.shown=RXS.pv[key];RXS.ek.err='';rxEdSync()}     /* an older answer than the sliders: ignored */
 else if(RXS.hover===t)rxTileRedraw(t)}
async function rxLoadMade(){const r=await api('/api/particles/emoji-lottie');RXS.made=r.ok?(r.j.reactions||[]):[];if(route_==='reactions')rxDraw()}
async function rxLoadPresets(){const r=await api('/api/particles/emoji-presets');RXS.presets=r.ok?(r.j.presets||[]):[];if(route_==='reactions')rxManyRedraw()}
/* the newest created first */
function rxAddMade(rs){RXS.made=[...rs.map(r=>({id:r.id,token:r.token,emoji:r.emoji,preset:r.preset,params:r.params,url:r.url,preview:r.preview,bytes:r.bytes,created:Date.now()/1000})).reverse(),...(RXS.made||[])]}
RENDER.reactions=async()=>{
 rxDraw();if(RXS.made===null)rxLoadMade();if(RXS.presets===null)rxLoadPresets();
 if(!RXS.bank){const b=await api('/api/particles/emoji-motions');if(b.ok){RXS.bank=b.j.motions||[];if(route_==='reactions')rxDraw()}}};

/* ---------- events ---------- */
document.addEventListener('input',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxq!==undefined){RXQ.q=t.value;clearTimeout(RXS.t);RXS.t=setTimeout(rxGridRedraw,150);return}
 if(!t.dataset.rxo||!RXS.ek)return;
 const o=rxOpt(t.dataset.rxo);if(rxIsSim(o[0]))RXS.ek.sim[o[0]]=+t.value;else RXS.ek[o[0]]=+t.value;
 const out=t.parentNode&&t.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,t.value);
 clearTimeout(RXS.t);const tok=RXS.ek.token;RXS.t=setTimeout(()=>rxPlay(tok),300)});
/* another motion: its own simulation, not the old one's tweaks */
document.addEventListener('change',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxapply!==undefined){RXS.apply=t.value||'';rxManyRedraw();return}
 if(t.dataset.rxpre===undefined||!RXS.ek)return;RXS.ek.preset=t.value||'';RXS.ek.sim={};rxPlay(RXS.ek.token)});
/* pointing at an emoji plays its reaction over it, after a short pause, so sweeping across the rows asks for nothing */
document.addEventListener('mouseover',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||route_!=='reactions')return;
 const t=b.dataset.t;if(RXS.hover===t)return;
 const was=RXS.hover;RXS.hover=t;if(was&&was!==t)rxTileRedraw(was);
 clearTimeout(RXS.hT);RXS.hT=setTimeout(()=>{if(RXS.hover===t)rxPlay(t)},220)});
document.addEventListener('mouseout',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||(ev.relatedTarget&&b.contains(ev.relatedTarget)))return;
 const t=b.dataset.t;if(RXS.hover!==t)return;RXS.hover='';clearTimeout(RXS.hT);rxTileRedraw(t)});
if(typeof window!=='undefined'&&window.addEventListener)window.addEventListener('resize',()=>{if(route_==='reactions')rxClip()});

/* ---------- actions ---------- */
/* a click opens the emoji in the editor; with Select several on it ticks it instead */
ACT.rxpick=el=>{
 const t=el.dataset.t;
 if(RXS.multi){if(RXS.sel.has(t))RXS.sel.delete(t);else{if(RXS.sel.size>=RXMANY)return toast(`At most ${RXMANY} at once`,1);RXS.sel.add(t)}rxTileRedraw(t);rxManyRedraw();return}
 if(RXS.ek&&RXS.ek.token===t)return;RXS.ek=rxNew(t);RXS.hover='';rxDraw();rxPlay(t)};
ACT.rxmulti=()=>{RXS.multi=!RXS.multi;RXS.sel.clear();if(RXS.multi)RXS.ek=null;rxDraw()};
ACT.rxclear=()=>{RXS.sel.clear();rxDraw()};
ACT.rxmany=async el=>{
 const tokens=[...RXS.sel];if(!tokens.length||RXS.busyMany)return;RXS.busyMany=true;rxManyRedraw();
 const r=await post('/api/particles/emoji-lottie/batch',{tokens,...(RXS.apply?{preset_id:RXS.apply}:{})});RXS.busyMany=false;
 if(!r.ok){rxManyRedraw();return toast(r.j.error||'Could not create them',1)}
 rxAddMade(r.j.reactions||[]);RXS.sel.clear();rxDraw();
 const bad=r.j.errors||[];toast(`${(r.j.reactions||[]).length} reaction${(r.j.reactions||[]).length===1?'':'s'} created`+(bad.length?`; ${bad.length} could not be made (${bad.map(e=>e.token).join(', ')})`:''),bad.length?1:0)};
/* Save preset: the editor's settings, kept on the server as the next Preset NN */
ACT.rxsave=async()=>{
 const k=RXS.ek;if(!k)return;
 const r=await post('/api/particles/emoji-presets',{settings:rxSettings(k)});
 if(!r.ok)return toast(r.j.error||'Could not save the preset',1);
 RXS.presets=[...(RXS.presets||[]),r.j];toast(`Saved as ${r.j.name}: use it with Select several`)};
ACT.rxpdel=async el=>{
 const r=await post(`/api/particles/emoji-presets/${el.dataset.id}/delete`,{});if(!r.ok)return toast(r.j.error||'Could not delete it',1);
 RXS.presets=r.j.presets||[];RXS.apply='';rxManyRedraw()};
ACT.rxclose=()=>{RXS.ek=null;rxDraw()};
ACT.rxreset=el=>{const k=RXS.ek;if(!k)return;if(el.dataset.g==='sim'){k.sim={};k.preset=''}else Object.assign(k,RXD);rxEdRedraw();rxPlay(k.token)};
/* Edit: the editor again, with that reaction's motion, simulation and shape */
ACT.rxedit=el=>{
 const r=(RXS.made||[]).find(x=>x.token===el.dataset.t&&x.id===el.dataset.id);if(!r)return;
 const p=r.params||{},m=rxRow(r.token);
 RXS.ek=rxNew(r.token,{preset:r.preset&&r.preset!==m.preset?r.preset:'',sim:Object.fromEntries(RXSIM.map(o=>[o[0],p[o[0]]]).filter(([,v])=>v!=null)),
  particle_size:p.particle_size??1,size_var:p.size_max!=null?rxOwnVar(p):null,size_in_dur:p.size_in_dur??RXD.size_in_dur,size_out_dur:p.size_out_dur??RXD.size_out_dur,hue_var:p.hue_var??RXD.hue_var});
 rxDraw();rxPlay(r.token);
 const ed=document.querySelector&&document.querySelector('[data-rxed]');if(ed&&ed.scrollIntoView)ed.scrollIntoView({block:'nearest',behavior:'smooth'})};
ACT.rxdl=el=>{const a=document.createElement('a');a.href=el.dataset.u;a.download=`${el.dataset.n}.lottie.json`;document.body.appendChild(a);a.click();a.remove()};
ACT.rxcreate=async()=>{
 const k=RXS.ek;if(!k||k.busy)return;k.busy=true;rxEdRedraw();
 const r=await post('/api/particles/emoji-lottie',rxBody(k));k.busy=false;
 if(!r.ok){k.err=r.j.error||'Could not create the reaction';return rxEdRedraw()}
 rxAddMade([r.j]);
 RXS.ek=null;rxDraw();toast(`${r.j.emoji} ${r.j.token} created: download its Lottie from its card`)};
