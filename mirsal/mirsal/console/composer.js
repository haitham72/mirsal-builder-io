/* The Generate menu ("composer"): one prompt box with reference images inside it, the model and the stroke in the bar under it, and the sticker styles as
   large cards. It replaces the old input row on the Studio screen; everything below it (prepared sheets, prompt preview, results) is unchanged.
   Generate always makes a NEW sheet with Higgsfield when it is available (prepared sheets stay one click away in the chips below); without it, the old
   lookup of prepared sheets runs. Every control is wired: the model/style/stroke/references go to /api/live/sheet exactly as shown. */
'use strict';
const CP={refs:[],pop:null,ai:false,go:false,menu:false,styles:false};
try{CP.ai=localStorage.getItem('mirsal.ai')==='1'}catch(e){}
const aiOn=()=>CP.ai&&!!(typeof GAI!=='undefined'&&GAI.configured);
/* GAI is GET /api/ai: `configured` is true when ANY backend the person's engine choice allows can answer (auto: the local model when LM Studio listens, else the cloud key; local; cloud with a key), so LM Studio alone enables the chip. When it is off, the tooltip says which of the two is missing */
function aiWhy(){const g=typeof GAI!=='undefined'?GAI:{},av=g.availability||{},pref=g.preference||'auto',lw=(av.local&&av.local.why)||'',cw=(av.cloud&&av.cloud.why)||'';
  if(pref==='local')return `Local is chosen and it is not available${lw?' ('+lw+')':''}. Start LM Studio, or pick Auto or Cloud below.`;
  if(pref==='cloud')return `Cloud is chosen and ${cw||'OPENAI_API_KEY is missing from mirsal/.env'}. Add it, or pick Auto or Local below.`;
  return 'No AI model is reachable: start LM Studio (free) or add OPENAI_API_KEY to mirsal/.env.'}
function aiChipTitle(){const g=typeof GAI!=='undefined'?GAI:{};
  if(!g.configured)return aiWhy();
  const cloud=g.provider==='openai';
  return `Writes nine different, expressive concepts from your text before the sheet is sent, with the engine chosen below (${gdEngineName()||'no model'}). ${cloud?'Cloud: one small OpenAI call.':'Local: free.'} Off = your text goes straight into the prompt template.`}

const STROKES=[[0,'None'],[4,'Thin'],[8,'Medium'],[12,'Bold'],[16,'Max']];
try{const o=localStorage.getItem('mirsal.outline');if(o!==null&&STROKES.some(s=>s[0]===+o))GS.outline=+o}catch(e){}
const strokeName=px=>(STROKES.find(s=>s[0]===px)||[px,px+' px'])[1];
const glyph=px=>`<svg class=cp-gl viewBox="0 0 40 40" aria-hidden=true><rect width=40 height=40 rx=11 fill="#cbd5e1"/><circle cx="20" cy="20" r="${(11.5-px*0.12).toFixed(1)}" fill="#3B82F6" stroke="#fff" stroke-width="${(px*0.3).toFixed(1)}"/></svg>`;
const liveReady=()=>!!(LIVE.hf&&LIVE.hf.available&&!LIVE.hf.error&&LIVE.m);

function composerMount(){const g=document.querySelector('.gen2');if(!g||!LIVE.m||document.getElementById('cpwrap'))return;
  const prev=$('prompt')?$('prompt').value:'';
  g.querySelectorAll(':scope > .sh, :scope > .gform, :scope > .gopts, #lvpanel').forEach(n=>n.remove());
  const w=document.createElement('section');w.id='cpwrap';w.className='cp';g.insertBefore(w,g.firstChild);
  w.innerHTML=`<div class=cp-halo></div>
   <header class=cp-head><img class=cp-orb src=/assets/brand/mirsal-logo.png alt=""><h1>Studio</h1><span class=cp-gap></span><div class=cp-top id=cptop></div></header>
   <div class=cp-box id=cpbox>
    <div class=cp-refs id=cprefs></div>
    <textarea id=prompt rows=2 placeholder="Describe your stickers, for example: an angel reading a newspaper" autocomplete=off spellcheck=false></textarea>
    <div class=cp-bar id=cpbar></div>
    <div class=cp-engwrap id=cpeng hidden></div>
    <div class=cp-drop>Drop images to use them as references</div>
   </div>
   <div class=cp-styles id=cpstyles></div>`;
  const p=$('prompt');p.value=gdOn()?GD.prompt:SES.prompt||prev||'';
  p.oninput=()=>grow();
  p.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ACT.ggo()}};
  const grow=()=>{p.style.height='auto';p.style.height=Math.min(p.scrollHeight,190)+'px'};grow();
  const box=$('cpbox');
  ['dragenter','dragover'].forEach(t=>box.addEventListener(t,e=>{if(e.dataTransfer&&[...e.dataTransfer.types].includes('Files')){e.preventDefault();box.classList.add('over')}}));
  ['dragleave','drop'].forEach(t=>box.addEventListener(t,e=>{if(t==='drop'||e.target===box)box.classList.remove('over')}));
  box.addEventListener('drop',e=>{if(e.dataTransfer&&e.dataTransfer.files.length){e.preventDefault();cpAddFiles([...e.dataTransfer.files])}});
  p.addEventListener('paste',e=>{const fs=[...(e.clipboardData&&e.clipboardData.files||[])].filter(f=>f.type.startsWith('image/'));if(fs.length){e.preventDefault();cpAddFiles(fs)}});
  composerDraw()}
function composerDraw(){if(!document.getElementById('cpwrap'))return;cpDrawRefs();cpDrawBar();cpDrawStyles();cpDrawTop()}

/* ---------- Higgsfield credits at the top, with a drop-down: balance, today's spend, the usage log and the recent batches */
function cpDrawTop(){const el=$('cptop');if(!el)return;const h=LIVE.hf;
  const me=typeof ME!=='undefined'?ME:null;                 // an office member (auth.js) pays from their own balance: their credits, and the way to ask for more
  if(me&&me.id!=='local'&&me.credits_left!=null){const n=Math.round(me.credits_left*10)/10;
    el.innerHTML=`<button class="cp-cr${n<=0?' off':''}" data-act=aucreditask title="Your own credits (each person starts with 10). Click to ask Haitham for more."><span class=cp-coin>◈</span><b>${n}</b><small>${n<=0?'no credits: ask for more':'credits'}</small></button>`;return}
  if(!h||h.available===false){el.innerHTML=`<span class=cp-cr off title="${esc(h&&h.error||'Higgsfield is not available')}">Higgsfield off</span>`;return}
  const items=(typeof HB!=='undefined'?HB.items:[]).slice(0,8),nRun=(LIVE.q||[]).filter(j=>['REQUESTED','CLAIMED'].includes(j.status)&&Date.now()/1000-(j.created_at||0)<86400).length;
  el.innerHTML=`<button class="cp-cr ${CP.menu?'open':''}" data-act=cpmenu aria-haspopup=true aria-expanded=${CP.menu} title="Higgsfield credits left. Click for the usage and your recent batches."><span class=cp-coin>◈</span><b>${h.error?'!':fcr(Math.round(h.credits*10)/10)}</b><small>credits</small>${nRun?`<span class=cp-run title="${nRun} running">${nRun} running</span>`:''}<i></i></button>
   ${CP.menu?`<div class=cp-menu role=menu><div class=cp-mh><div><small>Credits left</small><b>${h.error?'?':fcr(h.credits)}</b></div><div><small>Spent today</small><b>${fcr(h.spent_today)}</b></div><button class="btn sm" data-act=lusage>Usage log</button></div>
     ${h.error?`<div class=cp-mw>${esc(h.error)}</div>`:''}
     <div class=cp-ml>${items.length?items.map(it=>`<button data-act=hopen data-id=${it.id}><span class=cp-mt>${(()=>{const c=(it.cells||[]).find(c=>c.png);return c?`<img src="/out/${esc(it.generation_id)}/${esc(c.png)}" alt="">`:''})()}</span><span><b>${esc(titleCase(String(it.prompt||'').replace(/_/g,' ')))}</b><small>${esc(it.generation_id)} · edited ${ago(it.edited||it.created)}</small></span></button>`).join(''):'<div class=cp-mw>No batches yet.</div>'}</div>
     </div>`:''}`}
ACT.cpmenu=e=>{CP.menu=!CP.menu;cpDrawTop();if(e&&e.stopPropagation)e.stopPropagation()};
document.addEventListener('click',e=>{if(CP.menu&&!inside(e,'cp-top')){CP.menu=false;cpDrawTop()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&CP.menu){CP.menu=false;cpDrawTop()}});

/* ---------- reference images (inside the prompt box) */
function cpDrawRefs(){const el=$('cprefs');if(!el)return;const {model}=lsel('image'),ok=!model||model.refs!==false;
  el.innerHTML=CP.refs.map((r,i)=>`<div class="cp-ref ${r.busy?'busy':''}" title="${esc(r.name)}"><img src="${esc(r.url)}" alt=""><button data-act=cprefx data-i=${i} aria-label="Remove ${esc(r.name)}">${ic('x')}</button></div>`).join('')
    +(CP.refs.length<4?`<button class=cp-add data-act=cpadd ${ok?'':'disabled'} title="${ok?'Add reference images':esc(model.label)+' does not take reference images'}">${ic('plus')}<span>${CP.refs.length?'':'Reference'}</span></button>`:'')
    +`<input type=file id=cpfile accept="image/png,image/jpeg,image/webp" multiple hidden>`;
  const f=$('cpfile');if(f)f.onchange=()=>{cpAddFiles([...f.files]);f.value=''};
  el.classList.toggle('has',CP.refs.length>0)}
ACT.cpadd=()=>{const f=$('cpfile');if(f)f.click()};
ACT.cprefx=el=>{CP.refs.splice(+el.dataset.i,1);cpDrawRefs()};
async function cpAddFiles(files){const {model}=lsel('image');if(model&&model.refs===false){toast(`${model.label} does not take reference images`,1);return}
  for(const f of files){if(CP.refs.length>=4){toast('Up to 4 reference images',1);break}
    if(!/^image\/(png|jpe?g|webp)$/.test(f.type)){toast(`${f.name}: use PNG, JPG or WebP`,1);continue}
    const t={id:null,name:f.name,busy:true,url:URL.createObjectURL(f)};CP.refs.push(t);cpDrawRefs();
    let j={};try{const r=await fetch('/api/live/ref?name='+encodeURIComponent(f.name),{method:'POST',body:f});j=await r.json();if(!r.ok)throw new Error(j.error||'Upload failed')}
    catch(e){CP.refs=CP.refs.filter(x=>x!==t);toast(e.message,1);cpDrawRefs();continue}
    t.id=j.id;t.busy=false;cpDrawRefs()}}

/* ---------- the bar: model, stroke, price, Generate */
function cpDrawBar(){const el=$('cpbar');if(!el)return;const {model,sel}=lsel('image'),st=GS.outline;
  const sty=(LIVE.m&&LIVE.m.styles||[]).find(x=>x.id===LIVE.style);
  el.innerHTML=`<button class=cp-chip data-act=lmodels title="Choose the image model">${logoHtml(model)}<span><b>${esc(model?model.label:'Model')}</b><em>${esc(optSummary(model,sel))}</em></span></button>
   <button class="cp-chip ${CP.styles?'open':''}" data-act=cpstyles aria-expanded=${!!CP.styles} title="Choose the look of the stickers">${sty?`<img class=cp-chipimg src="/assets/styles/${esc(sty.id)}" alt="">`:''}<span><b>Style</b><em>${esc(sty?sty.label:'Choose')}</em></span></button>
   <div class=cp-pw><button class="cp-chip ${CP.pop==='stroke'?'open':''}" data-act=cpstroke aria-haspopup=true aria-expanded=${CP.pop==='stroke'}>${glyph(st)}<span><b>Stroke</b><em>${strokeName(st)}</em></span></button>
    ${CP.pop==='stroke'?`<div class=cp-pop role=menu>${STROKES.map(([px,n])=>`<button role=menuitemradio aria-checked=${px===st} class="${px===st?'on':''}" data-act=cpstrokeset data-px=${px}>${glyph(px)}<span><b>${n}</b><em>${px?px+' px':'no border'}</em></span></button>`).join('')}</div>`:''}</div>
   <button class="cp-chip cp-ai ${LIVE.loop?'on':''}" data-act=cploop aria-pressed=${!!LIVE.loop} title="Off: the animation plays once through and Mirsal closes the loop itself. On: the video prompt asks for a loop and Kling ends on its first pose. A loop wording makes the stickers bounce several times in the 3 seconds."><span class=cp-sw><i></i></span><span><b>Loop</b><em>${LIVE.loop?'On':'Off'}</em></span></button>
   <button class="cp-chip cp-ai ${aiOn()?'on':''}" data-act=cpai aria-pressed=${aiOn()} ${GAI&&GAI.configured?'':'disabled'} title="${esc(aiChipTitle())}"><span class=cp-sw><i></i></span><span><b>AI enhancer</b><em>${aiOn()?'On':'Off'}</em></span></button>
   <span class=cp-gap></span>
   ${GD&&!gdOn()?'<button class="btn sm" data-act=gdtab data-t=plan title="Return to the prompt you were editing">Prompt draft</button>':''}
   <button id=go class=cp-go data-act=gprompt title="${aiOn()&&GAI.provider==='openai'?'Shows the prompt you can edit before any sheet is paid for; the AI enhancer makes one small OpenAI call to write it. No batch is created and no Higgsfield credits are spent.':'Free. Shows the prompt you can edit before any sheet is paid for; no batch is created.'} Pressing Enter in the box still starts a paid sheet at once.">Generate prompt <span class=cp-bp>${aiOn()&&GAI.provider==='openai'?'1 AI call':'free'}</span></button>`;
  cpDrawEngine()}
/* the AI enhancer's engine: the AI screen's own control (Auto / Local / Cloud, the local model drop-down, the one line saying which model answers or why it cannot; agent.js, AIENG.rows) shown under the bar while the enhancer is On,
   and also while it cannot run, so the person can pick an engine that can. One implementation, the same endpoints (an owner picks; a member sees the server's refusal as a toast). */
const cpEngSrc=()=>{const g=typeof GAI!=='undefined'?GAI:{};return{agent:{provider:g.provider||'none',model:g.model||''},agent_status:{},availability:g.availability||{},preference:g.preference||'auto',noModel:'no model, the built-in prompt is used'}};
function cpDrawEngine(){const el=$('cpeng');if(!el)return;const show=typeof AIENG!=='undefined'&&(CP.ai||!(GAI&&GAI.configured));
  el.hidden=!show;if(!show){el.innerHTML='';el._h='';return}          // forget what was drawn: turning the enhancer On again must draw the engine again (it stayed empty)
  AIENG.ensure();
  const html=`<div class="ai-set on cp-eng" aria-label="AI enhancer engine" title="Local: free. Cloud: one small OpenAI call.">${AIENG.rows(cpEngSrc())}</div>`;
  if(el._h!==html){el._h=html;el.innerHTML=html}}          // only when it changed: the bar is redrawn often, and a redraw would close an open drop-down
ACT.cploop=()=>{LIVE.loop=!LIVE.loop;lsave();cpDrawBar();document.querySelectorAll('[data-lvloop]').forEach(c=>c.checked=LIVE.loop)};
ACT.cpai=()=>{CP.ai=!CP.ai;gstore('mirsal.ai',CP.ai?'1':'0');cpDrawBar();if(CP.ai){if(typeof AIENG!=='undefined')AIENG.load();if(typeof aiRefresh==='function')aiRefresh()}};      // turning it On reads the engine and the models again (LM Studio may have started since the page opened)
ACT.cpstroke=e=>{CP.pop=CP.pop==='stroke'?null:'stroke';cpDrawBar();if(e&&e.stopPropagation)e.stopPropagation()};
ACT.cpstrokeset=el=>{GS.outline=+el.dataset.px;gstore('mirsal.outline',GS.outline);CP.pop=null;cpDrawBar()};
const inside=(e,cls)=>e.composedPath().some(n=>n.classList&&n.classList.contains(cls));      // the path at the time of the click: the clicked node may already be replaced by a redraw
document.addEventListener('click',e=>{if(CP.pop&&!inside(e,'cp-pw')){CP.pop=null;cpDrawBar()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&CP.pop){CP.pop=null;cpDrawBar()}});
drawOutline=function(){cpDrawBar()};                 // the old On/Off pills are gone; the Request tab's On/Off still sets GS.outline and lands here

/* ---------- the styles: hidden until the Style chip is clicked (Haitham, 2026-10-04: the always-open tiles took three rows); picking one closes them */
ACT.cpstyles=e=>{CP.styles=!CP.styles;cpDrawBar();cpDrawStyles();if(e&&e.stopPropagation)e.stopPropagation()};
ACT.cpstylepick=el=>{CP.styles=false;ACT.lstyle(el)};
function cpDrawStyles(){const el=$('cpstyles');if(!el||!LIVE.m)return;
  if(!CP.styles){el.innerHTML='';return}
  el.innerHTML=LIVE.m.styles.map(s=>`<button class="cp-style ${LIVE.style===s.id?'on':''}" data-act=cpstylepick data-id="${esc(s.id)}" aria-pressed=${LIVE.style===s.id}><img src="/assets/styles/${esc(s.id)}" alt="" loading=lazy><span><b>${esc(s.label)}</b><em>${esc(s.hint)}</em></span></button>`).join('')}

/* ---------- Generate: a NEW sheet with Higgsfield (after the price is confirmed), else the prepared-sheet lookup */
const _ggo=ACT.ggo;
ACT.ggo=()=>{const p=(($('prompt')||{}).value||'').trim();
  if(!p){say('Write what you want first, for example <b>an angel reading a newspaper</b>.');return}
  if(liveReady()){say('');
    if(CP.refs.some(r=>r.busy)){toast('Wait for the reference images to finish uploading',1);return}
    if(CP.go)return;CP.go=true;const b=$('go');if(b)b.disabled=true;
    gdHide();liveStart('sheet',{prompt:p,ai:aiOn(),refs:CP.refs.filter(r=>r.id).map(r=>r.id)}).finally(()=>{CP.go=false;cpDrawBar()});return}
  if(CP.refs.length){say('Reference images need Higgsfield, which is not available right now.');return}
  return _ggo()};
ACT.gsug=el=>{$('prompt').value=el.dataset.s.replace(/_/g,' ');_ggo()};      // a prepared-sheet chip uses the prepared sheet, never a new generation
