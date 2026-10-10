/* Home (#/home): the first screen and the Mirsal logo's target. Haitham's Higgsfield-style page (web/mockups/home-library.html) drawn from the caller's real
   library (GET /api/library): the featured stickers, the shortcuts into the app, the packs with search and filters, how it works. Nothing here is a preview:
   every card opens the real pack, every shortcut opens the real screen (docs/design.md "Home"). */
'use strict';
const HM={q:'',filter:'all'};
const HM_TINTS=['ice','lilac','cream','lavender','mint','rose','sand','green'];
/* what a pack is, for the filters and the card's subtitle (pure) */
const hmPackInfo=p=>{const st=p.stickers||[],animated=st.filter(s=>s.type==='animated').length,particles=st.some(s=>Array.isArray(s.particles)&&s.particles.length);
 const tags=[animated?'animated':null,st.length-animated?'static':null,particles?'particles':null].filter(Boolean);
 return{animated,still:st.length-animated,particles,tags,telegram:((p.telegram||{}).sets||[]).map(x=>x.link).find(Boolean)||'',
  label:animated?(st.length-animated?'Mixed pack':'Animated'):'Static pack',
  text:(p.name+' '+st.map(s=>s.name+' '+(s.emoji||'')).join(' ')).toLowerCase()}};
const hmShown=(p,q,filter)=>{const i=hmPackInfo(p);return(filter==='all'||i.tags.includes(filter))&&(!q||i.text.includes(q))};
/* up to three stickers for the hero, newest pack first, animated first (pure) */
const hmHero=packs=>{const out=[];for(const p of [...packs].sort((a,b)=>(b.created||0)-(a.created||0))){
  const st=p.stickers||[],s=st.find(x=>x.id===p.cover)||st.find(x=>x.type==='animated')||st[0];if(s)out.push(s);if(out.length===3)break}return out};
const hmIc=n=>`<span class=hm-ti>${ic(n)}</span>`;
function hmCard(p,i){const x=hmPackInfo(p),sub=[x.animated?`${x.animated} animated`:'',x.still?`${x.still} static`:'',x.particles?'With particles':''].filter(Boolean).join(' · ');
 return`<article class=hm-card data-id=${p.id}><button class="hm-art hm-${HM_TINTS[i%HM_TINTS.length]}" data-act=openpack data-id=${p.id} aria-label="Open ${esc(p.name)}"><span class=hm-type>${x.animated?ic('film'):''}${x.label}</span>${coverMedia(p)}<span class=hm-open>Open pack ↗</span></button>
  <div class=hm-info><div><h3>${esc(p.name)}</h3><p>${sub||'Empty pack'}</p></div><span>${x.telegram?`<a href="${esc(x.telegram)}" target=_blank rel="noopener noreferrer" title="Open in Telegram">${ic('telegram')}</a>`:''}${p.stickers.length} sticker${p.stickers.length===1?'':'s'}</span></div></article>`}
function hmGallery(){const box=$('hm-gal');if(!box)return;const q=HM.q.trim().toLowerCase(),ps=LIB.packs.filter(p=>hmShown(p,q,HM.filter));
 box.innerHTML=ps.map(hmCard).join('');$('hm-empty').hidden=!!ps.length||!LIB.packs.length;
 document.querySelectorAll('#s-home [data-act=hmfilter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.f===HM.filter)))}
RENDER.home=async()=>{await loadLib();const ps=LIB.packs,st=ps.flatMap(p=>p.stickers),anim=st.filter(s=>s.type==='animated').length,hero=hmHero(ps),
  owner=typeof ME==='undefined'||!ME||ME.role==='owner',canImport=typeof ACT.impackopen==='function'&&owner;
 $('s-home').innerHTML=`<div class=hm>
 <div class=hm-intro><div><div class=hm-eye>Your creative playground${ps.length?` · ${ps.length} pack${ps.length===1?'':'s'}`:''}</div><h1>A little more expressive.</h1><p>Turn the things you love into stickers worth sending.</p>
  ${ps.length?`<div class=hm-sum><span>${ps.length} pack${ps.length===1?'':'s'}</span><span>${st.length} sticker${st.length===1?'':'s'}</span><span>${anim} animated</span></div>`:''}</div>
  <div class=hm-intro-end><label class=hm-search>${ic('search')}<input id=hm-q type=search placeholder="Search your library" aria-label="Search your packs" value="${esc(HM.q)}"></label><button class="btn pri" data-act=hmai>${ic('ai')} Start creating</button></div></div>
 <div class=hm-feat>
  <article class=hm-hero><div class=hm-copy><span class=hm-badge><i></i>Made for your imagination</span><h2>Big feelings.<br><em>Little stickers.</em></h2><p>A character, an inside joke, a whole mood. Make it yours, then bring it to life.</p><button class="btn pri" data-act=hmai>${ps.length?'Make a new pack':'Make your first pack'} ${ic('chev')}</button></div>
   <div class=hm-heroart aria-hidden=true>${hero.map((s,i)=>media(s,'hm-hc hm-hc'+i)).join('')}<span class="hm-bub hm-b1">made by you ♡</span><span class="hm-bub hm-b2">your little universe.</span><span class=hm-spark>✦</span></div></article>
  <div class=hm-side>
   <article class="hm-mini hm-lilac"><span class=hm-badge>Give it a little life</span><h3>From cute to moving.</h3><p>Turn a still sticker into a tiny moment.</p><button class=hm-go data-act=hmfilter data-f=animated data-scroll=1>Explore animation ${ic('chev')}</button>${hero[1]||hero[0]?media(hero[1]||hero[0],'hm-miniart'):''}</article>
   <article class="hm-mini hm-peach"><span class=hm-badge>The finishing touch</span><h3>A sprinkle of magic.</h3><p>Add particles that make every reaction pop.</p><button class=hm-go data-act=nav data-to=effects>Try particle effects ${ic('chev')}</button><div class=hm-orbit aria-hidden=true></div></article>
  </div></div>
 <div class=hm-tools>
  <button class=hm-tool data-act=hmai>${hmIc('ai')}<div><h3>Create with AI</h3><p>Start with a little idea</p></div>${ic('chev')}</button>
  <button class=hm-tool data-act=nav data-to=generate>${hmIc('gen')}<div><h3>Sticker Studio</h3><p>Make every detail yours</p></div>${ic('chev')}</button>
  ${canImport?`<button class=hm-tool data-act=impackopen>${hmIc('upload')}<div><h3>Bring your own</h3><p>Start from an existing sheet</p></div>${ic('chev')}</button>`:`<button class=hm-tool data-act=nav data-to=create>${hmIc('create')}<div><h3>From a photo</h3><p>Turn a picture into a sticker</p></div>${ic('chev')}</button>`}
  <button class=hm-tool data-act=nav data-to=library>${hmIc('lib')}<div><h3>Your library</h3><p>Every sticker, every pack</p></div>${ic('chev')}</button></div>
 <section class=hm-disc id=hm-disc><div class=hm-head><div><h2>Made by you. Ready to express.</h2><p>Your characters, your reactions, your little universe.</p></div><button class=hm-link data-act=hmfilter data-f=all data-clear=1>View all packs ${ic('chev')}</button></div>
  ${ps.length?`<div class=hm-filters role=group aria-label="Filter packs"><button class=hm-filter data-act=hmfilter data-f=all>All packs</button><button class=hm-filter data-act=hmfilter data-f=animated>Animated</button><button class=hm-filter data-act=hmfilter data-f=static>Static stickers</button><button class=hm-filter data-act=hmfilter data-f=particles>With particles</button></div>
  <div class=hm-gal id=hm-gal></div><p class=hm-empty id=hm-empty role=status hidden>No packs match. Try a different search or filter.</p>`
  :`<div class=hm-none><h3>No packs yet</h3><p>Describe an idea to the AI, or open the Studio: your first pack lands here.</p><button class="btn pri" data-act=hmai>${ic('ai')} Create with AI</button></div><div id=hm-gal hidden></div><p id=hm-empty hidden></p>`}</section>
 <section class=hm-journey><div><div class=hm-eye>An idea is all you need</div><h2>Your imagination.<br>Delivered as a sticker.</h2><p>From the first thought to the final pack, make something that feels like you.</p><button class=hm-link data-act=hmfilm>Watch the film ${ic('chev')}</button></div>
  <div class=hm-steps><article class=hm-step><span class=hm-num>01 / IMAGINE</span>${hmIc('ai')}<h3>Tell your idea</h3><p>Describe a character, a feeling, or a moment.</p></article><article class=hm-step><span class=hm-num>02 / MAKE IT YOURS</span>${hmIc('lib')}<h3>Shape the details</h3><p>Review your stickers. Add motion and a little magic.</p></article><article class=hm-step><span class=hm-num>03 / SHARE</span>${hmIc('telegram')}<h3>Send a little joy</h3><p>Export your pack, ready for your next conversation.</p></article></div></section>
 <footer class=hm-foot><span class=hm-brand><img src=/assets/brand/mirsal-logo.png alt="">mirsal<b>.</b></span><span>Small stickers. Endless expression.</span></footer></div>`;
 const i=$('hm-q');i.oninput=e=>{HM.q=e.target.value;hmGallery()};hmGallery()};
ACT.hmfilter=el=>{HM.filter=el.dataset.f;if(el.dataset.clear){HM.q='';const i=$('hm-q');if(i)i.value=''}hmGallery();
 if(el.dataset.scroll||el.dataset.clear){const d=$('hm-disc');if(d)d.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})}};
/* a clean AI chat: what the logo did before Home (the next message starts a new conversation) */
ACT.hmai=()=>{try{localStorage.setItem('mirsal.ai.sid','')}catch(e){}if(typeof A!=='undefined'){A.sid=null;A.sess=null}
 if(route_==='agent'&&typeof ACT.agnew==='function')ACT.agnew();else location.hash='#/agent'};
ACT.hmfilm=()=>{if(typeof wlOpen==='function')wlOpen()};
/* the home button: the Mirsal logo opens Home (the welcome film opens once per browser session on its own, and from Home's "Watch the film") */
ACT.home=()=>{if(route_==='home'){$('s-home').scrollTo({top:0,behavior:'smooth'});RENDER.home()}else location.hash='#/home'};
