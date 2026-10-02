/* AI: the agentic chat. A conversation with memory whose backend is the Studio itself (the same engine, the same gates).
   Everything here is rendering: the agent (rules + a small model + a LangGraph graph) lives on the server, `/api/chat/*`.
   The pure helpers at the top are exported for node tests (tests/js/agent.test.js); the DOM half only runs in the browser. */
'use strict';
const AIU=(()=>{
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 /* **bold** and line breaks, after escaping: the model's text is never trusted as HTML */
 const md=s=>esc(s).replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>').replace(/\n/g,'<br>');
 const credits=n=>n==null||n===0?'free':`about ${+(+n).toFixed(1)} credit${+n===1?'':'s'}`;
 const stepSummary=steps=>{const s=(steps||[]),n=s.filter(x=>x.kind!=='final').length,last=s[s.length-1];return `${n} step${n===1?'':'s'}${last&&last.kind==='final'?' · '+last.label:''}`};
 /* index of the tile the track is showing, from its scroll position */
 const nearest=(scrollLeft,tileW,gap,n)=>Math.max(0,Math.min(n-1,Math.round(scrollLeft/(tileW+gap))));
 const atEnds=(left,width,full)=>({start:left<4,end:left+width>=full-4});
 const rel=(ts,now)=>{const d=Math.max(0,(now??Date.now()/1000)-ts);return d<60?'just now':d<3600?Math.floor(d/60)+' min':d<86400?Math.floor(d/3600)+' h':Math.floor(d/86400)+' d'};
 /* a message's signature: the page only rebuilds a message whose signature changed (so carousels keep their scroll and videos keep playing) */
 const sig=m=>JSON.stringify([m.status,m.text,(m.steps||[]).map(s=>[s.kind,s.label,s.status,s.detail&&s.detail.lines&&s.detail.lines.length]),m.chips,
  (m.cards||[]).map(c=>[c.type,c.generation,c.job,c.job_status,c.job_stage,c.animating,c.estimate,c.names&&c.names.length,
   ((c.data&&c.data.stickers)||c.stickers||[]).map(s=>[s.id,s.status,s.still,s.anim_status,!!s.png,!!s.webm])])]);
 /* does anything on this card still move? (then the page keeps polling) */
 const cardLive=c=>{if(c.type!=='generation')return false;
  if(c.job&&!c.generation)return !['FAILED','TIMEOUT'].includes(c.job_status);
  const st=(c.data&&c.data.stickers)||[];if(!st.length)return !!c.generation;
  return st.some(x=>x.status==='PENDING')||(!!c.animating&&st.some(x=>x.status==='READY'&&['PENDING','RUNNING'].includes(x.anim_status)))};
 const needPoll=s=>!!s&&(s.working||(s.messages||[]).some(m=>(m.cards||[]).some(cardLive)));
 const sid=h=>{const m=/^#?\/?agent\/(S\d+)/.exec(h||'');return m?m[1]:null};
 /* the last assistant message: only its plan card is the live one (a pending Create belongs to the newest plan) */
 const lastBot=ms=>{const a=ms||[];for(let i=a.length-1;i>=0;i--)if(a[i]&&a[i].role!=='user')return a[i];return null};
 return {esc,md,credits,stepSummary,nearest,atEnds,rel,sig,cardLive,needPoll,sid,lastBot};
})();
if(typeof module!=='undefined')module.exports=AIU;

if(typeof document!=='undefined'&&typeof ACT!=='undefined'){(()=>{
const A={sid:null,sess:null,sessions:[],agent:null,busy:false,sel:new Set(),open:new Set(),els:new Map(),poll:0,setOpen:false,drawer:false,since:0};
const SUGG=['a teddy bear waving','falcon stickers','my dog as a banana','Eid mubarak greetings'];
ICONS.ai='<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 3.5l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6zM5.5 16l.6 1.6 1.6.6-1.6.6L5.5 20l-.6-1.7-1.6-.6 1.6-.6z"/>';
ICONS.send='<path d="M12 19V5M6 11l6-6 6 6"/>';
SCREENS.push('agent');RAIL.unshift(['agent','ai','AI']);RAILOF.agent='agent';
const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};

/* ---------- the living background (ambient motion + the pointer) */
let bgOn=false;
function bgInit(root){if(bgOn)return;bgOn=true;
 const calm=matchMedia('(prefers-reduced-motion:reduce)').matches;let tx=0,ty=0,x=0,y=0,raf=0;
 const set=()=>{root.style.setProperty('--gx',x.toFixed(1)+'px');root.style.setProperty('--gy',y.toFixed(1)+'px');
  root.style.setProperty('--px',((x/Math.max(1,root.clientWidth))-.5).toFixed(3));root.style.setProperty('--py',((y/Math.max(1,root.clientHeight))-.5).toFixed(3))};
 const tick=()=>{x+=(tx-x)*.11;y+=(ty-y)*.11;set();raf=(Math.abs(tx-x)>.4||Math.abs(ty-y)>.4)?requestAnimationFrame(tick):0};
 const home=()=>{tx=x=root.clientWidth*.62;ty=y=root.clientHeight*.26;set()};home();
 if(calm)return;
 root.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;const r=root.getBoundingClientRect();tx=e.clientX-r.left;ty=e.clientY-r.top;if(!raf)raf=requestAnimationFrame(tick)},{passive:true});
 root.addEventListener('pointerleave',()=>{tx=root.clientWidth*.62;ty=root.clientHeight*.26;if(!raf)raf=requestAnimationFrame(tick)});
}

/* ---------- data */
async function loadSessions(){const r=await api('/api/chat/sessions');if(r.ok)A.sessions=r.j.sessions;return A.sessions}
async function loadAgent(){const r=await api('/api/chat/agent');if(r.ok)A.agent=r.j;pill()}
async function loadSession(id,quiet){const r=await api('/api/chat/sessions/'+id);
 if(!r.ok){if(r.status===404){A.sid=null;A.sess=null;store.set('mirsal.ai.sid','');paint();return null}if(!quiet)toast(r.j.error||'Could not load the chat',1);return null}
 A.sess=r.j;paint();return r.j}
async function ensureSession(){if(A.sid)return A.sid;const r=await post('/api/chat/sessions',{});if(!r.ok){toast(r.j.error||'Could not start a chat',1);return null}
 A.sid=r.j.id;A.sess=Object.assign({messages:[],subjects:[],interactions:[],working:false},r.j);store.set('mirsal.ai.sid',A.sid);history.replaceState(null,'','#/agent/'+A.sid);return A.sid}

/* ---------- the screen */
RENDER.agent=async arg=>{
 const root=$('s-agent');
 if(!root.dataset.ready){root.dataset.ready=1;root.innerHTML=`<div class=ai-bg><i class="ai-blob b1"></i><i class="ai-blob b2"></i><i class="ai-blob b3"></i><i class=ai-dots></i><i class=ai-glow></i></div>
  <div class=ai id=ai><div class=ai-main>
   <div class=ai-top><button class="ai-ibtn menu" data-act=agdrawer title="Chats" aria-label="Chats">${ic('hist')}</button><span class=ttl id=ai-ttl></span><span class=sp></span><button type=button class=ai-pill id=ai-pill data-act=agset title="AI engine"><i></i><span>…</span></button>
    <button class=ai-ibtn data-act=agnew title="New chat" aria-label="New chat">${ic('plus')}</button></div>
   <div class=ai-scroll id=ai-scroll><div class=ai-col id=ai-col></div></div>
   <div class=ai-dock><div class=ai-dock-in>
    <div class=ai-set id=ai-set></div>
    <div class=ai-sel id=ai-sel></div>
    <form class=ai-box id=ai-box autocomplete=off><button type=button class=ai-ibtn data-act=agset title="Settings" aria-label="Settings">${ic('settings')}</button>
     <textarea id=ai-in rows=1 placeholder="Make or change stickers" aria-label="Message"></textarea>
     <button class=ai-send id=ai-send type=submit aria-label="Send" disabled>${ic('send')}</button></form>
    <div class=ai-sugg id=ai-sugg></div>
   </div></div></div>
   <div class=ai-drawer id=ai-drawer><div class=scrim data-act=agdrawer></div><div class=sheet id=ai-sheet></div></div></div>`;
  bgInit(root);
  const ta=$('ai-in'),form=$('ai-box');
  const fit=()=>{ta.style.height='auto';ta.style.height=Math.min(132,ta.scrollHeight)+'px';$('ai-send').disabled=A.busy||!ta.value.trim()};
  ta.addEventListener('input',fit);
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();form.requestSubmit()}});
  form.addEventListener('submit',e=>{e.preventDefault();const t=ta.value;ta.value='';fit();agSend(t)});
  root.addEventListener('scroll',e=>{const t=e.target;if(t.classList&&t.classList.contains('car-track'))carSync(t)},true);
  carDrag(root);
 }
 await Promise.all([loadSessions(),loadAgent()]);
 const want=AIU.sid(location.hash)||(arg&&/^S\d+$/.test(arg)?arg:null)||A.sid||(location.hash.replace(/^#\/?/,'')==='agent'?null:null);
 if(want&&want!==A.sid||(want&&!A.sess)){A.sid=want;store.set('mirsal.ai.sid',want);A.els.clear();await loadSession(want,true)}
 else if(!want&&!A.sid){const last=store.get('mirsal.ai.sid');if(last&&A.sessions.some(s=>s.id===last)&&location.hash.replace(/^#\/?/,'')!=='agent/new'){A.sid=last;A.els.clear();await loadSession(last,true)}}
 paint();agList();setTimeout(()=>{const t=$('ai-in');if(t&&route_==='agent')t.focus({preventScroll:true})},60);
 if(AIU.needPoll(A.sess))startPoll();
};
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&A.sess&&AIU.needPoll(A.sess))startPoll()});

function pill(){const p=$('ai-pill');if(!p)return;const a=A.agent;if(!a){return}
 const on=a.agent.provider!=='none',nm=(a.agent.model||'').split('/').pop().replace(/:\d+$/,'');
 p.className='ai-pill'+(on?' up':'');p.querySelector('span').textContent=on?(a.preference==='auto'?'Auto · ':'')+(a.agent.provider==='local'?'Local · ':'Cloud · ')+nm:'Rules only';
 p.title=on?`The assistant runs on ${a.agent.model} (${a.agent.provider}), your choice: ${a.preference}. Vision checks: ${a.vision.model||'off'}. Click to change.`:'No language model is reachable: the assistant still works from rules. Click for details.'}

/* ---------- painting (a keyed diff: only a message whose signature changed is rebuilt) */
function paint(){
 const root=$('ai');if(!root)return;const s=A.sess,msgs=(s&&s.messages)||[],hero=!msgs.length;
 root.classList.toggle('is-hero',hero);$('ai-ttl').textContent=hero?'':(s.title||'');
 const col=$('ai-col'),sc=$('ai-scroll');
 if(hero){A.els.clear();if(!col.querySelector('.ai-hero'))col.innerHTML=`<div class="ai-hero ai-hero-in"><h1 class=ai-greet>What will you create today?</h1></div>`;
  $('ai-sugg').innerHTML=SUGG.map(t=>`<button class=ai-chip data-act=agchip data-text="${AIU.esc(t)}">${AIU.esc(t)}</button>`).join('')}
 else{
  $('ai-sugg').innerHTML='';
  let list=col.querySelector('.ai-msgs');if(!list){col.innerHTML='<div class=ai-msgs id=ai-msgs role=log aria-live=polite></div>';list=col.querySelector('.ai-msgs');A.els.clear()}
  const near=sc.scrollHeight-sc.scrollTop-sc.clientHeight<160;let changed=false;
  msgs.forEach((m,i)=>{const k=AIU.sig(m)+'|'+(A.open.has(m.id)?1:0)+[...A.open].filter(x=>x.startsWith(m.id+':')).join(',');let el=A.els.get(m.id);
   if(!el){el=document.createElement('div');A.els.set(m.id,el);list.appendChild(el);changed=true}
   if(el._k!==k){const keep=[...el.querySelectorAll('.car-track')].map(t=>t.scrollLeft);el._k=k;el.className='ai-m '+(m.role==='user'?'user':'bot'+(m.status==='working'?' working':''));
    el.innerHTML=m.role==='user'?`<div class=b>${AIU.esc(m.text)}</div>`:botHTML(m);
    el.querySelectorAll('.car-track').forEach((t,j)=>{if(keep[j])t.scrollLeft=keep[j];carSync(t)});changed=true}});
  for(const [id,el] of [...A.els])if(!msgs.some(m=>m.id===id)){el.remove();A.els.delete(id)}
  if(changed&&(near||msgs[msgs.length-1].role==='user'))requestAnimationFrame(()=>sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'}));
 }
 selChips();setSet();busyUi();
}
function busyUi(){const w=!!(A.sess&&A.sess.working)||A.busy;const b=$('ai-send');if(!b)return;b.classList.toggle('busy',w);b.disabled=w||!$('ai-in').value.trim()}

function botHTML(m){
 const work=m.status==='working',steps=m.steps||[];
 const tr=steps.length||work?traceHTML(m,work):'';
 const text=m.text?`<div class="ai-text${m.status==='error'?' ai-err':''}">${AIU.md(m.text)}</div>`:'';
 const cards=(m.cards||[]).map((c,i)=>cardHTML(c,m,i)).join('');
 const chips=(m.chips&&m.chips.length&&!work)?`<div class=ai-chips>${m.chips.map(c=>c.action?`<button class="ai-chip${c.action==='confirm'?' pri':''}" data-act=agaction data-type="${AIU.esc(c.action)}">${AIU.esc(c.label)}</button>`
   :`<button class=ai-chip data-act=agchip data-text="${AIU.esc(c.text||c.label)}">${AIU.esc(c.label)}</button>`).join('')}</div>`:'';
 return `<div class=ai-av>${ic('ai')}</div><div class=ai-body>${tr}${text}${cards}${chips}</div>`}

function traceHTML(m,work){
 const steps=m.steps||[],open=work||A.open.has(m.id);
 if(!open)return `<button class="tr-sum" data-act=agtrace data-m="${m.id}">${ic('chev')}<span>${AIU.esc(AIU.stepSummary(steps))}</span></button>`;
 const rows=steps.map(s=>({...s}));const hasFinal=rows.length&&rows[rows.length-1].kind==='final';
 if(work&&!hasFinal)rows.push({kind:'think',label:'Thinking'});
 const head=!work?`<button class="tr-sum open" data-act=agtrace data-m="${m.id}">${ic('chev')}<span>${AIU.esc(AIU.stepSummary(steps))}</span></button>`:'';
 return head+`<div class=tr>`+rows.map((s,i)=>{const k=`${m.id}:${i}`,d=s.detail&&s.detail.lines&&s.detail.lines.length,isOpen=A.open.has(k);
  const cls=['tr-row',s.kind==='think'?'tr-think k-final':'k-'+s.kind,i===0?'is-first':'',i===rows.length-1?'is-last':'',s.status==='error'?'k-error':'',isOpen?'tr-open':''].filter(Boolean).join(' ');
  const t=d?`<button class=tr-t data-act=agstep data-k="${k}"><span>${AIU.esc(s.label)}</span>${ic('chev')}</button>`
   :`<span class=tr-t><span>${AIU.esc(s.label)}${s.kind==='think'?'<span class=dots></span>':''}</span></span>`;
  return `<div class="${cls}"><i class=tr-mk></i>${t}${d&&isOpen?`<div class=tr-d>${s.detail.lines.map(l=>`<div>${AIU.esc(l)}</div>`).join('')}</div>`:''}</div>`}).join('')+`</div>`}

function cardHTML(c,m,i){
 if(c.type==='plan'){const last=AIU.lastBot((A.sess&&A.sess.messages)||[]),done=!(A.sess&&A.sess.pending)||!last||m.id!==last.id;
  return `<div class="ai-card plan${done?' is-done':''}"><div class=ai-ch><b>${AIU.esc(c.subject)}</b><small>${c.count} stickers · ${AIU.esc(c.grid)} · ${AIU.esc(c.style)}</small></div>
   <div class=plan-tags>${(c.names||[]).map(n=>`<span>${AIU.esc(n)}</span>`).join('')}</div>
   <div class=plan-foot><div class=price>${c.free?'Free: no provider call.':`Costs <b>${AIU.credits(c.estimate)}</b>${c.balance!=null?` · balance ${+(+c.balance).toFixed(0)}`:''}`}</div>
    </div></div>`}   /* the go-ahead lives in the two chips under the message (Create it / Not yet), the same place as "Allow AI vision / Not now": one pair of buttons, never two */
 if(c.type==='generation'){
  const st=(c.data&&c.data.stickers)||[],ready=st.filter(x=>x.status==='READY').length,gid=c.generation;
  let note='';
  if(!gid){note=c.job_status==='FAILED'||c.job_status==='TIMEOUT'?`<span class=ai-err>The model could not make this sheet${c.job_error?': '+AIU.esc(c.job_error):''}. Nothing more was spent.</span>`:`Drawing the sheet${c.job_stage?' · '+AIU.esc(c.job_stage):''}…`}
  else if(!st.length)note='Cutting the stickers…';else if(st.some(x=>x.status==='PENDING'))note='Cutting the stickers…';
  else if(c.animating&&st.some(x=>['PENDING','RUNNING'].includes(x.anim_status)))note='Animating…';
  const meta=gid?`${gid}${c.data&&c.data.parent?' · from '+c.data.parent:''} · ${ready} ready`:'';
  return `<div class="ai-card gen"><div class=ai-ch><b>${AIU.esc(c.subject||'Stickers')}</b><small>${meta}</small><span class=sp></span>${gid?`<button class=ai-link data-act=agstudio data-g="${gid}">Open in Studio</button>`:''}</div>
   ${carHTML(st.length?st:null,gid)}${note?`<div class=car-note>${note}</div>`:''}</div>`}
 if(c.type==='stickers'){return `<div class="ai-card"><div class=ai-ch><b>${c.stickers.length===1?'Sticker':'Stickers'}</b><small>${c.stickers.length} found</small></div>${carHTML(c.stickers.map(x=>({...x,status:'READY',name:x.key})),null)}</div>`}
 return ''}

function carHTML(st,gid){
 const tiles=st?st:Array.from({length:6},(_,i)=>({id:'w'+i,index:i+1,status:'PENDING',wait:true}));
 const n=tiles.length;
 return `<div class=car><div class=car-vp><button class="car-nav prev" data-act=agcar data-dir=prev aria-label="Previous" disabled>${ic('prev')}</button>
  <div class=car-track tabindex=0 aria-label="Stickers, swipe or use the arrow keys">${tiles.map(tileHTML).join('')}</div>
  <button class="car-nav next" data-act=agcar data-dir=next aria-label="Next">${ic('next')}</button></div>
  <div class=car-dots>${tiles.map((_,i)=>`<i class="${i===0?'on':''}"></i>`).join('')}</div></div>`}

function tileHTML(s){
 const wait=s.wait||(s.status==='PENDING'),bad=s.status==='FAILED'||s.still==='REJECTED',id=s.id||'';
 const media=s.webm&&(s.anim_status==='READY'||!s.anim_status)&&s.status==='READY'?`<video src="${AIU.esc(s.webm)}" autoplay loop muted playsinline preload=metadata></video>`
  :s.png?`<img src="${AIU.esc(s.png)}" alt="${AIU.esc(s.key||'')}" draggable=false loading=lazy>`:'';
 const emo=Array.isArray(s.emoji)?s.emoji.join(''):(s.emoji||'');
 const badge=s.still==='APPROVED'?`<span class=ag-bd title="Approved">${ic('check')}</span>`:s.still==='REJECTED'?`<span class="ag-bd is-no" title="Rejected">${ic('x')}</span>`:'';
 const cap=s.wait?'':`<b>${s.index!=null?s.index:''}</b><span>${AIU.esc(String(s.key||s.name||'').replace(/_/g,' '))} ${AIU.esc(emo)}</span>`;
 return `<figure class="ag-tile${A.sel.has(id)?' is-sel':''}${bad?' is-bad':''}${wait?' is-wait':''}" data-act=agtile data-id="${AIU.esc(id)}"><div class=ag-ph>${media}</div>${badge}<figcaption class=ag-nm>${cap}</figcaption></figure>`}

/* ---------- carousel: arrows, dots, drag with a mouse, native swipe on touch */
function carSync(t){const car=t.closest('.car');if(!car)return;const tiles=t.querySelectorAll('.ag-tile');if(!tiles.length)return;
 const w=tiles[0].offsetWidth,i=AIU.nearest(t.scrollLeft,w,12,tiles.length),e=AIU.atEnds(t.scrollLeft,t.clientWidth,t.scrollWidth);
 car.querySelectorAll('.car-dots i').forEach((d,k)=>d.classList.toggle('on',k===i));
 const p=car.querySelector('.car-nav.prev'),n=car.querySelector('.car-nav.next');if(p)p.disabled=e.start;if(n)n.disabled=e.end}
function carDrag(root){let d=null;
 root.addEventListener('pointerdown',e=>{const t=e.target.closest&&e.target.closest('.car-track');if(!t||e.pointerType!=='mouse'||e.button!==0)return;d={t,x:e.clientX,l:t.scrollLeft,moved:false}});
 window.addEventListener('pointermove',e=>{if(!d)return;const dx=e.clientX-d.x;if(!d.moved&&Math.abs(dx)>5){d.moved=true;d.t.classList.add('is-drag')}if(d.moved)d.t.scrollLeft=d.l-dx});
 window.addEventListener('pointerup',()=>{if(!d)return;const t=d.t,moved=d.moved;d=null;if(moved){t.classList.remove('is-drag');const w=t.querySelector('.ag-tile').offsetWidth+12;t.scrollTo({left:Math.round(t.scrollLeft/w)*w,behavior:'smooth'});
   t.dataset.dragged=1;setTimeout(()=>delete t.dataset.dragged,60)}});
 root.addEventListener('keydown',e=>{const t=e.target.closest&&e.target.closest('.car-track');if(!t)return;if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();stepCar(t,e.key==='ArrowRight'?1:-1)}})}
function stepCar(t,dir){const tile=t.querySelector('.ag-tile');if(!tile)return;const w=tile.offsetWidth+12,per=Math.max(1,Math.floor(t.clientWidth/w));t.scrollBy({left:dir*w*per,behavior:'smooth'})}

/* ---------- actions */
ACT.agcar=el=>{const t=el.closest('.car').querySelector('.car-track');stepCar(t,el.dataset.dir==='next'?1:-1)};
ACT.agtile=el=>{if(el.closest('.car-track')&&el.closest('.car-track').dataset.dragged)return;const id=el.dataset.id;if(!id||id[0]==='w')return;
 if(A.sel.has(id))A.sel.delete(id);else A.sel.add(id);
 document.querySelectorAll(`.ag-tile[data-id="${CSS.escape(id)}"]`).forEach(t=>t.classList.toggle('is-sel',A.sel.has(id)));selChips()};
ACT.agsel=()=>{A.sel.clear();document.querySelectorAll('.ag-tile.is-sel').forEach(t=>t.classList.remove('is-sel'));selChips()};
function selChips(){const el=$('ai-sel');if(!el)return;const n=A.sel.size;
 el.innerHTML=n?`<span class=ai-selchip>${n} selected: say what to change<button data-act=agsel aria-label="Clear selection">${ic('x')}</button></span>`:'';
 const ta=$('ai-in');if(ta)ta.placeholder=n?'e.g. make these more energetic':'Make or change stickers'}
ACT.agchip=el=>agSend(el.dataset.text);
ACT.agaction=el=>agSend('',{type:el.dataset.type});
ACT.agtrace=el=>{const k=el.dataset.m;if(A.open.has(k))A.open.delete(k);else A.open.add(k);paint()};
ACT.agstep=el=>{const k=el.dataset.k;if(A.open.has(k))A.open.delete(k);else A.open.add(k);paint()};
ACT.agstudio=el=>{const n=+String(el.dataset.g).replace(/\D/g,'');if(typeof SES!=='undefined'){SES={prompt:'',gens:[n],off:[],pack:''};if(typeof saveSes==='function')saveSes()}location.hash='#/studio'};
ACT.agnew=()=>{A.sid=null;A.sess=null;A.sel.clear();A.els.clear();A.drawer=false;store.set('mirsal.ai.sid','');const c=$('ai-col');if(c)c.innerHTML='';history.replaceState(null,'','#/agent');paint();agList();const t=$('ai-in');if(t)t.focus()};
ACT.agopen=el=>{A.drawer=false;location.hash='#/agent/'+el.dataset.id};
ACT.agdel=el=>{const id=el.dataset.id;confirmDlg('Delete this chat? The stickers it made stay in the Studio.',async()=>{await post(`/api/chat/sessions/${id}/delete`);if(A.sid===id)ACT.agnew();await loadSessions();agList()},'Delete')};
ACT.agdrawer=()=>{A.drawer=!A.drawer;$('ai-drawer').classList.toggle('on',A.drawer);if(A.drawer)agList()};
ACT.agset=()=>{A.setOpen=!A.setOpen;setSet()};
ACT.agsetgrid=async el=>saveSet({grid:el.dataset.v});
ACT.agsetask=async()=>saveSet({ask_before_spending:!(A.sess?A.sess.settings.ask_before_spending:true)});
ACT.agbe=async el=>{const r=await post('/api/ai/backend',{backend:el.dataset.v});if(r.ok){await loadAgent();setSet()}else toast(r.j.error||'Could not change the AI engine',1)};
async function saveSet(p){const sid=await ensureSession();if(!sid)return;const r=await post(`/api/chat/sessions/${sid}/settings`,p);if(r.ok){A.sess.settings=r.j.settings;setSet()}else toast(r.j.error,1)}
/* the AI engine row: Auto keeps a working backend and only a failed call switches it; Local / Cloud are used as chosen. A backend that is not available says why. */
function beRow(){const a=A.agent||{},av=a.availability||{},pref=a.preference||'auto';
 const b=(v,label)=>{const ok=v==='auto'||(av[v]&&av[v].ok);const why=v==='auto'?'Use the local model when LM Studio answers, otherwise the cloud; keep what works':(av[v]&&av[v].why)||(av[v]&&av[v].model)||'';
  return `<button data-act=agbe data-v=${v} class="${pref===v?'on':''}${ok?'':' is-off'}" title="${AIU.esc(ok&&v!=='auto'?av[v].model:why)}">${label}</button>`};
 const now=a.agent&&a.agent.provider!=='none'?`now: ${a.agent.provider==='local'?'local':'cloud'} · ${AIU.esc((a.agent.model||'').replace(/:\d+$/,''))}`:'now: rules only';
 const warn=pref!=='auto'&&av[pref]&&!av[pref].ok?` · <span class=ai-err>${AIU.esc(av[pref].why||'not available')}</span>`:'';
 return `<div class=r><div><b>AI engine</b><small>${now}${warn}</small></div><div class=ai-seg>${b('auto','Auto')}${b('local','Local')}${b('cloud','Cloud')}</div></div>`}
function setSet(){const el=$('ai-set');if(!el)return;el.classList.toggle('on',A.setOpen);if(!A.setOpen)return;
 const st=A.sess?A.sess.settings:{grid:'3x3',ask_before_spending:true};
 el.innerHTML=`<div class=r><div><b>Grid</b><small>How many stickers in one sheet</small></div><div class=ai-seg><button data-act=agsetgrid data-v=3x3 class="${st.grid==='3x3'?'on':''}">3×3</button><button data-act=agsetgrid data-v=2x2 class="${st.grid==='2x2'?'on':''}">2×2</button></div></div>
  ${beRow()}
  <div class=r><div><b>Ask before spending</b><small>Show the price and wait for your go-ahead</small></div><button type=button class="ai-sw${st.ask_before_spending?' on':''}" data-act=agsetask role=switch aria-checked="${!!st.ask_before_spending}" aria-label="Ask before spending"></button></div>`}
document.addEventListener('click',e=>{if(A.setOpen&&!e.target.closest('.ai-set')&&!e.target.closest('[data-act=agset]')){A.setOpen=false;setSet()}});

/* ---------- sending and polling */
async function agSend(text,action){
 text=(text||'').trim();if(!text&&!action)return;if(A.busy||(A.sess&&A.sess.working))return toast('Still working on your last message.');
 const sid=await ensureSession();if(!sid)return;A.busy=true;busyUi();
 const r=await post(`/api/chat/sessions/${sid}/messages`,{text,action,selected:[...A.sel]});
 if(!r.ok){A.busy=false;busyUi();return toast(r.status===409?'Still working on your last message.':(r.j.error||'Could not send'),1)}
 A.sel.clear();selChips();A.setOpen=false;setSet();
 try{await loadSession(sid,true)}catch(e){}            // a paint error must not stop this turn from being polled
 startPoll();
}
function startPoll(){clearTimeout(A.poll);A.since=A.since||Date.now();
 const tick=async()=>{if(route_!=='agent'||document.hidden||!A.sid){A.busy=false;return}
  let s=null;
  try{s=await loadSession(A.sid,true)}catch(e){s=null}                  // one failed frame must never stop the polling (a paint error used to freeze the chat at "Thinking")
  if(!s){if(A.sid){A.busy=false;busyUi();A.poll=setTimeout(tick,2500)}return}   // a failed read: try again (a 404 has already cleared A.sid)
  if(AIU.needPoll(s)){A.busy=!!s.working;A.poll=setTimeout(tick,s.working?700:(Date.now()-A.since>120000?4000:1600))}
  else{A.busy=false;A.since=0;busyUi();await loadSessions();agList()}};
 A.poll=setTimeout(tick,500)}

/* ---------- the second column: chats (and the phone drawer) */
function listHTML(){const rows=A.sessions.map(s=>`<div class="sess-row${s.id===A.sid?' on':''}" data-act=agopen data-id="${s.id}"><div class=t><b>${AIU.esc(s.title||'New chat')}</b><small>${s.subjects.length?AIU.esc(s.subjects.slice(0,3).join(', '))+' · ':''}${AIU.rel(s.updated)}</small></div><button class=x data-act=agdel data-id="${s.id}" aria-label="Delete chat">${ic('trash')}</button></div>`).join('');
 return `<button class=sess-new data-act=agnew>${ic('plus')}New chat</button>${rows||'<div class=mut style="padding:14px 18px">Your chats will be here.</div>'}`}
window.agList=function agList(){if(route_!=='agent')return;const c2=$('col2');if(c2)c2.innerHTML=`<div class=c2h><h1>Chats</h1></div><div class=c2l>${listHTML()}</div>`;const sh=$('ai-sheet');if(sh)sh.innerHTML=`<div class=c2h><h1>Chats</h1></div>`+listHTML()};
const agList=window.agList;
})()}
