/* Mirsal Sticker Builder: shell, router, Library, Generate (lifecycle console), Settings. No external libraries. */
'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api=async(u,o)=>{const r=await fetch(u,o);let j={};try{j=await r.json()}catch(e){}return{ok:r.ok,status:r.status,j}};
const post=(u,b,h)=>api(u,{method:'POST',headers:{'Content-Type':'application/json',...(h||{})},body:JSON.stringify(b||{})});
/* one key per click: a retry or a second tab with the same key is answered with the first result, never run (and paid) twice */
const ikey=()=>(self.crypto&&crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2));
let toastT=0;function toast(m,bad){const t=$('toast');t.textContent=m||'';t.className=(m?'on ':'')+(bad?'bad':'');clearTimeout(toastT);if(m)toastT=setTimeout(()=>t.className='',bad?6000:3500)}
const say=t=>{const m=$('msg');if(m)m.innerHTML=t||''};   // callers escape what they pass
const ICONS={
 ai:'<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3.5l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6zM5.5 16l.6 1.6 1.6.6-1.6.6L5.5 20l-.6-1.7-1.6-.6 1.6-.6z"/>',panel:'<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M9 4v16"/>',
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
 plus:'<path d="M12 5v14M5 12h14"/>',search:'<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',hist:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',folder:'<path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>',film:'<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 4v16M16 4v16M3 9h5M16 9h5M3 15h5M16 15h5"/>',telegram:'<path d="M21 4L3 11l6 2 2 6 3-4 5 4z"/><path d="M9 13l8-6"/>',play:'<path d="M8 5l11 7-11 7z"/>',photo:'<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
 eyeb:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',check:'<path d="M5 12l5 5 9-10"/>',first:'<path d="M6 5v14M18 6l-9 6 9 6z"/>',last:'<path d="M18 5v14M6 6l9 6-9 6z"/>',prev:'<path d="M15 6l-6 6 6 6"/>',next:'<path d="M9 6l6 6-6 6"/>',users:'<circle cx="9" cy="8" r="3.2"/><path d="M3 19c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M16 4.8a3.2 3.2 0 0 1 0 6.4M17.5 13.6c2.1.6 3.5 2.6 3.5 5.4"/>',chart:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'};
const ic=n=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[n]||''}</svg>`;

/* ---------- actions (event delegation: no inline handler names, which can collide with Element methods such as animate()) */
const ACT={};
document.addEventListener('click',e=>{const el=e.target.closest('[data-act]');if(!el)return;const f=ACT[el.dataset.act];if(f){e.preventDefault();if(el.closest('#col2'))document.body.classList.remove('c2open');f(el,e)}});

/* ---------- dialogs */
function dlg(html){$('dlg').innerHTML=`<div class=dbox>${html}</div>`;$('dlg').classList.add('on')}
function closeDlg(){$('dlg').classList.remove('on');$('dlg').innerHTML=''}
$('dlg').addEventListener('mousedown',e=>{if(e.target.id==='dlg')closeDlg()});
ACT.dlgx=closeDlg;
let ASK=null;
function askText(title,value,cb,ok='Save'){ASK=cb;dlg(`<h2>${esc(title)}</h2><input type=text id=askv value="${esc(value)}"><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=askok>${ok}</button></div>`);const i=$('askv');i.focus();i.select();i.onkeydown=e=>{if(e.key==='Enter')ACT.askok()}}
ACT.askok=()=>{const v=$('askv').value.trim();closeDlg();if(v&&ASK)ASK(v)};
/* a sticker's id (G103/S2) is its own control, never part of its name: hover shows it, one click copies it (P5 of the UI/UX spec) */
ACT.copyid=async el=>{const v=el.dataset.v||'';if(!v)return;try{await navigator.clipboard.writeText(v);toast('Copied '+v)}catch(e){toast(v+' (copy it from here)')}};
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
/* the packs of one batch group sit together, as the Studio sits the batches (pack.group from GET /api/library, flow/groups.pack_groups): entries {pack} or
   {group, packs} in the order the first pack of each appears (pure) */
const packEntries=ps=>{const out=[],at={};for(const p of ps||[]){if(!p.group){out.push({pack:p});continue}
  if(at[p.group])at[p.group].packs.push(p);else{at[p.group]={group:p.group,packs:[p]};out.push(at[p.group])}}
  for(const e of out)if(e.packs)e.packs.sort((a,b)=>(b.lead?1:0)-(a.lead?1:0));     /* the parent (Assign as parent in the Studio) leads its group */
  return out};
const PKFOLD=new Map();      /* group -> open (true) / closed (false) as the person left it; untouched, a group is open while the pack in view is in it */
async function loadLib(){const r=await api('/api/library');if(r.ok)LIB=r.j;return LIB}
const media=(s,cls='')=>s.type==='animated'?`<video class="${cls}" src="/lib/${encodeURIComponent(s.file)}" autoplay loop muted playsinline></video>`:`<img class="${cls}" src="/lib/${encodeURIComponent(s.file)}" loading=lazy>`;
const coverMedia=p=>{const s=p.stickers.find(x=>x.id===p.cover)||p.stickers[0];return s?media(s):'<span class=mut>—</span>'};
const packById=id=>LIB.packs.find(p=>p.id===id);

/* ---------- router */
const SCREENS=['agent','effects','generate','history','library','create','editor','pack','export','settings','animate','chat','prepare','users'],RENDER={};
const RAIL=[['agent','ai','AI'],['generate','gen','Studio'],['library','lib','Library'],['chat','chat','Chat'],['create','create','Create'],['users','users','Users'],['settings','settings','Settings']],RAILOF={effects:'create',pack:'library',editor:'create',export:'create',animate:'library',prepare:'create'};
let route_='generate',PACK_ID=null;
function drawRail(){$('c2tog').innerHTML=ic('panel');$('rail').innerHTML=`<button class=logo data-act=home title="Home: the welcome" aria-label="Mirsal home"><img src=/assets/brand/mirsal-logo.png alt=""></button>`+RAIL.filter(([k])=>k!=='users'||typeof AUV==='undefined'||AUV.staff(typeof ME==='undefined'?null:ME)).map(([k,i,l])=>`<button class="rbtn ${(RAILOF[route_]||route_)===k?'on':''}" data-act=nav data-to=${k}>${ic(i)}<span>${l}</span></button>`).join('')}
/* narrow screens: the second column is a drawer (studio.css, 'the shell on narrow screens') */
ACT.c2tog=()=>document.body.classList.toggle('c2open');
ACT.nav=el=>{location.hash='#/'+(el.dataset.to==='generate'?'studio':el.dataset.to)};
function route(){SEL.clear();const h=location.hash.replace(/^#\/?/,'')||'agent',ps=h.split('/'),n=ps[0]==='studio'?'generate':ps[0],a=ps.slice(1).join('/');route_=SCREENS.includes(n)?n:'agent';document.body.classList.remove('c2open');
 SCREENS.forEach(s=>$('s-'+s).classList.toggle('on',s===route_));drawRail();drawCol2();if(RENDER[route_])RENDER[route_](a)}
window.addEventListener('hashchange',route);

/* ---------- second column: packs (occupies the chat-list position of the Mirsal mockup; every row is a real pack) */
let C2Q='';
/* the second column of a section: the list that belongs to it, in the same place on every screen. Studio and Create list the earlier batches (live.js); Settings and the full-screen tools (editor, export, prepare, animate) have no list */
const COL2=['agent','generate','library','pack','chat','create','users'];
function drawCol2(){const on=COL2.includes(route_);document.body.classList.toggle('col2',on);if(!on)return;
 if(route_==='generate'||route_==='create')return typeof histCol==='function'?histCol():0;
 if(route_==='chat')return chList();
 if(route_==='users')return typeof usCol==='function'?usCol():0;
 if(route_==='agent')return typeof agList==='function'?agList():0;
 const q=C2Q.trim().toLowerCase(),cur=route_==='pack'?PACK_ID:null;
 $('col2').innerHTML=`<div class=c2h><h1>Packs</h1><button class=iconbtn data-act=newpack title="New pack">${ic('plus')}</button></div>
  <div class=c2s><input type=search id=c2q placeholder="Search packs…" value="${esc(C2Q)}"></div>
  <div class=c2l>${packEntries(LIB.packs.filter(p=>!q||p.name.toLowerCase().includes(q))).map(e=>{const row=(p,sub)=>`<div class="crow${sub?' sub':''} ${p.id===cur?'on':''}" data-act=openpack data-id=${p.id}><div class=cv>${coverMedia(p)}</div><div><b>${esc(p.name)}</b><small>${p.stickers.length} stickers</small></div><span class=meta>${p.stickers.some(s=>s.type==='animated')?'animated':''}</span></div>`;
   if(e.pack)return row(e.pack);const open=PKFOLD.has(e.group)?PKFOLD.get(e.group):e.packs.some(p=>p.id===cur),f=e.packs[0];
   const sub=p=>row(p,true).replace(/<\/div>$/,`<button class="link pkmerge" data-act=pkmerge data-id=${p.id} data-into=${f.id} title="One pack: its animated stickers replace their stills in ${esc(f.name)}, the rest moves there, and this pack goes to the trash">Merge into parent</button></div>`);
   return`<div class="crow pkgrp ${f.id===cur?'on':''}" data-act=openpack data-id=${f.id}><div class=cv>${coverMedia(f)}</div><div><b>${esc(f.name)}</b><small>${e.packs.length} packs · group ${esc(e.group)}</small></div><button class=iconbtn data-act=pkgrp data-g=${esc(e.group)} title="${open?'Fold the group':'Show every pack of the group'}" aria-expanded=${open}>${ic('chev')}</button></div>${open?e.packs.slice(1).map(sub).join(''):''}`}).join('')||'<div class=mut style="padding:14px">No packs yet.</div>'}</div>`;
 const i=$('c2q');i.oninput=e=>{C2Q=e.target.value;const pos=e.target.selectionStart;drawCol2();const n=$('c2q');n.focus();n.setSelectionRange(pos,pos)}}

/* ---------- Library (DESKTOP_01) */
let PACKS_ALL=false,LCL=[],LCI=null;
/* bulk selection (the square marker on a sticker), shared by the pack screen and My Stickers */
const SEL=new Map(),selKey=(p,i)=>p+':'+i;
const selRefresh=()=>{if(route_==='pack')drawPack();else if(route_==='library')libBody()};
ACT.lsel=el=>{const k=selKey(el.dataset.p,el.dataset.id);if(SEL.has(k))SEL.delete(k);else SEL.set(k,{pack_id:el.dataset.p,id:el.dataset.id});selRefresh()};
ACT.lselall=()=>{(route_==='pack'?(packById(PACK_ID)||{stickers:[]}).stickers.map(s=>({pack_id:PACK_ID,id:s.id})):LCL.map(s=>({pack_id:s.pack_id,id:s.id}))).forEach(x=>SEL.set(selKey(x.pack_id,x.id),x));selRefresh()};
ACT.lselnone=()=>{SEL.clear();selRefresh()};
/* the whole selection into one pack in ONE request (all or nothing); the selection is cleared only when it moved */
async function moveSelection(to){const items=[...SEL.values()];if(!items.length)return false;
  const r=await post('/api/stickers/move',{to,items});if(!r.ok){toast(r.j.error||'Could not move',1);return false}
  SEL.clear();await loadLib();drawCol2();selRefresh();const p=packById(to);
  toast(`Moved ${r.j.moved} sticker${r.j.moved===1?'':'s'} to ${p?p.name:'the pack'}${r.j.skipped?` (${r.j.skipped} already there)`:''}`);return true}
ACT.lselmove=()=>{if(SEL.size)pickPack(pid=>moveSelection(pid),`Move ${SEL.size} sticker${SEL.size===1?'':'s'} to`)};
ACT.lseldel=()=>{const items=[...SEL.values()];if(!items.length)return;
  confirmDlg(`Delete ${items.length} sticker${items.length===1?'':'s'}? This cannot be undone.`,async()=>{const r=await post('/api/stickers/delete',{items});if(!r.ok)return toast(r.j.error,1);
    SEL.clear();await loadLib();drawCol2();selRefresh();toast(`Deleted ${r.j.deleted} sticker${r.j.deleted===1?'':'s'}`)})};
/* Explorer-style selection on the pack screen and My Stickers: drag a box on empty space (a plain drag selects only what it touches, Shift adds,
   Ctrl un-selects what it touches again), Ctrl/Shift+click on a sticker toggles it, Ctrl+A selects all, Esc clears. A plain press on a sticker still
   opens it / drags it to reorder. */
const MQ={m:null,quiet:0};
const selScroller=el=>{for(let n=el;n&&n!==document.body;n=n.parentElement){const o=getComputedStyle(n).overflowY;if((o==='auto'||o==='scroll')&&n.scrollHeight>n.clientHeight)return n}return document.scrollingElement};
const cellKey=c=>{const b=c.querySelector('.selbox');return b?selKey(b.dataset.p,b.dataset.id):null};
const cellItem=c=>{const b=c.querySelector('.selbox');return b?{pack_id:b.dataset.p,id:b.dataset.id}:null};
function mqRect(m){const x0=m.x0-m.sc.scrollLeft,y0=m.y0-m.sc.scrollTop;return{l:Math.min(x0,m.cx),t:Math.min(y0,m.cy),r:Math.max(x0,m.cx),b:Math.max(y0,m.cy)}}
function mqHits(m,R){return[...m.grid.querySelectorAll('.cell')].filter(c=>{const r=c.getBoundingClientRect();return r.left<R.r&&r.right>R.l&&r.top<R.b&&r.bottom>R.t})}
function mqResult(m,hits){const out=new Map(m.mode==='replace'?[]:m.base);
  hits.forEach(c=>{const k=cellKey(c);if(!k)return;if(m.mode==='toggle'){if(out.has(k))out.delete(k);else out.set(k,cellItem(c))}else out.set(k,cellItem(c))});return out}
function mqUpdate(){const m=MQ.m;if(!m)return;const R=mqRect(m);
  if(!m.moved){if(Math.hypot(m.cx-(m.x0-m.sc.scrollLeft),m.cy-(m.y0-m.sc.scrollTop))<5)return;m.moved=true;document.body.classList.add('marq');m.grid.classList.add('mdim');m.box=document.createElement('div');m.box.className='marquee';document.body.appendChild(m.box)}
  Object.assign(m.box.style,{left:R.l+'px',top:R.t+'px',width:(R.r-R.l)+'px',height:(R.b-R.t)+'px'});
  const res=mqResult(m,mqHits(m,R));m.grid.querySelectorAll('.cell').forEach(c=>c.classList.toggle('msel',res.has(cellKey(c))))}
function mqScroll(){const m=MQ.m;if(!m)return;const r=m.sc===document.scrollingElement?{top:0,bottom:innerHeight}:m.sc.getBoundingClientRect();
  const d=m.cy<r.top+44?-(r.top+44-m.cy)/3:m.cy>r.bottom-44?(m.cy-(r.bottom-44))/3:0;if(d&&m.moved){m.sc.scrollTop+=d;mqUpdate()}m.raf=requestAnimationFrame(mqScroll)}
function mqEnd(commit){const m=MQ.m;if(!m)return;MQ.m=null;cancelAnimationFrame(m.raf);document.body.classList.remove('marq');m.grid.classList.remove('mdim');if(m.box)m.box.remove();
  if(m.moved&&commit){const res=mqResult(m,mqHits(m,mqRect(m)));SEL.clear();res.forEach((v,k)=>SEL.set(k,v));MQ.quiet=Date.now()+250;selRefresh()}
  else if(!m.moved&&commit&&m.mode==='replace'&&SEL.size){SEL.clear();selRefresh()}else if(m.moved)selRefresh()}
document.addEventListener('mousedown',e=>{if(e.button!==0||MQ.m)return;const scr=e.target.closest('#s-pack,#s-library');if(!scr)return;
  const grid=e.target.closest('.grid.selgrid');if(!grid)return;          /* only inside the sticker grid (its gaps, or Shift/Ctrl on a sticker): the rest of the screen keeps the mouse */
  if(e.target.closest('button,input,select,textarea,a,label,.selbox,.selbar,.hov,.cap,.phead,.tabs,.fab,.seeall'))return;
  const mod=e.shiftKey||e.ctrlKey||e.metaKey;if(e.target.closest('.cell')&&!mod)return;
  e.preventDefault();const sc=selScroller(grid);
  MQ.m={grid,sc,x0:e.clientX+sc.scrollLeft,y0:e.clientY+sc.scrollTop,cx:e.clientX,cy:e.clientY,mode:e.ctrlKey||e.metaKey?'toggle':e.shiftKey?'add':'replace',moved:false,base:new Map(SEL),box:null,raf:0};
  MQ.m.raf=requestAnimationFrame(mqScroll)});
document.addEventListener('mousemove',e=>{if(!MQ.m)return;MQ.m.cx=e.clientX;MQ.m.cy=e.clientY;mqUpdate()});
document.addEventListener('mouseup',()=>mqEnd(true));
window.addEventListener('blur',()=>mqEnd(false));
document.addEventListener('click',e=>{if(Date.now()<MQ.quiet){e.stopPropagation();e.preventDefault();return}
  if(!(e.ctrlKey||e.metaKey||e.shiftKey))return;const c=e.target.closest('.selgrid .cell');if(!c||e.target.closest('.hov,.selbox'))return;
  const k=cellKey(c);if(!k)return;e.stopPropagation();e.preventDefault();if(SEL.has(k))SEL.delete(k);else SEL.set(k,cellItem(c));selRefresh()},true);
document.addEventListener('keydown',e=>{if(!['pack','library'].includes(route_)||/input|textarea|select/i.test((document.activeElement||{}).tagName||'')||$('dlg').classList.contains('on')||$('modal').classList.contains('on'))return;
  if(e.key==='Escape'&&SEL.size){SEL.clear();selRefresh()}
  else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='a'&&document.querySelector('.grid.selgrid')){e.preventDefault();ACT.lselall()}});
function selBarHtml(total){return SEL.size?`<div class=selbar><b>${SEL.size} selected</b><button class=link data-act=lselall>Select all ${total}</button><button class=link data-act=lselnone>Clear</button><button class="btn sm" data-act=lselmove title="Move all the selected stickers into one pack (or a new one)">${ic('lib')} Move ${SEL.size} to…</button><button class="btn dng sm" data-act=lseldel>${ic('trash')} Delete ${SEL.size}</button></div>`:''}
RENDER.library=async()=>{await loadLib();drawCol2();
  $('s-library').innerHTML=`<div class=page><div class=ph><h1>Sticker Library</h1></div>
   <input type=search id=libq placeholder="Search stickers or packs…" value="${esc(LIBQ)}" style="margin-bottom:14px">
   <div class=tabs><button class="tab ${LIBTAB==='recent'?'on':''}" data-act=libtab data-t=recent>Recent</button><button class="tab ${LIBTAB==='mine'?'on':''}" data-act=libtab data-t=mine>My Stickers</button><button class="tab ${LIBTAB==='particles'?'on':''}" data-act=libtab data-t=particles>Particles</button><button class="tab ${LIBTAB==='trending'?'on':''}" data-act=libtab data-t=trending>Trending</button></div>
   <div id=libbody></div><div class=fab><button class="btn pri" data-act=nav data-to=create>${ic('plus')} Create</button></div></div>`;
  $('libq').oninput=e=>{LIBQ=e.target.value;libBody()};libBody()};
ACT.libtab=el=>{LIBTAB=el.dataset.t;RENDER.library()};
ACT.pkmerge=el=>{const a=packById(el.dataset.id),b=packById(el.dataset.into);if(!a||!b)return;
  confirmDlg(`Merge “${a.name}” into “${b.name}”? Its animated stickers replace their stills there (names, emoji and particles stay), the others move over, and “${a.name}” goes to the trash (you can restore it).`,async()=>{
    const r=await post(`/api/packs/${a.id}/merge`,{into:b.id});if(!r.ok)return toast(r.j.error||'Could not merge',1);
    await loadLib();toast(`${r.j.upgraded} upgraded to animated, ${r.j.moved} moved into “${b.name}”`);location.hash='#/pack/'+b.id;drawCol2()},'Merge')};
ACT.pkgrp=el=>{const g=el.dataset.g,open=el.getAttribute('aria-expanded')==='true';PKFOLD.set(g,!open);drawCol2()};
ACT.seeall=el=>{if(el.dataset.k==='st'){LIBTAB='mine'}else PACKS_ALL=!PACKS_ALL;RENDER.library()};
function libBody(){const q=LIBQ.trim().toLowerCase(),hit=s=>!q||(s.name+' '+s.emoji+' '+(s.pack||'')).toLowerCase().includes(q);
 const stTile=(s,i)=>`<div class=st data-act=lcopen data-i=${i} title="${esc(s.name)}">${media(s)}<span class=em>${esc(s.emoji)}</span></div>`;
  let h='';
  if(LIBTAB==='particles'){h=typeof spLibHtml==='function'?spLibHtml():'';if(typeof spLibSync==='function')spLibSync()}
  else if(LIBTAB==='trending'){h='<div id=tr-box></div>';if(typeof trLoad==='function')setTimeout(trLoad)}
  else if(!LIB.total&&!LIB.packs.length)h=`<div class="card" style="text-align:center;padding:40px"><h2>Nothing here yet</h2><p class=mut>Make a pack in the Studio, or create a sticker from a photo.</p><button class="btn pri" data-act=nav data-to=generate>${ic('gen')} Open Studio</button> <button class=btn data-act=nav data-to=create>${ic('create')} Create from photo</button></div>`;
 else if(LIBTAB==='recent'){const rs=LIB.recent.filter(hit),ps=packEntries(LIB.packs.filter(p=>!q||p.name.toLowerCase().includes(q)||p.stickers.some(hit))),shown=PACKS_ALL?ps:ps.slice(0,4);
  LCL=rs;
  h=`<div class=row style="justify-content:space-between;margin:6px 0"><h2>Recent</h2><button class=seeall data-act=seeall data-k=st>See all ${ic('chev')}</button></div><div class=strip>${rs.map(stTile).join('')||'<span class=mut>No matches.</span>'}</div>
  <div class=row style="justify-content:space-between;margin:14px 0 8px"><h2>My Packs</h2>${ps.length>4?`<button class=seeall data-act=seeall data-k=pk>${PACKS_ALL?'Show less':'See all'} ${ic('chev')}</button>`:''}</div>
  <div class=plist>${shown.map(e=>{const row=p=>`<div class=packrow data-act=openpack data-id=${p.id}><div class=cover>${coverMedia(p)}</div><div style="flex:1"><b>${esc(p.name)}</b><br><small>${p.stickers.length} stickers</small></div>${ic('chev')}</div>`;
   return e.pack?row(e.pack):`<div class=pkgroup><div class=pkgh>Group ${esc(e.group)} · ${e.packs.length} packs</div>${e.packs.map(row).join('')}</div>`}).join('')||'<div class=mut style="padding:14px">No packs.</div>'}</div>`}
 else{const all=LIB.packs.flatMap(p=>p.stickers.map(s=>({...s,pack_id:p.id,pack:p.name}))).filter(hit);LCL=all;
  h=`<div class=mut style="margin-bottom:8px">Tick the square, or drag a box over the stickers (Shift adds, Ctrl un-selects). Then delete them together.</div>${selBarHtml(all.length)}<div class="grid selgrid ${SEL.size?'selmode':''}">${all.map((s,i)=>`<div class="cell ${SEL.has(selKey(s.pack_id,s.id))?'sel':''}" data-act=lcopen data-i=${i}><span class="selbox ${SEL.has(selKey(s.pack_id,s.id))?'on':''}" data-act=lsel data-p=${s.pack_id} data-id=${s.id} title="Select"></span>${media(s)}<div class=cap>${esc(s.emoji)} ${esc(s.name)}</div></div>`).join('')||'<span class=mut>No matches.</span>'}</div>`}
 $('libbody').innerHTML=h}
ACT.openpack=el=>{location.hash='#/pack/'+el.dataset.id};
ACT.newpack=()=>askText('New pack name','My Pack',async n=>{const r=await post('/api/packs',{name:n});if(r.ok){await loadLib();location.hash='#/pack/'+r.j.id}else toast(r.j.error,1)},'Create');

/* ---------- Settings */
RENDER.settings=async()=>{const r=await api('/api/generations'),h=r.j.health||{},p=r.j.paths||{},tgc=await tgSettingsCard(),ai=(await api('/api/ai')).j||{},staff=(typeof AUV==='undefined')||AUV.staff((typeof ME==='undefined')?null:ME);
 $('s-settings').innerHTML=`<div class=page><div class=ph><h1>Settings & health</h1></div><div class=card style="margin-top:12px"><div class=kv>
  <span>watch folder (read-only)</span><span>${esc(p.input)}</span><span>output</span><span>${esc(p.out)}</span>${staff?`<span>ffmpeg</span><span>${esc(h.ffmpeg||'not found')}</span>
  <span>VP9 + alpha encoder</span><span>${h.vp9?'<b style="color:var(--pri-d)">ready</b>':'<b style="color:var(--bad)">missing</b>: final WEBM encodes will fail (live preview still works). Run <code>python -m mirsal doctor</code>'}</span>`:''}</div></div>
  <div class=card style="margin-top:16px"><h2>AI expansion</h2>${ai.configured?`<div class=kv><span>model</span><span><b>${esc(ai.model)}</b></span></div><div class=mut>Type a subject and the AI expands it into the full set, with a key name, tags and emoji for every sticker (Studio, Prompt).</div>`:`<div class=mut>Off. Add <code>OPENAI_API_KEY=…</code> to <code>mirsal/.env</code> (git-ignored) and restart the server: the AI then expands a subject and names every sticker. Until then the built-in sets are used.</div>`}</div>
  ${tgc}<p class=mut style="margin-top:16px">Photo cutout uses the engine's chroma key for green/blue screens and OpenCV GrabCut otherwise (offline). A learned matte model is planned for Phase 3C.</p></div>`};
