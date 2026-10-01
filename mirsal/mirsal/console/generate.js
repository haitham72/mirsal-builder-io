/* Generate: create {subject} -> create more -> add 1-n.
   A session is the batches (sheets) the user has created for one request. Each batch is a real generation; "Create more" makes the next one on purpose;
   Animate and Add act on every included batch. The review gates are still decided and recorded by the server behind those clicks:
   Generate approves the plan, the x on a tile is a human reject, Add approves what was kept and the pack. */
'use strict';
const GM=new Map();                       // generation id -> its latest state
let SES={prompt:'',gens:[],off:[],pack:''},bg='checker',glast='',MD=null,VG=null,GINP=[],GHEALTH=null;
const GS={outline:12,tile:220};
const ANIM=new Set();                     // batches the user pressed Animate on, until the server reports them animating
try{const o=localStorage.getItem('mirsal.outline');if(o!==null&&!isNaN(+o))GS.outline=+o>0?12:0;const t=+localStorage.getItem('mirsal.tile');if(t>=130&&t<=420)GS.tile=t;
  const s=JSON.parse(localStorage.getItem('mirsal.session')||'null');if(s&&Array.isArray(s.gens))SES={prompt:s.prompt||'',gens:s.gens,off:s.off||[],pack:s.pack||''}}catch(e){}
const gstore=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const saveSes=()=>gstore('mirsal.session',JSON.stringify(SES));
const wait=ms=>new Promise(f=>setTimeout(f,ms));
const BGS=[['checker','Transparent'],['light','Light'],['dark','Dark'],['wall','Wallpaper']];
const titleCase=s=>s.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());

/* a step that has to wait for a running job waits quietly; it never scolds the user with "busy" */
async function postWait(u,b,label){let r=await post(u,b);
  for(let n=0;n<180&&!r.ok&&r.status===409&&/busy/i.test(r.j.error||'');n++){say(label||'Waiting for the previous step to finish…');await wait(1000);r=await post(u,b)}
  say('');return r}

/* ---------- live preview: the paired 3x3 video is played in the browser and keyed like the stickers, so Animate shows motion at once
   while the real 512x512 WEBMs encode on the server (one hidden video per batch) */
const PVS=new Map(),PVON=new Set();
function pvEnsure(g){let p=PVS.get(g.number);if(p)return p;
  const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.style.cssText='position:fixed;width:1px;height:1px;opacity:0;pointer-events:none';
  v.src=`/src/${g.number}/video`;document.body.appendChild(v);v.play().catch(()=>{});p={v,cal:{},t:-1};PVS.set(g.number,p);return p}
function vcell(g,v,i){const G=g.source.grid,sw=g.source.sheet_size;if(G&&sw){const r=G.rects[i-1],kx=v.videoWidth/sw[0],ky=v.videoHeight/sw[1];return[r[0]*kx,r[1]*ky,r[2]*kx,r[3]*ky]}
  const n=g.grid?g.grid[1]:3,w=v.videoWidth/n,h=v.videoHeight/n;return[((i-1)%n)*w,((i-1)/n|0)*h,w,h]}
function pvCalibrate(g,v,i){const [X,Y,cw,ch]=vcell(g,v,i),S=96,c=document.createElement('canvas');c.width=c.height=S;const x=c.getContext('2d',{willReadFrequently:true});
  x.drawImage(v,X,Y,cw,ch,0,0,S,S);const d=x.getImageData(0,0,S,S).data,D=[];
  for(let y=0;y<S;y++)for(let xx=0;xx<S;xx++){if(y>2&&y<S-3&&xx>2&&xx<S-3)continue;const o=(y*S+xx)*4,r=d[o],gg=d[o+1],b=d[o+2];D.push(gg-Math.max(r,b))}
  D.sort((a,b)=>a-b);return Math.max(.5*D[D.length>>1],8)}
function pvDraw(cv,g,p,i){const v=p.v;if(!v||v.readyState<2||!v.videoWidth)return;
  const t=g.stickers[i-1],m=t.metrics||{},c=m.cell,b=m.bbox,S=cv.width,[X,Y,cw,ch]=vcell(g,v,i);
  let fx=.5,fy=.5,fs=1;if(c&&b&&m.scale){fx=(b[0]+b[2])/2/c[2];fy=(b[1]+b[3])/2/c[3];fs=Math.min(3,(512/m.scale)/c[2])}
  const side=fs*(cw+ch)/2,cx=X+fx*cw,cy=Y+fy*ch;let sx=cx-side/2,sy=cy-side/2,sw=side,sh=side;
  const x0=Math.max(sx,X),y0=Math.max(sy,Y),x1=Math.min(sx+sw,X+cw),y1=Math.min(sy+sh,Y+ch),k=S/side;
  const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,S,S);if(x1<=x0||y1<=y0)return;
  ctx.drawImage(v,x0,y0,x1-x0,y1-y0,(x0-sx)*k,(y0-sy)*k,(x1-x0)*k,(y1-y0)*k);
  if(p.cal[i]===undefined)p.cal[i]=pvCalibrate(g,v,i);const T=p.cal[i],im=ctx.getImageData(0,0,S,S),d=im.data;
  for(let o=0;o<d.length;o+=4){if(!d[o+3])continue;const r=d[o],gg=d[o+1],bb=d[o+2],mx=Math.max(r,bb);let a=2*(T-(gg-mx))/T;a=a<0?0:a>1?1:a;
    if(a<.98&&a>0&&gg>mx)d[o+1]=mx;d[o+3]=d[o+3]*a}
  ctx.putImageData(im,0,0);cv.dataset.d=1}
function pvLoop(){requestAnimationFrame(pvLoop);
  document.querySelectorAll('canvas[data-pv]').forEach(cv=>{const g=GM.get(+cv.dataset.g),p=PVS.get(+cv.dataset.g);if(!g||!p)return;
    const fresh=p.v.currentTime!==p.t;if(fresh||!cv.dataset.d)pvDraw(cv,g,p,+cv.dataset.pv)});
  PVS.forEach(p=>p.t=p.v.currentTime)}
requestAnimationFrame(pvLoop);

/* ---------- state helpers */
const making=g=>['requested','sheet_picked','keyed'].includes(g.stage)&&!g.error;
const animPhase=g=>g.stickers.some(t=>['READY','FAILED'].includes(t.anim_status));
const processing=g=>g.stickers.some(t=>t.anim_status==='PROCESSING');
const isOff=(g,t)=>animPhase(g)&&t.anim_status==='READY'?t.review.anim==='REJECTED':t.review.still==='REJECTED';
const keptStills=g=>g.stickers.filter(t=>t.status==='READY'&&t.review.still!=='REJECTED');
const keptAnim=g=>g.stickers.filter(t=>t.anim_status==='READY'&&t.review.still!=='REJECTED'&&t.review.anim!=='REJECTED');
const keptOf=g=>animPhase(g)?keptAnim(g):keptStills(g);
const sheetOf=g=>[...g.video_sheets].reverse().find(v=>v.status!=='REJECTED');
const sessionGens=()=>SES.gens.map(id=>GM.get(id)).filter(Boolean);
const included=()=>sessionGens().filter(g=>!SES.off.includes(g.number));
const nAdded=(g,pid)=>keptOf(g).filter(t=>((g.added||{})[pid]||[]).includes(`${animPhase(g)?'animated':'static'}:${t.index}`)).length;

/* ---------- the screen */
RENDER.generate=async()=>{
  $('s-generate').innerHTML=`<div class=gen2>
   <div class=sh>${ic('gen')} Sticker generator</div>
   <div class=gform>${ic('search')}<input id=prompt type=text placeholder="Describe the stickers, for example: teddy bear for school" autocomplete=off><button id=go class="btn pri gbig" data-act=ggo>Generate</button></div>
   <div class=gopts><span class=mut>White outline</span><div class=tabs id=opills></div><span class=mut id=ohint></span></div>
   <div id=gsug class=gsug></div><div id=msg class=gmsg></div><div id=ghealth></div><div id=gres></div></div>`;
  $('prompt').value=SES.prompt||'';$('prompt').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ACT.ggo()}};
  document.documentElement.style.setProperty('--tile',GS.tile+'px');
  drawOutline();glast='';await loadInputs();drawSug();tick(true)};
function drawOutline(){const on=GS.outline>0;$('opills').innerHTML=[[12,'On'],[0,'Off']].map(([px,l])=>`<button class="tab ${(on?12:0)===px?'on':''}" data-act=goutline data-px=${px}>${l}</button>`).join('');
  $('ohint').textContent=on?'white border around each sticker, also on the animation':'stickers are cut out with no border'}
ACT.goutline=el=>{GS.outline=+el.dataset.px;gstore('mirsal.outline',GS.outline);drawOutline()};
async function loadInputs(){const r=await api('/api/inputs');if(r.ok)GINP=r.j.inputs;const h=await api('/api/generations');if(h.ok)GHEALTH=h.j.health}
function drawSug(){const el=$('gsug');if(!el)return;
  el.innerHTML=GINP.length?`<span class=mut>Prepared sheets:</span>`+GINP.map(s=>`<button class=chip2 data-act=gsug data-s="${esc(s.subject)}">${esc(s.subject.replace(/_/g,' '))} <small>${s.variants.length} ${s.variants.length>1?'sheets':'sheet'}</small></button>`).join(''):`<span class=mut>No prepared sheets found in Phase_01/Images_gen. Use History to check the folders.</span>`}
ACT.gsug=el=>{$('prompt').value=el.dataset.s.replace(/_/g,' ');ACT.ggo()};

/* a new request starts a session with Batch 1; "Create more" adds the next batch */
async function create(prompt,variant,more){
  say('');const body={prompt,variant:variant||undefined,outline:GS.outline};
  const r=await postWait('/api/generations',body,'Finishing the previous sheet…');
  if(!r.ok){say(`${esc(r.j.error||'Could not start')} ${r.status===404?`<button class="btn sm" data-act=ghiggs>Get the Higgsfield prompt for this</button>`:''}`);return false}
  if(more){SES.gens.push(r.j.id)}else{SES={prompt,gens:[r.j.id],off:[],pack:''};for(const p of PVS.values())p.v.remove();PVS.clear();PVON.clear();ANIM.clear()}
  saveSes();glast='';MD=null;tick(true);return true}
ACT.ggo=()=>{const p=$('prompt').value.trim();if(!p){say('Write what you want first, for example <b>teddy bear for school</b>.');return}create(p,0,false)};
function openGen(id){SES={prompt:'',gens:[id],off:[],pack:''};saveSes();glast='';MD=null;tick(true)}
ACT.gmore=async()=>{const gs=sessionGens();if(!gs.length)return;const s=gs[0].source.subject,used=new Set(gs.map(g=>String(g.source.subject_id)));
  await loadInputs();const inp=GINP.find(x=>x.subject===s),next=inp&&inp.variants.find(v=>!used.has(String(v.folder)));
  if(!next){toast(`That is every prepared sheet of “${s.replace(/_/g,' ')}”. Put another in Images_gen, or get the Higgsfield prompt to make a new one.`,1);return}
  create(SES.prompt||s.replace(/_/g,' '),next.variant,true)};
ACT.gbdrop=el=>{const id=+el.dataset.g;SES.gens=SES.gens.filter(x=>x!==id);SES.off=SES.off.filter(x=>x!==id);saveSes();glast='';tick(true)};
ACT.ginc=el=>{const id=+el.dataset.g;SES.off=el.checked?SES.off.filter(x=>x!==id):SES.off.concat(id);saveSes();glast='';tick(true)};
document.addEventListener('change',e=>{if(e.target.classList&&e.target.classList.contains('ginc'))ACT.ginc(e.target);
  if(e.target.id==='gbgsel'){bg=e.target.value;glast='';tick(true);if(MD)gmodal()}});
document.addEventListener('input',e=>{if(e.target.id==='gsize'){GS.tile=+e.target.value;document.documentElement.style.setProperty('--tile',GS.tile+'px');gstore('mirsal.tile',GS.tile)}});

/* ---------- the result */
function tileHtml(g,t){const base=`/out/${g.generation_id}/`,off=isOff(g,t),bad=t.status==='FAILED',live=!off&&PVON.has(g.number)&&t.status==='READY'&&g.source.video_path&&!t.webm;
  const m=t.webm&&t.anim_status==='READY'?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:live?`<canvas data-g=${g.number} data-pv=${t.index} width=288 height=288></canvas><span class=livebadge>live preview</span>`:t.png?`<img src="${base+t.png}" loading=lazy>`:`<div class=gbadmsg>${esc(t.reason||t.status)}</div>`;
  const warn=(t.metrics.warnings||[]).concat(t.anim_metrics&&t.anim_metrics.warnings||[]);
  return`<div class="gt ${off?'off':''} ${bad?'bad':''}"><div class="gtv bg-${bg}" data-act=gopen data-g=${g.number} data-i=${t.index}>${m}</div><span class=gem>${esc(t.emoji)}</span>
    ${t.status==='READY'&&t.anim_status!=='FAILED'?`<button class=gx data-act=gdrop data-g=${g.number} data-i=${t.index} data-off=${off?0:1} title="${off?'Bring this one back':'Drop this one from the set'}">${off?ic('plus'):ic('x')}</button>`:''}
    <div class=gcap><b>${esc(t.key.replace(/_/g,' '))}</b>${bad?`<div class=gprob>Blocked: ${esc(t.reason)}</div>`:t.anim_status==='FAILED'?`<div class=gprob>No animation: ${esc(t.anim_reason)}</div>`:warn.length?`<div class=gwarn>check: ${esc(warn.join(', '))}</div>`:''}${off?'<div class=gwarn>Dropped</div>':''}</div></div>`}
function batchHtml(g,k,total){
  const inc=!SES.off.includes(g.number),s=g.source;
  const head=`<div class=gbhead>${total>1?`<label class=gbinc title="Include this batch when you Animate or Add"><input type=checkbox class=ginc data-g=${g.number} ${inc?'checked':''}> <b>Batch ${k+1}</b></label>`:`<b>Batch ${k+1}</b>`}
    <span class=mut>sheet ${s.subject_id} · ${g.generation_id}${s.has_video?'':' · no video prepared'}</span>
    <span class=gbact>${s.has_video||making(g)?'':`<button class="btn sm" data-act=gvideo data-g=${g.number} ${keptStills(g).length?'':'disabled'} title="This sheet has no prepared video: make one from the sheet in your own tool">${ic('film')} Make a video…</button>`}
    <button class="btn sm" data-act=gsheet data-g=${g.number} title="The raw and keyed sheet, the measured cut lines, each sticker's boundary and the sheet analysis">${ic('eye')} Green screen & cuts</button>
    ${total>1?`<button class="btn sm" data-act=gbdrop data-g=${g.number} title="Take this batch out of the session">${ic('x')}</button>`:''}</span></div>`;
  if(making(g))return`<section class=gbatch>${head}<div class=gwork><div class=spin></div><b>Making your stickers…</b><div class=mut>${g.stage==='requested'?'Reading the sheet':g.stage==='sheet_picked'?'Removing the background':'Cutting and checking each sticker'}</div></div></section>`;
  const sheetErr=g.stickers.every(t=>t.status==='FAILED')&&(g.verify.sheet||[]).find(c=>!c.ok&&c.severity!=='WARN');
  if(sheetErr)return`<section class=gbatch>${head}<div class=gwork><b>This sheet cannot be used</b><div class=mut>${esc(sheetErr.detail||sheetErr.name)}</div></div></section>`;
  return`<section class="gbatch ${inc?'':'excl'}">${head}${g.error?`<div class=warn>${esc(g.error)}</div>`:''}<div class=gtiles>${g.stickers.map(t=>tileHtml(g,t)).join('')}</div></section>`}
function gview(){
  const gs=sessionGens();if(!gs.length)return'';
  const inc=included(),n=inc.reduce((a,g)=>a+keptOf(g).length,0),ready=gs.every(g=>!making(g));
  const todoAnim=inc.filter(g=>g.source.has_video&&!animPhase(g)&&!processing(g)&&!ANIM.has(g.number)&&keptStills(g).length);
  const busyAnim=gs.some(g=>processing(g)||(ANIM.has(g.number)&&!animPhase(g)));
  const done=inc.reduce((a,g)=>a+g.stickers.filter(t=>['READY','FAILED'].includes(t.anim_status)).length,0),tot=inc.reduce((a,g)=>a+(g.source.has_video?keptStills(g).length:0),0);
  const pk=SES.pack&&packById(SES.pack),added=pk?inc.reduce((a,g)=>a+nAdded(g,SES.pack),0):0,allAdded=pk&&n>0&&added>=n;
  const kind=inc.some(g=>animPhase(g))?'animated ':'';
  let bar;
  if(!ready)bar=`<span class=gstat>Making your stickers…</span>`;
  else if(busyAnim)bar=`<span class=gstat>Animating ${done} of ${tot}…</span><button class="btn pri gbig" disabled>Animating…</button>`;
  else if(todoAnim.length)bar=`<span class=gstat>${n} sticker${n===1?'':'s'} in ${inc.length} batch${inc.length===1?'':'es'}</span><button class=link data-act=gadd ${n?'':'disabled'}>or add the stills</button><button class="btn pri gbig" data-act=ganimate>${ic('play')} Animate${inc.length>1?` ${todoAnim.length} batch${todoAnim.length===1?'':'es'}`:''}</button>`;
  else bar=`<span class=gstat>${n} ${kind}sticker${n===1?'':'s'} in ${inc.length} batch${inc.length===1?'':'es'}${allAdded?` · added to “${esc(pk.name)}”`:''}</span><button class="btn pri gbig" data-act=gadd ${n&&!allAdded?'':'disabled'}>${allAdded?'Added ✓':`Add ${n} to a pack`}</button>${allAdded?`<button class="btn gbig" data-act=gopenpack>Open pack</button>`:''}`;
  return`<div class=ghead><div><h2 style="margin:0">${esc(titleCase(gs[0].source.subject))}</h2><div class=mut>${gs.length} batch${gs.length===1?'':'es'} · ${gs[0].outline_px?gs[0].outline_px+' px outline':'no outline'}</div></div>
    <button class="btn" data-act=gmore ${ready&&!busyAnim?'':'disabled'} title="Create another sheet of the same subject">${ic('plus')} Create more</button>
    <span style="margin-left:auto" class=gview><label class=mut>Background <select id=gbgsel>${BGS.map(([k,l])=>`<option value=${k} ${bg===k?'selected':''}>${l}</option>`).join('')}</select></label>
    <label class=mut>Size <input type=range id=gsize min=130 max=420 step=10 value=${GS.tile}></label></span></div>
   ${gs.map((g,k)=>batchHtml(g,k,gs.length)).join('')}
   <div class=gbar>${bar}</div>
   <details class=gmore><summary class=mut>Prompt</summary><div class=mut>${esc(gs[0].plan_source||'')}</div><textarea readonly rows=4>${esc(gs[0].sheet_prompt||'')}</textarea></details>`}

/* ---------- Animate, Add */
ACT.ganimate=async()=>{const todo=included().filter(g=>g.source.has_video&&!animPhase(g)&&!processing(g)&&keptStills(g).length);if(!todo.length)return;
  todo.forEach(g=>{ANIM.add(g.number);PVON.add(g.number);if(g.source.video_path)pvEnsure(g)});glast='';tick(true);
  for(const g of todo){const r=await postWait(`/api/generations/${g.number}/animate`,{scope:'pack'},'Waiting for the previous animation…');if(!r.ok){toast(r.j.error,1);ANIM.delete(g.number)}}};
ACT.gdrop=async el=>{const r=await postWait(`/api/generations/${el.dataset.g}/drop`,{index:+el.dataset.i,dropped:el.dataset.off==='1'});if(!r.ok)toast(r.j.error,1);glast='';tick(true)};
ACT.gadd=async()=>{await loadLib();const inc=included(),n=inc.reduce((a,g)=>a+keptOf(g).length,0);if(!n)return;
  const ps=LIB.packs,def=SES.pack&&packById(SES.pack)?SES.pack:'',base=titleCase(inc[0].source.subject);
  let name=base,k=2;while(ps.some(p=>p.name.toLowerCase()===name.toLowerCase()))name=`${base} ${k++}`;
  const anim=inc.some(g=>animPhase(g));
  dlg(`<h2>Add to a pack</h2><div class=mut>${n} ${anim?'animated stickers':'stickers'} from ${inc.length} batch${inc.length===1?'':'es'}</div>
   <label class=radio><input type=radio name=gp value=new ${def?'':'checked'}> <b>New pack</b></label>
   <div class=fld><input type=text id=gpname value="${esc(name)}" maxlength=60 placeholder="Pack name" autocomplete=off></div>
   ${ps.length?`<label class=radio><input type=radio name=gp value=old ${def?'checked':''}> <b>An existing pack</b></label>
   <div class=fld><select id=gpold>${ps.map(p=>`<option value="${p.id}" ${p.id===def?'selected':''}>${esc(p.name)} (${p.stickers.length})</option>`).join('')}</select></div>`:''}
   <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=gaddgo>Add ${n}</button></div>`);
  const nm=$('gpname');nm.onfocus=()=>{const r=document.querySelector('input[name=gp][value=new]');if(r)r.checked=true};if(!def){nm.focus();nm.select()}
  nm.onkeydown=e=>{if(e.key==='Enter')ACT.gaddgo()};const old=$('gpold');if(old)old.onfocus=()=>{document.querySelector('input[name=gp][value=old]').checked=true}};
ACT.gaddgo=async()=>{const mode=(document.querySelector('input[name=gp]:checked')||{}).value||'new';let pid;
  if(mode==='old')pid=$('gpold').value;
  else{const nm=$('gpname').value.trim();if(!nm){toast('Give the pack a name',1);return}const r=await post('/api/packs',{name:nm});if(!r.ok)return toast(r.j.error,1);pid=r.j.id}
  closeDlg();let added=0,err='';
  for(const g of included()){if(!keptOf(g).length)continue;const r=await postWait(`/api/generations/${g.number}/add`,{pack_id:pid});if(r.ok)added+=r.j.added;else err=r.j.error}
  await loadLib();SES.pack=pid;saveSes();glast='';tick(true);
  if(err)toast(err,1);else toast(added?`Added ${added} to “${packById(pid).name}”`:'Those are already in that pack')};
ACT.gopenpack=()=>{if(SES.pack)location.hash='#/pack/'+SES.pack};

/* ---------- Make a video...: the one multi-step path, for a batch without a prepared video */
ACT.gvideo=async el=>{const id=+el.dataset.g,r=await postWait(`/api/generations/${id}/quick_sheet`);if(!r.ok){toast(r.j.error,1);return}glast='';VG=id;await tick(true);drawVdlg()};
function drawVdlg(){if(VG===null)return;const g=GM.get(VG);if(!g){VG=null;return}const v=sheetOf(g);if(!v){VG=null;closeDlg();return}
  if(v.status==='SLICED'){VG=null;closeDlg();toast('Animations are ready');glast='';return}
  const base=`/out/${g.generation_id}/`,st=v.status,work=st==='VIDEO_RETURNED';
  const row=(n,done,h)=>`<div class=vstep><span class="vn ${done?'ok':''}">${done?ic('check'):n}</span><div style="flex:1">${h}</div></div>`;
  dlg(`<div class=vdlg><h2>Make a video from this sheet</h2><div class=vgrid><img src="${base+v.file}" alt="Video sheet" class=vsheet>
   <div>${row(1,false,`<b>Download the sheet</b><div class=mut>${v.slots.length} of ${g.stickers.length} stickers on a flat green background, no outline.</div><a class="btn sm" href="${base+v.file}" download="${g.generation_id}-${v.id}-sheet.png">${ic('download')} Download sheet</a>`)}
   ${row(2,false,`<b>Animate it in your tool</b><div class=mut>Image to video, sheet as the first frame.</div><button class="btn sm" data-act=gcopyprompt>Copy video prompt</button>`)}
   ${row(3,st==='SLICED',`<b>Upload the video</b><div class=mut>${work?'Python is slicing the video…':st==='VIDEO_BLOCKED'?`<span style="color:var(--bad)">This video was not accepted (${esc(v.block||'')}). Upload a corrected one.</span>`:'It is cut into one animation per sticker.'}</div>
     <input type=file id=gvfile accept="video/*,.mp4,.mov,.webm,.mkv" hidden><button class="btn pri sm" data-act=gpickvideo ${work?'disabled':''}>${ic('plus')} ${st==='VIDEO_BLOCKED'?'Upload another video':'Upload video'}</button>`)}</div></div>
   <div class=row style="justify-content:flex-end"><button class=btn data-act=gvclose>Close</button></div></div>`);
  const f=$('gvfile');if(f)f.onchange=async()=>{const file=f.files[0];if(!file)return;const r=await fetch(`/api/generations/${g.number}/video_sheet/${v.id}/video?name=${encodeURIComponent(file.name)}`,{method:'POST',body:file});
    if(!r.ok){let j={};try{j=await r.json()}catch(e){}toast(j.error||'Upload failed',1)}glast='';tick(true)}}
ACT.gpickvideo=()=>{const f=$('gvfile');if(f)f.click()};
ACT.gvclose=()=>{VG=null;closeDlg()};
ACT.gcopyprompt=async()=>{const g=GM.get(VG),v=g&&sheetOf(g);try{await navigator.clipboard.writeText((v&&v.video_prompt)||(g&&g.video_prompt)||'');toast('Video prompt copied')}catch(e){toast('Copy failed',1)}};

/* ---------- Green screen & cuts: the raw / keyed sheet, the measured cut lines, each sticker's boundary, and the analysis */
const SV={g:null,view:'raw',lines:true,boxes:true};
ACT.gsheet=el=>{SV.g=+el.dataset.g;SV.view='raw';SV.lines=true;SV.boxes=true;sheetDlg()};
function sheetDlg(){const g=GM.get(SV.g);if(!g)return;const s=g.source,base=`/out/${g.generation_id}/`,size=s.sheet_size,G=s.grid;if(!size||!s.sheet_copy)return toast('This sheet has not been read yet',1);
  const [W,H]=size,keyedEv=[...g.events].reverse().find(e=>e.stage==='keyed'&&e.status==='done'),kd=(keyedEv&&keyedEv.detail)||{},th=(kd.threshold||[]).slice().sort((a,b)=>a-b);
  const img=SV.view==='keyed'&&s.keyed?base+s.keyed:base+s.sheet_copy;
  let svg='';const sw=Math.max(2,W/450);
  if(G&&SV.lines)svg+=G.xs.slice(1,-1).map(x=>`<line x1=${x} y1=0 x2=${x} y2=${H} stroke="#2563eb" stroke-width=${sw} stroke-dasharray="${W/50} ${W/90}"/>`).join('')+G.ys.slice(1,-1).map(y=>`<line x1=0 y1=${y} x2=${W} y2=${y} stroke="#2563eb" stroke-width=${sw} stroke-dasharray="${W/50} ${W/90}"/>`).join('');
  g.stickers.forEach(t=>{const m=t.metrics||{},c=m.cell,b=m.bbox;if(!c)return;
    if(SV.lines)svg+=`<text x=${c[0]+W/90} y=${c[1]+W/22} font-size=${W/26} font-weight=700 fill="#2563eb" stroke="#fff" stroke-width=${W/380} paint-order=stroke>${t.index}</text>`;
    if(SV.boxes&&b)svg+=`<rect x=${c[0]+b[0]} y=${c[1]+b[1]} width=${b[2]-b[0]} height=${b[3]-b[1]} fill=none stroke="${t.status==='FAILED'?'#ef4444':'#facc15'}" stroke-width=${sw*1.4}/>`});
  const checks=(g.verify.sheet||[]).map(c=>`<div class=chk><span class="${c.ok?'p':(c.severity==='WARN'?'w':'f')}">${c.ok?'✓':c.severity==='WARN'?'!':'✗'} ${esc(c.name)}</span> <span class=mut>${esc(c.detail||'')}</span></div>`).join('');
  const rows=g.stickers.map(t=>{const m=t.metrics||{};return`<tr><td>${t.index}</td><td>${t.status==='READY'?'<span style="color:var(--ok)">ready</span>':`<span style="color:var(--bad)">${esc(t.reason||t.status)}</span>`}</td><td>${m.fg_px!==undefined?m.fg_px:''}</td><td>${m.threshold!==undefined?m.threshold:''}</td><td>${m.scale||''}</td><td>${esc((m.warnings||[]).join(', '))}</td></tr>`}).join('');
  dlg(`<div class=sheetdlg><div class=mrow><h2 style="margin:0">Green screen & cuts <span class=mut style="font-weight:500">${g.generation_id} · sheet ${s.subject_id} · ${W}×${H}</span></h2><button class=btn data-act=gsclose>✕</button></div>
   <div class=gtoolbar><div class=tabs><button class="tab ${SV.view==='raw'?'on':''}" data-act=gsview data-v=raw>Raw sheet</button><button class="tab ${SV.view==='keyed'?'on':''}" data-act=gsview data-v=keyed ${s.keyed?'':'disabled'}>Background removed</button></div>
    <label class=mut><input type=checkbox data-act=gstog data-k=lines ${SV.lines?'checked':''}> Cut lines</label><label class=mut><input type=checkbox data-act=gstog data-k=boxes ${SV.boxes?'checked':''}> Sticker boundaries</label></div>
   <div class=sgrid><div class="sbox ${SV.view==='keyed'?'bg-'+bg:''}"><img src="${img}" alt="Sheet"><svg viewBox="0 0 ${W} ${H}">${svg}</svg></div>
    <div class=sside><h3>Analysis</h3>${checks||'<div class=mut>No sheet checks recorded.</div>'}
     <div class=kv style="margin:10px 0"><span>background sampled</span><span>${kd.bg?`rgb(${kd.bg.join(', ')})`:'?'}</span><span>key threshold</span><span>${th.length?`${th[0]} to ${th[th.length-1]} (per cell)`:'?'}</span><span>cut</span><span>${esc(kd.cut||(G&&G.method)||'?')}${G&&G.method!=='gutter'&&G.method!=='single'?' (a character may cross a cut)':''}</span><span>grid</span><span>${g.grid[0]}×${g.grid[1]}</span></div>
     <table class=stbl><tr><th>#</th><th>result</th><th>subject px</th><th>threshold</th><th>scale</th><th>warnings</th></tr>${rows}</table>
     <div class=mut style="margin-top:8px">Blue dashed lines: where the sheet is cut (in the gaps between characters). Yellow boxes: each sticker's measured boundary; red: blocked.</div></div></div></div>`)}
ACT.gsview=el=>{SV.view=el.dataset.v;sheetDlg()};
ACT.gstog=el=>{SV[el.dataset.k]=el.checked;sheetDlg()};
ACT.gsclose=()=>{SV.g=null;closeDlg()};

/* ---------- "Get the Higgsfield prompt": when nothing prepared matches the request */
ACT.ghiggs=async()=>{const p=$('prompt').value.trim();if(!p)return;
  const r=await post('/api/plan',{prompt:p,grid:'3x3',style_id:'flat_vector'});if(!r.ok)return toast(r.j.error,1);
  dlg(`<div class=vdlg><h2>Prompt for Higgsfield</h2><div class=mut>Nothing prepared matches “${esc(p)}”. Generate the sheet, name the folder as shown below, and it appears here.</div>
   <h3>Sheet prompt</h3><textarea readonly rows=9 id=hp1>${esc(r.j.sheet_prompt)}</textarea><div class=row><button class="btn sm" data-act=hcopy data-t=hp1>Copy sheet prompt</button></div>
   <h3>Video prompt</h3><textarea readonly rows=5 id=hp2>${esc(r.j.video_prompt)}</textarea><div class=row><button class="btn sm" data-act=hcopy data-t=hp2>Copy video prompt</button></div>
   <div id=hres></div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button><button class="btn pri" data-act=hreserve>Reserve the folder names</button></div></div>`)};
ACT.hcopy=async el=>{try{await navigator.clipboard.writeText($(el.dataset.t).value);toast('Copied')}catch(e){toast('Copy failed',1)}};
ACT.hreserve=async()=>{const r=await post('/api/tasks',{prompt:$('prompt').value.trim(),grid:'3x3',style_id:'flat_vector'});if(!r.ok)return toast(r.j.error,1);
  $('hres').innerHTML=`<div class=card style="margin:10px 0"><b>Create these two folders and name the downloads into them</b><br><code>${esc(r.j.paths.img)}</code><br><code>${esc(r.j.paths.vid)}</code><div class=mut>The sheet goes in <b>${esc(r.j.folders.img)}</b>, the video in <b>${esc(r.j.folders.vid)}</b>. Then press Generate again.</div></div>`};

/* ---------- one sticker, larger */
function gmodal(){if(!MD)return;const g=GM.get(MD.g);if(!g){MD=null;return}const t=g.stickers[MD.i-1],base=`/out/${g.generation_id}/`;
  const still=t.png?`<img src="${base+t.png}">`:`<div class=mut style="padding:12px">${esc(t.status)}${t.reason?': '+esc(t.reason):''}</div>`;
  const vid=t.webm&&t.anim_status==='READY'?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:`<div class=mut style="padding:12px">${t.anim_status==='NOT_REQUESTED'?'Not animated yet':esc(t.anim_status)+(t.anim_reason?': '+esc(t.anim_reason):'')}</div>`;
  const rows=cs=>(cs||[]).map(r=>`<div class=chk><span class="${r.ok?'p':(r.severity==='WARN'?'w':'f')}">${r.ok?'✓':r.severity==='WARN'?'!':'✗'} ${esc(r.name)}</span> <span class=mut>${esc(r.detail||'')}</span></div>`).join('');
  $('modal').innerHTML=`<div class=mbox style="width:min(900px,96vw)"><div class=mrow><button class="btn nav" data-act=gstep data-d=-1>‹</button>
   <div style="flex:1"><b>${esc(t.emoji)} ${esc(t.key.replace(/_/g,' '))}</b><div class=mut>${esc(t.tags.join(' · '))}</div></div>
   ${t.status==='READY'?`<button class=btn data-act=gedit>${ic('edit')} Edit</button>`:''}<button class="btn nav" data-act=gstep data-d=1>›</button><button class=btn data-act=gmclose>✕</button></div>
   <div class=mpanes><div class=pane><div class=mut>Sticker</div><div class="box bg-${bg}">${still}</div></div><div class=pane><div class=mut>Animation</div><div class="box bg-${bg}">${vid}</div></div></div>
   <details ${t.status==='FAILED'||(t.report||[]).some(r=>!r.ok)?'open':''}><summary class=mut>What Python checked</summary>${rows(t.report)||'<div class=mut>nothing yet</div>'}${rows(t.anim_report)}</details>
   <div class=mut style="margin-top:8px">${esc(t.prompt)}</div><div class=mut>← → to browse, Esc to close</div></div>`;
  $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')ACT.gmclose()}}
ACT.gopen=el=>{MD={g:+el.dataset.g,i:+el.dataset.i};gmodal()};
ACT.gmclose=()=>{MD=null;$('modal').classList.remove('on')};
ACT.gstep=el=>{if(!MD)return;const g=GM.get(MD.g),n=g.stickers.length;MD.i=((MD.i-1+(+el.dataset.d)+n)%n)+1;gmodal()};
ACT.gedit=()=>{const g=GM.get(MD.g),t=g.stickers[MD.i-1];ACT.gmclose();Ed.openImage(`/out/${g.generation_id}/${t.png}`,{outlined:g.outline_px>0,name:t.name,emoji:t.emoji})};
document.addEventListener('keydown',e=>{if(!MD)return;if(e.key==='Escape')ACT.gmclose();if(e.key==='ArrowRight')ACT.gstep({dataset:{d:1}});if(e.key==='ArrowLeft')ACT.gstep({dataset:{d:-1}})});

/* ---------- polling: only while this screen is open */
async function tick(force){try{
  if(route_!=='generate'&&!MD&&VG===null&&SV.g===null)return;
  const h=await api('/api/generations');if(h.ok)GHEALTH=h.j.health;
  const hh=$('ghealth');if(hh)hh.innerHTML=GHEALTH&&GHEALTH.vp9===false?'<div class=warn>This ffmpeg cannot encode VP9, so animations will fail. Run <code>python -m mirsal doctor</code>.</div>':'';
  let key='';for(const id of SES.gens){const r=await api('/api/generations/'+id);if(r.ok){GM.set(id,r.j);key+=JSON.stringify(r.j)}else if(r.status===404){SES.gens=SES.gens.filter(x=>x!==id);saveSes()}}
  for(const id of [...ANIM]){const g=GM.get(id);if(g&&animPhase(g)&&!processing(g))ANIM.delete(id)}
  key+=bg+SES.off.join()+SES.pack+[...ANIM].join()+(LIB.packs||[]).length;
  if(force||key!==glast){glast=key;const el=$('gres');if(el)el.innerHTML=gview();if(MD)gmodal();drawVdlg();if(SV.g!==null&&document.querySelector('.sheetdlg'))sheetDlg()}
}catch(e){const m=$('msg');if(m)m.textContent='Something went wrong: '+e.message}}
setInterval(tick,700);loadLib();
