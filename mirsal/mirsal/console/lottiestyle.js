/* Reaction effects, Lottie style (Haitham 2026-10-14): every file in mirsal/lottie/ is a reaction whose particles are that whole Lottie animation.
   Emoji style (reactions.js) stays; the Style switch on #/reactions picks one (kept in the browser). The viewer plays the EXACT export JSON
   (POST .../{file}/preview with the editor's unsaved values) in the bundled lottie-web player, 512 x 512, so viewer = export.
   Routes: GET /api/particles/lottie-reactions, POST .../{file} (save), POST .../{file}/preview, GET .../{file}/export.json, GET .../lottie-reactions.zip.
   Engine fields: engine/particles.py ParticleParams; settings list: flow/lottie_reactions.py SETTINGS. */

/* [key, label, min, max, step, unit], in groups */
const LSG=[
 ['Motion',[['magnitude','Speed',0,3,.05,'×'],['speed_var','Speed variation',0,1,.05,'%'],['speed_pulse','Speed pulse',0,1,.05,'%'],['pulse_hz','Pulse rate',.2,6,.1,'/s'],
  ['gravity','Gravity',-2,3,.05,''],['vortex','Swirl',-2,2,.05,''],['spread','Spread',10,360,5,'°'],['count','Amount',4,80,1,'']]],
 ['Spin',[['spin','Rotation',0,3,.05,'×'],['flip','Flip (cheap spin)',0,4,.05,'/s'],['flip_var','Flip variation',0,1,.05,'%']]],
 ['Shape',[['particle_size','Size',.25,3,.05,'×'],['size_var','Size variation',0,1,.05,'%'],['size_in_dur','Size in',0,1.5,.05,'s'],['size_out_dur','Size out',0,1.5,.05,'s']]],
 ['Fade out',[['fade_start','Fade out start',0,2,.05,'s'],['fade_dur','Fade out duration',0,2,.05,'s'],['fade_var','Fade out variation',0,1,.05,'s']]],
 ['Morph',[['morph_at','Morph at',0,2,.05,'s'],['morph_var','Morph variation',0,1,.05,'s']]],
 ['Children',[['children','Children',0,12,1,''],['child_size','Child size',.1,3,.05,'×'],['child_size_var','Child size variation',0,1,.05,'%']]]];
const LSO=LSG.flatMap(g=>g[1]);
const LS={files:null,start:null,sel:'',ed:null,doc:null,anim:null,t:0,err:'',busy:false,seq:0,lib:null};
const rxStyle=()=>{try{return localStorage.getItem('rx.style')==='lottie'?'lottie':'emoji'}catch(e){return 'emoji'}};
const rxStyleBar=()=>{const s=rxStyle();
 return `<div class=tabs role=tablist aria-label="Reaction style"><button class="tab ${s==='emoji'?'on':''}" data-act=rxstyle data-s=emoji role=tab aria-selected=${s==='emoji'}>Emoji style</button>`+
  `<button class="tab ${s==='lottie'?'on':''}" data-act=rxstyle data-s=lottie role=tab aria-selected=${s==='lottie'}>Lottie style</button></div>`};
const lsFile=f=>(LS.files||[]).find(x=>x.file===f);
const lsName=f=>String(f||'').replace(/\.json$/i,'');

/* ---------- markup ---------- */
function lsHtml(){
 if(!LS.files)return `<div class=fx-job><span class=spin></span> <span class=mut>Reading mirsal/lottie/…</span></div>`;
 return `${lsEditor()}<section class=rx-made data-lsfiles><div class=rx-ph><div class=sh>Lottie files <small class=mut>${LS.files.length}</small></div>`+
  `<small class=mut>Every <code>.json</code> in <code>mirsal/lottie/</code>; click one to make it a reaction</small><span class=sp></span>`+
  `<button class="btn sm" data-act=lszip title="Every file with its saved settings, one self-contained Lottie each, plus manifest.json">${ic('download')} Export all (.zip)</button></div>`+
  (LS.files.length?`<div class=ls-files>${LS.files.map(f=>`<button class="ls-f${LS.sel===f.file?' on':''}" data-act=lspick data-f="${esc(f.file)}" aria-pressed=${LS.sel===f.file}>`+
   `<b>${esc(f.name)}</b><small class=mut>${f.w}×${f.h} · ${f.fps} fps · ${f.frames} fr${f.saved?' · saved':''}</small></button>`).join('')}</div>`
   :`<div class=mut>No files yet: drop Lottie .json files into <code>mirsal/lottie/</code>.</div>`)+`</section>`}
function lsSlider(o){const v=LS.ed.settings[o[0]];
 return `<label class=rx-sl><span class=mut>${o[1]}</span><input type=range min=${o[2]} max=${o[3]} step=${o[4]} value="${v}" data-lso=${o[0]} aria-label="${o[1]}"><output>${rxFmt(o,v)}</output></label>`}
function lsTargets(){const others=(LS.files||[]).filter(f=>f.file!==LS.sel);
 if(!others.length)return '<small class=mut>Drop a second file to morph into it.</small>';
 return `<div class=ls-tg>${others.map(f=>`<label class=rx-dbgt><input type=checkbox data-lst="${esc(f.file)}" ${LS.ed.morph_targets.includes(f.file)?'checked':''}> ${esc(f.name)}</label>`).join('')}</div>`+
  `<small class=mut>Each particle turns into one of the ticked files at Morph at (0 = no morph).</small>`}
const lsStage=()=>`<div class=ls-player data-lsplayer></div>${LS.doc?rxDbgHtml([.5,.5]):''}${LS.doc||LS.err?'':'<span class=spin></span>'}`;
function lsEditor(){
 if(!LS.ed)return '<div data-lsed></div>';
 const f=lsFile(LS.sel)||{name:lsName(LS.sel)};
 return `<section class=rx-ed data-lsed><div class=rx-stage data-lsstage>${lsStage()}</div><div class=rx-ctl>
  <div class=rx-h><b>${esc(f.name)}</b><small class=mut>2 s · 512 × 512${LS.doc?` · ${LS.doc.layers.length} layers`:''}</small>${rxDbgToggle()}<button class=link data-act=lsclose aria-label="Close">${ic('x')}</button></div>
  <div class=rx-groups>${LSG.map(([t,os])=>`<div class=rx-grp><div class=rx-gh><b>${t}</b></div>${os.map(lsSlider).join('')}${t==='Morph'?lsTargets():''}</div>`).join('')}</div>
  ${LS.err?`<span class=fx-warn data-lserr>${esc(LS.err)}</span>`:'<span data-lserr></span>'}
  <div class=rx-foot><button class="btn pri" data-act=lssave ${LS.busy?'disabled':''}>Save</button><button class=btn data-act=lsdl ${LS.doc?'':'disabled'}>${ic('download')} JSON</button>`+
  `<button class=link data-act=lsreset>Reset to default</button></div></div></section>`}

/* ---------- the player (lottie-web, bundled: no CDN) ---------- */
let lsLib=null;
function lsLottie(){if(window.lottie)return Promise.resolve(window.lottie);
 if(!lsLib)lsLib=new Promise((ok,no)=>{const s=document.createElement('script');s.src='/ui/vendor/lottie-5.12.2.min.js';s.onload=()=>ok(window.lottie);s.onerror=no;document.head.appendChild(s)});
 return lsLib}
async function lsMount(){
 const box=document.querySelector&&document.querySelector('[data-lsplayer]');
 if(LS.anim){try{LS.anim.destroy()}catch(e){}LS.anim=null}
 if(!box||!LS.doc)return;
 const L=await lsLottie().catch(()=>null);if(!L){LS.err='The Lottie player could not be loaded.';return lsEdSync()}
 if(!box.isConnected)return;
 LS.anim=L.loadAnimation({container:box,renderer:'svg',loop:true,autoplay:true,animationData:JSON.parse(JSON.stringify(LS.doc))})}

/* ---------- server ---------- */
async function lsLoad(){const r=await api('/api/particles/lottie-reactions');
 if(r.ok){LS.files=r.j.files||[];LS.start=r.j.start||{}}else{LS.files=[];LS.err=r.j.error||'The Lottie files could not be read.'}}
async function lsPreview(){
 if(!LS.ed)return;const n=++LS.seq;
 const r=await post(`/api/particles/lottie-reactions/${encodeURIComponent(LS.sel)}/preview`,{settings:LS.ed.settings,morph_targets:LS.ed.morph_targets});
 if(n!==LS.seq||!LS.ed)return;
 if(!r.ok){LS.err=r.j.error||'The preview could not be made.';return lsEdSync()}
 LS.err='';LS.doc=r.j;lsEdSync(true)}
const lsSoon=()=>{clearTimeout(LS.t);LS.t=setTimeout(lsPreview,250)};
function lsEdSync(remount){
 const ed=document.querySelector&&document.querySelector('[data-lsed]');if(!ed)return rxDraw();
 const h=ed.querySelector('.rx-h small');if(h)h.textContent=`2 s · 512 × 512${LS.doc?` · ${LS.doc.layers.length} layers`:''}`;
 const e=ed.querySelector('[data-lserr]');if(e){e.className=LS.err?'fx-warn':'';e.textContent=LS.err}
 const dl=ed.querySelector('[data-act=lsdl]');if(dl)dl.disabled=!LS.doc;
 if(remount){const st=ed.querySelector('[data-lsstage]');if(st){st.innerHTML=lsStage();lsMount()}}}
function lsOpen(file){const f=lsFile(file);if(!f)return;
 LS.sel=file;LS.ed={settings:{...(LS.start||{}),...(f.settings||{})},morph_targets:[...(f.morph_targets||[])]};LS.doc=null;LS.err='';rxDraw();lsPreview()}

/* ---------- actions ---------- */
ACT.rxstyle=el=>{try{localStorage.setItem('rx.style',el.dataset.s==='lottie'?'lottie':'emoji')}catch(e){}RENDER.reactions()};
ACT.lspick=el=>lsOpen(el.dataset.f);
ACT.lsclose=()=>{LS.sel='';LS.ed=null;LS.doc=null;if(LS.anim){try{LS.anim.destroy()}catch(e){}LS.anim=null}rxDraw()};
ACT.lsreset=()=>{if(!LS.ed)return;LS.ed.settings={...(LS.start||{})};LS.ed.morph_targets=[];rxDraw();lsPreview()};
ACT.lssave=async()=>{if(!LS.ed||LS.busy)return;LS.busy=true;
 const r=await post(`/api/particles/lottie-reactions/${encodeURIComponent(LS.sel)}`,{settings:LS.ed.settings,morph_targets:LS.ed.morph_targets});LS.busy=false;
 if(!r.ok){LS.err=r.j.error||'Could not save.';return lsEdSync()}
 const f=lsFile(LS.sel);if(f){f.saved=true;f.settings=r.j.settings;f.morph_targets=r.j.morph_targets}toast(`Saved ${lsName(LS.sel)}`);rxDraw()};
ACT.lsdl=()=>{if(!LS.doc)return;const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([JSON.stringify(LS.doc)],{type:'application/json'}));a.download=`${lsName(LS.sel)}-reaction.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),4000)};
ACT.lszip=()=>{const a=document.createElement('a');a.href='/api/particles/lottie-reactions.zip';a.download='lottie-reactions.zip';a.click()};
document.addEventListener('input',ev=>{const t=ev.target;if(!t||!t.dataset||t.dataset.lso===undefined||!LS.ed)return;
 const o=LSO.find(x=>x[0]===t.dataset.lso);if(!o)return;LS.ed.settings[o[0]]=+t.value;
 const out=t.parentNode.querySelector('output');if(out)out.textContent=rxFmt(o,+t.value);lsSoon()});
document.addEventListener('change',ev=>{const t=ev.target;if(!t||!t.dataset||t.dataset.lst===undefined||!LS.ed)return;
 const f=t.dataset.lst,m=LS.ed.morph_targets.filter(x=>x!==f);if(t.checked)m.push(f);LS.ed.morph_targets=m;lsPreview()});
