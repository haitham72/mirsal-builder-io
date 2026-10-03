/* Particles in the Studio (docs/effects.md): the batch the Studio presents gets two things, both from this file.
   1. The Particles TAB next to Stickers and Animation: a small guided flow. Pick a pack and how the particles are made (the pack's own stickers: free; drawn by an AI: credits, the price on the button;
      a Kling video: credits), then the stickers burst with them, with live sliders, and Add puts the results into the pack. It is the particle studio's own flow (effects.js: state SP here, FX there;
      every effect function is shared), only smaller; "Open in the particle studio" opens the same effect there (#/effects/E###).
   2. The Particles SECTION under the batch (drawn into #gpart): for each sticker of the batch that is in a library pack, what was made and saved for it (the gallery of the library's sticker view),
      and one line for the stickers that are not in a pack yet. Every particle made is stored in its effect and therefore appears here, "saved under the sticker".
   Nothing is decided here: the engine does it behind /api/effects and /api/packs/{id}/particles. Top-level names in this file start with SP / sp (the scripts share ONE global scope). */
'use strict';
const SPKINDS=[['pack','Pack stickers','Free','The stickers of the pack fly out as the particles. Nothing is drawn and nothing is spent.'],
 ['drawn','Drawn particles','Costs credits','An AI draws a sheet of 4 or 9 different small particles for the burst. The price is on the button before anything is spent.'],
 ['video','Video particles','Costs credits','Kling makes a 3-second clip of bursts on a green screen, 4 cells at a time. The price is on the button before anything is spent.']];
const SPMAX=24;                       // a run takes at most this many stickers (flow/effects.MAX_STICKERS)
const SP=Object.assign(fxNew('sp'),{kind:'pack',src:'own',mode:'sim',selFor:'',t:0});
FXS.sp=SP;
SP.root=()=>$('sp-root');SP.alive=()=>route_==='generate'&&GS.tab==='particles'&&!!$('sp-root');SP.draw=()=>spDraw();
/* the three choices: the pack stickers and the drawn sheet are simulations (mode sim), the video is Kling (mode video); src says where the burst's particles come from */
function spKind(k){SP.kind=k;SP.mode=k==='video'?'video':'sim';SP.src=k==='pack'?'own':k==='drawn'?'drawn':'video'}
try{const s=JSON.parse(localStorage.getItem('mirsal.sp')||'null');if(s){SP.eid=/^E\d+$/.test(s.eid||'')?s.eid:'';SP.pack=typeof s.pack==='string'?s.pack:'';SP.grid=s.grid==='3x3'?'3x3':'2x2';spKind(['pack','drawn','video'].includes(s.kind)?s.kind:'pack')}}catch(e){}
const spSave=()=>{try{localStorage.setItem('mirsal.sp',JSON.stringify({eid:SP.eid,pack:SP.pack,kind:SP.kind,grid:SP.grid}))}catch(e){}};

/* ---------- which library stickers came from a batch (pure): the pack sticker of cell `index` of batch `gid`, a still preferred to an animated one */
const spGid=v=>{const m=String(v==null?'':v).toUpperCase().match(/^G?(\d+)$/);return m?'G'+m[1].padStart(3,'0'):''};
function spLinkIndex(packs,gid){const out={},want=spGid(gid);if(!want)return out;
 for(const p of packs||[])for(const s of p.stickers||[]){const src=s.source||{};if(spGid(src.generation)!==want||!src.index)continue;
  const cur=out[src.index];if(!cur||(cur.sticker.type==='animated'&&s.type!=='animated'))out[src.index]={pack_id:p.id,pack:p.name,sticker:s}}
 return out}
const spHere=(p,gids)=>p.stickers.filter(s=>(gids||[]).includes(spGid((s.source||{}).generation))).length;
/* the stickers a run starts with: the ones of the open batch that are in this pack, else the pack's first ones */
function spPickSel(p,gids){const mine=p.stickers.filter(s=>(gids||[]).includes(spGid((s.source||{}).generation)));return new Set((mine.length?mine:p.stickers).slice(0,SPMAX).map(s=>s.id))}
function spDefaultPack(packs,gids,sesPack){let best=null;for(const p of packs){const n=spHere(p,gids);if(n&&(!best||n>best.n))best={id:p.id,n}}
 if(best)return best.id;if(sesPack&&packs.some(p=>p.id===sesPack))return sesPack;const f=packs.find(p=>p.stickers.length);return f?f.id:''}
const spGids=gs=>gs.map(g=>spGid(g.generation_id));

/* ---------- the tab: setup (pure builder) */
function spSetupHtml(S,packs,gids){const p=packs.find(x=>x.id===S.pack),n=S.sel.size,over=n>SPMAX;
 return `<div class=pwstep><span class=pwn>1</span><b>Choose the pack</b></div>
  <div class=fx-packs>${packs.map(x=>`<button class="fx-pack${x.id===S.pack?' on':''}" data-act=sppack data-id=${esc(x.id)}><span class=fx-cv>${coverMedia(x)}</span><b>${esc(x.name)}</b><small>${x.stickers.length} stickers${spHere(x,gids)?` · ${spHere(x,gids)} from this batch`:''}</small></button>`).join('')||'<div class=mut>Make a pack first: add this batch to a pack (the Pack step).</div>'}</div>
  <div class=pwstep style="margin-top:16px"><span class=pwn>2</span><b>How are the particles made</b></div>
  <div class=sp-modes>${SPKINDS.map(([k,l,tag,txt])=>`<button class="sp-mode${S.kind===k?' on':''}" data-act=spkind data-v=${k} aria-pressed=${S.kind===k}><b>${l}</b><em>${tag}</em><small>${txt}</small></button>`).join('')}</div>
  ${S.kind==='video'?`<div class=row><span class=mut>Cells in one clip</span><div class=tabs style="margin:0;gap:6px"><button class="tab${S.grid==='2x2'?' on':''}" data-act=spgrid data-v=2x2>2 x 2</button><button class="tab${S.grid==='3x3'?' on':''}" data-act=spgrid data-v=3x3>3 x 3</button></div>${S.grid==='3x3'?'<span class=fx-warn>3 x 3 was measured poor: particles cross cells and nothing ends empty.</span>':''}</div>`:''}
  ${p?`<div class=pwstep style="margin-top:16px"><span class=pwn>3</span><b>${S.kind==='pack'?'Which stickers fly out (they are the particles and they burst)':'Which stickers get particles'}</b><button class=link data-act=spall data-v=1>all</button><button class=link data-act=spall data-v=0>none</button></div>
  <div class=fx-sts>${p.stickers.map(s=>`<button class="fx-st${S.sel.has(s.id)?' on':''}" data-act=spst data-id=${esc(s.id)} title="${esc(s.name)}" aria-pressed=${S.sel.has(s.id)}>${media(s)}<span>${esc(s.emoji||'')}</span></button>`).join('')}</div>
  <div class=row><button class="btn pri gbig" data-act=spstart ${n&&!over?'':'disabled'}>${ic('fx')} Continue with ${n} sticker${n===1?'':'s'}</button>${over?`<span class=fx-warn>A run takes at most ${SPMAX} stickers: untick some.</span>`:'<span class=mut>Nothing is drawn or spent yet.</span>'}</div>`:''}`}
const spSetup=gs=>spSetupHtml(SP,LIB.packs.filter(x=>x.stickers.length),spGids(gs));
ACT.sppack=el=>{SP.pack=el.dataset.id;SP.selFor=SP.pack;const p=packById(SP.pack);SP.sel=p?spPickSel(p,spGids(sessionGens())):new Set();spSave();spDraw()};
ACT.spkind=el=>{spKind(el.dataset.v);spSave();spDraw()};
ACT.spgrid=el=>{SP.grid=el.dataset.v;spSave();spDraw()};
ACT.spst=el=>{const i=el.dataset.id;SP.sel.has(i)?SP.sel.delete(i):SP.sel.add(i);spDraw()};
ACT.spall=el=>{const p=packById(SP.pack);SP.sel=el.dataset.v==='1'&&p?new Set(p.stickers.map(s=>s.id)):new Set();spDraw()};
/* the vision model looks at pictures only with the person's yes (asked once, like everywhere): the pack stickers need none */
ACT.spstart=()=>{if(SP.kind!=='pack'&&vlmState()===null){VLM.then=()=>spStart();return dlg(`<h2>Allow AI vision of your stickers?</h2><p class=mut>To choose what bursts out of each sticker and to suggest particles, the pictures are sent to the vision model: the local one (LM Studio) when it is running, otherwise the cloud one if you set it up. You are asked once. Without it a built-in table of common emoji decides.</p>
   <div class=row style="justify-content:flex-end"><button class=btn data-act=spnovlm>Use the table</button><button class="btn pri" data-act=vlmyes>Allow</button></div>`)}
 spStart()};
ACT.spnovlm=()=>{vlmSet('0');closeDlg();spStart()};
async function spStart(){const k=SP.kind,r=await post('/api/effects',{pack_id:SP.pack,sticker_ids:[...SP.sel],mode:k==='video'?'video':'sim',grid:k==='video'?SP.grid:'2x2',note:'',allow_vlm:k==='pack'?false:vlmState()==='1'});
 if(!r.ok)return toast(r.j.error||'Could not start',1);
 fxReset(SP);SP.eid=r.j.id;spSave();await fxLoad(SP);spDraw()}
ACT.spreset=()=>{fxReset(SP);SP.eid='';spSave();spDraw()};

/* ---------- the tab: the effect in progress */
const spKindName=k=>(SPKINDS.find(x=>x[0]===k)||[,'Particles'])[1];
function spHead(e){return `<div class=sp-eh><div><b>${esc(e.pack_name||'')}</b> <span class=mut>· ${esc(spKindName(SP.kind))} · ${esc(e.id)}</span></div>
  <div class=sp-ea><a class=link href="#/effects/${esc(e.id)}" title="The same effect, in the full particle studio">Open in the particle studio</a><button class=link data-act=spreset>Start over</button></div></div>`}
function spBody(gs){const e=SP.rec;let h;
 if(!SP.eid)h=spSetup(gs);
 else if(!e)h='<div class=fx-job><span class=spin></span> <span class=mut>Reading the effect…</span></div>';
 else if(e.status==='NEW')h=spHead(e)+'<div class=fx-job style="margin-top:12px"><span class=spin></span> <b>Looking at your stickers…</b> <span class=mut>choosing what bursts out of each</span></div>';
 else if(e.status==='ERROR')h=spHead(e)+`<div class=warn>${esc(e.error||'The analysis failed')} <button class=btn data-act=spreset>Back</button></div>`;
 else h=spHead(e)+fxBody(SP,e);
 return `<div class=sp-h><h2>${ic('fx')} Particles</h2><span class=mut>Give the stickers of a pack a burst of particles, like the effect Telegram plays when you press an emoji. Whatever you make is saved under its sticker.</span></div>${h}`}
function spDraw(){const el=$('sp-root');if(!el)return;el.innerHTML=spBody(sessionGens());SP.last=fxSig(SP);fxAfterDraw(SP)}
function spView(gs){if(!SP.pack||!packById(SP.pack))SP.pack=spDefaultPack(LIB.packs,spGids(gs),SES.pack);
 if(SP.selFor!==SP.pack){SP.selFor=SP.pack;const p=packById(SP.pack);SP.sel=p?spPickSel(p,spGids(gs)):new Set()}
 if(SP.eid&&Date.now()-SP.t>3000){SP.t=Date.now();fxLoad(SP).then(()=>{if(SP.alive()&&fxSig(SP)!==SP.last)SP.draw()})}        // coming back to the tab: read the effect again
 return `<section class="gplan sp fx" id=sp-root data-fxx=sp>${spBody(gs)}</section>`}
/* the tab is part of the Studio's header and body: generate.js owns both, so they are wrapped here (the way live.js wraps drawRail) instead of being edited */
const spWasBody=gbodyHtml;
gbodyHtml=function(gs,c){return GS.tab==='particles'?spView(gs):spWasBody(gs,c)};
/* the tab's step goes right after Animation; the steps after it are numbered again (Pack becomes 6) */
const spMade=gs=>{let n=0;for(const l of gs.map(g=>spLinkIndex(LIB.packs,g.generation_id)))for(const x of Object.values(l)){const c=(PKPT.c[x.pack_id]||{})[x.sticker.id];if(c)n+=c.created+c.saved}return n};
function spSteps(h,gs){const at=h.indexOf('data-act=gadd'),i=at<0?-1:h.lastIndexOf('<button class="gst',at);if(i<0)return h;
 const n=spMade(gs),cur=GS.tab==='particles',btn=`<button class="gst ${n?'done':'todo'} ${cur?'cur':''}" data-act=gtab data-t=particles><span class=gsm>${n?ic('check'):5}</span><span class=gsl><b>Particles</b><small>${n?`${n} made`:'None yet'}</small></span></button>`;
 return(h.slice(0,i)+btn+h.slice(i)).split('<button class="gst').map((x,k)=>k?x.replace(/<span class=gsm>\d<\/span>/,`<span class=gsm>${k}</span>`):x).join('<button class="gst')}
const spWasSteps=stepsHtml;
stepsHtml=function(c){return spSteps(spWasSteps(c),c.gs)};
/* "Make particles" for one sticker (the section below, the library's sticker view in the Studio) and "Create particles for pack" */
const spShowTab=()=>{GS.tab='particles';glast='';if(typeof tick==='function')tick(true);const r=document.getElementById('gres');if(r)r.scrollIntoView({behavior:'smooth',block:'start'})};
function spOpenFor(pack,sid){fxReset(SP);SP.eid='';const p=packById(pack);SP.pack=pack;SP.selFor=pack;SP.sel=sid?new Set([sid]):p?spPickSel(p,spGids(sessionGens())):new Set();spSave();spShowTab()}
ACT.spopen=()=>spShowTab();
ACT.spmake=el=>spOpenFor(el.dataset.p,el.dataset.s);

/* ---------- the section under the batch: the particles of each of its stickers that is in a pack (pure builder + a loader) */
const SPS={sig:'',busy:false,html:'',el:null,loaded:false};
const spThumb=(gid,c)=>c.png?`<img src="/out/${esc(gid)}/${esc(c.png)}" alt="" loading=lazy>`:'';
/* b: {gid, cells: [{index, key, png, link: {pack_id, pack, sticker} | null, n: particles made + saved, det: the sticker's answer | null}]} */
function spSecBatchHtml(b,many){const got=b.cells.filter(c=>c.link&&c.n>0),none=b.cells.filter(c=>c.link&&!c.n),free=b.cells.filter(c=>!c.link);
 return `<div class=sp-bt>${many?`<div class=sp-bh><b>${esc(b.gid)}</b></div>`:''}
  ${got.map(c=>`<div class=sp-st><div class=sp-sth><span class=sp-th>${spThumb(b.gid,c)}</span><b>S${c.index}${c.key?' · '+esc(String(c.key).replace(/_/g,' ')):''}</b><span class=mut>in <button class=link data-act=ptsaved data-id=${esc(c.link.pack_id)}>${esc(c.link.pack)}</button></span><button class="btn sm" data-act=spmake data-p=${esc(c.link.pack_id)} data-s=${esc(c.link.sticker.id)}>${ic('fx')} Make more</button></div>${ptBody(c.det,{id:c.link.sticker.id,pack_id:c.link.pack_id})}</div>`).join('')}
  ${none.length?`<div class=sp-line><span class=mut>No particles yet, click one to make some:</span>${none.map(c=>`<button class=sp-chip data-act=spmake data-p=${esc(c.link.pack_id)} data-s=${esc(c.link.sticker.id)} title="Make particles for S${c.index} (in ${esc(c.link.pack)})"><span class=sp-th>${spThumb(b.gid,c)}</span>S${c.index}</button>`).join('')}</div>`:''}
  ${free.length?`<div class=sp-line><span class=sp-ths>${free.map(c=>`<span class=sp-th title="S${c.index}">${spThumb(b.gid,c)}</span>`).join('')}</span><span class=mut>Add to a pack to give ${free.length===1?'it':'them'} particles</span></div>`:''}</div>`}
const spSecHtml=bs=>bs.length?`<section class=sp-sec><div class=sp-sech><h2>${ic('fx')} Particles</h2><span class=mut>What was made for each sticker of this batch that is in a pack. Saved results show here.</span><button class="btn sm pri" data-act=spopen>${ic('fx')} Create particles for pack</button></div>${bs.map(b=>spSecBatchHtml(b,bs.length>1)).join('')}</section>`:'';
/* the data of the section from what the Studio and the library already hold */
function spSecData(){const out=[];for(const id of SES.gens){const g=GM.get(id);if(!g)continue;const ix=spLinkIndex(LIB.packs,g.generation_id);
  out.push({gid:g.generation_id,cells:g.stickers.filter(t=>t.status==='READY'&&t.png&&(t.review||{}).still!=='REJECTED').map(t=>{const l=ix[t.index]||null,c=l?(PKPT.c[l.pack_id]||{})[l.sticker.id]:null;
   return{index:t.index,key:t.key,png:t.png,link:l,n:c?c.created+c.saved:0,det:l?PKPT.d[l.sticker.id]||null:null}})})}
 return out}
function spSecDraw(){const el=$('gpart');if(!el)return;const html=spSecHtml(spSecData());if(html!==SPS.html||el!==SPS.el){SPS.html=html;SPS.el=el;el.innerHTML=html}}      // a new container (the Studio was left and opened again) is filled again
/* read what each linked sticker has (one cheap request per pack for the counts, the full answer only for a sticker that has some) and redraw when something changed */
async function spSecSync(force){if(SPS.busy||!$('gpart'))return;SPS.busy=true;
 try{const data=spSecData(),links=data.flatMap(b=>b.cells.filter(c=>c.link).map(c=>c.link)),sig=data.map(b=>b.gid+':'+b.cells.map(c=>c.index+(c.link?c.link.sticker.id:'')).join(',')).join('|');
  let changed=force||sig!==SPS.sig||!SPS.loaded;SPS.sig=sig;
  for(const pid of new Set(links.map(l=>l.pack_id))){const r=await api(`/api/packs/${pid}/particles`);if(r.ok&&JSON.stringify(r.j)!==JSON.stringify(PKPT.c[pid]||null)){PKPT.c[pid]=r.j;changed=true}}
  if(changed){await Promise.all(links.filter(l=>{const c=(PKPT.c[l.pack_id]||{})[l.sticker.id];return c&&c.created+c.saved>0}).map(l=>ptLoad({pack_id:l.pack_id,id:l.sticker.id})))}
  SPS.loaded=data.length>0;spSecDraw()}
 finally{SPS.busy=false}}
setInterval(()=>{if(route_==='generate'&&!document.hidden)spSecSync()},2500);
