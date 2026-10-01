/* Mirsal Sticker Builder: shell, router, Library, Generate (lifecycle console), Settings. No external libraries. */
'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api=async(u,o)=>{const r=await fetch(u,o);let j={};try{j=await r.json()}catch(e){}return{ok:r.ok,status:r.status,j}};
const post=(u,b)=>api(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});
let toastT=0;function toast(m,bad){const t=$('toast');t.textContent=m||'';t.className=(m?'on ':'')+(bad?'bad':'');clearTimeout(toastT);if(m)toastT=setTimeout(()=>t.className='',bad?6000:3500)}
const say=t=>{$('msg').textContent=t||''};
const ICONS={
 gen:'<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
 lib:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
 create:'<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
 settings:'<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
 undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',redo:'<path d="M15 14l5-5-5-5"/><path d="M20 9H10a6 6 0 000 12h3"/>',
 text:'<path d="M5 6V4h14v2M12 4v16M9 20h6"/>',emoji:'<circle cx="12" cy="12" r="9"/><path d="M8.5 14a4 4 0 007 0M9 9.5h.01M15 9.5h.01"/>',
 sticker:'<path d="M4 6a2 2 0 012-2h12a2 2 0 012 2v8l-6 6H6a2 2 0 01-2-2z"/><path d="M14 20v-4a2 2 0 012-2h4"/>',
 border:'<rect x="4" y="4" width="16" height="16" rx="4" stroke-dasharray="3 3"/>',
 adjust:'<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 010 18z" fill="currentColor"/>',
 erase:'<path d="M20 20H9L4 15l9-9 7 7-6 6"/><path d="M8 11l5 5"/>',restore:'<path d="M3 12a9 9 0 109-9 9 9 0 00-7 3.4L3 8"/><path d="M3 3v5h5"/>',
 chat:'<path d="M4 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2h-7l-5 4v-4H6a2 2 0 01-2-2z"/>',
 eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 eyeoff:'<path d="M3 3l18 18M10.6 6.2A9.6 9.6 0 0112 5c6 0 10 7 10 7a17 17 0 01-3 3.7M6.6 6.7A17 17 0 002 12s4 7 10 7a9.7 9.7 0 004.3-1"/>',
 lock:'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',unlock:'<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 017-2.5"/>',
 trash:'<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',x:'<path d="M6 6l12 12M18 6L6 18"/>',chev:'<path d="M9 6l6 6-6 6"/>',
 download:'<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',star:'<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
 edit:'<path d="M4 20h4L19 9l-4-4L4 16z"/>',up:'<path d="M6 15l6-6 6 6"/>',down:'<path d="M6 9l6 6 6-6"/>',back:'<path d="M15 6l-6 6 6 6"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',play:'<path d="M8 5l11 7-11 7z"/>',photo:'<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
 eyeb:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',check:'<path d="M5 12l5 5 9-10"/>',first:'<path d="M6 5v14M18 6l-9 6 9 6z"/>',last:'<path d="M18 5v14M6 6l9 6-9 6z"/>',prev:'<path d="M15 6l-6 6 6 6"/>',next:'<path d="M9 6l6 6-6 6"/>'};
const ic=n=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[n]||''}</svg>`;

/* ---------- actions (event delegation: no inline handler names, which can collide with Element methods such as animate()) */
const ACT={};
document.addEventListener('click',e=>{const el=e.target.closest('[data-act]');if(!el)return;const f=ACT[el.dataset.act];if(f){e.preventDefault();f(el,e)}});

/* ---------- dialogs */
function dlg(html){$('dlg').innerHTML=`<div class=dbox>${html}</div>`;$('dlg').classList.add('on')}
function closeDlg(){$('dlg').classList.remove('on');$('dlg').innerHTML=''}
$('dlg').addEventListener('mousedown',e=>{if(e.target.id==='dlg')closeDlg()});
ACT.dlgx=closeDlg;
let ASK=null;
function askText(title,value,cb,ok='Save'){ASK=cb;dlg(`<h2>${esc(title)}</h2><input type=text id=askv value="${esc(value)}"><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=askok>${ok}</button></div>`);const i=$('askv');i.focus();i.select();i.onkeydown=e=>{if(e.key==='Enter')ACT.askok()}}
ACT.askok=()=>{const v=$('askv').value.trim();closeDlg();if(v&&ASK)ASK(v)};
function confirmDlg(msg,cb,ok='Delete'){ASK=cb;dlg(`<h2>${esc(msg)}</h2><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=cfok>${ok}</button></div>`)}
ACT.cfok=()=>{closeDlg();if(ASK)ASK()};
let PK=null;
async function pickPack(cb,title='Add to pack'){await loadLib();PK=cb;
 dlg(`<h2>${esc(title)}</h2>${LIB.packs.map(p=>`<div class=pl data-act=pk data-id=${p.id}><div class=cover>${coverMedia(p)}</div><div><b>${esc(p.name)}</b><br><small>${p.stickers.length} stickers</small></div></div>`).join('')||'<div class=mut>No packs yet: create one.</div>'}
  <div class=row><input type=text id=npn placeholder="New pack name"><button class="btn pri" data-act=pknew>Create</button></div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button></div>`)}
ACT.pk=el=>{closeDlg();PK(el.dataset.id)};
ACT.pknew=async()=>{const r=await post('/api/packs',{name:$('npn').value});if(!r.ok)return toast(r.j.error,1);closeDlg();PK(r.j.id)};

/* ---------- library cache + media helpers */
let LIB={packs:[],recent:[],total:0},LIBQ='',LIBTAB='recent';
async function loadLib(){const r=await api('/api/library');if(r.ok)LIB=r.j;return LIB}
const media=(s,cls='')=>s.type==='animated'?`<video class="${cls}" src="/lib/${encodeURIComponent(s.file)}" autoplay loop muted playsinline></video>`:`<img class="${cls}" src="/lib/${encodeURIComponent(s.file)}" loading=lazy>`;
const coverMedia=p=>{const s=p.stickers.find(x=>x.id===p.cover)||p.stickers[0];return s?media(s):'<span class=mut>—</span>'};
const packById=id=>LIB.packs.find(p=>p.id===id);

/* ---------- router */
const SCREENS=['generate','library','create','editor','pack','export','settings','animate','chat','prepare'],RENDER={};
const RAIL=[['generate','gen','Generate'],['library','lib','Library'],['chat','chat','Chat'],['create','create','Create'],['settings','settings','Settings']],RAILOF={pack:'library',editor:'create',export:'create',animate:'library',prepare:'create'};
let route_='library',PACK_ID=null;
function drawRail(){$('rail').innerHTML=`<div class=logo>M</div>`+RAIL.map(([k,i,l])=>`<button class="rbtn ${(RAILOF[route_]||route_)===k?'on':''}" data-act=nav data-to=${k}>${ic(i)}<span>${l}</span></button>`).join('')}
ACT.nav=el=>{location.hash='#/'+el.dataset.to};
function route(){const h=location.hash.replace(/^#\/?/,'')||'library',ps=h.split('/'),n=ps[0],a=ps.slice(1).join('/');route_=SCREENS.includes(n)?n:'library';
 SCREENS.forEach(s=>$('s-'+s).classList.toggle('on',s===route_));drawRail();drawCol2();if(RENDER[route_])RENDER[route_](a)}
window.addEventListener('hashchange',route);

/* ---------- second column: packs (occupies the chat-list position of the Mirsal mockup; every row is a real pack) */
let C2Q='';
function drawCol2(){const on=['library','pack','chat'].includes(route_);document.body.classList.toggle('col2',on);if(!on)return;
 if(route_==='chat')return chList();
 const q=C2Q.trim().toLowerCase(),cur=route_==='pack'?PACK_ID:null;
 $('col2').innerHTML=`<div class=c2h><h1>Packs</h1><button class=iconbtn data-act=newpack title="New pack">${ic('plus')}</button></div>
  <div class=c2s><input type=search id=c2q placeholder="Search packs…" value="${esc(C2Q)}"></div>
  <div class=c2l>${LIB.packs.filter(p=>!q||p.name.toLowerCase().includes(q)).map(p=>`<div class="crow ${p.id===cur?'on':''}" data-act=openpack data-id=${p.id}><div class=cv>${coverMedia(p)}</div><div><b>${esc(p.name)}</b><small>${p.stickers.length} stickers</small></div><span class=meta>${p.stickers.some(s=>s.type==='animated')?'animated':''}</span></div>`).join('')||'<div class=mut style="padding:14px">No packs yet.</div>'}</div>`;
 const i=$('c2q');i.oninput=e=>{C2Q=e.target.value;const pos=e.target.selectionStart;drawCol2();const n=$('c2q');n.focus();n.setSelectionRange(pos,pos)}}

/* ---------- Library (DESKTOP_01) */
let PACKS_ALL=false,LCL=[],LCI=null;
RENDER.library=async()=>{await loadLib();drawCol2();
 $('s-library').innerHTML=`<div style="max-width:1000px;margin:0 auto"><div class=sh>${ic('sticker')} Sticker Library</div>
  <input type=search id=libq placeholder="Search stickers or packs…" value="${esc(LIBQ)}" style="margin-bottom:14px">
  <div class=tabs><button class="tab ${LIBTAB==='recent'?'on':''}" data-act=libtab data-t=recent>Recent</button><button class="tab ${LIBTAB==='mine'?'on':''}" data-act=libtab data-t=mine>My Stickers</button></div>
  <div id=libbody></div><div class=fab><button class="btn pri" data-act=nav data-to=create>${ic('plus')} Create</button></div></div>`;
 $('libq').oninput=e=>{LIBQ=e.target.value;libBody()};libBody()};
ACT.libtab=el=>{LIBTAB=el.dataset.t;RENDER.library()};
ACT.seeall=el=>{if(el.dataset.k==='st'){LIBTAB='mine'}else PACKS_ALL=!PACKS_ALL;RENDER.library()};
function libBody(){const q=LIBQ.trim().toLowerCase(),hit=s=>!q||(s.name+' '+s.emoji+' '+(s.pack||'')).toLowerCase().includes(q);
 const stTile=(s,i)=>`<div class=st data-act=lcopen data-i=${i} title="${esc(s.name)}">${media(s)}<span class=em>${esc(s.emoji)}</span></div>`;
 let h='';
 if(!LIB.total&&!LIB.packs.length)h=`<div class="card" style="text-align:center;padding:40px"><h2>Nothing here yet</h2><p class=mut>Generate a pack from a prepared sheet, or create a sticker from a photo.</p><button class="btn pri" data-act=nav data-to=generate>${ic('gen')} Generate</button> <button class=btn data-act=nav data-to=create>${ic('create')} Create from photo</button></div>`;
 else if(LIBTAB==='recent'){const rs=LIB.recent.filter(hit),ps=LIB.packs.filter(p=>!q||p.name.toLowerCase().includes(q)||p.stickers.some(hit)),shown=PACKS_ALL?ps:ps.slice(0,4);
  LCL=rs;
  h=`<div class=row style="justify-content:space-between;margin:6px 0"><h2>Recent</h2><button class=seeall data-act=seeall data-k=st>See all ${ic('chev')}</button></div><div class=strip>${rs.map(stTile).join('')||'<span class=mut>No matches.</span>'}</div>
  <div class=row style="justify-content:space-between;margin:14px 0 8px"><h2>My Packs</h2>${ps.length>4?`<button class=seeall data-act=seeall data-k=pk>${PACKS_ALL?'Show less':'See all'} ${ic('chev')}</button>`:''}</div>
  <div class=plist>${shown.map(p=>`<div class=packrow data-act=openpack data-id=${p.id}><div class=cover>${coverMedia(p)}</div><div style="flex:1"><b>${esc(p.name)}</b><br><small>${p.stickers.length} stickers</small></div>${ic('chev')}</div>`).join('')||'<div class=mut style="padding:14px">No packs.</div>'}</div>`}
 else{const all=LIB.packs.flatMap(p=>p.stickers.map(s=>({...s,pack_id:p.id,pack:p.name}))).filter(hit);LCL=all;
  h=`<div class=grid>${all.map((s,i)=>`<div class=cell data-act=lcopen data-i=${i}>${media(s)}<div class=cap>${esc(s.emoji)} ${esc(s.name)}</div></div>`).join('')||'<span class=mut>No matches.</span>'}</div>`}
 $('libbody').innerHTML=h}
ACT.openpack=el=>{location.hash='#/pack/'+el.dataset.id};
ACT.newpack=()=>askText('New pack name','My Pack',async n=>{const r=await post('/api/packs',{name:n});if(r.ok){await loadLib();location.hash='#/pack/'+r.j.id}else toast(r.j.error,1)},'Create');

/* ---------- Settings */
RENDER.settings=async()=>{const r=await api('/api/generations'),h=r.j.health||{},p=r.j.paths||{};
 $('s-settings').innerHTML=`<div style="max-width:760px;margin:0 auto"><h1>Settings & health</h1><div class=card style="margin-top:12px"><div class=kv>
  <span>watch folder (read-only)</span><span>${esc(p.input)}</span><span>output</span><span>${esc(p.out)}</span><span>ffmpeg</span><span>${esc(h.ffmpeg||'not found')}</span>
  <span>VP9 + alpha encoder</span><span>${h.vp9?'<b style="color:var(--pri-d)">ready</b>':'<b style="color:var(--bad)">missing</b>: final WEBM encodes will fail (live preview still works). Run <code>python -m mirsal doctor</code>'}</span></div></div>
  <p class=mut>Photo cutout uses the engine's chroma key for green/blue screens and OpenCV GrabCut otherwise (offline). A learned matte model is planned for Phase 3C.</p></div>`};

/* ================= Generate: the lifecycle console (Phase 1) ================= */
let sel=null,bg='checker',last='',open=new Set(),busy=false,cur=null,mi=null;
$('go').onclick=async()=>{const p=$('prompt').value.trim();if(!p)return;const r=await post('/api/generations',{prompt:p});say(r.ok?'':r.j.error);if(r.ok){sel=r.j.id;last=''}};
$('more').onclick=async()=>{if(!sel)return;const r=await post(`/api/generations/${sel}/more`);say(r.ok?'':r.j.error);if(r.ok){sel=r.j.id;last=''}};
async function useInput(subject,variant){const r=await post('/api/generations',{prompt:$('prompt').value.trim()||subject.replace(/_/g,' '),variant});say(r.ok?'':r.j.error);if(r.ok){sel=r.j.id;last=''}}
async function loadInputs(){const r=await api('/api/inputs');if(!r.ok)return;$('inputs').innerHTML=r.j.inputs.length?r.j.inputs.map(s=>`<div class=gen style="cursor:default"><b>${s.subject}</b>${s.variants.map(v=>`<div class=chk style="margin:4px 0"><b>${String(v.folder)}</b> ${v.sheet}<br><span class=mut>${v.video?'3x3 video':'no video'} · ${v.clips} clips · pairing ${v.pairing}${v.plan?' · prompts '+v.plan:' · stub labels'}</span> <button class="btn sm" onclick="useInput('${s.subject}',${v.variant})">Use</button></div>`).join('')}</div>`).join(''):'<div class=mut>No prepared inputs found. Check Phase_01/Images_gen (run: python -m mirsal doctor).</div>'}
// live preview: the paired 3x3 video is played in the browser, each cell keyed + framed like its sticker, so a click shows motion at once.
const PV={gid:null,all:false,idx:new Set(),v:null,cal:{},t:-1};
function pvOn(i){return PV.gid===sel&&(PV.all||PV.idx.has(i))}
function pvVideo(){if(PV.v&&PV.v.dataset.gid==sel)return PV.v;if(PV.v){PV.v.pause();PV.v.remove()}
  const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.dataset.gid=sel;v.style.cssText='position:fixed;width:1px;height:1px;opacity:0;pointer-events:none';
  v.src=`/src/${sel}/video`;document.body.appendChild(v);v.play().catch(()=>{});PV.v=v;PV.cal={};PV.t=-1;return v}
// cell i of the video: the still's measured cut (source.grid.rects on the sheet) scaled to the video, else equal thirds
function vcell(g,v,i){const G=g&&g.source.grid,sw=g&&g.source.sheet_size;if(G&&sw){const r=G.rects[i-1],kx=v.videoWidth/sw[0],ky=v.videoHeight/sw[1];return[r[0]*kx,r[1]*ky,r[2]*kx,r[3]*ky]}
  const w=v.videoWidth/3,h=v.videoHeight/3;return[((i-1)%3)*w,((i-1)/3|0)*h,w,h]}
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
async function playVideo(scope,index){
  if(!cur)return;
  if(PV.gid!=sel){PV.gid=sel;PV.all=false;PV.idx=new Set()}
  if(scope==='pack')PV.all=true;else PV.idx.add(index);
  if(cur.source.video_path)pvVideo();
  last='';
  const r=await post(`/api/generations/${sel}/animate`,{scope,index});
  say(r.ok?(r.j.message||'live preview playing; encoding the final 512×512 WEBM…'):r.status===409?'live preview playing (final encode waits: another job is running)':r.j.error)}
const setbg=b=>{bg=b;last='';if(mi!==null)drawModal()};
function openModal(i){mi=i;drawModal()}
function closeModal(){mi=null;$('modal').classList.remove('on')}
function step(d){if(cur){const n=cur.stickers.length;mi=((mi-1+d+n)%n)+1;drawModal()}}
document.addEventListener('keydown',e=>{if(mi===null)return;if(e.key==='Escape')closeModal();if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1)});
const bgBtns=()=>['checker','light','dark','wall'].map(x=>`<button class="${x==bg?'act':''}" onclick="setbg('${x}')">${x}</button>`).join('');
function drawModal(){
  if(mi===null||!cur)return;
  const g=cur,t=g.stickers[mi-1],s=g.source,base=`/out/${g.generation_id}/`,m=t.metrics||{},c=m.cell,b=m.bbox,am=t.anim_metrics||{};
  let raw='';if(c&&s.sheet_copy){const col=(c[0]/c[2])|0,row=(c[1]/c[3])|0;raw=`<div class=box style="background-image:url(${base+s.sheet_copy});background-size:300% 300%;background-position:${col*50}% ${row*50}%">${b?`<div class=bbox style="left:${b[0]/c[2]*100}%;top:${b[1]/c[3]*100}%;width:${(b[2]-b[0])/c[2]*100}%;height:${(b[3]-b[1])/c[3]*100}%"></div>`:''}</div>`}
  const still=t.png?`<img src="${base+t.png}">`:`<div class=mut style="padding:12px">${t.status}${t.reason?': '+t.reason:''}</div>`;
  const live=pvOn(t.index)&&t.status==='READY'&&s.video_path;
  const vid=t.webm?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:live?canvasFor(t.index,384):`<div class=mut style="padding:12px">${t.anim_status==='NOT_REQUESTED'&&t.status==='READY'&&s.has_video?`<button class="btn pri sm" onclick="playVideo('slice',${t.index})">▶ Animate this</button>`:''} </div><div class=mut style="padding:0 12px">${t.anim_status}${t.anim_reason?': '+t.anim_reason:''}</div>`;
  const chk=(t.report||[]).map(r=>`<div class=chk><span class="${r.ok?'p':'f'}">${r.ok?'✓':'✗'} ${r.name}</span> <span class=mut>${r.detail||''}</span></div>`).join('');
  const att=(m.attempts||[]).map(a=>a.note?`<div class=chk>🔍 <b>dissect</b>: ${Object.entries(a.note).map(([k,v])=>k+' '+v).join(' · ')}</div>`:`<div class=chk>${a.ok?'✓':'✗'} <b>${a.name}</b> ${a.reason?'('+a.reason+')':''}</div>`).join('')+(m.ruled_out?'<div class=chk style="color:var(--bad)">ruled out: keying could not be repaired</div>':'')+(m.recovered_by?`<div class=chk class=p>recovered by: ${m.recovered_by}</div>`:'');
  const kv=o=>Object.entries(o).filter(([k])=>!['attempts','cell','bbox','recovered_by','ruled_out'].includes(k)).map(([k,v])=>`<span>${k}</span><span>${typeof v==='object'?JSON.stringify(v):v}</span>`).join('');
  const thumbs=g.stickers.map(x=>`<div class="thumb ${x.status} ${x.index===mi?'on':''}" onclick="openModal(${x.index})" title="${x.name}">${x.png?`<img src="${base+x.png}">`:x.index}</div>`).join('');
  const ready=t.status==='READY';
  $('modal').innerHTML=`<div class=mbox><div class=mrow><button class="btn nav" onclick="step(-1)">‹</button>
    <div style="flex:1"><b>${t.emoji} ${t.index}/${cur.stickers.length} · ${t.name}</b><div class=mut>${t.prompt}</div></div>
    <div class=toggles>${bgBtns()}</div>${ready?`<button class=btn data-act=editgen data-i=${t.index}>${ic('edit')} Edit</button><button class="btn pri" data-act=addgen data-i=${t.index}>${ic('plus')} Add to pack</button>`:''}<button class="btn nav" onclick="step(1)">›</button><button class=btn onclick="closeModal()">✕</button></div>
    <div class=mpanes>
      <div class=pane><div class=mut>raw cell + bounding box</div>${raw||'<div class=mut>n/a</div>'}</div>
      <div class=pane><div class=mut>sticker (${m.format||'-'}, ${m.kb||'-'}KB)</div><div class="box bg-${bg}">${still}</div></div>
      <div class=pane><div class=mut>video ${t.webm?am.source||'':live?'live preview (final WEBM encoding…)':''} ${am.kb?am.kb+'KB':''}</div><div class="box bg-${bg}">${vid}</div>${t.webm?`<div class=row><button class="btn sm" data-act=addgen data-i=${t.index} data-k=animated>${ic('plus')} Add animated to pack</button></div>`:''}</div>
    </div>
    <div class=mpanes><div class=pane><b>checks</b>${chk||'<div class=mut>none</div>'}${att?'<br><b>keying recovery</b>'+att:''}</div>
      <div class=pane><b>metrics</b><div class=kv>${kv(m)}</div>${Object.keys(am).length?'<br><b>video metrics</b><div class=kv>'+kv(am)+'</div>':''}</div></div>
    <div class=thumbs>${thumbs}</div><div class=mut>← → to browse, Esc to close</div></div>`;
  $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')closeModal()};
}
ACT.addgen=el=>{const i=+el.dataset.i,k=el.dataset.k||'static',gid=sel;pickPack(async pid=>{const r=await post(`/api/packs/${pid}/stickers`,{from_generation:{id:gid,index:i,kind:k}});
  if(r.ok){await loadLib();toast(`Added "${r.j.name}" to ${packById(pid)?.name||'pack'}`)}else toast(r.j.error,1)})};
ACT.editgen=el=>{const t=cur.stickers[+el.dataset.i-1];closeModal();Ed.openImage(`/out/${cur.generation_id}/${t.png}`,{outlined:true,name:t.name,emoji:t.emoji})};
function stepState(events,stage){const e=events.filter(x=>x.stage===stage);if(!e.length)return{s:'',ms:''};const l=e[e.length-1];return{s:l.status,ms:l.ms?l.ms+' ms':'',d:l.detail}}
function detailText(d){if(!d)return'';if(typeof d==='string')return d;return Object.entries(d).map(([k,v])=>k+': '+(typeof v==='object'?JSON.stringify(v):v)).join(' · ')}
// the measured cut lines (gutter cuts), or the thirds overlay for results written before grids were measured
function cutLines(s){const G=s.grid,W=s.sheet_size;if(!G||!W)return'<div class=grid3></div>';
  return G.xs.slice(1,-1).map(x=>`<i class=cutv style="left:${100*x/W[0]}%"></i>`).join('')+G.ys.slice(1,-1).map(y=>`<i class=cuth style="top:${100*y/W[1]}%"></i>`).join('')}
function render(g){
  const s=g.source,base=`/out/${g.generation_id}/`;
  const steps=g.stages.map(st=>{const x=stepState(g.events,st);return`<div class="step ${x.s}"><b>${st}</b><small>${x.s||'pending'} ${x.ms}</small><br><small>${esc(detailText(x.d).slice(0,80))}</small></div>`}).join('');
  const sheet=s.sheet_copy?`<div><div class=mut>raw sheet (${s.sheet_size.join('×')}) · ${s.sheet}</div><div class=sheetbox style="background-image:url(${base+s.sheet_copy})">${cutLines(s)}</div></div>`:'';
  const keyed=s.keyed?`<div><div class=mut>keyed (background removed)</div><div class="sheetbox bg-${bg}" style="background-size:100% 100%"><img src="${base+s.keyed}" style="width:100%;height:100%"></div></div>`:'';
  const tiles=g.stickers.map(t=>{
    const m=t.metrics||{},c=m.cell,b=m.bbox;let raw='';
    if(c&&s.sheet_copy){const col=(c[0]/c[2])|0,row=(c[1]/c[3])|0;raw=`<div class=raw style="background-image:url(${base+s.sheet_copy});background-size:300% 300%;background-position:${col*50}% ${row*50}%">${b?`<div class=bbox style="left:${b[0]/c[2]*100}%;top:${b[1]/c[3]*100}%;width:${(b[2]-b[0])/c[2]*100}%;height:${(b[3]-b[1])/c[3]*100}%"></div>`:''}</div>`}
    const clipw=!s.video_path&&((s.clips||{})[t.index]||{}).webm,live=pvOn(t.index)&&t.status==='READY';
    const out=t.webm?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:live&&s.video_path?canvasFor(t.index,192):live&&clipw?`<video src="/src/${sel}/clip/${t.index}" autoplay loop muted playsinline></video><span class=livebadge>live preview</span>`:t.png?`<img src="${base+t.png}">`:`<span class=mut style="padding:6px;display:block">${t.status}${t.reason?': '+t.reason:''}</span>`;
    const chk=(t.report||[]).map(r=>`<span class="${r.ok?'p':'f'}">${r.ok?'✓':'✗'} ${r.name}</span>`).join(' ');
    const an=t.anim_status!=='NOT_REQUESTED'?`<div class=chk>video: ${t.anim_status}${t.anim_reason?' ('+t.anim_reason+')':''} ${t.anim_metrics.kb?t.anim_metrics.kb+'KB seam '+t.anim_metrics.loop_seam:''}</div>`:'';
    const can=t.status==='READY'&&s.has_video&&t.anim_status!=='READY';
    return`<div class="tile ${t.status}"><div class=pv onclick="openModal(${t.index})" title="click to enlarge">${raw}<div class="out bg-${bg}">${out}</div></div>
      <h4 onclick="openModal(${t.index})">${t.emoji} ${t.name}</h4><div class=mut>${t.prompt}</div>
      <div class=chk>${t.status} ${m.scale_mode?'· '+m.scale_mode+' scale '+m.scale:''} ${m.kb?'· '+m.kb+'KB':''} ${m.recovered_by?'· recovered: '+m.recovered_by:''} ${m.ruled_out?'· ruled out':''}</div>
      <details data-k=${t.index} ${open.has(t.index)?'open':''}><summary class=mut>checks</summary><div class=chk>${chk}</div><div class=chk>${JSON.stringify(m)}</div></details>${an}
      <div class=row><button class="btn sm" ${can?'':'disabled'} onclick="playVideo('slice',${t.index})">▶ Animate this</button>${t.status==='READY'?`<button class="btn sm" data-act=editgen data-i=${t.index}>Edit</button><button class="btn sm" data-act=addgen data-i=${t.index} data-k=${t.webm?'animated':'static'}>+ Pack</button>`:''}</div></div>`}).join('');
  const anyReady=g.stickers.some(t=>t.status==='READY'),allReady=g.stickers.filter(t=>t.status==='READY').length;
  return`<h1>${g.generation_id} · ${g.task_slug} · ${s.subject} variant ${s.variant}/${s.n_variants} ${g.busy?'<span class=badge>working…</span>':''}</h1>
   <div class=mut>${esc(g.prompt)}</div><div class=mut>labels from: <b>${g.plan_source||"stub (prompter.py)"}</b>${(g.plan_source||"stub").startsWith("stub")?" (invented by the stub, NOT read from the image)":""}</div><details><summary class=mut>sheet / video prompt (copy)</summary><textarea readonly rows=5>${g.sheet_prompt||''}</textarea><textarea readonly rows=3>${g.video_prompt||''}</textarea></details>${g.error?`<p style="color:var(--bad)">${g.error}</p>`:''}
   <div class=steps>${steps}</div>
   <div class=panel><div class=toggles>background: ${bgBtns()}</div><br><div class=pair>${sheet}${keyed}</div></div>
   <div class=panel><div class=row style="margin-top:0"><b>Slices (512×512 max, in slices/)</b>
     <button class="btn pri" ${anyReady&&s.has_video?'':'disabled'} onclick="playVideo('pack')">▶ Animate all ${g.stickers.length}</button>
     <button class=btn ${allReady?'':'disabled'} data-act=addall>${ic('plus')} Add all ${allReady} to pack</button>
     ${s.has_video?'':'<span class=mut>no video prepared for this variation</span>'}</div><div class=tiles>${tiles}</div></div>`}
ACT.addall=()=>{const gid=sel,ready=cur.stickers.filter(t=>t.status==='READY').map(t=>t.index);pickPack(async pid=>{let n=0,bad='';for(const i of ready){const r=await post(`/api/packs/${pid}/stickers`,{from_generation:{id:gid,index:i,kind:'static'}});if(r.ok)n++;else bad=r.j.error}
  await loadLib();toast(`Added ${n} stickers to ${packById(pid)?.name||'pack'}${bad?' ('+bad+')':''}`,!!bad)},'Add all to pack')};
async function tick(){try{await tick2()}catch(e){$('msg').textContent='UI error: '+e.message}}
async function tick2(){
  if(route_!=='generate'&&mi===null)return;
  const l=await api('/api/generations');if(l.ok){busy=l.j.busy;const h=l.j.health||{};$('health').innerHTML=h.vp9===false?'<div class=warn>⚠ this ffmpeg cannot encode VP9 → the final WEBM will fail. Live preview still works. Run <code>python -m mirsal doctor</code>.</div>':'';
    $('list').innerHTML=l.j.generations.map(g=>`<div class="gen ${g.id==sel?'sel':''}" onclick="sel=${g.id};last=''"><b>${g.generation_id}</b> <span class=badge>${g.stage}</span><br><small>${g.subject} v${g.variant} · ${esc(g.prompt)}</small></div>`).join('');if(sel===null&&l.j.generations.length)sel=l.j.generations[0].id}
  if(sel!==null){const r=await api('/api/generations/'+sel);if(r.ok){const k=JSON.stringify(r.j)+bg;if(k!==last){document.querySelectorAll('details[data-k]').forEach(d=>d.open?open.add(+d.dataset.k):open.delete(+d.dataset.k));last=k;cur=r.j;$('main').innerHTML=render(r.j);if(mi!==null)drawModal()}}}
}
RENDER.generate=()=>{last='';tick()};
setInterval(tick,500);loadInputs();setInterval(()=>{if(route_==='generate')loadInputs()},5000);
