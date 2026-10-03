/* The welcome modal: shown once when the app is first opened in a browser session, and again whenever the Mirsal logo (the home button) is pressed.
   Page 0 is a fast-cut ad film (Seedance 2.5, /assets/welcome/welcome.mp4), pages 1-4 are the features as sliding images (Nano Banana 2): stickers from one idea, stickers that move,
   emoji particle bursts, the AI chat. The slides are data (WL_SLIDES), the markup is built by pure functions. Nothing here talks to the server except the assets; the files are real files
   under console/assets/welcome/ (a missing one just leaves the soft gradient behind the text, the modal still works). docs/onboarding.md has the prompts that made the media. */
'use strict';
ICONS.wlplay='<path d="M8 5.5v13l11-6.5z" fill="currentColor"/>';
ICONS.wlpause='<path d="M8 5h3v14H8zM13 5h3v14h-3z" fill="currentColor"/>';
ICONS.wlsound='<path d="M4 9.5v5h3.5L12 18.5v-13L7.5 9.5z" fill="currentColor"/><path d="M15.5 9a4 4 0 010 6M18 6.5a7.5 7.5 0 010 11"/>';
ICONS.wlmute='<path d="M4 9.5v5h3.5L12 18.5v-13L7.5 9.5z" fill="currentColor"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>';

const WL_SLIDES=[
 {id:'film',kind:'video',src:'/assets/welcome/welcome.mp4',poster:'/assets/welcome/welcome-poster.jpg',kicker:'Welcome to Mirsal',title:'Describe it. Watch it come alive.',
  body:'Animated stickers, emoji bursts and an AI that remembers your taste, checked for Telegram at every step.'},
 {id:'ideas',kind:'image',src:'/assets/welcome/s1.webp',kicker:'Stickers',title:'One idea, a whole pack',
  body:'Describe it once and get a sheet of nine stickers. You approve every one, every emoji tag, at every gate.',cta:['Start in the Studio','studio']},
 {id:'motion',kind:'image',src:'/assets/welcome/s2.webp',kicker:'Animation',title:'Stickers that move',
  body:'Each sticker becomes a 3-second animation, 512 px at 30 fps and under 256 KB, checked frame by frame.',cta:['Open your library','library']},
 {id:'burst',kind:'image',src:'/assets/welcome/s3.webp',kicker:'Particle effects',title:'Emoji that burst',
  body:'Press an emoji and related pieces fly out and fall: bat signals from Batman, gold bars from jewelry. Simulate it free, or have Kling draw it.',cta:['Make particles','effects']},
 {id:'chat',kind:'image',src:'/assets/welcome/s4.webp',kicker:'AI chat',title:'Just tell the AI',
  body:'Say "three sticker packs of fruits": it plans them, shows one price, and runs them together. Say "the cherries were too realistic" and it remembers.',cta:['Open the AI chat','agent']},
];
const WL={i:0,open:false,muted:false,needTap:false,auto:true,timer:0,tick:0};      // sound is ON by default; a browser that refuses sound without a gesture gets the film muted until the first tap (wlSync)
const WL_SEEN='mirsal.welcome.seen',WL_OFF='mirsal.welcome.off',WL_STEP=6500;
const wlGet=(s,k)=>{try{return s.getItem(k)}catch(e){return null}},wlSet=(s,k,v)=>{try{s.setItem(k,v)}catch(e){}};
const wlReduced=()=>!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);

function wlSlideHTML(s,i){
 const media=s.kind==='video'
  ?`<video class=wl-v id=wl-v muted playsinline preload=auto poster="${esc(s.poster)}" aria-label="A short fast-cut film about Mirsal"><source src="${esc(s.src)}" type="video/mp4"></video>
    <div class=wl-vc><button class=wl-ib data-act=wlplay id=wl-pp aria-label="Play or pause">${ic('wlplay')}</button><span class=wl-hint id=wl-hint hidden>Tap for sound</span><button class=wl-ib data-act=wlsound id=wl-snd aria-label="Sound on or off">${ic('wlsound')}</button></div>`
  :`<img class=wl-i src="${esc(s.src)}" alt="" loading=${i<2?'eager':'lazy'} onerror="this.style.display='none'">`;
 return `<section class="wl-s ${s.kind}" data-i=${i} aria-roledescription=slide aria-label="${esc(s.title)}">
  <div class=wl-m>${media}</div>
  <div class=wl-t><span class=wl-k>${esc(s.kicker)}</span><h2>${esc(s.title)}</h2><p>${esc(s.body)}</p>
   ${s.cta?`<button class="btn pri wl-cta" data-act=wlgo data-to="${esc(s.cta[1])}">${esc(s.cta[0])}</button>`:`<button class="btn pri wl-cta" data-act=wlnext>See what it does ${ic('next')}</button>`}</div></section>`}
function wlHTML(slides){
 return `<div class=wl role=dialog aria-modal=true aria-label="Welcome to Mirsal">
  <button class=wl-x data-act=wlclose aria-label="Close">${ic('x')}</button>
  <div class=wl-vp><div class=wl-track id=wl-track>${slides.map(wlSlideHTML).join('')}</div>
   <button class="wl-nav prev" data-act=wlprev aria-label="Previous">${ic('prev')}</button><button class="wl-nav next" data-act=wlnext aria-label="Next">${ic('next')}</button></div>
  <div class=wl-foot><div class=wl-dots id=wl-dots role=tablist>${slides.map((s,i)=>`<button class=wl-d role=tab data-act=wlgoto data-i=${i} aria-label="${esc(s.title)}"><i></i></button>`).join('')}</div>
   <label class=wl-off><input type=checkbox id=wl-off ${wlGet(localStorage,WL_OFF)==='1'?'checked':''}> Don't open this when the app starts</label>
   <button class=link data-act=wlclose>Skip</button></div></div>`}

function wlSync(){
 const tr=$('wl-track');if(!tr)return;tr.style.transform=`translateX(${-100*WL.i}%)`;
 tr.querySelectorAll('.wl-s').forEach((el,k)=>{el.toggleAttribute('inert',k!==WL.i);el.setAttribute('aria-hidden',k===WL.i?'false':'true')});
 document.querySelectorAll('#wl-dots .wl-d').forEach((d,k)=>{d.classList.toggle('on',k===WL.i);d.classList.toggle('done',k<WL.i);d.setAttribute('aria-selected',k===WL.i?'true':'false')});
 const p=document.querySelector('.wl-nav.prev'),n=document.querySelector('.wl-nav.next');if(p)p.hidden=WL.i===0;if(n)n.hidden=WL.i===WL_SLIDES.length-1;
 const v=$('wl-v');if(v){if(WL.i===0){v.muted=WL.muted;if(!wlReduced()){const pr=v.play();if(pr&&pr.catch)pr.catch(()=>{if(!WL.muted){WL.muted=true;WL.needTap=true;v.muted=true;const p2=v.play();if(p2&&p2.catch)p2.catch(()=>0)}wlPP()})}}else v.pause();wlPP()}
 clearTimeout(WL.timer);cancelAnimationFrame(WL.tick);const bar=document.querySelector('#wl-dots .wl-d.on i');document.querySelectorAll('#wl-dots .wl-d i').forEach(i=>i.style.transform='');
 if(WL.open&&WL.auto&&!wlReduced()&&WL.i>0&&WL.i<WL_SLIDES.length-1){if(bar)bar.style.transform='scaleX(0)';const t0=performance.now(),step=t=>{if(!WL.open||!WL.auto)return;const f=Math.min(1,(t-t0)/WL_STEP);if(bar)bar.style.transform=`scaleX(${f})`;if(f>=1)return wlStep(1,true);WL.tick=requestAnimationFrame(step)};WL.tick=requestAnimationFrame(step)}}
function wlPP(){const v=$('wl-v'),b=$('wl-pp'),s=$('wl-snd'),h=$('wl-hint');if(b&&v)b.innerHTML=ic(v.paused?'wlplay':'wlpause');if(s)s.innerHTML=ic(WL.muted?'wlmute':'wlsound');if(h)h.hidden=!(WL.needTap&&WL.muted)}
function wlStep(d,byTimer){if(!byTimer)WL.auto=false;WL.i=Math.max(0,Math.min(WL_SLIDES.length-1,WL.i+d));wlSync()}
function wlOpen(){if(WL.open)return;WL.open=true;WL.i=0;WL.auto=true;WL.muted=false;WL.needTap=false;wlSet(sessionStorage,WL_SEEN,'1');
 const el=$('welcome');el.innerHTML=wlHTML(WL_SLIDES);el.classList.add('on');document.body.classList.add('wl-on');
 const v=$('wl-v');if(v){v.addEventListener('ended',()=>{if(WL.open&&WL.i===0&&WL.auto)wlStep(1,true)});v.addEventListener('play',wlPP);v.addEventListener('pause',wlPP)}
 wlSync();const x=el.querySelector('.wl-x');if(x)x.focus()}
function wlClose(){if(!WL.open)return;WL.open=false;clearTimeout(WL.timer);cancelAnimationFrame(WL.tick);const v=$('wl-v');if(v)v.pause();
 const el=$('welcome');el.classList.remove('on');el.innerHTML='';document.body.classList.remove('wl-on')}
ACT.wlclose=wlClose;ACT.wlnext=()=>wlStep(1);ACT.wlprev=()=>wlStep(-1);
ACT.wlgoto=el=>{WL.auto=false;WL.i=+el.dataset.i;wlSync()};
ACT.wlgo=el=>{const to=el.dataset.to;wlClose();location.hash='#/'+to};
ACT.wlplay=()=>{const v=$('wl-v');if(!v)return;WL.auto=false;v.paused?v.play().catch(()=>0):v.pause();wlPP()};
ACT.wlsound=()=>{const v=$('wl-v');WL.needTap=false;WL.muted=!WL.muted;if(v){v.muted=WL.muted;if(!WL.muted&&v.paused)v.play().catch(()=>0)}wlPP()};
document.addEventListener('change',e=>{if(e.target&&e.target.id==='wl-off')wlSet(localStorage,WL_OFF,e.target.checked?'1':'0')});     // not a data-act: the click handler's preventDefault would undo the tick
/* the home button: the Mirsal logo goes to a clean AI screen and opens the welcome again */
ACT.home=()=>{const there=route_==='agent'&&$('s-agent').dataset.ready;if(there&&typeof ACT.agnew==='function')ACT.agnew();
 else{try{localStorage.setItem('mirsal.ai.sid','')}catch(e){}if(typeof A!=='undefined'){A.sid=null;A.sess=null}location.hash='#/agent'}wlOpen()};
document.addEventListener('keydown',e=>{if(!WL.open)return;if(e.key==='Escape'){e.stopPropagation();wlClose()}else if(e.key==='ArrowRight')wlStep(1);else if(e.key==='ArrowLeft')wlStep(-1);
 else if(e.key===' '&&WL.i===0&&!/button|input/i.test((document.activeElement||{}).tagName||'')){e.preventDefault();ACT.wlplay()}},true);
document.addEventListener('click',e=>{if(WL.open&&e.target.id==='welcome')wlClose()});
/* a browser that would not play with sound (no gesture yet) played the film muted: the first tap or key inside the modal (not on the sound button, which decides for itself) turns the sound on */
const wlUnlock=e=>{if(!WL.open||!WL.needTap||!WL.muted||WL.i!==0)return;if(e.target&&e.target.closest&&e.target.closest('[data-act=wlsound],[data-act=wlclose],.wl-x'))return;
 const v=$('wl-v');if(!v)return;WL.muted=false;WL.needTap=false;v.muted=false;if(v.paused)v.play().catch(()=>0);wlPP()};
document.addEventListener('pointerdown',wlUnlock,true);document.addEventListener('keydown',wlUnlock,true);
/* the first open of a browser session (not when the person asked not to see it at start) */
window.addEventListener('load',()=>{if(wlGet(sessionStorage,WL_SEEN)!=='1'&&wlGet(localStorage,WL_OFF)!=='1')setTimeout(wlOpen,450)});
