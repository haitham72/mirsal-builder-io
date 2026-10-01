/* Live generation (Higgsfield): the credits chip and usage log, the style tiles, the model selector, the "make it" confirmation with its price,
   and the cards that follow a running sheet / Kling job. Everything here calls a real endpoint (/api/higgsfield, /api/models, /api/usage, /api/live/*);
   the engine and the review gates are unchanged: a finished sheet runs through the same stills run, a video only starts from an approved video sheet. */
'use strict';
const LIVE={hf:null,m:null,style:'flat_vector',img:{id:'',options:{}},vid:{id:'',options:{}},jobs:[],est:{}};
try{const s=JSON.parse(localStorage.getItem('mirsal.live')||'null');if(s){LIVE.style=s.style||LIVE.style;LIVE.img=s.img||LIVE.img;LIVE.vid=s.vid||LIVE.vid;LIVE.jobs=Array.isArray(s.jobs)?s.jobs:[]}}catch(e){}
const lsave=()=>gstore('mirsal.live',JSON.stringify({style:LIVE.style,img:LIVE.img,vid:LIVE.vid,jobs:LIVE.jobs}));
const fcr=n=>n==null?'?':(+n).toLocaleString(undefined,{maximumFractionDigits:2});
const lkind=k=>k==='image'||k==='video'?k:(k==='sheet'||k==='single'?'image':'video');

/* ---------- models */
function lfind(kind,id){const m=LIVE.m;if(!m)return null;return(m[kind]||[]).find(x=>x.id===id)||((m.more||{})[kind]||[]).find(x=>x.id===id)||null}
function lsel(kind){const key=kind==='image'?'img':'vid',cur=LIVE[key];let m=lfind(kind,cur.id);
  if(!m&&LIVE.m){m=lfind(kind,LIVE.m.defaults[kind]);cur.id=m?m.id:'';cur.options={}}
  if(m){const o={};for(const op of m.options)o[op.name]=(cur.options||{})[op.name]&&op.choices.includes(String(cur.options[op.name]))?String(cur.options[op.name]):op.default;cur.options=o}
  return{model:m,sel:cur}}
const logoHtml=(m,cls='')=>m&&m.logo?`<img class="lv-logo ${cls}" src="/assets/vendors/${esc(m.logo)}" alt="">`:`<span class="lv-logo mono ${cls}">${esc((m&&m.label||'?').slice(0,1))}</span>`;
const optSummary=(m,sel)=>m?m.options.map(o=>sel.options[o.name]!=null?(o.name==='duration'?sel.options[o.name]+' s':sel.options[o.name]):'').filter(Boolean).join(' · '):'';

/* ---------- credits chip (bottom of the rail) and the usage log */
async function refreshHf(){const r=await api('/api/higgsfield');if(r.ok){const was=LIVE.hf&&!LIVE.hf.error&&LIVE.hf.available;LIVE.hf=r.j;drawChip();if(!!was!==!!(r.j&&!r.j.error&&r.j.available)&&typeof composerDraw==='function')composerDraw()}}
function drawChip(){const rail=$('rail');if(!rail)return;let b=document.getElementById('lvchip');if(!b){b=document.createElement('button');b.id='lvchip';b.className='lv-chip';b.dataset.act='lusage';rail.appendChild(b)}
  const h=LIVE.hf;b.title=!h?'Higgsfield':h.error?h.error:`${fcr(h.credits)} credits left · ${fcr(h.spent_today)} spent today · ${h.plan||''} plan. Click for the usage log.`;
  b.className='lv-chip'+(h&&(h.error||h.available===false)?' off':'');
  b.innerHTML=!h?'<b>…</b><small>credits</small>':h.available===false?'<b>off</b><small>Higgsfield</small>':h.error?'<b>!</b><small>Higgsfield</small>':`<b>${h.credits>=100?Math.round(h.credits).toLocaleString():fcr(Math.round(h.credits*10)/10)}</b><small>credits</small>`}
const _drawRail=drawRail;drawRail=function(){_drawRail();drawChip()};
ACT.lusage=async()=>{dlg('<div class="vdlg lv-usage"><h2>Usage</h2><div class=mut>Loading…</div></div>');
  const [u,h]=await Promise.all([api('/api/usage?limit=150'),api('/api/higgsfield')]);if(!u.ok)return toast(u.j.error||'Could not load the usage',1);if(h.ok){LIVE.hf=h.j;drawChip()}
  const U=u.j,H=LIVE.hf||{},when=ts=>ts?new Date(ts*1000).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'',
    kindName={image:'image',video:'video',llm:'text'};
  const tile=(l,v)=>`<div class=lv-tile><small>${l}</small><b>${v}</b></div>`;
  dlg(`<div class="vdlg lv-usage"><h2>Usage</h2>
   <div class=lv-tiles>${tile('Credits left',H.credits!=null?fcr(H.credits):'?')}${tile('Spent today',fcr(U.today))}${tile('Spent in total',fcr(U.credits_spent))}${tile('Calls logged',U.calls)}</div>
   ${H.error?`<div class=warn>${esc(H.error)}</div>`:''}
   <h3>By model</h3>${U.by_model.length?`<table class=stbl><tr><th>Model<th>Used for<th>Calls<th>Credits</tr>${U.by_model.map(m=>`<tr><td>${logoHtml(m,'sm')} ${esc(m.label)}<td>${kindName[m.group]||m.group}<td>${m.calls}<td>${fcr(m.credits)}</tr>`).join('')}</table>`:'<div class=mut>Nothing generated yet.</div>'}
   <h3>By request</h3>${U.runs.length?`<table class=stbl><tr><th>Request<th>Batch<th>Jobs<th>Credits</tr>${U.runs.map(r=>`<tr><td>${esc(r.prompt||r.run)}<td>${esc(r.generation||'')}<td>${r.jobs.map(j=>`${j.kind}${j.status==='DONE'?'':' ('+j.status.toLowerCase()+')'}`).join(', ')}<td>${fcr(r.credits)}</tr>`).join('')}</table>`:'<div class=mut>No requests yet.</div>'}
   <h3>Every call</h3>${U.rows.length?`<div class=lv-scroll><table class=stbl><tr><th>When<th>Model<th>What<th>Settings<th>Seconds<th>Credits<th>Status</tr>${U.rows.map(r=>`<tr><td>${when(r.ts)}<td>${logoHtml(r,'sm')} ${esc(r.label)}<td>${esc(kindName[r.group]||r.group)}${r.job?' · '+esc(r.job):''}<td>${esc(r.params||'')}<td>${r.latency_ms?Math.round(r.latency_ms/1000):''}<td>${r.credits!=null?fcr(r.credits):(r.tokens?r.tokens+' tokens':'')}<td>${r.status==='OK'?'ok':`<span style="color:var(--bad)">${esc(r.status||'')}</span>`}</tr>`).join('')}</table></div>`:'<div class=mut>No calls yet.</div>'}
   <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button></div></div>`)};

/* ---------- styles + models panel under the request box */
function livePanel(){const g=document.querySelector('.gen2');if(!g||document.getElementById('lvpanel')||!LIVE.m)return;
  const opts=document.querySelector('.gopts'),el=document.createElement('div');el.id='lvpanel';(opts?opts.insertAdjacentElement('afterend',el):g.appendChild(el));drawPanel()}
function drawPanel(){const el=document.getElementById('lvpanel');if(!el||!LIVE.m)return;
  const im=lsel('image'),vi=lsel('video');
  el.innerHTML=`<div class=lv-row><span class=mut>Style</span><div class=lv-styles>${LIVE.m.styles.map(s=>`<button class="lv-style ${LIVE.style===s.id?'on':''}" data-act=lstyle data-id="${esc(s.id)}" title="${esc(s.hint)}"><img src="/assets/styles/${esc(s.id)}" alt="" loading=lazy><span>${esc(s.label)}</span></button>`).join('')}</div></div>
   <div class=lv-row><span class=mut>Models</span><button class="lv-model" data-act=lmodels>${logoHtml(im.model)}<span><small>Image</small><b>${esc(im.model?im.model.label:'?')}</b><em>${esc(optSummary(im.model,im.sel))}</em></span></button>
    <button class="lv-model" data-act=lmodels>${logoHtml(vi.model)}<span><small>Animation</small><b>${esc(vi.model?vi.model.label:'?')}</b><em>${esc(optSummary(vi.model,vi.sel))}</em></span></button>
    <span class=mut id=lvhint>${LIVE.hf&&LIVE.hf.available===false?'Higgsfield is not installed: only prepared sheets can be used.':'Used when no prepared sheet matches the request.'}</span></div>`}
ACT.lstyle=el=>{LIVE.style=el.dataset.id;lsave();drawPanel();if(typeof composerDraw==='function')composerDraw();if(typeof planPreview==='function')planPreview()};

/* ---------- the model dialog */
let LMD=null;
ACT.lmodels=()=>{LMD={};drawModels()};
function modelCard(kind,m,on){return`<button class="lv-mcard ${on?'on':''}" data-act=lmpick data-k=${kind} data-id="${esc(m.id)}">${logoHtml(m)}<span><b>${esc(m.label)}</b>${m.note?`<small>${esc(m.note)}</small>`:''}</span></button>`}
function modelSection(kind,title){const {model,sel}=lsel(kind),more=(LIVE.m.more||{})[kind]||[],isMore=model&&more.some(x=>x.id===model.id);
  return`<h3>${title}</h3><div class=lv-mgrid>${LIVE.m[kind].map(m=>modelCard(kind,m,model&&m.id===model.id)).join('')}</div>
   ${model?`<div class=lv-mopts>${model.options.map(o=>o.choices.length<2?`<span class=mut>${esc(o.label)}: <b>${esc(o.choices[0])}</b></span>`:`<label>${esc(o.label)} <select data-lvopt="${kind}|${esc(o.name)}">${o.choices.map(c=>`<option value="${esc(c)}" ${sel.options[o.name]===c?'selected':''}>${esc(c)}</option>`).join('')}</select></label>`).join('')}
    <span class=mut id=lvest-${kind}></span></div>`:''}
   ${more.length?`<details ${isMore?'open':''}><summary class=mut>All Higgsfield ${kind} models (${more.length} more${LIVE.m.counts&&LIVE.m.counts[kind]?` of ${LIVE.m.counts[kind]}`:''})</summary>
     <select data-lvmore="${kind}"><option value="">Choose another model…</option>${more.map(m=>`<option value="${esc(m.id)}" ${model&&m.id===model.id?'selected':''}>${esc(m.label)} (${esc(m.id)})</option>`).join('')}</select></details>`:''}`}
function drawModels(){if(!LIVE.m)return;
  dlg(`<div class="vdlg lv-md"><h2>Models</h2><div class=mut>What makes the sheet and what animates it. The price in credits is on the Generate button.</div>
   ${modelSection('image','Images')}${modelSection('video','Animation')}
   <div class=row style="justify-content:flex-end"><button class="btn pri" data-act=lmdone>Done</button></div></div>`);
  for(const k of ['image','video'])lcost(k)}
ACT.lmpick=el=>{const key=el.dataset.k==='image'?'img':'vid';LIVE[key]={id:el.dataset.id,options:{}};lsave();drawModels()};
ACT.lmdone=()=>{drawPanel();if(typeof composerDraw==='function')composerDraw();closeDlg()};
document.addEventListener('change',e=>{const t=e.target;if(t.dataset&&t.dataset.lvvid){LIVE.vid={id:t.value,options:{}};lsave();lsel('video');glast='';if(typeof tick==='function')tick(true);return}
  if(t.dataset&&t.dataset.lvopt){const [k,n]=t.dataset.lvopt.split('|'),key=k==='image'?'img':'vid';LIVE[key].options[n]=t.value;lsave();lcost(k)}
  if(t.dataset&&t.dataset.lvmore&&t.value){const key=t.dataset.lvmore==='image'?'img':'vid';LIVE[key]={id:t.value,options:{}};lsave();drawModels()}});
async function lcost(kind,quiet){const {model,sel}=lsel(kind);if(!model)return null;const key=kind+model.id+JSON.stringify(sel.options);
  if(LIVE.est[key]===undefined){const r=await post('/api/live/cost',{kind,model:model.id,options:sel.options});LIVE.est[key]=r.ok?r.j.credits:null}
  const e=document.getElementById('lvest-'+kind);if(e&&!quiet)e.textContent=LIVE.est[key]==null?'price not available':`≈ ${fcr(LIVE.est[key])} credits per ${kind==='image'?'sheet':'clip'}`;
  return LIVE.est[key]}

/* ---------- run: no questions. The price is on the button, the selection is the one made before; Generate just starts */
const liveReadyNow=()=>!!(LIVE.hf&&LIVE.hf.available&&!LIVE.hf.error&&LIVE.m);
function liveOffer(prompt){if(!liveReadyNow())return false;liveStart('sheet',{prompt,ai:typeof aiOn==='function'&&aiOn(),refs:[]});return true}
async function liveStart(kind,ctx){const isSheet=kind==='sheet',im=lsel('image'),vi=lsel('video'),est=await lcost(isSheet?'image':'video',true);
  if(est!=null&&LIVE.hf&&LIVE.hf.credits!=null&&est>LIVE.hf.credits){toast(`Not enough credits: this costs ${fcr(est)} and ${fcr(LIVE.hf.credits)} are left`,1);return false}
  const body=isSheet?{prompt:ctx.prompt,grid:'3x3',style_id:LIVE.style,ai:!!ctx.ai,outline:GS.outline,model:im.sel.id,options:im.sel.options,refs:ctx.refs||[]}
    :{kind:'video',generation:ctx.g,model:vi.sel.id,options:vi.sel.options};
  const r=await postWait(isSheet?'/api/live/sheet':'/api/live/video',body,'Finishing the previous step…');
  if(!r.ok){toast(r.j.error||'Could not start',1);return false}
  const m=lfind(isSheet?'image':'video',r.j.model);
  LIVE.jobs.push({id:r.j.job,kind:isSheet?'sheet':'video',label:isSheet?ctx.prompt:`Batch ${ctx.g}`,model:m?m.label:r.j.model,est:r.j.estimate,t0:Date.now(),gen:isSheet?null:ctx.g,ai:r.j.expanded_by==='ai'});
  if(isSheet&&ctx.ai&&r.j.expanded_by!=='ai')toast(`The AI enhancer could not be used (${r.j.expand_error||'no answer'}): the built-in prompt was sent instead`,1);
  lsave();say('');drawLive();liveTick();refreshHf();return true}

/* ---------- the animation box under the green screen: a model drop-down and one priced button (no dialog, no confirmation) */
const lcached=kind=>{const {model,sel}=lsel(kind);return model?LIVE.est[kind+model.id+JSON.stringify(sel.options)]:undefined};
function vgenBox(g){if(!liveReadyNow()||g.source.has_video||making(g))return'';
  const run=LIVE.jobs.find(j=>j.kind==='video'&&j.gen===g.number&&!j.error);
  if(run)return`<div class="lv-vgen run"><div class=spin></div><span>Animating with ${esc(run.model)}…<small data-lvt="${run.t0}">${Math.round((Date.now()-run.t0)/1000)}s</small></span></div>`;
  const {model,sel}=lsel('video'),c=lcached('video');if(c===undefined)lcost('video',true).then(fillPrices);
  return`<div class=lv-vgen><select class=lv-vsel data-lvvid aria-label="Animation model">${LIVE.m.video.map(m=>`<option value="${esc(m.id)}" ${model&&m.id===model.id?'selected':''}>${esc(m.label)}</option>`).join('')}</select>
   <button class="btn pri lv-vgo" data-act=lvgen data-g=${g.number} ${keptStills(g).length?'':'disabled'}>Generate<span class=lv-vp data-lvprice=video>${c==null?(c===undefined?'…':''):'◈ '+fcr(c)}</span></button></div>
   <div class=lv-vnote>${esc(optSummary(model,sel))} · <button class=link data-act=gvideo data-g=${g.number}>use my own tool</button></div>`}
function fillPrices(){const c=lcached('video');document.querySelectorAll('[data-lvprice=video]').forEach(e=>e.textContent=c==null?'':'◈ '+fcr(c))}
ACT.lvgen=async el=>{el.disabled=true;const ok=await liveStart('video',{g:+el.dataset.g});if(!ok)el.disabled=false;glast='';if(typeof tick==='function')tick(true)};

/* ---------- running jobs */
function drawLive(){const el=document.getElementById('glive');if(!el)return;
  el.innerHTML=LIVE.jobs.map(j=>`<div class="card lv-job ${j.error?'bad':''}">${j.error?'<span class=lv-x>!</span>':'<div class=spin></div>'}<div style="flex:1;min-width:0"><b>${j.error?'That did not work':j.kind==='sheet'?`Making the sheet with ${esc(j.model)}`:`Animating with ${esc(j.model)}`}</b>
    <div class=mut>${esc(j.label)}${j.ai?' · AI-enhanced':''} · job ${esc(j.id)} · ${j.error?esc(j.error):`<span data-lvt="${j.t0}">${Math.round((Date.now()-j.t0)/1000)}s</span> · ${esc(j.status||'waiting for Higgsfield')} · ≈ ${fcr(j.est)} credits`}</div></div>
    ${j.error?`<button class="btn sm" data-act=ljdismiss data-id="${esc(j.id)}">Dismiss</button>`:''}</div>`).join('')}
ACT.ljdismiss=el=>{LIVE.jobs=LIVE.jobs.filter(j=>j.id!==el.dataset.id);lsave();drawLive()};
let LTB=false;
async function liveTick(){if(LTB||!LIVE.jobs.length)return;LTB=true;try{
  for(const j of [...LIVE.jobs]){if(j.error)continue;const r=await api('/api/jobs/'+j.id);if(!r.ok){if(r.status===404){LIVE.jobs=LIVE.jobs.filter(x=>x.id!==j.id)}continue}
    const s=r.j;j.status=s.status==='REQUESTED'?'starting':s.status==='CLAIMED'?'Higgsfield is working':s.status.toLowerCase();
    if(s.status==='FAILED'||s.status==='TIMEOUT'){j.error=s.error||s.status.toLowerCase();refreshHf()}
    else if(s.status==='DONE'&&(j.kind==='video'||s.generation)){
      LIVE.jobs=LIVE.jobs.filter(x=>x.id!==j.id);await refreshHf();
      toast(`${j.kind==='sheet'?'Sheet':'Animation'} ready: ${fcr(s.cost)} credits used${LIVE.hf&&LIVE.hf.credits!=null?`, ${fcr(LIVE.hf.credits)} left`:''}`);
      if(j.kind==='sheet'){SES={prompt:j.label,gens:[+String(s.generation).replace(/\D/g,'')],off:[],pack:''};saveSes();GS.tab='stickers';glast='';
        for(const p of PVS.values())p.v.remove();PVS.clear();PVON.clear();ANIM.clear();location.hash='#/studio'}
      else{GS.tab='anim';glast=''}
      if(typeof tick==='function')tick(true)}}
  lsave();drawLive()}finally{LTB=false}}
setInterval(liveTick,2500);
setInterval(()=>{document.querySelectorAll('[data-lvt]').forEach(e=>e.textContent=Math.round((Date.now()-(+e.dataset.lvt))/1000)+'s')},1000);

/* ---------- start-up and hooks into the Studio screen */
const _rg=RENDER.generate;
const showPanel=()=>{typeof composerMount==='function'?composerMount():livePanel()};
RENDER.generate=async function(){await _rg.apply(this,arguments);showPanel();drawLive()};
async function liveInit(){const [m,h]=await Promise.all([api('/api/models'),api('/api/higgsfield')]);if(m.ok){LIVE.m=m.j;if(!m.j.styles.some(s=>s.id===LIVE.style))LIVE.style=m.j.default_style;lsel('image');lsel('video')}
  if(h.ok)LIVE.hf=h.j;drawChip();if(route_==='generate'){showPanel();drawLive()};liveTick()}
setInterval(refreshHf,20000);
liveInit();
