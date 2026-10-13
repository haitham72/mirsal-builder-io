/* Reaction effects (#/reactions, Create > + New): the emoji bank ONLY. docs/reaction.md section 13, docs/design.md (Create's tabs).
   Its own screen and its own state (prefix rx): it shares nothing with effects.js / particles.js (the Studio's pack particles keep #/effects). */
'use strict';
const RXPRESETS=['burst','fountain','vortex','rain','confetti'];
/* Three parts, top to bottom:
   1. Search + TWO rows of small emojis (the matches; pointing at one plays its reaction over it, in place).
   2. The picked emoji in one editor card: its reaction playing (its fixed animation, flying as the emoji's own glyph), Motion, Size in / Size out, Hue, Create reaction.
   3. Only what was created, each in one simple card: the reaction playing, the emoji and its name, the motion, Download Lottie, Edit.
   No packs, no stickers, no Kling, no sheets (those stay in the Studio; #/effects stays the Studio's particle editor). Everything is the server's: GET /api/particles/emoji-motions
   (the bank), POST /api/particles/emoji-preview (a looping WebP), POST /api/particles/emoji-lottie (create: the stored Lottie + its loop), GET /api/particles/emoji-lottie (the created). */
const RXQ={q:''};
/* Simulation: how they move (the motion's own values until moved: only touched keys are sent, in k.sim). Shape: how each emoji looks. */
const RXSIM=[['magnitude','Speed',0,3,.05,'×'],['gravity','Gravity',-2,3,.05,''],['vortex','Swirl',-2,2,.05,''],['spin','Rotation',0,3,.05,'×'],['count','Amount',4,80,1,''],['spread','Spread',10,360,5,'°']];
const RXO=[['particle_size','Size',.25,3,.05,'×'],['size_var','Size variation',0,1,.05,'%'],['size_in_dur','Size in',0,1.5,.05,'s'],['size_out_dur','Size out',0,1.5,.05,'s'],['hue_var','Hue',0,180,5,'°']];
const RXD={particle_size:1,size_var:null,size_in_dur:.4,size_out_dur:.4,hue_var:25};   /* size_var null = the motion's own range (the slider shows it) */
const rxFmt=(o,v)=>o[5]==='%'?Math.round(v*100)+'%':o[5]==='×'?'×'+(+v):(+v)+o[5];
const rxOpt=key=>RXSIM.find(o=>o[0]===key)||RXO.find(o=>o[0]===key);
const rxIsSim=key=>RXSIM.some(o=>o[0]===key);
const rxOwnVar=p=>p&&p.size_max+p.size_min>0?Math.round((p.size_max-p.size_min)/(p.size_max+p.size_min)*1e4)/1e4:.35;   /* a motion's own variation, from its size range */
const RXPX=256;                                  /* a reaction loop's side: sharp at the 200 CSS px it is shown at */
const RXN=48;                                    /* tiles drawn; rxClip shows exactly two rows of them, whatever the width */
const RXS={bank:null,ek:null,hover:'',pv:{},par:{},hT:0,t:0,made:null}; /* ek: the picked emoji and its options; pv: preview url per request; made: the created reactions (server) */
const rxNew=(t,par)=>({token:t,preset:'',...RXD,sim:{},...(par||{}),own:null,err:'',busy:false});   /* own: the last params the server answered with (the untouched values shown) */
function rxList(){const bank=RXS.bank||[],q=RXQ.q.trim().toLowerCase();
 return (q?bank.filter(m=>(m.token+' '+m.emoji+' '+(m.motion||'')).toLowerCase().includes(q)):bank).slice(0,RXN)}
const rxBody=k=>({token:k.token,...Object.fromEntries(Object.entries(k.sim||{}).map(([a,v])=>[a,+v])),particle_size:+k.particle_size,...(k.size_var!=null?{size_var:+k.size_var}:{}),size_in_dur:+k.size_in_dur,size_out_dur:+k.size_out_dur,hue_var:+k.hue_var,...(k.preset?{preset:k.preset}:{})});
const rxKey=b=>JSON.stringify(b);
const rxRow=t=>(RXS.bank||[]).find(m=>m.token===t)||{token:t,emoji:'',preset:'',motion:''};
const rxFor=t=>RXS.ek&&RXS.ek.token===t?rxBody(RXS.ek):rxBody({token:t,preset:'',...RXD,sim:{}});
/* the value a slider shows: what the person set, else what the motion has (from the server's last answer) */
function rxVal(k,o){const key=o[0];
 if(rxIsSim(key))return k.sim[key]!=null?k.sim[key]:k.own&&k.own[key]!=null?k.own[key]:null;
 return key==='size_var'&&k.size_var==null?(k.own?rxOwnVar(k.own):null):k[key]}
const rxShow=(o,v)=>v==null?'…':rxFmt(o,v);           /* null: the motion's own value is not known yet (no answer from the server so far) */
const rxSlider=(k,o)=>{const v=rxVal(k,o);return `<label class=rx-sl><span class=mut>${o[1]}</span><input type=range min=${o[2]} max=${o[3]} step=${o[4]} value="${v??(o[2]+o[3])/2}" data-rxo=${o[0]} aria-label="${o[1]}"><output>${rxShow(o,v)}</output></label>`};
function rxTile(m){const on=!!RXS.ek&&RXS.ek.token===m.token,pv=RXS.hover===m.token&&!on?RXS.pv[rxKey(rxFor(m.token))]:'';
 return `<button class="rx-e${on?' on':''}${pv?' play':''}" data-act=rxpick data-t="${esc(m.token)}" title="${esc(m.token)}" aria-label="${esc(m.token)}" aria-pressed=${on}><span class=rx-g>${esc(m.emoji||'?')}</span>${pv?`<img class=rx-fx src="${esc(pv)}" alt="">`:''}</button>`}
function rxPick(){const list=rxList(),n=(RXS.bank||[]).length;
 return `<section class=rx-pick><div class=rx-top><input type=search data-rxq placeholder="Search ${n} emoji" value="${esc(RXQ.q)}" aria-label="Search the emoji bank"></div>
  <div class=rx-grid data-rxwall>${list.map(rxTile).join('')||'<span class=mut>No match.</span>'}</div></section>`}
function rxStage(k){const pv=RXS.pv[rxKey(rxBody(k))]||k.shown;return pv?`<img src="${esc(pv)}" alt="${esc(k.token)} reaction">`:k.err?'':'<span class=spin></span>'}
function rxEditor(){const k=RXS.ek;if(!k)return '';const m=rxRow(k.token);
 return `<section class=rx-ed data-rxed><div class=rx-stage data-rxstage>${rxStage(k)}</div>
  <div class=rx-ctl><div class=rx-h><span class=rx-g>${esc(m.emoji)}</span><b>${esc(m.token)}</b><button class=link data-act=rxclose aria-label="Close">${ic('x')}</button></div>
   ${m.motion?`<small class=mut>${esc(m.motion)}</small>`:''}
   <label class=rx-sl><span class=mut>Motion</span><select data-rxpre aria-label="Motion"><option value=""${k.preset?'':' selected'}>its own · ${esc(m.preset||'')}</option>${RXPRESETS.map(n=>`<option value=${n}${k.preset===n?' selected':''}>${n}</option>`).join('')}</select></label>
   <div class=rx-groups>
    <div class=rx-grp><div class=rx-gh><b>Simulation</b><button class=link data-act=rxreset data-g=sim ${Object.keys(k.sim).length?'':'disabled'}>Reset</button></div>${RXSIM.map(o=>rxSlider(k,o)).join('')}</div>
    <div class=rx-grp><div class=rx-gh><b>Shape</b><button class=link data-act=rxreset data-g=shape>Reset</button></div>${RXO.map(o=>rxSlider(k,o)).join('')}<small class=mut>Hue 0 keeps the emoji's own colours.</small></div>
   </div>${k.err?`<span class=fx-warn>${esc(k.err)}</span>`:''}
   <div class=row><button class="btn pri" data-act=rxcreate ${k.busy?'disabled':''}>${k.busy?'<span class=spin></span> Creating…':'Create reaction'}</button></div></div></section>`}
function rxCard(r){return `<article class=rx-card><div class=rx-stage>${r.preview?`<img src="${esc(r.preview)}" alt="${esc(r.token)} reaction" loading=lazy>`:`<span class=rx-g>${esc(r.emoji)}</span>`}</div>
  <div class=rx-meta><span class=rx-g>${esc(r.emoji)}</span><b>${esc(r.token)}</b><small class=mut>${esc(r.preset||'')} · ${esc(r.id||'')}</small></div>
  <div class=rx-acts><button class="btn sm pri" data-act=rxdl data-u="${esc(r.url)}" data-n="${esc(r.token+' '+r.id)}">${ic('download')} Lottie</button><button class="btn sm" data-act=rxedit data-t="${esc(r.token)}" data-id="${esc(r.id)}">Edit</button></div></article>`}
function rxMade(){const m=RXS.made;
 if(m===null)return `<section class=rx-made><div class=sh>Your reactions</div><span class=spin></span></section>`;
 return `<section class=rx-made><div class=sh>Your reactions <small class=mut>${m.length||''}</small></div>
  ${m.length?`<div class=rx-cards>${m.map(rxCard).join('')}</div>`:'<div class=mut>Nothing created yet: pick an emoji above.</div>'}</section>`}
function rxHtml(){
 if(!RXS.bank)return `<div class="page rx"><div class=fx-job><span class=spin></span> <span class=mut>Reading the emoji bank…</span></div></div>`;
 return `<div class="page rx">${rxPick()}${rxEditor()}${rxMade()}</div>`}
function rxDraw(){const el=$('s-reactions');if(!el)return;const q=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.rxq!==undefined;
 el.innerHTML=rxHtml();rxClip();if(q){const i=el.querySelector('[data-rxq]');if(i){i.focus();try{i.setSelectionRange(i.value.length,i.value.length)}catch(e){}}}}
/* two rows only: the grid counts its own columns and every tile past the second row is not shown (a search narrows the rows instead) */
function rxClip(){const w=document.querySelector&&document.querySelector('[data-rxwall]');if(!w||!w.children)return;
 const cols=Math.max(1,String(getComputedStyle(w).gridTemplateColumns||'').split(' ').filter(Boolean).length);
 [...w.children].forEach((el,i)=>{el.style.display=i<2*cols?'':'none'})}
if(typeof window!=='undefined'&&window.addEventListener)window.addEventListener('resize',()=>{if(route_==='reactions')rxClip()});
/* repaint one part (a tile, the editor) so the rest of the page and the search box do not move */
function rxTileRedraw(t){const el=document.querySelector&&document.querySelector(`.rx-e[data-t="${t}"]`);if(!el)return;const shown=el.style.display;el.outerHTML=rxTile(rxRow(t));
 const nu=document.querySelector(`.rx-e[data-t="${t}"]`);if(nu)nu.style.display=shown}
function rxEdRedraw(){const el=document.querySelector&&document.querySelector('[data-rxed]');if(el&&RXS.ek)el.outerHTML=rxEditor();else rxDraw()}
function rxEdSync(){const k=RXS.ek,el=document.querySelector&&document.querySelector('[data-rxed]');if(!k||!el)return rxDraw();
 const st=el.querySelector('[data-rxstage]');if(st)st.innerHTML=rxStage(k);
 el.querySelectorAll('[data-rxo]').forEach(i=>{const o=rxOpt(i.dataset.rxo);if(!o||i===document.activeElement)return;const v=rxVal(k,o);if(v!=null)i.value=v;const out=i.parentNode.querySelector('output');if(out)out.textContent=rxShow(o,v)});
 const r=el.querySelector('[data-act=rxreset][data-g=sim]');if(r)r.disabled=!Object.keys(k.sim).length}
async function rxPlay(t){const b=rxFor(t),k=rxKey(b),ed=()=>RXS.ek&&RXS.ek.token===t;
 if(!RXS.pv[k]){const r=await post('/api/particles/emoji-preview',{...b,size:RXPX});
  if(!r.ok){if(ed()){RXS.ek.err=r.j.error||'The reaction could not be made.';rxEdRedraw()}return}
  RXS.pv[k]=r.j.url;RXS.par[k]=r.j.params}
 if(ed()){if(k!==rxKey(rxBody(RXS.ek)))return;RXS.ek.own=RXS.par[k];RXS.ek.shown=RXS.pv[k];RXS.ek.err='';rxEdSync()}else if(RXS.hover===t)rxTileRedraw(t)}
async function rxLoadMade(){const r=await api('/api/particles/emoji-lottie');RXS.made=r.ok?(r.j.reactions||[]):[];if(route_==='reactions')rxDraw()}
RENDER.reactions=async()=>{rxDraw();if(RXS.made===null)rxLoadMade();
 if(!RXS.bank){const b=await api('/api/particles/emoji-motions');if(b.ok){RXS.bank=b.j.motions||[];if(route_==='reactions')rxDraw()}}};
document.addEventListener('input',ev=>{const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.rxq!==undefined){RXQ.q=t.value;clearTimeout(RXS.t);RXS.t=setTimeout(()=>{const w=document.querySelector('[data-rxwall]');if(w){w.innerHTML=rxList().map(rxTile).join('')||'<span class=mut>No match.</span>';rxClip()}},150)}
 else if(t.dataset.rxo&&RXS.ek){const o=rxOpt(t.dataset.rxo);if(rxIsSim(o[0]))RXS.ek.sim[o[0]]=+t.value;else RXS.ek[o[0]]=+t.value;const out=t.parentNode&&t.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,t.value);
  clearTimeout(RXS.t);const tok=RXS.ek.token;RXS.t=setTimeout(()=>rxPlay(tok),300)}});
document.addEventListener('change',ev=>{const t=ev.target;if(t&&t.dataset&&t.dataset.rxpre!==undefined&&RXS.ek){RXS.ek.preset=t.value||'';RXS.ek.sim={};rxPlay(RXS.ek.token)}});   /* another motion: its own simulation, not the old one's tweaks */
ACT.rxreset=el=>{const k=RXS.ek;if(!k)return;if(el.dataset.g==='sim')k.sim={};else Object.assign(k,RXD);rxEdSync();rxPlay(k.token)};
/* pointing at an emoji plays its reaction over it (after a short pause, so sweeping across the rows asks for nothing) */
document.addEventListener('mouseover',ev=>{const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||route_!=='reactions')return;const t=b.dataset.t;if(RXS.hover===t)return;
 const was=RXS.hover;RXS.hover=t;if(was&&was!==t)rxTileRedraw(was);clearTimeout(RXS.hT);RXS.hT=setTimeout(()=>{if(RXS.hover===t)rxPlay(t)},220)});
document.addEventListener('mouseout',ev=>{const b=ev.target&&ev.target.closest&&ev.target.closest('.rx-e');if(!b||(ev.relatedTarget&&b.contains(ev.relatedTarget)))return;const t=b.dataset.t;if(RXS.hover!==t)return;RXS.hover='';clearTimeout(RXS.hT);rxTileRedraw(t)});
ACT.rxpick=el=>{const t=el.dataset.t,was=RXS.ek&&RXS.ek.token;if(was===t)return;RXS.ek=rxNew(t);RXS.hover='';rxDraw();rxPlay(t)};
ACT.rxclose=()=>{RXS.ek=null;rxDraw()};
ACT.rxedit=el=>{const r=(RXS.made||[]).find(x=>x.token===el.dataset.t&&x.id===el.dataset.id);if(!r)return;const p=r.params||{},m=rxRow(r.token);
 RXS.ek=rxNew(r.token,{preset:r.preset&&r.preset!==m.preset?r.preset:'',sim:Object.fromEntries(RXSIM.map(o=>[o[0],p[o[0]]]).filter(([,v])=>v!=null)),particle_size:p.particle_size??1,size_var:p.size_max!=null?rxOwnVar(p):null,size_in_dur:p.size_in_dur??RXD.size_in_dur,size_out_dur:p.size_out_dur??RXD.size_out_dur,hue_var:p.hue_var??RXD.hue_var});
 rxDraw();rxPlay(r.token);const ed=document.querySelector&&document.querySelector('[data-rxed]');if(ed&&ed.scrollIntoView)ed.scrollIntoView({block:'nearest',behavior:'smooth'})};
ACT.rxdl=el=>{const a=document.createElement('a');a.href=el.dataset.u;a.download=`${el.dataset.n}.lottie.json`;document.body.appendChild(a);a.click();a.remove()};
ACT.rxcreate=async()=>{const k=RXS.ek;if(!k||k.busy)return;k.busy=true;rxEdRedraw();
 const r=await post('/api/particles/emoji-lottie',rxBody(k));k.busy=false;
 if(!r.ok){k.err=r.j.error||'Could not create the reaction';return rxEdRedraw()}
 RXS.made=[{id:r.j.id,token:r.j.token,emoji:r.j.emoji,preset:r.j.preset,params:r.j.params,url:r.j.url,preview:r.j.preview,bytes:r.j.bytes,created:Date.now()/1000},...(RXS.made||[])];
 RXS.ek=null;rxDraw();toast(`${r.j.emoji} ${r.j.token} created: download its Lottie from its card`)};
