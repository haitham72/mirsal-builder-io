/* The Generate menu ("composer"): one prompt box with reference images inside it, the model and the stroke in the bar under it, and the sticker styles as
   large cards. It replaces the old input row on the Studio screen; everything below it (prepared sheets, prompt preview, results) is unchanged.
   Generate always makes a NEW sheet with Higgsfield when it is available (prepared sheets stay one click away in the chips below); without it, the old
   lookup of prepared sheets runs. Every control is wired: the model/style/stroke/references go to /api/live/sheet exactly as shown. */
'use strict';
const CP={refs:[],pop:null,ai:false,go:false};
try{CP.ai=localStorage.getItem('mirsal.ai')==='1'}catch(e){}
const aiOn=()=>CP.ai&&!!(typeof GAI!=='undefined'&&GAI.configured);
const STROKES=[[0,'None'],[4,'Thin'],[8,'Medium'],[12,'Bold'],[16,'Max']];
try{const o=localStorage.getItem('mirsal.outline');if(o!==null&&STROKES.some(s=>s[0]===+o))GS.outline=+o}catch(e){}
const strokeName=px=>(STROKES.find(s=>s[0]===px)||[px,px+' px'])[1];
const glyph=px=>`<svg class=cp-gl viewBox="0 0 40 40" aria-hidden=true><rect width=40 height=40 rx=11 fill="#0e1633"/><circle cx="20" cy="20" r="${(11.5-px*0.12).toFixed(1)}" fill="#3466ff" stroke="#fff" stroke-width="${(px*0.3).toFixed(1)}"/></svg>`;
const liveReady=()=>!!(LIVE.hf&&LIVE.hf.available&&!LIVE.hf.error&&LIVE.m);

function composerMount(){const g=document.querySelector('.gen2');if(!g||!LIVE.m||document.getElementById('cpwrap'))return;
  const prev=$('prompt')?$('prompt').value:'';
  g.querySelectorAll(':scope > .sh, :scope > .gform, :scope > .gopts, #lvpanel').forEach(n=>n.remove());
  const w=document.createElement('section');w.id='cpwrap';w.className='cp';g.insertBefore(w,g.firstChild);
  w.innerHTML=`<div class=cp-halo></div>
   <header class=cp-head><img class=cp-orb src=/assets/brand/mirsal-logo.png alt=""><h1>Studio</h1></header>
   <div class=cp-box id=cpbox>
    <div class=cp-refs id=cprefs></div>
    <textarea id=prompt rows=2 placeholder="Describe your stickers, for example: an angel reading a newspaper" autocomplete=off spellcheck=false></textarea>
    <div class=cp-bar id=cpbar></div>
    <div class=cp-drop>Drop images to use them as references</div>
   </div>
   <div class=cp-styles id=cpstyles></div>`;
  const p=$('prompt');p.value=SES.prompt||prev||'';
  p.oninput=()=>{grow();planPreview()};planPreview();
  p.onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ACT.ggo()}};
  const grow=()=>{p.style.height='auto';p.style.height=Math.min(p.scrollHeight,190)+'px'};grow();
  const box=$('cpbox');
  ['dragenter','dragover'].forEach(t=>box.addEventListener(t,e=>{if(e.dataTransfer&&[...e.dataTransfer.types].includes('Files')){e.preventDefault();box.classList.add('over')}}));
  ['dragleave','drop'].forEach(t=>box.addEventListener(t,e=>{if(t==='drop'||e.target===box)box.classList.remove('over')}));
  box.addEventListener('drop',e=>{if(e.dataTransfer&&e.dataTransfer.files.length){e.preventDefault();cpAddFiles([...e.dataTransfer.files])}});
  p.addEventListener('paste',e=>{const fs=[...(e.clipboardData&&e.clipboardData.files||[])].filter(f=>f.type.startsWith('image/'));if(fs.length){e.preventDefault();cpAddFiles(fs)}});
  composerDraw()}
function composerDraw(){if(!document.getElementById('cpwrap'))return;cpDrawRefs();cpDrawBar();cpDrawStyles()}

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
  el.innerHTML=`<button class=cp-chip data-act=lmodels title="Choose the image model">${logoHtml(model)}<span><b>${esc(model?model.label:'Model')}</b><em>${esc(optSummary(model,sel))}</em></span></button>
   <div class=cp-pw><button class="cp-chip ${CP.pop==='stroke'?'open':''}" data-act=cpstroke aria-haspopup=true aria-expanded=${CP.pop==='stroke'}>${glyph(st)}<span><b>Stroke</b><em>${strokeName(st)}</em></span></button>
    ${CP.pop==='stroke'?`<div class=cp-pop role=menu>${STROKES.map(([px,n])=>`<button role=menuitemradio aria-checked=${px===st} class="${px===st?'on':''}" data-act=cpstrokeset data-px=${px}>${glyph(px)}<span><b>${n}</b><em>${px?px+' px':'no border'}</em></span></button>`).join('')}</div>`:''}</div>
   <button class="cp-chip cp-ai ${aiOn()?'on':''}" data-act=cpai aria-pressed=${aiOn()} ${GAI&&GAI.configured?'':'disabled'} title="${GAI&&GAI.configured?'Writes nine different, expressive concepts from your text before the sheet is sent. One small OpenAI call; off = your text goes straight into the prompt template.':'Add OPENAI_API_KEY to mirsal/.env to use the AI enhancer.'}"><span class=cp-sw><i></i></span><span><b>AI enhancer</b><em>${aiOn()?'On':'Off'}</em></span></button>
   <span class=cp-gap></span>
   <button id=go class=cp-go data-act=ggo title="Starts at once with the model, style and stroke shown here. The number is the price in Higgsfield credits.">Generate${liveReady()?'<span class=cp-bp id=cpprice>…</span>':''}</button>`;
  if(liveReady())lcost('image',true).then(c=>{const e=$('cpprice');if(e)e.textContent=c==null?'':'◈ '+fcr(c)})}
ACT.cpai=()=>{CP.ai=!CP.ai;gstore('mirsal.ai',CP.ai?'1':'0');cpDrawBar();planPreview()};
ACT.cpstroke=e=>{CP.pop=CP.pop==='stroke'?null:'stroke';cpDrawBar();if(e&&e.stopPropagation)e.stopPropagation()};
ACT.cpstrokeset=el=>{GS.outline=+el.dataset.px;gstore('mirsal.outline',GS.outline);CP.pop=null;cpDrawBar()};
document.addEventListener('click',e=>{if(CP.pop&&!e.target.closest('.cp-pw')){CP.pop=null;cpDrawBar()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&CP.pop){CP.pop=null;cpDrawBar()}});
drawOutline=function(){cpDrawBar()};                 // the old On/Off pills are gone; the Request tab's On/Off still sets GS.outline and lands here

/* ---------- the styles */
function cpDrawStyles(){const el=$('cpstyles');if(!el||!LIVE.m)return;
  el.innerHTML=LIVE.m.styles.map(s=>`<button class="cp-style ${LIVE.style===s.id?'on':''}" data-act=lstyle data-id="${esc(s.id)}" aria-pressed=${LIVE.style===s.id}><img src="/assets/styles/${esc(s.id)}" alt="" loading=lazy><span><b>${esc(s.label)}</b><em>${esc(s.hint)}</em></span></button>`).join('')}

/* ---------- Generate: a NEW sheet with Higgsfield (after the price is confirmed), else the prepared-sheet lookup */
const _ggo=ACT.ggo;
ACT.ggo=()=>{const p=(($('prompt')||{}).value||'').trim();
  if(!p){say('Write what you want first, for example <b>an angel reading a newspaper</b>.');return}
  if(liveReady()){say('');
    if(CP.refs.some(r=>r.busy)){toast('Wait for the reference images to finish uploading',1);return}
    if(CP.go)return;CP.go=true;const b=$('go');if(b)b.disabled=true;
    liveStart('sheet',{prompt:p,ai:aiOn(),refs:CP.refs.filter(r=>r.id).map(r=>r.id)}).finally(()=>{CP.go=false;cpDrawBar()});return}
  if(CP.refs.length){say('Reference images need Higgsfield, which is not available right now.');return}
  return _ggo()};
ACT.gsug=el=>{$('prompt').value=el.dataset.s.replace(/_/g,' ');planPreview();_ggo()};      // a prepared-sheet chip uses the prepared sheet, never a new generation
