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
  (m.cards||[]).map(c=>[c.type,c.generation,c.job,c.job_status,c.job_stage,c.job_info,c.animating,c.estimate,c.names&&c.names.length,
   ((c.data&&c.data.stickers)||c.stickers||[]).map(s=>[s.id,s.status,s.still,s.anim_status,!!s.png,!!s.webm]),c.data&&c.data.problem&&c.data.problem.check,c.data&&c.data.allow,c.run&&[c.run.step,c.run.status,c.run.updated]])]);
 /* does anything on this card still move? (then the page keeps polling) */
 const cardLive=c=>{if(c.type!=='generation')return false;
  if(c.job&&!c.generation)return !['FAILED','TIMEOUT'].includes(c.job_status);
  const st=(c.data&&c.data.stickers)||[];if(!st.length)return !!c.generation;
  return st.some(x=>x.status==='PENDING')||(!!c.animating&&st.some(x=>x.status==='READY'&&['PENDING','RUNNING'].includes(x.anim_status)))};
 const needPoll=s=>!!s&&(s.working||(s.creator_run&&s.creator_run.status==='running')||(s.messages||[]).some(m=>(m.cards||[]).some(cardLive)));
 const sid=h=>{const m=/^#?\/?agent\/(S\d+)/.exec(h||'');return m?m[1]:null};
 /* the last assistant message: only its plan card is the live one (a pending Create belongs to the newest plan) */
 const lastBot=ms=>{const a=ms||[];for(let i=a.length-1;i>=0;i--)if(a[i]&&a[i].role!=='user')return a[i];return null};
 /* what the engine pill says (GET /api/chat/agent). A model that answers: "Local · qwen3.5-4b". Rules only, and WHY: a local engine that is set up but cannot answer reads "Rules only (local model not loaded)"
    and the tooltip carries the server's own reason (`agent_status.reason`), never just "Rules only". */
 const engine=a=>{
  if(!a||!a.agent)return {on:false,rules:false,label:'…',title:''};
  const ag=a.agent,st=a.agent_status||{},loc=(a.availability||{}).local||{},pref=a.preference||'auto',nm=String(ag.model||'').split('/').pop().replace(/:\d+$/,'');
  if(ag.provider!=='none'&&!st.fallback)return {on:true,rules:false,label:(pref==='auto'?'Auto · ':'')+(ag.provider==='local'?'Local · ':'Cloud · ')+nm,
   title:`The assistant runs on ${ag.model} (${ag.provider}), your choice: ${pref}. Vision checks: ${(a.vision&&a.vision.model)||'off'}. Click to change.`};
  const why=String(st.reason||loc.why||'No language model is reachable').replace(/\.+$/,'');
  return {on:false,rules:true,label:pref!=='cloud'&&loc.ok===false?'Rules only (local model not loaded)':'Rules only',title:`${why}. The assistant still works from its rules. Click for details.`}};
 /* the one line under the model dropdown (GET /api/llm/models): the model in use, or why the local model cannot answer, in the server's last sentence ("Load qwen3.5-4b in LM Studio ...") */
 const modelNote=m=>{if(!m)return '';if(m.ok)return `now: ${m.current}`;const why=String(m.why||'');return 'Local model not loaded: '+(why.split(/\.\s+/).pop()||why)};
 return {esc,md,credits,stepSummary,nearest,atEnds,rel,sig,cardLive,needPoll,sid,lastBot,engine,modelNote};
})();
if(typeof module!=='undefined')module.exports=AIU;

if(typeof document!=='undefined'&&typeof ACT!=='undefined'){(()=>{
const A={sid:null,sess:null,sessions:[],agent:null,llm:null,llmBusy:false,busy:false,sel:new Set(),open:new Set(),els:new Map(),shown:undefined,poll:0,setOpen:false,since:0,pre:''};
const SUGG=['a teddy bear waving','falcon stickers','my dog as a banana','Eid mubarak greetings'];
ICONS.send='<path d="M12 19V5M6 11l6-6 6 6"/>';

const store={get(k){try{return localStorage.getItem(k)}catch(e){return null}},set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
A.pre=store.get('mirsal.ai.style')||'';        // the style picked last: what a chat that has no session yet will start with

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
async function loadAgent(){const r=await api('/api/chat/agent');if(r.ok)A.agent=r.j;pill();drawBar()}
/* the local server's models for the engine row's dropdown (no count limit); the first call may wait while the server loads its model */
async function loadModels(){const r=await api('/api/llm/models');A.llm=r.ok?r.j:{models:[],current:'',ok:false,why:'Could not read the model list'};engRedraw()}
/* the engine control (Auto / Local / Cloud + the local model) is ONE implementation for two screens: the AI screen's gear panel and the Studio's AI enhancer (composer.js, cpDrawEngine).
   Both draw it with beRow() and both end up in engRedraw(); the Studio hands in its own source (GET /api/ai, shaped like GET /api/chat/agent) through AIENG.rows. */
function engRedraw(){if(A.setOpen)setSet();if(typeof cpDrawEngine==='function')cpDrawEngine()}
const engSync=()=>typeof aiRefresh==='function'?aiRefresh():null;        // the Studio's copy of the same facts (generate.js)
let ENGSRC=null;
async function loadSession(id,quiet){const r=await api('/api/chat/sessions/'+id);
 if(!r.ok){if(r.status===404){A.sid=null;A.sess=null;store.set('mirsal.ai.sid','');paint();return null}if(!quiet)toast(r.j.error||'Could not load the chat',1);return null}
 A.sess=r.j;paint();return r.j}
async function ensureSession(){if(A.sid)return A.sid;const r=await post('/api/chat/sessions',{});if(!r.ok){toast(r.j.error||'Could not start a chat',1);return null}
 A.sid=r.j.id;A.sess=Object.assign({messages:[],subjects:[],interactions:[],working:false},r.j);store.set('mirsal.ai.sid',A.sid);history.replaceState(null,'','#/agent/'+A.sid);await applyPre();return A.sid}
/* a chat starts with the style picked last (picking one before the first message must not create an empty chat) */
async function applyPre(){const def=(A.agent&&A.agent.default_style)||'flat_vector';if(!A.pre||A.pre===def||!A.sid)return;
 const r=await post(`/api/chat/sessions/${A.sid}/settings`,{style_id:A.pre});if(r.ok&&A.sess)A.sess.settings=r.j.settings}

/* ---------- the screen */
RENDER.agent=async arg=>{
 const root=$('s-agent');
 if(!root.dataset.ready){root.dataset.ready=1;root.innerHTML=`<div class=ai-bg><i class="ai-blob b1"></i><i class="ai-blob b2"></i><i class="ai-blob b3"></i><i class=ai-dots></i><i class=ai-glow></i></div>
  <div class=ai id=ai><div class=ai-main>
   <div class=ai-top><span class=ttl id=ai-ttl></span><span class=sp></span><button type=button class=ai-pill id=ai-pill data-act=agset title="AI engine"><i></i><span>…</span></button>
    <button class=ai-ibtn data-act=agnew title="New chat" aria-label="New chat">${ic('plus')}</button></div>
   <div class=ai-scroll id=ai-scroll><div class=ai-col id=ai-col></div></div>
   <div class=ai-dock><div class=ai-dock-in>
    <div class=ai-set id=ai-set></div>
    <div class=ai-sel id=ai-sel></div>
    <form class=ai-box id=ai-box autocomplete=off><button type=button class=ai-ibtn data-act=agset title="Settings" aria-label="Settings">${ic('settings')}</button>
     <textarea id=ai-in rows=1 placeholder="Make or change stickers" aria-label="Message"></textarea>
     <button class=ai-send id=ai-send type=submit aria-label="Send" disabled>${ic('send')}</button></form>
    <div class=ag-bar id=ag-bar></div>
    <div class=ag-styles id=ag-styles role=radiogroup aria-label="Style"></div>
    <div class=ai-sugg id=ai-sugg></div>
   </div></div></div></div>`;
  bgInit(root);
  const ta=$('ai-in'),form=$('ai-box');
  const fit=()=>{ta.style.height='auto';ta.style.height=Math.min(132,ta.scrollHeight)+'px';$('ai-send').disabled=A.busy||!ta.value.trim()};
  ta.addEventListener('input',fit);
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();form.requestSubmit()}});
  form.addEventListener('submit',e=>{e.preventDefault();const t=ta.value;ta.value='';fit();agSend(t)});
  root.addEventListener('scroll',e=>{const t=e.target;if(t.classList&&t.classList.contains('car-track'))carSync(t)},true);
  carDrag(root);
 }
 loadAgent().catch(()=>{});                       /* not awaited: the answer includes the local model's readiness probe, which can take a moment while the server loads it; the pill and the tiles fill in when it arrives */
 await loadSessions();
 const want=AIU.sid(location.hash)||(arg&&/^S\d+$/.test(arg)?arg:null)||A.sid||(location.hash.replace(/^#\/?/,'')==='agent'?null:null);
 if(want&&want!==A.sid||(want&&!A.sess)){A.sid=want;store.set('mirsal.ai.sid',want);A.els.clear();await loadSession(want,true)}
 else if(!want&&!A.sid){const last=store.get('mirsal.ai.sid');if(last&&A.sessions.some(s=>s.id===last)&&location.hash.replace(/^#\/?/,'')!=='agent/new'){A.sid=last;A.els.clear();await loadSession(last,true)}}
 paint();agList();setTimeout(()=>{const t=$('ai-in');if(t&&route_==='agent')t.focus({preventScroll:true})},60);
 if(AIU.needPoll(A.sess))startPoll();
};
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&A.sess&&AIU.needPoll(A.sess))startPoll()});

function pill(){const p=$('ai-pill');if(!p||!A.agent)return;const e=AIU.engine(A.agent);
 p.className='ai-pill'+(e.on?' up':'');p.querySelector('span').textContent=e.label;p.title=e.title}

/* keep the bottom of a chat in view for a moment after it was opened: pictures and cards load and grow, and the page must not drift up and down while they do (stops at once when the person scrolls) */
function pinBottom(sc,list){if(typeof ResizeObserver==='undefined')return;let stop=false;const off=()=>{stop=true;ro.disconnect()};
 const ro=new ResizeObserver(()=>{if(!stop)sc.scrollTop=sc.scrollHeight});ro.observe(list);
 ['wheel','touchstart','keydown','mousedown'].forEach(e=>sc.addEventListener(e,off,{once:true,passive:true}));setTimeout(off,1200)}
/* ---------- painting (a keyed diff: only a message whose signature changed is rebuilt) */
function paint(){
 const root=$('ai');if(!root)return;drawBar();const s=A.sess,msgs=(s&&s.messages)||[],hero=!msgs.length;
 root.classList.toggle('is-hero',hero);$('ai-ttl').textContent=hero?'':(s.title||'');
 const col=$('ai-col'),sc=$('ai-scroll');
 if(hero){A.shown=A.sid;A.els.clear();if(!col.querySelector('.ai-hero'))col.innerHTML=`<div class="ai-hero ai-hero-in"><h1 class=ai-greet>What will you create today?</h1></div>`;
  $('ai-sugg').innerHTML=SUGG.map(t=>`<button class=ai-chip data-act=agchip data-text="${AIU.esc(t)}">${AIU.esc(t)}</button>`).join('')}
 else{
  $('ai-sugg').innerHTML='';
  let list=col.querySelector('.ai-msgs');if(!list){col.innerHTML='<div class=ai-msgs id=ai-msgs role=log aria-live=polite></div>';list=col.querySelector('.ai-msgs');A.els.clear()}
  const switched=A.shown!==A.sid;                          // a different chat than the one on screen: start clean, land at its bottom at once, no swipe
  if(switched){list.innerHTML='';A.els.clear();list.classList.remove('is-switched');void list.offsetWidth;list.classList.add('is-switched')}
  const near=switched||sc.scrollHeight-sc.scrollTop-sc.clientHeight<160;let changed=false;
  msgs.forEach((m,i)=>{const k=AIU.sig(m)+'|'+(A.open.has(m.id)?1:0)+[...A.open].filter(x=>x.startsWith(m.id+':')).join(',')+((m.chips||[]).some(c=>c.setting)?String(A.sess&&A.sess.settings&&A.sess.settings.allow_vlm):'');let el=A.els.get(m.id);
   if(!el){el=document.createElement('div');A.els.set(m.id,el);list.appendChild(el);changed=true}
   if(el._k!==k){const keep=[...el.querySelectorAll('.car-track')].map(t=>t.scrollLeft);el._k=k;el.className='ai-m '+(m.role==='user'?'user':'bot'+(m.status==='working'?' working':''));
    el.innerHTML=m.role==='user'?`<div class=b>${AIU.esc(m.text)}</div>`:botHTML(m);
    el.querySelectorAll('.car-track').forEach((t,j)=>{if(keep[j])t.scrollLeft=keep[j];carSync(t)});changed=true}});
  for(const [id,el] of [...A.els])if(!msgs.some(m=>m.id===id)){el.remove();A.els.delete(id)}
  if(switched){A.shown=A.sid;sc.scrollTop=sc.scrollHeight;pinBottom(sc,list)}
  else if(changed&&(near||msgs[msgs.length-1].role==='user'))requestAnimationFrame(()=>sc.scrollTo({top:sc.scrollHeight,behavior:'smooth'}));
 }
  selChips();setSet();busyUi();
}
function busyUi(){const w=!!(A.sess&&A.sess.working)||A.busy;const b=$('ai-send');if(!b)return;b.classList.toggle('busy',w);b.disabled=w||!$('ai-in').value.trim()}

function botHTML(m){
 const work=m.status==='working',steps=m.steps||[];
 const tr=steps.length||work?traceHTML(m,work):'';
 const text=m.text?`<div class="ai-text${m.status==='error'?' ai-err':''}">${AIU.md(m.text)}</div>`:'';
 const cards=(m.cards||[]).map((c,i)=>cardHTML(c,m,i)).join('');
 const chips=(m.chips&&m.chips.length&&!work)?`<div class=ai-chips>${m.chips.map(chipHTML).join('')}</div>`:'';
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

/* a chip under a message: a go-ahead / action button, a suggestion, or (c.setting) a ONE-TIME switch that writes a setting through the settings route and makes no chat turn (UI/UX spec P9, P10).
   The switch reads the live setting: undecided it glows (subtle, rotating, at rest under reduced motion) on the right; decided it says "AI vision on" / "AI vision off" and flips on a press. */
function chipHTML(c){
 if(c.setting){const k=Object.keys(c.setting)[0],cur=A.sess&&A.sess.settings?A.sess.settings[k]:null,on=cur===true,off=cur===false,next={[k]:!on};
  return `<span class="ai-vis${cur==null&&c.glow?' glow':''}${on?' is-on':''}"><button class="ai-chip" data-act=agsetting data-set="${AIU.esc(JSON.stringify(next))}" aria-pressed=${on} title="${on?'Click to switch it off':'Click to switch it on'}">${AIU.esc(on?(c.on||c.label):off?(c.off||c.label):c.label)}</button></span>`}
 if(c.editor)return `<button class="ai-chip pri" data-act=agedit data-g="${AIU.esc(c.editor.generation)}" data-i=${+c.editor.index}>${AIU.esc(c.label)}</button>`;
 return c.action?`<button class="ai-chip${c.action==='confirm'||c.action==='names_apply'?' pri':''}" data-act=agaction data-type="${AIU.esc(c.action)}"${c.generation?` data-g="${AIU.esc(c.generation)}"`:''}${c.indexes?` data-i="${AIU.esc(JSON.stringify(c.indexes))}"`:''}>${AIU.esc(c.label)}</button>`
  :`<button class=ai-chip data-act=agchip data-text="${AIU.esc(c.text||c.label)}">${AIU.esc(c.label)}</button>`}
function cardHTML(c,m,i){
 if(c.type==='plan'){const last=AIU.lastBot((A.sess&&A.sess.messages)||[]),done=!(A.sess&&A.sess.pending)||!last||m.id!==last.id;
  return `<div class="ai-card plan${done?' is-done':''}"><div class=ai-ch><b>${AIU.esc(c.subject)}</b><small>${c.count} stickers · ${AIU.esc(c.grid)} · ${AIU.esc(c.style)}</small></div>
   <div class=plan-tags>${(c.names||[]).map(n=>`<span>${AIU.esc(n)}</span>`).join('')}</div>
   <div class=plan-foot><div class=price>${c.free?'Free: no provider call.':`Costs <b>${AIU.credits(c.estimate)}</b>${c.creator&&c.creator.video?` (sheet ${+c.creator.sheet} + animation ${+c.creator.video})`:''}${c.balance!=null?` · balance ${+(+c.balance).toFixed(0)}`:''}`}${c.creator?`<br><small>Then straight to Telegram: ${c.creator.scope==='video'?'animated':'static'}, ${c.creator.bypass?'approving for you, stopping at any rejection':'one click from you at each approval'}.</small>`:''}</div>
    </div></div>`}   /* the go-ahead lives in the two chips under the message (Create it / Not yet), the same place as "Allow AI vision / Not now": one pair of buttons, never two */
 if(c.type==='multi'){const last=AIU.lastBot((A.sess&&A.sess.messages)||[]),done=!(A.sess&&A.sess.pending)||!last||m.id!==last.id;
  return `<div class="ai-card plan multi${done?' is-done':''}"><div class=ai-ch><b>${AIU.esc(c.title)}</b><small>${c.items.length} sheets · ${AIU.esc(c.grid)}</small></div>
   ${c.items.map(it=>`<div class=multi-item><div class=multi-h><b>${AIU.esc(it.subject)}</b><small>${it.count} stickers · ${AIU.esc(it.style)}</small></div>${it.changes&&it.changes.length?`<div class=multi-ch>${it.changes.map(x=>`<span>${AIU.esc(x)}</span>`).join('')}</div>`:''}
    <div class=plan-tags>${(it.names||[]).map(n=>`<span>${AIU.esc(n)}</span>`).join('')}</div></div>`).join('')}
   ${(c.assumed||[]).map(x=>`<div class=multi-assume>${AIU.esc(x)}</div>`).join('')}
   <div class=plan-foot><div class=price>${c.free?'Free: no provider call.':`All together <b>${AIU.credits(c.estimate)}</b>${c.balance!=null?` · balance ${+(+c.balance).toFixed(0)}`:''}`}</div></div></div>`}
 if(c.type==='particles_approve')return `<div class="ai-card plan"><p>Approve this batch as a pack first, so the particles have a sticker to live in</p><button class="btn pri" data-act=agpapprove data-g=${AIU.esc(c.generation)}>Approve as a pack</button></div>`;
 if(c.type==='particles_scope')return `<div class="ai-card plan"><b>Particles · ${AIU.esc(c.pack)}</b><button class="btn pri" data-act=agpscope data-p=${AIU.esc(c.pack_id)} data-k=${AIU.esc(c.kind||'drawn')} data-id=${AIU.esc(c.set||'')}>${c.kind==='video'?'Video from scratch':'Create particles'}</button></div>`;
 if(c.type==='effects')return `<div class="ai-card plan"><div class=ai-ch><b>Particle effects · ${AIU.esc(c.id)}</b><small>${AIU.esc(c.pack)} · ${c.count} stickers</small><span class=sp></span><a class=ai-link href="#/effects/${AIU.esc(c.id)}">Open effects</a></div></div>`
 if(c.type==='particles_plan')return `<div class="ai-card plan"><div class=ai-ch><b>${c.op==='more'?'More particles':'Particles'} · ${AIU.esc(c.op==='more'?(c.name||c.set):c.pack)}</b><small>${AIU.esc(c.grid)} · ${(c.elements||[]).length} particles</small></div>
   <div class=plan-tags>${(c.elements||[]).map(n=>`<span>${AIU.esc(n)}</span>`).join('')}</div>
   <div class=plan-foot><div class=price>${c.estimate==null?'The price is shown before anything is spent.':`<b>${AIU.credits(c.estimate)}</b>`}</div></div></div>`
 if(c.type==='particles')return `<div class="ai-card plan"><div class=ai-ch><b>Particles · ${AIU.esc(c.name||c.set)}</b><small>${AIU.esc(c.set)}${c.drawing?' · drawing':''}</small><span class=sp></span>${c.pack_id?`<a class=ai-link href="#/pack/${AIU.esc(c.pack_id)}">Open the pack's particle studio</a>`:`<a class=ai-link href="#/library">Open the Library</a>`}</div></div>`
 if(c.type==='generation'){
  const st=(c.data&&c.data.stickers)||[],ready=st.filter(x=>x.status==='READY').length,gid=c.generation;
  let note='';
  if(['FAILED','TIMEOUT'].includes(c.job_status))note=JR.controls(c.job_info||{id:c.job,status:c.job_status,error:c.job_error});
  else if(!gid){note=`Drawing the sheet${c.job_stage?' · '+AIU.esc(c.job_stage):''}…`}
  else if(c.data&&c.data.problem)note=problemHTML(c.data.problem,gid);
  else if(!st.length)note='Cutting the stickers…';else if(st.some(x=>x.status==='PENDING'))note='Cutting the stickers…';
  else if(c.animating&&st.some(x=>['PENDING','RUNNING'].includes(x.anim_status)))note='Animating…';
  const meta=gid?`${gid}${c.data&&c.data.parent?' · from '+c.data.parent:''} · ${ready} ready`:'';
  return `<div class="ai-card gen"><div class=ai-ch><b>${AIU.esc(c.subject||'Stickers')}</b><small>${meta}</small><span class=sp></span>${gid?`<button class=ai-link data-act=agstudio data-g="${gid}">Open in Studio</button>`:''}</div>
   ${(c.data&&c.data.video_sheets||[]).filter(v=>v.status!=='REJECTED').map(v=>SR.picture(c.data,v)).join('')}${c.data?SR.bulk(c.data):''}${carHTML(st.length?st:null,gid,(c.data&&c.data.allow)||null)}${note?`<div class=car-note>${note}</div>`:''}</div>`}
 if(c.type==='creator'){const g=c.run&&(m.cards||[]).find(x=>x.type==='generation'&&x.generation===c.run.generation);return runHTML(c.run,(g&&g.data&&g.data.allow)||null)}
 if(c.type==='stickers'){return `<div class="ai-card"><div class=ai-ch><b>${c.stickers.length===1?'Sticker':'Stickers'}</b><small>${c.stickers.length} found</small></div>${carHTML(c.stickers.map(x=>({...x,status:'READY',name:x.key})),null)}</div>`}
 return ''}

/* a sheet Python blocked: what happened in words, what was already paid, and one button that states the price (the click is the go-ahead) */
function problemHTML(p,gid){const got=p.received?`The sheet was received${p.received.job?' ('+AIU.esc(p.received.job)+')':''}${p.received.cost?' and paid for ('+AIU.credits(p.received.cost)+')':''}; nothing is lost, this batch just has no stickers.`:'';
 return `<div class=ai-problem><b>${AIU.esc(p.title)}</b><span>${AIU.esc(p.why)}</span><span>${AIU.esc(p.fix)}</span><small>${got}</small>
  ${p.cut_anyway?`<button class="ai-chip pri" data-act=agcut data-g="${AIU.esc(gid)}" title="Cut the sheet that was received, as it is, for free">Cut it anyway · free</button>`:''}
  <button class="ai-chip${p.cut_anyway?'':' pri'}" data-act=agretry data-g="${AIU.esc(gid)}">Try the sheet again · ${p.retry_estimate?AIU.credits(p.retry_estimate):'price shown by the provider'}</button></div>`}
/* the creator's run: where it stands, as a short list; what it stopped for is the message under it, with its buttons.
   The stop message carries the batch's own carousel (the backend attaches the generation card next to the run card), so the rejected stickers are visible
   where the buttons that decide about them are. The bulk pair below allows or takes back every allow-able sticker or animation of the run's batch. */
function runHTML(r,allow){if(!r)return '';
 const rows=(r.steps||[]).map(s=>`<li class="${s.state}"><i></i>${AIU.esc(s.label)}</li>`).join('');
 const st=r.status==='running'?'Working…':r.status==='waiting'?'Waiting for you':r.status==='done'?'On Telegram':r.status==='failed'?'Failed':'Stopped';
 const why=r.stop?`<div class=run-why>${AIU.esc(r.stop.why)}</div>`:r.waiting?`<div class=run-why>${AIU.esc(r.waiting.why)}</div>`:'';
 return `<div class="ai-card ai-run is-${r.status}"><div class=ai-ch><b>${AIU.esc(r.subject)}</b><small>${r.scope==='video'?'animated':'static'} pack · ${r.bypass?'auto-approve':'you approve'}</small><span class=sp></span><span class=run-st>${st}</span>
  ${r.status==='running'?`<button class=ai-link data-act=agaction data-type=creator_stop>Stop</button>`:''}</div><ol class=run-steps>${rows}</ol>${why}${runAllowRow(r,allow)}</div>`}
/* the same pair the Studio has, on the creator's card, per kind: N counts what is allow-able NOW. It reads the batch's allow block (gates.allow_info) that rides on the generation card next to the run. */
function runAllowRow(r,al){const gid=r.generation;if(!al||!gid||r.status==='done')return '';
 const rows=[['still','sticker'],['animation','animation'],['video_sheet','video sheet']].map(([kind,what])=>{const a=al[kind]||{can:[],undo:[]},n=a.can.length,b=a.undo.length;if(!n&&!b)return '';
  return `<span class=run-alw>${n?`<button class="ai-chip pri" data-act=agallowall data-g="${AIU.esc(gid)}" data-kind=${kind} data-allow=1 title="Use every ${what} anyway that Python blocked as a judgement call">Use all anyway (${n})</button>`:''}
   ${b?`<button class=ai-chip data-act=agallowall data-g="${AIU.esc(gid)}" data-kind=${kind} data-allow=0 title="Block the ${what}s you allowed again">Take all back (${b})</button>`:''}</span>`}).join('');
 return rows?`<div class=run-bulk>${rows}<span class=mut>or allow one sticker below</span></div>`:''}
function carHTML(st,gid,allow){
 const tiles=st?st:Array.from({length:6},(_,i)=>({id:'w'+i,index:i+1,status:'PENDING',wait:true}));
 const n=tiles.length;
 return `<div class=car><div class=car-vp><button class="car-nav prev" data-act=agcar data-dir=prev aria-label="Previous" disabled>${ic('prev')}</button>
  <div class=car-track tabindex=0 aria-label="Stickers, swipe or use the arrow keys">${tiles.map(s=>tileHTML(s,gid,allow)).join('')}</div>
  <button class="car-nav next" data-act=agcar data-dir=next aria-label="Next">${ic('next')}</button></div>
  <div class=car-dots>${tiles.map((_,i)=>`<i class="${i===0?'on':''}"></i>`).join('')}</div></div>`}

/* one tile of the chat's carousel. A blocked sticker is never dimmed and never hidden: it wears the locked red marks (hatched while it is not in the set,
   solid with a check once it was allowed by the person), its reason stays readable under it, and the allow button sits on the tile itself, per kind.
   `allow` is the batch's allow block (flow/gates.py allow_info) that the card's own data carries; without it a blocked tile says its reason and offers nothing. */
function tileHTML(s,gid,allow){
 const wait=s.wait||(s.status==='PENDING'),id=s.id||'';
 const stB=s.status==='FAILED'||s.still==='REJECTED',anB=s.anim_status==='FAILED'||s.anim==='REJECTED',bad=stB||anB;
 const media=s.webm&&(s.anim_status==='READY'||!s.anim_status)&&s.status==='READY'?`<video src="${AIU.esc(s.webm)}" autoplay loop muted playsinline preload=metadata></video>`
  :s.png?`<img src="${AIU.esc(s.png)}" alt="${AIU.esc(s.key||'')}" draggable=false loading=lazy>`:'';
 const emo=Array.isArray(s.emoji)?s.emoji.join(''):(s.emoji||'');
 const A0=k=>(allow&&allow[k])||{can:[],allowed:[],undo:[],why:{},final:{}};
 const btn=(k,take)=>`<button class="${take?'ai-chip':'ai-chip pri'}" data-act=agallow data-g="${AIU.esc(gid||'')}" data-i=${s.index} data-kind=${k} data-allow=${take?0:1}${take?'':' title="Python\'s check is a judgement call: you decide. It is recorded, and you can take it back"'}>${take?'Take it back':'Use it anyway'}</button>`;
 const row=(k,blocked,rawWhy)=>{const a=A0(k);if(s.index==null||!blocked)return null;
  if(a.can.includes(s.index))return{btn:btn(k,false),whys:[a.why[s.index]||humanWhy(rawWhy)],allowed:false};
  if(a.undo.includes(s.index))return{btn:btn(k,true),whys:['allowed by you'],allowed:true};
  if(a.allowed.includes(s.index))return{btn:'',whys:['allowed by you'],allowed:true};
  const ws=[a.why[s.index]||humanWhy(rawWhy)];if(a.final[s.index]&&ws.indexOf(a.final[s.index])<0)ws.push(a.final[s.index]);
  return{btn:'',whys:ws,allowed:false}};
 const rS=row('still',stB,s.reason),rA=row('animation',anB,s.anim_reason);
 const allowed=!!((rS&&rS.allowed)||(rA&&rA.allowed));
 const badge=s.still==='APPROVED'?`<span class=ag-bd title="Approved">${ic('check')}</span>`:allowed?`<span class="ag-bd is-ok" title="Allowed by you">${ic('check')}</span>`:bad?`<span class="ag-bd is-no" title="Rejected">${ic('x')}</span>`:'';
 const cap=s.wait?'':`<b>${s.index!=null?s.index:''}</b><span>${AIU.esc(String(s.title||s.key||s.name||'').replace(/_/g,' '))} ${AIU.esc(emo)}</span>`;
 const whys=[...((rS&&rS.whys)||[]),...((rA&&rA.whys)||[])].filter((w,i,arr)=>w&&arr.indexOf(w)===i);
 const btns=[rS&&rS.btn,rA&&rA.btn].filter(Boolean).join('');
 const stateWord=!bad?'':allowed?' (allowed by you)':' (rejected)';
 const albl=`S${s.index!=null?s.index:''} ${String(s.title||s.key||s.name||'').replace(/_/g,' ')}${stateWord}`;
 return `<figure class="ag-tile${A.sel.has(id)?' is-sel':''}${bad?' is-bad':''}${allowed?' is-allowed':''}${wait?' is-wait':''}" data-act=agtile data-id="${AIU.esc(id)}" tabindex="0" role="button" aria-label="${AIU.esc(albl)}"><div class=ag-ph>${media}${bad?`<span class="ag-hatch${allowed?' is-on':''}" aria-hidden=true></span>`:''}</div>${badge}<figcaption class=ag-nm>${cap}</figcaption>${id?`<button class=ag-id data-act=copyid data-v="${AIU.esc(id)}" title="${AIU.esc(id)} · click to copy the id" aria-label="Copy the id ${AIU.esc(id)}">${AIU.esc(id)}</button>`:''}
  ${whys.length?`<div class=ag-why>${whys.map(w=>AIU.esc(w)).join('<br>')}</div>`:''}${btns?`<div class=ag-alw>${btns}</div>`:''}</figure>`}
const humanWhy=r=>String(r||'failed').replace(/_/g,' ');

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
ACT.agedit=el=>{if(typeof studioEditSticker==='function')studioEditSticker(+String(el.dataset.g).replace(/\D/g,''),+el.dataset.i,'agent')};          /* the editor opens at once on that slice (no chat turn); its Save lands back here */
ACT.agsetting=async el=>{try{await saveSet(JSON.parse(el.dataset.set))}catch(e){return}paint()};          /* a one-time switch: the setting is saved and nothing is sent to the chat */
ACT.agaction=el=>{const a={type:el.dataset.type};if(el.dataset.g)a.generation=el.dataset.g;if(el.dataset.i){try{a.indexes=JSON.parse(el.dataset.i)}catch(e){}}agSend('',a)};
ACT.agcut=async el=>{const r=await post(`/api/generations/${el.dataset.g}/recut`);if(!r.ok)return toast(r.j.error||'Could not cut the sheet',1);toast('Cutting the sheet…');if(A.sid)await loadSession(A.sid,true);startPoll()};
ACT.agretry=el=>agSend('',{type:'retry_sheet',generation:el.dataset.g});
ACT.agtrace=el=>{const k=el.dataset.m;if(A.open.has(k))A.open.delete(k);else A.open.add(k);paint()};
ACT.agstep=el=>{const k=el.dataset.k;if(A.open.has(k))A.open.delete(k);else A.open.add(k);paint()};
ACT.agstudio=el=>{const n=+String(el.dataset.g).replace(/\D/g,'');if(typeof SES!=='undefined'){SES={prompt:'',gens:[n],off:[],pack:''};if(typeof saveSes==='function')saveSes()}location.hash='#/studio'};
ACT.agallow=async el=>{const gid=el.dataset.g,n=+String(gid||'').replace(/\D/g,'');if(!n)return;
 const r=await post(`/api/generations/${n}/allow`,{kind:el.dataset.kind==='still'?'still':'animation',index:+el.dataset.i,allow:el.dataset.allow!=='0'});
 if(!r.ok)return toast(r.j.error||'Could not change it',1);
 toast(el.dataset.allow==='0'?'The permission is taken back':'Used anyway: cutting it again…');
 if(A.sid)await loadSession(A.sid,true);startPoll()};
ACT.agallowall=async el=>{const gid=el.dataset.g,n=+String(gid||'').replace(/\D/g,'');if(!n)return;const allow=el.dataset.allow==='1',kind=['still','video_sheet'].includes(el.dataset.kind)?el.dataset.kind:'animation';
 if(el.disabled)return;const row=el.closest('.run-alw'),btns=row?[...row.querySelectorAll('button[data-act=agallowall]')]:[el];
 btns.forEach(b=>{b.disabled=true;b.setAttribute('aria-busy','true')});el.textContent='Cutting again…';
 try{const r=await post(`/api/generations/${n}/allow`,{all:true,allow,kind});
 if(!r.ok)return toast(r.j.error||'Could not change it',1);
 toast(allow?`Allowed ${r.j.indexes.length}: cutting their ${kind==='still'?'pictures':'animations'}…`:`Took back ${r.j.indexes.length}`);
 if(A.sid)await loadSession(A.sid,true);startPoll()}
 finally{btns.forEach(b=>{if(b.isConnected){b.disabled=false;b.removeAttribute('aria-busy')}})}};
/* the carousel's tiles are figures: Enter or Space on a focused one selects it like a click (a figure answers neither key by itself) */
document.addEventListener('keydown',e=>{const t=e.target;if((e.key==='Enter'||e.key===' ')&&t&&t.dataset&&t.dataset.act==='agtile'&&String(t.tagName||'').toLowerCase()==='figure'){e.preventDefault();ACT.agtile(t,e)}});
ACT.agnew=()=>{A.sid=null;A.sess=null;A.sel.clear();A.els.clear();store.set('mirsal.ai.sid','');const c=$('ai-col');if(c)c.innerHTML='';history.replaceState(null,'','#/agent');paint();agList();const t=$('ai-in');if(t)t.focus()};
ACT.agopen=el=>{location.hash='#/agent/'+el.dataset.id};
ACT.agdel=el=>{const id=el.dataset.id;confirmDlg('Delete this chat? The stickers it made stay in the Studio.',async()=>{await post(`/api/chat/sessions/${id}/delete`);if(A.sid===id)ACT.agnew();await loadSessions();agList()},'Delete')};
ACT.agset=()=>{A.setOpen=!A.setOpen;setSet();if(A.setOpen)loadModels()};
ACT.agsetgrid=async el=>saveSet({grid:el.dataset.v});
/* the sheet size in the bar is ONE chip that flips on click (it used to be a native <select>, and .ag-sel in the settings panel is display:block;width:100%, which stretched this chip over its own row) */
ACT.aggridtoggle=async el=>saveSet({grid:((A.sess&&A.sess.settings&&A.sess.settings.grid)||'3x3')==='2x2'?'3x3':'2x2'});
/* the sheet size in the bar is one chip that flips on click; the settings panel keeps its own side-by-side pair (ai-seg) below */
/* ---------- under the box: what the next sheet will be made with, one click from changing it (the same settings as the gear, and the style tiles the Studio has, smaller) */
const styleNow=()=>(A.sess&&A.sess.settings&&A.sess.settings.style_id)||A.pre||(A.agent&&A.agent.default_style)||'flat_vector';
function drawBar(){const bar=$('ag-bar'),box=$('ag-styles');if(!bar||!box)return;
 const st=(A.sess&&A.sess.settings)||{grid:'3x3',ask_before_spending:true},list=(A.agent&&A.agent.styles)||[],cur=styleNow();
 const now=list.find(s=>s.id===cur);
 bar.innerHTML=`${now?`<span class="ag-chip ag-cur" title="The style of the next sheet"><img src="/assets/styles/${AIU.esc(now.id)}" alt="">${AIU.esc(now.label)} style</span>`:''}<button type="button" class="ag-chip ag-grid" data-act="aggridtoggle" title="How many stickers in one sheet: nine (3×3) or four (2×2). Click to change.">${ic('lib')}${st.grid==='2x2'?'2×2 sheet':'3×3 sheet'}</button>
  <button type=button class="ag-chip${st.ask_before_spending?'':' warn'}" data-act=agsetask title="${st.ask_before_spending?'The price is shown and you say go before anything is spent':'Sheets start at once, without showing the price first'}">${ic(st.ask_before_spending?'check':'x')}${st.ask_before_spending?'Asks before spending':'Spends without asking'}</button>`;
 box.innerHTML=list.map(s=>`<button type=button class="ag-st${s.id===cur?' on':''}" role=radio aria-checked=${s.id===cur} data-act=agstyle data-id="${AIU.esc(s.id)}" title="${AIU.esc(s.label)}: ${AIU.esc(s.hint)}"><img src="/assets/styles/${AIU.esc(s.id)}" alt="" loading=lazy><b>${AIU.esc(s.label)}</b></button>`).join('')}
ACT.agstyle=async el=>{A.pre=el.dataset.id;store.set('mirsal.ai.style',A.pre);if(A.sess)await saveSet({style_id:A.pre});else drawBar()};
ACT.agsetask=async()=>saveSet({ask_before_spending:!(A.sess?A.sess.settings.ask_before_spending:true)});
ACT.agbe=async el=>{const r=await post('/api/ai/backend',{backend:el.dataset.v});if(r.ok){await Promise.all([loadAgent(),engSync()]);engRedraw()}else toast(r.j.error||'Could not change the AI engine',1)};
async function saveSet(p){const sid=await ensureSession();if(!sid)return;const r=await post(`/api/chat/sessions/${sid}/settings`,p);if(r.ok){A.sess.settings=r.j.settings;setSet();drawBar()}else toast(r.j.error,1)}
/* the AI engine row: Auto keeps a working backend and only a failed call switches it; Local / Cloud are used as chosen. A backend that is not available says why. */
function beRow(){const a=ENGSRC||A.agent||{},av=a.availability||{},pref=a.preference||'auto';
 const b=(v,label)=>{const ok=v==='auto'||(av[v]&&av[v].ok);const why=v==='auto'?'Use the local model when LM Studio answers, otherwise the cloud; keep what works':(av[v]&&av[v].why)||(av[v]&&av[v].model)||'';
  return `<button data-act=agbe data-v=${v} class="${pref===v?'on':''}${ok?'':' is-off'}" title="${AIU.esc(ok&&v!=='auto'?av[v].model:why)}">${label}</button>`};
 const now=a.agent&&a.agent.provider!=='none'&&!AIU.engine(a).rules?`now: ${a.agent.provider==='local'?'local':'cloud'} · ${AIU.esc((a.agent.model||'').replace(/:\d+$/,''))}`:`now: ${AIU.esc(a.noModel||'rules only')}`;
 const warn=pref!=='auto'&&av[pref]&&!av[pref].ok?` · <span class=ai-err>${AIU.esc(av[pref].why||'not available')}</span>`:'';
 return `<div class=r><div><b>AI engine</b><small>${now}${warn}</small></div><div class=ai-seg>${b('auto','Auto')}${b('local','Local')}${b('cloud','Cloud')}</div></div>${modelRow()}`}
/* the local model, part of the engine row: a dropdown of every model the local server lists (LM Studio, vLLM: GET /api/llm/models), the one in use selected, and one line saying why when it cannot answer.
   A pick is POST /api/ai/backend {model}; the first answer after a switch can take a moment while the server loads it. */
function modelRow(){const m=A.llm,pref=((ENGSRC||A.agent)||{}).preference||'auto';
 if(A.llmBusy||!m)return `<div class="r ag-mrow"><div><small>${A.llmBusy?'Switching the local model: the first answer can take a moment…':'Checking the local model…'}</small></div></div>`;
 if(!m.models.length&&pref==='cloud')return '';
 const sel=m.models.length?`<select class=ag-sel data-agmodel aria-label="Local model">${m.models.map(x=>`<option value="${AIU.esc(x.id)}"${x.id===m.current?' selected':''}>${AIU.esc(x.id)}${x.loaded?' · loaded':''}</option>`).join('')}</select>`:'';
 return `<div class="r ag-mrow"><div><b>Local model</b><small class="${m.ok?'':'ai-err'}" title="${AIU.esc(m.why||'')}">${AIU.esc(AIU.modelNote(m))}</small></div>${sel}</div>`}
document.addEventListener('change',async e=>{const s=e.target;if(!s||!s.dataset||s.dataset.agmodel===undefined)return;
 A.llmBusy=true;engRedraw();
 const r=await post('/api/ai/backend',{model:s.value});
 if(!r.ok)toast((r.j&&r.j.error)||'Could not change the local model',1);
 await Promise.all([loadModels(),loadAgent(),engSync()]);A.llmBusy=false;engRedraw()});
/* what the Studio calls: rows(source) draws the same engine row and model row from its own source; ensure() reads the local server's models once; load() reads them again */
globalThis.AIENG={rows:src=>{ENGSRC=src||null;try{return beRow()}finally{ENGSRC=null}},ensure:()=>{if(!A.llm&&!A.llmLoading){A.llmLoading=true;loadModels().finally(()=>{A.llmLoading=false})}},load:loadModels};
/* the agentic creator: one click from a request to a pack on Telegram. Any rejection still stops it. */
function crRows(st){const c=Object.assign({on:false,scope:'images',bypass:false},st.creator||{});
 let h=`<div class=r><div><b>Agentic creator</b><small>One go-ahead: request, sheet, approval, pack, Telegram</small></div><button type=button class="ai-sw${c.on?' on':''}" data-act=agcr data-k=on role=switch aria-checked="${c.on}" aria-label="Agentic creator"></button></div>`;
 if(c.on)h+=`<div class=r><div><b>Send to Telegram as</b><small>Images: the stills as a static pack. Full video: animated first (a second paid call)</small></div><div class=ai-seg><button data-act=agcr data-k=scope data-v=images class="${c.scope==='images'?'on':''}">Images</button><button data-act=agcr data-k=scope data-v=video class="${c.scope==='video'?'on':''}">Full video</button></div></div>
  <div class=r><div><b>Approve everything for me</b><small>${c.bypass?'On: no questions on the way. Any rejection still stops it':'Off: it stops at each approval and waits for one click'}</small></div><button type=button class="ai-sw${c.bypass?' on':''}" data-act=agcr data-k=bypass role=switch aria-checked="${c.bypass}" aria-label="Approve everything automatically"></button></div>`;
 return h}
ACT.agcr=async el=>{const cur=Object.assign({on:false,scope:'images',bypass:false},(A.sess&&A.sess.settings.creator)||{}),k=el.dataset.k;
 const next=k==='scope'?{scope:el.dataset.v}:{[k]:!cur[k]};
 await saveSet({creator:Object.assign({},cur,next)})};
function setSet(){const el=$('ai-set');if(!el)return;el.classList.toggle('on',A.setOpen);if(!A.setOpen)return;
 const st=A.sess?A.sess.settings:{grid:'3x3',ask_before_spending:true};
 el.innerHTML=`<div class=r><div><b>Grid</b><small>How many stickers in one sheet</small></div><div class=ai-seg><button data-act=agsetgrid data-v=3x3 class="${st.grid==='3x3'?'on':''}">3×3</button><button data-act=agsetgrid data-v=2x2 class="${st.grid==='2x2'?'on':''}">2×2</button></div></div>
  ${beRow()}
  ${crRows(st)}
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

/* ---------- the second column: chats (the shared column; on narrow screens it is the shell's drawer, app.js) */
function listHTML(){const rows=A.sessions.map(s=>`<div class="sess-row${s.id===A.sid?' on':''}" data-act=agopen data-id="${s.id}"><div class=t><b>${AIU.esc(s.title||'New chat')}</b><small>${s.subjects.length?AIU.esc(s.subjects.slice(0,3).join(', '))+' · ':''}${AIU.rel(s.updated)}</small></div><button class=x data-act=agdel data-id="${s.id}" aria-label="Delete chat">${ic('trash')}</button></div>`).join('');
 return `<button class=sess-new data-act=agnew>${ic('plus')}New chat</button>${rows||'<div class=mut style="padding:14px 18px">Your chats will be here.</div>'}`}
window.agList=function agList(){if(route_!=='agent')return;const c2=$('col2');if(c2)c2.innerHTML=`<div class=c2h><h1>Chats</h1></div><div class=c2l>${listHTML()}</div>`;};
const agList=window.agList;
})()}
