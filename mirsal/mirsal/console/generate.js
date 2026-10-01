/* Generate: type a request -> the stickers appear -> Animate -> Add to pack.
   The review gates (plan, stills, video sheet, animation, pack) are still recorded by the server, but they happen behind those clicks:
   Generate approves the plan, the little x drops a sticker from the set, Animate and Add are the decisions on what is kept. */
'use strict';
let sel=null,cur=null,bg='checker',glast='',mi=null,GINP=[],GHEALTH=null;
const GS={outline:12,pack:'',busyAdd:false};
try{const o=localStorage.getItem('mirsal.outline');if(o!==null&&!isNaN(+o))GS.outline=+o>0?12:0;GS.pack=localStorage.getItem('mirsal.pack')||''}catch(e){}
const OUTLINES=[[12,'On'],[0,'Off']];
const gstore=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};

/* ---------- the live preview: the paired 3x3 video is played in the browser and keyed like the stickers, so Animate shows motion at once
   while the real 512x512 WEBMs encode on the server */
const PV={gid:null,all:false,v:null,cal:{},t:-1};
const pvOn=i=>PV.gid===sel&&PV.all;
function pvVideo(){if(PV.v&&PV.v.dataset.gid==sel)return PV.v;if(PV.v){PV.v.pause();PV.v.remove()}
  const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.dataset.gid=sel;v.style.cssText='position:fixed;width:1px;height:1px;opacity:0;pointer-events:none';
  v.src=`/src/${sel}/video`;document.body.appendChild(v);v.play().catch(()=>{});PV.v=v;PV.cal={};PV.t=-1;return v}
function vcell(g,v,i){const G=g&&g.source.grid,sw=g&&g.source.sheet_size;if(G&&sw){const r=G.rects[i-1],kx=v.videoWidth/sw[0],ky=v.videoHeight/sw[1];return[r[0]*kx,r[1]*ky,r[2]*kx,r[3]*ky]}
  const n=g&&g.grid?g.grid[1]:3,w=v.videoWidth/n,h=v.videoHeight/n;return[((i-1)%n)*w,((i-1)/n|0)*h,w,h]}
function pvCalibrate(v,i){
  const [X,Y,cw,ch]=vcell(cur,v,i),S=96,c=document.createElement('canvas');c.width=c.height=S;const x=c.getContext('2d',{willReadFrequently:true});
  x.drawImage(v,X,Y,cw,ch,0,0,S,S);const d=x.getImageData(0,0,S,S).data,D=[];
  for(let y=0;y<S;y++)for(let xx=0;xx<S;xx++){if(y>2&&y<S-3&&xx>2&&xx<S-3)continue;const o=(y*S+xx)*4,r=d[o],g=d[o+1],b=d[o+2];D.push(g-Math.max(r,b))}
  D.sort((a,b)=>a-b);return Math.max(.5*D[D.length>>1],8)}
function pvDraw(cv,i){
  const v=PV.v,g=cur;if(!v||!g||v.readyState<2||!v.videoWidth)return;
  const t=g.stickers[i-1],m=t.metrics||{},c=m.cell,b=m.bbox,S=cv.width,[X,Y,cw,ch]=vcell(g,v,i);
  let fx=.5,fy=.5,fs=1;if(c&&b&&m.scale){fx=(b[0]+b[2])/2/c[2];fy=(b[1]+b[3])/2/c[3];fs=Math.min(3,(512/m.scale)/c[2])}
  const side=fs*(cw+ch)/2,cx=X+fx*cw,cy=Y+fy*ch;let sx=cx-side/2,sy=cy-side/2,sw=side,sh=side;
  const x0=Math.max(sx,X),y0=Math.max(sy,Y),x1=Math.min(sx+sw,X+cw),y1=Math.min(sy+sh,Y+ch),k=S/side;
  const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,S,S);if(x1<=x0||y1<=y0)return;
  ctx.drawImage(v,x0,y0,x1-x0,y1-y0,(x0-sx)*k,(y0-sy)*k,(x1-x0)*k,(y1-y0)*k);
  if(PV.cal[i]===undefined)PV.cal[i]=pvCalibrate(v,i);const T=PV.cal[i],im=ctx.getImageData(0,0,S,S),d=im.data;
  for(let o=0;o<d.length;o+=4){if(!d[o+3])continue;const r=d[o],gg=d[o+1],bb=d[o+2],mx=Math.max(r,bb);let a=2*(T-(gg-mx))/T;a=a<0?0:a>1?1:a;
    if(a<.98&&a>0&&gg>mx)d[o+1]=mx;d[o+3]=d[o+3]*a}
  ctx.putImageData(im,0,0);cv.dataset.d=1}
function pvLoop(){requestAnimationFrame(pvLoop);const v=PV.v;if(!v||PV.gid!=sel||!cur)return;
  const fresh=v.currentTime!==PV.t;PV.t=v.currentTime;
  document.querySelectorAll('canvas[data-pv]').forEach(cv=>{if(fresh||!cv.dataset.d)pvDraw(cv,+cv.dataset.pv)})}
requestAnimationFrame(pvLoop);
const canvasFor=(i,size)=>`<canvas data-pv=${i} width=${size} height=${size}></canvas><span class=livebadge>live preview</span>`;

/* ---------- state helpers */
const making=g=>['requested','sheet_picked','keyed'].includes(g.stage)&&!g.error;
const animPhase=g=>g.stickers.some(t=>['READY','FAILED'].includes(t.anim_status));
const processing=g=>g.stickers.some(t=>t.anim_status==='PROCESSING');
const isOff=(g,t)=>animPhase(g)&&t.anim_status==='READY'?t.review.anim==='REJECTED':t.review.still==='REJECTED';
const keptStills=g=>g.stickers.filter(t=>t.status==='READY'&&t.review.still!=='REJECTED');
const keptAnim=g=>g.stickers.filter(t=>t.anim_status==='READY'&&t.review.still!=='REJECTED'&&t.review.anim!=='REJECTED');
const sheetOf=g=>[...g.video_sheets].reverse().find(v=>v.status!=='REJECTED');
const subjectName=g=>g.source.subject.replace(/_/g,' ');
const folderOf=g=>`img-${g.source.subject_id}-${g.source.subject}`;
const packName=g=>subjectName(g).replace(/\b\w/g,c=>c.toUpperCase());

/* ---------- the screen */
RENDER.generate=async()=>{
  $('s-generate').innerHTML=`<div class=gen2>
   <div class=sh>${ic('gen')} Sticker generator</div>
   <div class=gform>${ic('search')}<input id=prompt type=text placeholder="Describe the stickers, for example: teddy bear for school" autocomplete=off><button id=go class="btn pri gbig" data-act=ggo>Generate</button></div>
   <div class=gopts><span class=mut>White outline</span><div class=tabs id=opills></div><span class=mut id=ohint></span></div>
   <div id=gsug class=gsug></div><div id=msg class=gmsg></div><div id=ghealth></div><div id=gres></div></div>`;
  $('prompt').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ACT.ggo()}};
  drawOutline();glast='';await loadInputs();drawSug();tick()};
function drawOutline(){$('opills').innerHTML=OUTLINES.map(([px,l])=>`<button class="tab ${(GS.outline>0?12:0)===px?'on':''}" data-act=goutline data-px=${px}>${l}</button>`).join('');
  $('ohint').textContent=GS.outline?'white border around each sticker, also on the animation':'stickers are cut out with no border'}
ACT.goutline=el=>{GS.outline=+el.dataset.px;gstore('mirsal.outline',GS.outline);drawOutline()};
async function loadInputs(){const r=await api('/api/inputs');if(r.ok)GINP=r.j.inputs;const h=await api('/api/generations');if(h.ok)GHEALTH=h.j.health}
function drawSug(){const el=$('gsug');if(!el)return;
  el.innerHTML=GINP.length?`<span class=mut>Prepared sheets:</span>`+GINP.map(s=>`<button class=chip2 data-act=gsug data-s="${esc(s.subject)}">${esc(s.subject.replace(/_/g,' '))} <small>${s.variants.length} ${s.variants.length>1?'sheets':'sheet'}</small></button>`).join(''):`<span class=mut>No prepared sheets found in Phase_01/Images_gen. Use History to check the folders.</span>`}
ACT.gsug=el=>{$('prompt').value=el.dataset.s.replace(/_/g,' ');ACT.ggo()};
async function startGen(variant){
  const p=$('prompt').value.trim()||(cur?subjectName(cur):'');if(!p){say('Write what you want first, for example <b>teddy bear for school</b>.');return}
  say('');let r=await post('/api/generations',{prompt:p,variant:variant||undefined,outline:GS.outline});
  for(let n=0;n<6&&!r.ok&&r.status===409&&r.j.error==='busy';n++){await new Promise(f=>setTimeout(f,1200));r=await post('/api/generations',{prompt:p,variant:variant||undefined,outline:GS.outline})}   // the previous sheet is still being cut: wait, do not scold
  if(!r.ok){say(`${esc(r.j.error==='busy'?'Still finishing the previous sheet. Try again in a moment.':r.j.error||'Could not start')} ${r.status===404?`<button class="btn sm" data-act=ghiggs>Get the Higgsfield prompt for this</button>`:''}`);return}
  sel=r.j.id;glast='';mi=null;PV.all=false;tick()}
ACT.ggo=()=>startGen();
ACT.gvariant=async el=>{const f=el.dataset.f,hit=(window.GGENS||[]).filter(g=>g.folder===f);
  if(hit.length){sel=hit[0].id;glast='';tick();return}
  const p=$('prompt').value.trim()||subjectName(cur);const v=+el.dataset.v;await startGen(v)};

/* ---------- the result */
function gview(g){
  const s=g.source,base=`/out/${g.generation_id}/`,n=g.stickers.length,cols=g.grid?g.grid[1]:3;
  if(making(g))return`<div class=gwork><div class=spin></div><b>Making your stickers…</b><div class=mut>${g.stage==='requested'?'Reading the sheet':g.stage==='sheet_picked'?'Removing the background':'Cutting and checking each sticker'}</div></div>`;
  const sheetErr=g.stickers.every(t=>t.status==='FAILED')&&(g.verify.sheet||[]).find(c=>!c.ok&&c.severity!=='WARN');
  if(sheetErr)return`<div class=gwork><b>This sheet cannot be used</b><div class=mut>${esc(sheetErr.detail||sheetErr.name)}</div><div class=mut>Check the image in History, or generate the sheet again.</div></div>`;
  const ap=animPhase(g),proc=processing(g),done=g.stickers.filter(t=>['READY','FAILED'].includes(t.anim_status)).length;
  const tiles=g.stickers.map(t=>{const off=isOff(g,t),bad=t.status==='FAILED',live=!off&&pvOn(t.index)&&t.status==='READY'&&s.video_path;
    const m=t.webm&&t.anim_status==='READY'?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:live?canvasFor(t.index,288):t.png?`<img src="${base+t.png}" loading=lazy>`:`<div class=gbadmsg>${esc(t.reason||t.status)}</div>`;
    const warn=(t.metrics.warnings||[]).concat(t.anim_metrics&&t.anim_metrics.warnings||[]);
    return`<div class="gt ${off?'off':''} ${bad?'bad':''}"><div class="gtv bg-${bg}" data-act=gopen data-i=${t.index}>${m}</div><span class=gem>${esc(t.emoji)}</span>
      ${t.status==='READY'&&t.anim_status!=='FAILED'?`<button class=gx data-act=gdrop data-i=${t.index} data-off=${off?0:1} title="${off?'Bring this one back':'Drop this one from the set'}">${off?ic('plus'):ic('x')}</button>`:''}
      <div class=gcap><b>${esc(t.key.replace(/_/g,' '))}</b>${bad?`<div class=gprob>Blocked: ${esc(t.reason)}</div>`:t.anim_status==='FAILED'?`<div class=gprob>No animation: ${esc(t.anim_reason)}</div>`:warn.length?`<div class=gwarn>check: ${esc(warn.join(', '))}</div>`:''}${off?'<div class=gwarn>Dropped</div>':''}</div></div>`}).join('');
  const chips=((GINP.find(x=>x.subject===s.subject)||{}).variants||[]);
  const gens=window.GGENS||[];
  const variants=chips.length>1?`<div class=tabs>${chips.map(v=>`<button class="tab ${String(v.folder)===String(s.subject_id)?'on':''}" data-act=gvariant data-v=${v.variant} data-f="img-${v.folder}-${esc(s.subject)}" title="${gens.some(x=>x.folder==='img-'+v.folder+'-'+s.subject)?'Open what was made from this sheet':'Generate from this sheet'}">${v.folder}</button>`).join('')}</div>`:'';
  const pack=packSelect(g),addedAll=(ap?keptAnim(g):keptStills(g)).length>0&&(ap?keptAnim(g):keptStills(g)).every(t=>((g.added||{})[GS.pack]||[]).includes(`${ap?'animated':'static'}:${t.index}`));
  const kept=(ap?keptAnim(g):keptStills(g)).length;
  let bar;
  if(proc)bar=`<span class=gstat>Animating ${done} of ${keptStills(g).length}…</span><button class="btn pri gbig" disabled>Animating…</button>`;
  else if(ap)bar=`<span class=gstat>${kept} animated ${kept===1?'sticker':'stickers'} ready${g.stickers.some(t=>t.anim_status==='FAILED')?`, ${g.stickers.filter(t=>t.anim_status==='FAILED').length} blocked`:''}</span>${pack}<button class="btn pri gbig" data-act=gadd ${kept&&!addedAll?'':'disabled'}>${addedAll?'Added ✓':`Add ${kept} to pack`}</button>${addedAll?`<button class="btn gbig" data-act=gopenpack>Open pack</button>`:''}`;
  else{const ks=keptStills(g).length,nb=g.stickers.filter(t=>t.status==='FAILED').length;
    const add=`<button class="btn ${s.has_video?'':'pri'} gbig" data-act=gadd ${ks&&!addedAll?'':'disabled'}>${addedAll?'Added ✓':s.has_video?'Add stills':`Add ${ks} to pack`}</button>`;
    bar=`<span class=gstat>${ks} ${ks===1?'sticker':'stickers'} ready${nb?`, ${nb} blocked by the checks`:''}</span>${s.has_video?'':`<button class=link data-act=gvideo ${ks?'':'disabled'} title="This sheet has no prepared video: make one from the sheet in your own tool">Make a video…</button>`}${s.has_video?'':pack}
      ${s.has_video?`<button class="btn pri gbig" data-act=ganimate ${ks?'':'disabled'}>${ic('play')} Animate</button><button class=link data-act=gadd ${ks&&!addedAll?'':'disabled'}>${addedAll?'Added ✓':'or add the stills'}</button>`:add}${addedAll?`<button class="btn gbig" data-act=gopenpack>Open pack</button>`:''}`}
  return`<div class=ghead><div><h2 style="margin:0">${esc(g.task||subjectName(g))}</h2><div class=mut>${g.generation_id} · sheet ${s.subject_id}${s.has_video?'':' · no video prepared'}${g.outline_px?` · ${g.outline_px} px outline`:' · no outline'}</div></div>${variants}
     <button class="btn sm" style="margin-left:auto" data-act=gbg title="Check the stickers on another background">Background: ${({checker:'transparent',light:'light',dark:'dark',wall:'wallpaper'})[bg]}</button></div>
   ${g.error?`<div class=warn>${esc(g.error)}</div>`:''}
   <div class=gtiles style="grid-template-columns:repeat(${cols},minmax(0,1fr))">${tiles}</div>
   <div class=gbar>${bar}</div>
   <details class=gmore><summary class=mut>Prompt and checks</summary><div class=mut>${esc(g.plan_source||'')}</div><textarea readonly rows=4>${esc(g.sheet_prompt||'')}</textarea></details>`}
function packSelect(g){const p=(LIB.packs||[]).find(x=>x.id===GS.pack);
  return`<span class=gpack><span class=mut>to <b>${esc(p?p.name:packName(g))}</b>${p?'':' (new pack)'}</span> <button class=link data-act=gchangepack>change</button></span>`}
ACT.gchangepack=()=>pickPack(id=>{GS.pack=id;gstore('mirsal.pack',id);glast='';tick()},'Add these stickers to which pack?');
ACT.gbg=()=>{const o=['checker','light','dark','wall'];bg=o[(o.indexOf(bg)+1)%o.length];glast='';tick();if(mi!==null)gmodal()};

/* ---------- the three clicks */
ACT.ganimate=async()=>{if(!cur)return;if(PV.gid!=sel){PV.gid=sel;PV.all=false}PV.all=true;if(cur.source.video_path)pvVideo();glast='';
  const r=await post(`/api/generations/${sel}/animate`,{scope:'pack'});if(!r.ok&&r.status!==409)toast(r.j.error,1);else if(r.status===409)toast(r.j.error==='busy'?'Another job is running: the live preview plays, the final files encode next.':r.j.error,r.j.error!=='busy');tick()};
ACT.gdrop=async el=>{const r=await post(`/api/generations/${sel}/drop`,{index:+el.dataset.i,dropped:el.dataset.off==='1'});if(!r.ok)toast(r.j.error,1);glast='';tick()};
ACT.gadd=async()=>{if(!cur||GS.busyAdd)return;GS.busyAdd=true;const ex=LIB.packs.find(p=>p.id===GS.pack);
  const body=ex?{pack_id:ex.id}:{pack_name:packName(cur)};
  const r=await post(`/api/generations/${sel}/add`,body);GS.busyAdd=false;
  if(!r.ok){toast(r.j.error,1);return}
  await loadLib();GS.pack=r.j.pack_id;gstore('mirsal.pack',GS.pack);glast='';
  toast(r.j.added?`Added ${r.j.added} ${r.j.kind==='animated'?'animated stickers':'stickers'} to “${packById(r.j.pack_id).name}”`:'Those are already in that pack');tick()};
ACT.gopenpack=()=>{if(GS.pack)location.hash='#/pack/'+GS.pack};

/* ---------- "Make a video...": the one multi-step path, for sheets without a prepared video */
let VD=false;
ACT.gvideo=async()=>{const r=await post(`/api/generations/${sel}/quick_sheet`);if(!r.ok){toast(r.j.error,1);return}glast='';VD=true;await tick(true);drawVdlg()};
function drawVdlg(){if(!VD||!cur)return;const v=sheetOf(cur);if(!v){VD=false;closeDlg();return}
  if(v.status==='SLICED'){VD=false;closeDlg();toast('Animations are ready');glast='';return}
  const base=`/out/${cur.generation_id}/`,st=v.status,work=st==='VIDEO_RETURNED';
  const row=(n,done,h)=>`<div class=vstep><span class="vn ${done?'ok':''}">${done?ic('check'):n}</span><div style="flex:1">${h}</div></div>`;
  dlg(`<div class=vdlg><h2>Make a video from this sheet</h2><div class=vgrid><img src="${base+v.file}" alt="Video sheet" class=vsheet>
   <div>${row(1,false,`<b>Download the sheet</b><div class=mut>${v.slots.length} of ${cur.stickers.length} stickers on a flat green background, no outline.</div><a class="btn sm" href="${base+v.file}" download="${cur.generation_id}-${v.id}-sheet.png">${ic('download')} Download sheet</a>`)}
   ${row(2,false,`<b>Animate it in your tool</b><div class=mut>Image to video, sheet as the first frame.</div><button class="btn sm" data-act=gcopyprompt>Copy video prompt</button>`)}
   ${row(3,st==='SLICED',`<b>Upload the video</b><div class=mut>${work?'Python is slicing the video…':st==='VIDEO_BLOCKED'?`<span style="color:var(--bad)">This video was not accepted (${esc(v.block||'')}). Upload a corrected one.</span>`:'It is cut into one animation per sticker.'}</div>
     <input type=file id=gvfile accept="video/*,.mp4,.mov,.webm,.mkv" hidden><button class="btn pri sm" data-act=gpickvideo ${work?'disabled':''}>${ic('plus')} ${st==='VIDEO_BLOCKED'?'Upload another video':'Upload video'}</button>`)}</div></div>
   <div class=row style="justify-content:flex-end"><button class=btn data-act=gvclose>Close</button></div></div>`);
  const f=$('gvfile');if(f)f.onchange=async()=>{const file=f.files[0];if(!file)return;const r=await fetch(`/api/generations/${sel}/video_sheet/${v.id}/video?name=${encodeURIComponent(file.name)}`,{method:'POST',body:file});
    if(!r.ok){let j={};try{j=await r.json()}catch(e){}toast(j.error||'Upload failed',1)}glast='';tick(true)}}
ACT.gpickvideo=()=>{const f=$('gvfile');if(f)f.click()};
ACT.gvclose=()=>{VD=false;closeDlg()};
ACT.gcopyprompt=async()=>{const v=sheetOf(cur);try{await navigator.clipboard.writeText((v&&v.video_prompt)||cur.video_prompt||'');toast('Video prompt copied')}catch(e){toast('Copy failed: select the text in "Prompt and checks"',1)}};

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
function gmodal(){if(mi===null||!cur){return}const g=cur,t=g.stickers[mi-1],base=`/out/${g.generation_id}/`,off=isOff(g,t);
  const still=t.png?`<img src="${base+t.png}">`:`<div class=mut style="padding:12px">${esc(t.status)}${t.reason?': '+esc(t.reason):''}</div>`;
  const vid=t.webm&&t.anim_status==='READY'?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:`<div class=mut style="padding:12px">${t.anim_status==='NOT_REQUESTED'?'Not animated yet':esc(t.anim_status)+(t.anim_reason?': '+esc(t.anim_reason):'')}</div>`;
  const rows=cs=>(cs||[]).map(r=>`<div class=chk><span class="${r.ok?'p':(r.severity==='WARN'?'w':'f')}">${r.ok?'✓':r.severity==='WARN'?'!':'✗'} ${esc(r.name)}</span> <span class=mut>${esc(r.detail||'')}</span></div>`).join('');
  $('modal').innerHTML=`<div class=mbox style="width:min(900px,96vw)"><div class=mrow><button class="btn nav" data-act=gstep data-d=-1>‹</button>
   <div style="flex:1"><b>${esc(t.emoji)} ${esc(t.key.replace(/_/g,' '))}</b><div class=mut>${esc(t.tags.join(' · '))}</div></div>
   ${t.status==='READY'?`<button class=btn data-act=gedit data-i=${t.index}>${ic('edit')} Edit</button>`:''}<button class="btn nav" data-act=gstep data-d=1>›</button><button class=btn data-act=gmclose>✕</button></div>
   <div class=mpanes><div class=pane><div class=mut>Sticker</div><div class="box bg-${bg}">${still}</div></div><div class=pane><div class=mut>Animation</div><div class="box bg-${bg}">${vid}</div></div></div>
   <details ${t.status==='FAILED'||(t.report||[]).some(r=>!r.ok)?'open':''}><summary class=mut>What Python checked</summary>${rows(t.report)||'<div class=mut>nothing yet</div>'}${rows(t.anim_report)}</details>
   <div class=mut style="margin-top:8px">${esc(t.prompt)}</div><div class=mut>← → to browse, Esc to close</div></div>`;
  $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')ACT.gmclose()}}
ACT.gopen=el=>{mi=+el.dataset.i;gmodal()};
ACT.gmclose=()=>{mi=null;$('modal').classList.remove('on')};
ACT.gstep=el=>{const n=cur.stickers.length;mi=((mi-1+(+el.dataset.d)+n)%n)+1;gmodal()};
ACT.gedit=el=>{const t=cur.stickers[+el.dataset.i-1];ACT.gmclose();Ed.openImage(`/out/${cur.generation_id}/${t.png}`,{outlined:cur.outline_px>0,name:t.name,emoji:t.emoji})};
document.addEventListener('keydown',e=>{if(mi===null)return;if(e.key==='Escape')ACT.gmclose();if(e.key==='ArrowRight')ACT.gstep({dataset:{d:1}});if(e.key==='ArrowLeft')ACT.gstep({dataset:{d:-1}})});

/* ---------- polling: only while this screen is open */
async function tick(force){try{
  if(route_!=='generate'&&mi===null&&!VD)return;
  const l=await api('/api/generations');if(l.ok){window.GGENS=l.j.generations;GHEALTH=l.j.health;if(sel===null&&l.j.generations.length&&route_==='generate'&&!$('prompt').value&&!window.GSEEN){window.GSEEN=1}}
  const hh=$('ghealth');if(hh)hh.innerHTML=GHEALTH&&GHEALTH.vp9===false?'<div class=warn>This ffmpeg cannot encode VP9, so animations will fail. Run <code>python -m mirsal doctor</code>.</div>':'';
  if(sel!==null){const r=await api('/api/generations/'+sel);if(r.ok){const k=JSON.stringify(r.j)+bg+GS.pack+(LIB.packs||[]).length;if(force||k!==glast){glast=k;cur=r.j;const el=$('gres');if(el)el.innerHTML=gview(r.j);if(mi!==null)gmodal();drawVdlg()}}}
}catch(e){const m=$('msg');if(m)m.textContent='Something went wrong: '+e.message}}
setInterval(tick,600);loadLib();
