/* Reaction effects (#/reactions, Create > + New): the emoji bank ONLY. docs/reaction.md section 13, docs/design.md section 4 (Create's tabs).
   Its own screen and state (prefix rx); it shares nothing with effects.js / particles.js (the Studio's pack particles keep #/effects).
   Goal (Haitham, 2026-10-14): every one of the ~1800 bank emojis done. Top to bottom:
   - the WALL: every emoji (it scrolls), search, All | Done | Not done, "N/1800 done", Select (click ticks, Shift-click ticks the range), Export All | Selected;
     pointing at an emoji plays its reaction from its right edge (Telegram-like), the newest saved one when it has one;
   - the EDITOR: clicking an emoji opens its NEWEST SAVED reaction (Saved: v... to look at the others), else the start look (GET emoji-motions `start`);
     Create reaction (left) saves a new version; Presets (right): Save as new, Update the loaded one, Load, Remove;
   - ANIMATION PRESETS: the saved presets filed by motion, each with its preview: Open (to change and Update it), Apply to the selected, ×; and
     "random preset of each emoji's own motion" for Selected | Not done | All. Many emojis run in the background on the server (emoji-batches):
     a progress line, ticks appear as they are made, Cancel.
   Everything is the server's (flow/emoji_reactions.py): GET /api/particles/emoji-motions (the bank + start), POST emoji-preview (a looping WebP),
   POST/GET emoji-lottie (create / the created), emoji-presets (save, list, update, delete), emoji-batches (start, state, cancel), GET emoji-lottie.zip. */
'use strict';

/* ---------- settings: [key, label, min, max, step, unit] ---------- */
const RXPRESETS=['burst','fountain','vortex','rain','confetti'];
const RXSIM=[['magnitude','Speed',0,3,.05,'×'],['gravity','Gravity',-2,3,.05,''],['vortex','Swirl',-2,2,.05,''],['spin','Rotation',0,3,.05,'×'],['count','Amount',4,80,1,''],['spread','Spread',10,360,5,'°']];
const RXO=[['particle_size','Size',.25,3,.05,'×'],['size_var','Size variation',0,1,.05,'%'],['size_in_dur','Size in',0,1.5,.05,'s'],['size_out_dur','Size out',0,1.5,.05,'s'],['hue_var','Hue',0,180,5,'°']];
/* where every emoji starts; the server's EMOJI_START (GET emoji-motions `start`) replaces this copy as soon as the bank is read */
const RXSTART={magnitude:.7,gravity:1,vortex:0,spin:1,count:28,spread:360,particle_size:.3,size_var:.38,size_in_dur:.4,size_out_dur:.4,hue_var:25};
const RXPX=256;                                  /* a reaction loop's side: sharp at the 220 CSS px it is shown at */
const RXHOV=64;                                  /* the hover reaction's side: 60% smaller than the 160 px it was (Haitham, 2026-10-13) */
const RXPOLL=1500;                               /* a background run is asked for its progress this often */

/* ---------- state ----------
   bank: the emoji bank (server); start: the start look (server); made: every created reaction, newest first (server); ek: the emoji in the editor;
   hover: the emoji pointed at; pv / par: preview url and params per request (the server caches the files too); ppv: a preset card's preview;
   multi: Select is on; sel: the ticked emojis; anchor: the last ticked (Shift-click ticks from there); presets: the saved presets (server);
   apply: what Create N uses ('' = the start look, '*random', or a preset id); run: the background run being watched. */
const RXQ={q:'',f:'all'};
const RXS={bank:null,start:null,made:null,ek:null,hover:'',pv:{},par:{},ppv:{},hT:0,t:0,multi:false,sel:new Set(),anchor:'',presets:null,apply:'',run:null,runT:0,done:null};
const rxStart=()=>RXS.start||RXSTART;
/* one emoji in the editor: its motion override, the Simulation values (sim), the Shape values, the server's last answer (own), the saved version
   it was opened from (ver) and the preset it was loaded from (presetId) */
const rxNew=(t,par)=>{const s=rxStart();
 return {token:t,preset:'',sim:Object.fromEntries(RXSIM.map(o=>[o[0],s[o[0]]])),particle_size:s.particle_size,size_var:s.size_var,size_in_dur:s.size_in_dur,
  size_out_dur:s.size_out_dur,hue_var:s.hue_var,...(par||{}),own:null,shown:'',err:'',busy:false,ver:'',presetId:''}};

/* ---------- values ---------- */
const rxOpt=key=>RXSIM.find(o=>o[0]===key)||RXO.find(o=>o[0]===key);
const rxIsSim=key=>RXSIM.some(o=>o[0]===key);
const rxRow=t=>(RXS.bank||[]).find(m=>m.token===t)||{token:t,emoji:'',preset:'',motion:''};
/* the emojis that have a reaction (a Set, rebuilt when the created list changes) */
function rxDone(){if(!RXS.done)RXS.done=new Set((RXS.made||[]).map(r=>r.token));return RXS.done}
const rxSaved=t=>(RXS.made||[]).filter(r=>r.token===t);
function rxList(){
 const bank=RXS.bank||[],q=RXQ.q.trim().toLowerCase(),d=rxDone();
 return bank.filter(m=>(!q||(m.token+' '+m.emoji+' '+(m.motion||'')).toLowerCase().includes(q))&&(RXQ.f==='all'||(RXQ.f==='done')===d.has(m.token)))}
/* the request: every Simulation and Shape value, the motion only when overridden */
function rxBody(k){
 const sim=Object.fromEntries(Object.entries(k.sim||{}).filter(([,v])=>v!=null).map(([a,v])=>[a,+v]));
 return {token:k.token,...sim,particle_size:+k.particle_size,...(k.size_var!=null?{size_var:+k.size_var}:{}),
  size_in_dur:+k.size_in_dur,size_out_dur:+k.size_out_dur,hue_var:+k.hue_var,...(k.preset?{preset:k.preset}:{})}}
const rxKey=b=>JSON.stringify(b);
const rxSettings=k=>{const b=rxBody(k);delete b.token;return b};
/* a motion's own size variation, from its size range */
const rxOwnVar=p=>p&&p.size_max+p.size_min>0?Math.round((p.size_max-p.size_min)/(p.size_max+p.size_min)*1e4)/1e4:.35;
/* saved settings (a preset's, or a reaction's) as editor fields; a reaction saved before its settings were kept is read back from its params */
function rxFields(s,m){const st=rxStart();s=s||{};
 return {preset:s.preset&&s.preset!==m.preset?s.preset:'',sim:Object.fromEntries(RXSIM.map(o=>[o[0],s[o[0]]??st[o[0]]])),
  particle_size:s.particle_size??st.particle_size,size_var:s.size_var??st.size_var,size_in_dur:s.size_in_dur??st.size_in_dur,size_out_dur:s.size_out_dur??st.size_out_dur,hue_var:s.hue_var??st.hue_var}}
function rxFromRec(r){
 const m=rxRow(r.token),p=r.params||{};
 const s=r.settings||{preset:r.preset,...Object.fromEntries(RXSIM.map(o=>[o[0],p[o[0]]])),particle_size:p.particle_size,size_var:p.size_max!=null?rxOwnVar(p):null,
  size_in_dur:p.size_in_dur,size_out_dur:p.size_out_dur,hue_var:p.hue_var};
 return {...rxNew(r.token,rxFields(s,m)),ver:r.id}}
/* what an emoji plays: the editor's when it is open, else its newest saved reaction, else the start look */
const rxFor=t=>{if(RXS.ek&&RXS.ek.token===t)return rxBody(RXS.ek);const r=rxSaved(t)[0];return rxBody(r?rxFromRec(r):rxNew(t))};
/* what a slider shows: what the editor holds, else what the motion has; null = not known until the server answers */
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
const rxPlural=(n,w)=>`${n} ${w}${n===1?'':'s'}`;

/* ---------- views ---------- */
/* the hover reaction leaves from the tile's right edge, like Telegram's: the burst's own origin (a fountain starts low, rain at the top) sits on that edge */
function rxFxStyle(par){const [ox,oy]=(par&&par.origin)||[.5,.5];return `width:${RXHOV}px;height:${RXHOV}px;left:calc(100% - ${Math.round(ox*RXHOV)}px);top:calc(50% - ${Math.round(oy*RXHOV)}px)`}
/* the hover's own preview: the whole burst scaled into its square (fit), never cut at its edges (Haitham, 2026-10-14) */
const rxHovKey=t=>rxKey(rxFor(t))+'|fit';
function rxTile(m){
 const key=rxHovKey(m.token),ticked=RXS.multi&&RXS.sel.has(m.token),on=!RXS.multi&&!!RXS.ek&&RXS.ek.token===m.token,done=rxDone().has(m.token);
 const pv=RXS.hover===m.token&&!on?RXS.pv[key]:'';
 return `<button class="rx-e${on||ticked?' on':''}${done?' done':''}${pv?' play':''}" data-act=rxpick data-t="${esc(m.token)}" title="${esc(m.token)}${done?' · done':''}" aria-label="${esc(m.token)}" aria-pressed=${on||ticked}>`+
  `<span class=rx-g>${esc(m.emoji||'?')}</span>${ticked?`<span class=rx-tick>${ic('check')}</span>`:done?'<span class=rx-dot></span>':''}${pv?`<img class=rx-fx src="${esc(pv)}" style="${rxFxStyle(RXS.par[key])}" alt="">`:''}</button>`}
function rxRunHtml(){
 const r=RXS.run;if(!r||r.state!=='running')return '<div data-rxrun></div>';
 return `<div class=rx-run data-rxrun><span class=spin></span><span>Creating <b>${r.done}</b> of ${r.total}${r.errors&&r.errors.length?` · ${r.errors.length} failed`:''}${r.cancelling?' · stopping…':''}</span><button class=link data-act=rxbcancel>Cancel</button></div>`}
function rxPick(){
 const list=rxList(),total=(RXS.bank||[]).length,d=rxDone().size,n=RXS.sel.size,f=RXQ.f;
 const seg=(k,l)=>`<button type=button data-act=rxfilter data-f=${k} aria-pressed=${f===k}>${l}</button>`;
 return `<section class=rx-pick><div class=rx-top><input type=search data-rxq placeholder="Search ${total} emoji" value="${esc(RXQ.q)}" aria-label="Search the emoji bank">`+
  `<span class="gseg rx-f" role=group aria-label="Show">${seg('all','All')}${seg('done','Done')}${seg('todo','Not done')}</span>`+
  `<small class=mut><b>${d}</b>/${total} done</small><span class=sp></span>`+
  `<button class="btn sm${RXS.multi?' pri':''}" data-act=rxmulti aria-pressed=${RXS.multi}>${ic('check')} Select</button>`+
  `<span class=rx-exp><span class=mut>Export</span><button class="btn sm" data-act=rxzip data-w=all ${d?'':'disabled'} title="The newest Lottie of every emoji that has one, in one zip">${ic('download')} All</button>`+
  `<button class="btn sm" data-act=rxzip data-w=sel ${n?'':'disabled'} title="The newest Lottie of each selected emoji">Selected${n?' ('+n+')':''}</button></span></div>`+
  `${rxRunHtml()}<div class=rx-grid data-rxwall>${list.map(rxTile).join('')||'<span class=mut>No match.</span>'}</div>${rxMany()}</section>`}
/* Select: the ticked emojis and one way to create them all (the start look, a random preset of each one's own motion, or one preset) */
function rxMany(){
 if(!RXS.multi)return '<div data-rxmany></div>';
 const n=RXS.sel.size,ps=RXS.presets||[],busy=!!(RXS.run&&RXS.run.state==='running');
 const glyphs=[...RXS.sel].slice(0,40).map(t=>esc(rxRow(t).emoji)).join('');
 return `<div class=rx-many data-rxmany><span class=rx-many-sel>${n?`<b>${n}</b> <span class=rx-many-g>${glyphs}${n>40?'…':''}</span>`:'<span class=mut>Click to tick, Shift-click ticks the range</span>'}</span>`+
  `<button class=link data-act=rxselall>Select all shown</button>${n?'<button class=link data-act=rxclear>Clear</button>':''}`+
  `<label class=rx-pre><span class=mut>Look</span><select data-rxapply aria-label="Look for the ticked emojis"><option value=""${RXS.apply?'':' selected'}>The start look</option>`+
  `<option value="*random"${RXS.apply==='*random'?' selected':''} ${ps.length?'':'disabled'}>A random preset of its own motion</option>`+
  `${ps.map(p=>`<option value="${esc(p.id)}"${p.id===RXS.apply?' selected':''}>${esc(p.name)} · ${esc(p.motion||'')}</option>`).join('')}</select></label>`+
  `<button class="btn pri" data-act=rxmany ${n&&!busy?'':'disabled'}>Create ${n||''} reaction${n===1?'':'s'}</button></div>`}
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
/* the versions of the open emoji: Saved v... (newest first) */
function rxVersions(k){
 const vs=rxSaved(k.token);if(!vs.length)return '<small class=mut>not saved yet</small>';
 return `<label class=rx-ver><span class=mut>Saved</span><select data-rxver aria-label="Saved versions">${k.ver?'':'<option value="" selected>new, not saved</option>'}`+
  `${vs.map((r,i)=>`<option value="${esc(r.id)}"${r.id===k.ver?' selected':''}>v${vs.length-i} · ${esc(rxAgo(r.created))}</option>`).join('')}</select></label>`}
/* Presets: Save as new, Update the loaded one, Load (this motion's first), Remove */
function rxPresetMenu(k,m){
 const ps=RXS.presets||[],mo=k.preset||m.preset,own=ps.filter(p=>p.motion===mo),rest=ps.filter(p=>p.motion!==mo),cur=ps.find(p=>p.id===k.presetId);
 const item=(p,act,cls='btn')=>`<button class="${cls}" data-act=${act} data-id="${esc(p.id)}">${esc(p.name)} <small class=mut>${esc(p.motion||'')}</small></button>`;
 return `<details class="gh-more rx-pmenu"><summary class=btn aria-label="Presets">Presets ▾</summary><div class=gh-pop role=menu>`+
  `<button class=btn data-act=rxsave>Save as new preset</button>${cur?`<button class=btn data-act=rxpupd data-id="${esc(cur.id)}">Update “${esc(cur.name)}”</button>`:''}`+
  `${ps.length?`<div class=rx-pm-h>Load</div>${[...own,...rest].map(p=>item(p,'rxpload')).join('')}<div class=rx-pm-h>Remove</div>${ps.map(p=>item(p,'rxpdel','btn dng')).join('')}`:'<small class=mut>No preset saved yet</small>'}</div></details>`}
function rxEditor(){
 const k=RXS.ek;if(!k)return '<div data-rxed></div>';const m=rxRow(k.token),cur=k.ver&&rxSaved(k.token).find(r=>r.id===k.ver);
 return `<section class=rx-ed data-rxed><div class=rx-stage data-rxstage>${rxStage(k)}</div><div class=rx-ctl>
  <div class=rx-h><span class=rx-g>${esc(m.emoji)}</span><b>${esc(m.token)}</b>${rxVersions(k)}<button class=link data-act=rxclose aria-label="Close">${ic('x')}</button></div>
  ${m.motion?`<small class=mut>${esc(m.motion)}</small>`:''}
  <div class=rx-groups>
   ${rxGroup('Simulation','sim',true,rxMotion(k,m)+RXSIM.map(o=>rxSlider(k,o)).join(''))}
   ${rxGroup('Shape','shape',true,RXO.map(o=>rxSlider(k,o)).join('')+'<small class=mut>Hue 0 keeps the emoji\'s own colours.</small>')}
  </div>${k.err?`<span class=fx-warn>${esc(k.err)}</span>`:''}
  <div class=rx-foot><button class="btn pri" data-act=rxcreate ${k.busy?'disabled':''}>${k.busy?'<span class=spin></span> Creating…':'Create reaction'}</button>`+
  `${cur?`<button class=btn data-act=rxdl data-u="${esc(cur.url)}" data-n="${esc(k.token+' '+cur.id)}">${ic('download')} Lottie</button>`:''}<span class=sp></span>${rxPresetMenu(k,m)}</div></div></section>`}
/* Animation presets: the saved presets by motion, each with its preview; Open / Apply to selected / ×, and a random preset of each emoji's own motion for many */
function rxPresetCard(p){
 const n=RXS.sel.size,url=RXS.ppv[p.id]||'';
 return `<article class=rx-card title="${esc(p.name)}"><div class=rx-stage>${rxStageHtml(rxRow(p.token||'happy').emoji,url,p.name)}${url?'':'<span class=spin></span>'}</div>
  <div class=rx-meta><span class=rx-mt><b>${esc(p.name)}</b><small class=mut>${esc(p.motion||'')}${p.token?' · on '+esc(p.token):''}</small></span><button class=link data-act=rxpdel data-id="${esc(p.id)}" aria-label="Remove ${esc(p.name)}" title="Remove this preset">${ic('x')}</button></div>
  <div class=rx-acts><button class="btn sm" data-act=rxpopen data-id="${esc(p.id)}">Open</button><button class="btn sm" data-act=rxbatch data-m=preset data-id="${esc(p.id)}" data-w=sel ${n?'':'disabled'} title="Create every selected emoji with this preset">Apply to selected${n?' ('+n+')':''}</button></div></article>`}
function rxPresetsHtml(){
 const ps=RXS.presets;
 if(ps===null)return `<section class=rx-made><div class=sh>Animation presets</div><span class=spin></span></section>`;
 const total=(RXS.bank||[]).length,todo=total-rxDone().size,n=RXS.sel.size,busy=!!(RXS.run&&RXS.run.state==='running');
 const by={};ps.forEach(p=>(by[p.motion||'other']=by[p.motion||'other']||[]).push(p));
 return `<section class=rx-made data-rxpresets><div class=rx-ph><div class=sh>Animation presets <small class=mut>${ps.length||''}</small></div>`+
  `${ps.length?`<span class=rx-rnd><span class=mut>A random preset of each emoji's own motion</span>`+
  `<button class="btn sm" data-act=rxbatch data-m=random data-w=sel ${n&&!busy?'':'disabled'}>Selected${n?' ('+n+')':''}</button>`+
  `<button class="btn sm" data-act=rxbatch data-m=random data-w=todo ${todo&&!busy?'':'disabled'}>Not done (${todo})</button>`+
  `<button class="btn sm" data-act=rxbatch data-m=random data-w=all ${total&&!busy?'':'disabled'}>All ${total}</button></span>`:''}</div>`+
  `${ps.length?Object.entries(by).map(([mo,xs])=>`<div class=rx-pg><b>${esc(mo)}</b><div class=rx-cards>${xs.map(rxPresetCard).join('')}</div></div>`).join('')
   :'<div class=mut>No preset yet: open an emoji, shape its reaction, then Presets ▾ › Save as new preset.</div>'}</section>`}
function rxHtml(){
 if(!RXS.bank)return `<div class="page rx"><div class=fx-job><span class=spin></span> <span class=mut>Reading the emoji bank…</span></div></div>`;
 return `<div class="page rx">${rxPick()}${rxEditor()}${rxPresetsHtml()}</div>`}

/* ---------- page updates: repaint only what changed, so the search box, a dragged slider and the rest of the page never move ---------- */
function rxDraw(){
 const el=$('s-reactions');if(!el)return;
 const q=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.rxq!==undefined,
  w=el.querySelector&&el.querySelector('[data-rxwall]'),top=w?w.scrollTop:0;
 el.innerHTML=rxHtml();
 const w2=el.querySelector&&el.querySelector('[data-rxwall]');if(w2)w2.scrollTop=top;
 if(q){const i=el.querySelector('[data-rxq]');if(i){i.focus();try{i.setSelectionRange(i.value.length,i.value.length)}catch(e){}}}
 rxPresetPreviews()}
const rxSwap=(sel,html)=>{const el=document.querySelector&&document.querySelector(sel);if(el)el.outerHTML=html;else rxDraw()};
function rxGridRedraw(){const w=document.querySelector&&document.querySelector('[data-rxwall]');if(!w)return;w.innerHTML=rxList().map(rxTile).join('')||'<span class=mut>No match.</span>'}
function rxTileRedraw(t){const el=document.querySelector&&document.querySelector(`.rx-e[data-t="${t}"]`);if(el)el.outerHTML=rxTile(rxRow(t))}
function rxManyRedraw(){rxSwap('[data-rxmany]',rxMany())}
function rxRunRedraw(){rxSwap('[data-rxrun]',rxRunHtml())}
function rxPresetsRedraw(){rxSwap('[data-rxpresets]',rxPresetsHtml());rxPresetPreviews()}
function rxEdRedraw(){if(RXS.ek)rxSwap('[data-rxed]',rxEditor());else rxDraw()}
/* a preview answer: swap the picture and the values nobody is touching; the slider being dragged stays as it is */
function rxEdSync(){
 const k=RXS.ek,el=document.querySelector&&document.querySelector('[data-rxed]');if(!k||!el)return rxDraw();
 const st=el.querySelector('[data-rxstage]');if(st)st.innerHTML=rxStage(k);
 el.querySelectorAll('[data-rxo]').forEach(i=>{
  const o=rxOpt(i.dataset.rxo);if(!o||i===document.activeElement)return;
  const v=rxVal(k,o);if(v!=null)i.value=v;const out=i.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,v)})}

/* ---------- the server ---------- */
async function rxPlay(t){
 const b=rxFor(t),ed=()=>RXS.ek&&RXS.ek.token===t,fit=!ed(),key=fit?rxHovKey(t):rxKey(b);
 if(fit){if(await rxHovPreview(t)&&RXS.hover===t)rxTileRedraw(t);return}             /* the hover: the shared fit preview (rxHovPreview) */
 if(!RXS.pv[key]){
  const r=await post('/api/particles/emoji-preview',{...b,size:RXPX});
  if(!r.ok){if(ed()){RXS.ek.err=r.j.error||'The reaction could not be made.';rxEdRedraw()}return}
  RXS.pv[key]=r.j.url;RXS.par[key]=r.j.params}
 if(ed()){if(key!==rxKey(rxBody(RXS.ek)))return;RXS.ek.own=RXS.par[key];RXS.ek.shown=RXS.pv[key];RXS.ek.err='';rxEdSync()}}     /* an older answer than the sliders: ignored */
/* ---------- the same hover reaction anywhere else (Haitham, 2026-10-14: a pack's sticker plays its emoji's reaction when pointed at, the SAME effect
   as this screen's tiles: the same fit preview, cache and placement). rxFxOn(host, glyph) finds the glyph's bank emoji and puts the .rx-fx image on host. */
async function rxHovPreview(t){const key=rxHovKey(t);
 if(!RXS.pv[key]){const r=await post('/api/particles/emoji-preview',{...rxFor(t),size:RXPX,fit:true});if(!r.ok)return null;RXS.pv[key]=r.j.url;RXS.par[key]=r.j.params}
 return{url:RXS.pv[key],par:RXS.par[key]}}
async function rxBankEnsure(){
 if(!RXS.bank){const b=await api('/api/particles/emoji-motions');if(b.ok){RXS.bank=b.j.motions||[];if(b.j.start)RXS.start=b.j.start}}
 if(RXS.made===null)await rxLoadMade(true);
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
async function rxLoadMade(quiet){const r=await api('/api/particles/emoji-lottie');RXS.made=r.ok?(r.j.reactions||[]):[];RXS.done=null;if(!quiet&&route_==='reactions')rxDraw()}
async function rxLoadPresets(){const r=await api('/api/particles/emoji-presets');RXS.presets=r.ok?(r.j.presets||[]):[];if(route_==='reactions')rxDraw()}
/* each preset card shows its own look on the emoji it was made on (the same fit preview as the hover) */
async function rxPresetPreviews(){
 for(const p of RXS.presets||[]){
  if(RXS.ppv[p.id]!==undefined)continue;RXS.ppv[p.id]='';
  const r=await post('/api/particles/emoji-preview',{token:p.token||'happy',...(p.settings||{}),size:RXPX,fit:true});
  RXS.ppv[p.id]=r.ok?r.j.url:'';if(r.ok&&route_==='reactions'){const el=document.querySelector&&document.querySelector(`[data-act=rxpopen][data-id="${p.id}"]`);const c=el&&el.closest('.rx-card');if(c)c.outerHTML=rxPresetCard(p)}}}
/* the newest created first */
function rxAddMade(rs){RXS.made=[...rs.map(r=>({id:r.id,token:r.token,emoji:r.emoji,preset:r.preset,params:r.params,settings:r.settings,url:r.url,preview:r.preview,bytes:r.bytes,created:Date.now()/1000})).reverse(),...(RXS.made||[])];RXS.done=null}
/* a background run: its progress line, the ticks of what it made, and one toast at the end */
async function rxWatch(){
 clearTimeout(RXS.runT);const r0=RXS.run;if(!r0)return;
 const r=await api('/api/particles/emoji-batches/'+encodeURIComponent(r0.id));if(!r.ok)return;
 const fresh=(r.j.made||[]).map(x=>x.token).filter(t=>!rxDone().has(t));
 RXS.run=r.j;fresh.forEach(t=>rxDone().add(t));
 if(route_==='reactions'){rxRunRedraw();fresh.forEach(rxTileRedraw)}
 if(r.j.state==='running'){RXS.runT=setTimeout(rxWatch,RXPOLL);return}
 const n=(r.j.made||[]).length,bad=(r.j.errors||[]).length;
 toast(r.j.state==='done'?`${rxPlural(n,'reaction')} created${bad?`; ${bad} could not be made`:''}`:`Batch ${r.j.state}: ${rxPlural(n,'reaction')} created${r.j.note?' · '+r.j.note:''}`,bad?1:0);
 await rxLoadMade()}
async function rxRun(body,what){
 const r=await post('/api/particles/emoji-batches',body);
 if(!r.ok)return toast(r.j.error||'Could not start it',1);
 RXS.run=r.j;RXS.multi=false;RXS.sel.clear();rxDraw();toast(`Creating ${what} in the background: you can keep working`);RXS.runT=setTimeout(rxWatch,RXPOLL)}
RENDER.reactions=async()=>{
 rxDraw();if(RXS.presets===null)rxLoadPresets();
 if(!RXS.bank||RXS.made===null){await rxBankEnsure();if(route_==='reactions')rxDraw()}
 if(!RXS.run){const b=await api('/api/particles/emoji-batches');const live=b.ok&&(b.j.batches||[]).find(x=>x.state==='running');if(live){RXS.run=live;rxRunRedraw();rxWatch()}}};

/* ---------- events ---------- */
document.addEventListener('input',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxq!==undefined){RXQ.q=t.value;clearTimeout(RXS.t);RXS.t=setTimeout(rxGridRedraw,150);return}
 if(!t.dataset.rxo||!RXS.ek)return;
 const o=rxOpt(t.dataset.rxo);if(rxIsSim(o[0]))RXS.ek.sim[o[0]]=+t.value;else RXS.ek[o[0]]=+t.value;
 const out=t.parentNode&&t.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,t.value);
 clearTimeout(RXS.t);const tok=RXS.ek.token;RXS.t=setTimeout(()=>rxPlay(tok),300)});
/* another motion starts from the start values; another saved version opens as it was saved */
document.addEventListener('change',ev=>{
 const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxapply!==undefined){RXS.apply=t.value||'';return}
 if(t.dataset.rxver!==undefined&&RXS.ek){const r=rxSaved(RXS.ek.token).find(x=>x.id===t.value);if(r){RXS.ek=rxFromRec(r);rxEdRedraw();rxPlay(r.token)}return}
 if(t.dataset.rxpre===undefined||!RXS.ek)return;RXS.ek.preset=t.value||'';RXS.ek.sim=rxNew(RXS.ek.token).sim;rxPlay(RXS.ek.token)});
/* pointing at an emoji plays its reaction over it, after a short pause, so sweeping across the rows asks for nothing */
document.addEventListener('mouseover',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||route_!=='reactions')return;
 const t=b.dataset.t;if(RXS.hover===t)return;
 const was=RXS.hover;RXS.hover=t;if(was&&was!==t)rxTileRedraw(was);
 clearTimeout(RXS.hT);RXS.hT=setTimeout(()=>{if(RXS.hover===t)rxPlay(t)},220)});
document.addEventListener('mouseout',ev=>{
 const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||(ev.relatedTarget&&b.contains(ev.relatedTarget)))return;
 const t=b.dataset.t;if(RXS.hover!==t)return;RXS.hover='';clearTimeout(RXS.hT);rxTileRedraw(t)});

/* ---------- actions ---------- */
/* a click opens the emoji in the editor at its newest saved reaction; with Select on it ticks it (Shift: the whole range from the last tick) */
ACT.rxpick=(el,ev)=>{
 const t=el.dataset.t;
 if(RXS.multi){
  if(ev&&ev.shiftKey&&RXS.anchor&&RXS.anchor!==t){const ts=rxList().map(m=>m.token),a=ts.indexOf(RXS.anchor),b=ts.indexOf(t);
   if(a>=0&&b>=0){ts.slice(Math.min(a,b),Math.max(a,b)+1).forEach(x=>RXS.sel.add(x));RXS.anchor=t;rxGridRedraw();rxManyRedraw();rxPresetsRedraw();return}}
  if(RXS.sel.has(t))RXS.sel.delete(t);else RXS.sel.add(t);RXS.anchor=t;rxTileRedraw(t);rxManyRedraw();rxPresetsRedraw();return}
 if(RXS.ek&&RXS.ek.token===t)return;
 const r=rxSaved(t)[0];RXS.ek=r?rxFromRec(r):rxNew(t);RXS.hover='';rxDraw();rxPlay(t)};
ACT.rxfilter=el=>{RXQ.f=el.dataset.f||'all';rxDraw()};
ACT.rxmulti=()=>{RXS.multi=!RXS.multi;RXS.sel.clear();RXS.anchor='';if(RXS.multi)RXS.ek=null;rxDraw()};
ACT.rxselall=()=>{rxList().forEach(m=>RXS.sel.add(m.token));rxGridRedraw();rxManyRedraw();rxPresetsRedraw()};
ACT.rxclear=()=>{RXS.sel.clear();RXS.anchor='';rxDraw()};
/* Create N: the ticked emojis with the chosen look, in the background */
ACT.rxmany=()=>{
 const tokens=[...RXS.sel];if(!tokens.length)return;
 const a=RXS.apply,body=a==='*random'?{mode:'random'}:a?{mode:'preset',preset_id:a}:{mode:'start'};
 rxRun({tokens,...body},rxPlural(tokens.length,'reaction'))};
/* the presets' buttons and the random ones: Selected | Not done | All */
ACT.rxbatch=el=>{
 const w=el.dataset.w,m=el.dataset.m,body=m==='preset'?{mode:'preset',preset_id:el.dataset.id}:{mode:m||'start'};
 const total=(RXS.bank||[]).length,todo=total-rxDone().size;
 if(w==='sel'){const tokens=[...RXS.sel];if(!tokens.length)return;return rxRun({tokens,...body},rxPlural(tokens.length,'reaction'))}
 const n=w==='todo'?todo:total,go=()=>rxRun({...body,...(w==='todo'?{only_missing:true}:{})},rxPlural(n,'reaction'));
 confirmDlg(`Create ${rxPlural(n,'reaction')}${m==='random'?', each with a random preset of its own motion':''}? It runs in the background (about a second each)${w==='all'?'; emojis that are done get a new version':''}.`,go)};
ACT.rxbcancel=async()=>{if(!RXS.run)return;const r=await post(`/api/particles/emoji-batches/${encodeURIComponent(RXS.run.id)}/cancel`,{});if(r.ok){RXS.run={...RXS.run,cancelling:true};rxRunRedraw()}};
/* Export All | Selected: the newest Lottie of each, in one zip */
ACT.rxzip=el=>{
 const sel=el.dataset.w==='sel'?[...RXS.sel].filter(t=>rxDone().has(t)):null;
 if(sel&&!sel.length)return toast('None of the selected emojis has a reaction yet',1);
 const a=document.createElement('a');a.href='/api/particles/emoji-lottie.zip'+(sel?'?tokens='+encodeURIComponent(sel.join(',')):'');a.download='reactions.zip';
 document.body.appendChild(a);a.click();a.remove()};
/* Presets ▾ */
ACT.rxsave=async()=>{
 const k=RXS.ek;if(!k)return;
 const r=await post('/api/particles/emoji-presets',{settings:rxSettings(k),token:k.token});
 if(!r.ok)return toast(r.j.error||'Could not save the preset',1);
 RXS.presets=[...(RXS.presets||[]),r.j];k.presetId=r.j.id;rxEdRedraw();rxPresetsRedraw();toast(`Saved as ${r.j.name} (${r.j.motion})`)};
ACT.rxpupd=async el=>{
 const k=RXS.ek;if(!k)return;
 const r=await post(`/api/particles/emoji-presets/${encodeURIComponent(el.dataset.id)}`,{settings:rxSettings(k),token:k.token});
 if(!r.ok)return toast(r.j.error||'Could not update the preset',1);
 RXS.presets=(RXS.presets||[]).map(p=>p.id===r.j.id?r.j:p);delete RXS.ppv[r.j.id];rxPresetsRedraw();toast(`${r.j.name} updated`)};
ACT.rxpload=el=>{
 const k=RXS.ek,p=(RXS.presets||[]).find(x=>x.id===el.dataset.id);if(!k||!p)return;
 RXS.ek={...rxNew(k.token,rxFields(p.settings,rxRow(k.token))),presetId:p.id};rxEdRedraw();rxPlay(k.token)};
/* Open: the preset in the editor on the emoji it was made on, ready to change and Update */
ACT.rxpopen=el=>{
 const p=(RXS.presets||[]).find(x=>x.id===el.dataset.id);if(!p)return;const t=p.token||(RXS.ek&&RXS.ek.token)||'happy';
 RXS.multi=false;RXS.ek={...rxNew(t,rxFields(p.settings,rxRow(t))),presetId:p.id};rxDraw();rxPlay(t);
 const ed=document.querySelector&&document.querySelector('[data-rxed]');if(ed&&ed.scrollIntoView)ed.scrollIntoView({block:'nearest',behavior:'smooth'})};
ACT.rxpdel=async el=>{
 const r=await post(`/api/particles/emoji-presets/${el.dataset.id}/delete`,{});if(!r.ok)return toast(r.j.error||'Could not delete it',1);
 RXS.presets=r.j.presets||[];if(RXS.apply===el.dataset.id)RXS.apply='';if(RXS.ek&&RXS.ek.presetId===el.dataset.id)RXS.ek.presetId='';rxDraw()};
ACT.rxclose=()=>{RXS.ek=null;rxDraw()};
ACT.rxreset=el=>{const k=RXS.ek;if(!k)return;const s=rxNew(k.token);if(el.dataset.g==='sim'){k.sim=s.sim;k.preset=''}else ['particle_size','size_var','size_in_dur','size_out_dur','hue_var'].forEach(x=>k[x]=s[x]);rxEdRedraw();rxPlay(k.token)};
ACT.rxdl=el=>{const a=document.createElement('a');a.href=el.dataset.u;a.download=`${el.dataset.n}.lottie.json`;document.body.appendChild(a);a.click();a.remove()};
/* Create reaction: a new saved version of this emoji; the editor stays on it */
ACT.rxcreate=async()=>{
 const k=RXS.ek;if(!k||k.busy)return;k.busy=true;rxEdRedraw();
 const r=await post('/api/particles/emoji-lottie',rxBody(k));k.busy=false;
 if(!r.ok){k.err=r.j.error||'Could not create the reaction';return rxEdRedraw()}
 rxAddMade([r.j]);k.ver=r.j.id;rxDraw();toast(`${r.j.emoji} ${r.j.token}: saved as v${rxSaved(r.j.token).length}`)};
