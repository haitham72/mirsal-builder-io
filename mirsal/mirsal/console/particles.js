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
 ['existing','Use an existing set','Free','Pick a particle set you already saved and put it on this pack. Nothing is drawn and nothing is spent.']];
const SPMAX=24;                       // a run takes at most this many stickers (flow/effects.MAX_STICKERS)
const SP=Object.assign(fxNew('sp'),{kind:'pack',src:'own',mode:'sim',selFor:'',t:0});
FXS.sp=SP;
SP.root=()=>$('sp-root');SP.alive=()=>route_==='generate'&&GS.tab==='particles'&&!!$('sp-root');SP.draw=()=>spDraw();
/* the three choices: the pack stickers and the drawn sheet are simulations (mode sim), the video is Kling (mode video, pro studio only); src says where the burst's particles come from */
function spKind(k){SP.kind=k;SP.mode=k==='video'?'video':'sim';SP.src=k==='pack'?'own':k==='drawn'?'drawn':k==='existing'?'existing':'video'}
try{const s=JSON.parse(localStorage.getItem('mirsal.sp')||'null');if(s){SP.eid=/^E\d+$/.test(s.eid||'')?s.eid:'';SP.pack=typeof s.pack==='string'?s.pack:'';SP.grid=s.grid==='3x3'?'3x3':'2x2';spKind(['pack','drawn','existing'].includes(s.kind)?s.kind:'pack')}}catch(e){}
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
  ${!p?'<div class=mut>Make a pack first: add this batch to a pack (the Pack step).</div>':S.kind==='existing'?`<div class=pwstep style="margin-top:16px"><span class=pwn>2</span><b>Which set goes on ${esc(p.name)}</b></div>${spExistingHtml(S)}`
  :`<div class=pwstep style="margin-top:16px"><span class=pwn>3</span><b>${S.kind==='pack'?'Which stickers fly out (they are the particles and they burst)':'Which stickers get particles'}</b><button class=link data-act=spall data-v=1>all</button><button class=link data-act=spall data-v=0>none</button></div>
  <div class=fx-sts>${p.stickers.map(s=>`<button class="fx-st${S.sel.has(s.id)?' on':''}" data-act=spst data-id=${esc(s.id)} title="${esc(s.name)}" aria-pressed=${S.sel.has(s.id)}>${media(s)}<span>${esc(s.emoji||'')}</span></button>`).join('')}</div>
  <div class=row><button class="btn pri gbig" data-act=spstart ${n&&!over?'':'disabled'}>${ic('fx')} Continue with ${n} sticker${n===1?'':'s'}</button>${over?`<span class=fx-warn>A run takes at most ${SPMAX} stickers: untick some.</span>`:'<span class=mut>Nothing is drawn or spent yet.</span>'}</div>`}`}
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

/* ---------- Library > Particles: every durable set as a card (docs/particles_plan.md 5). Reads GET /api/particles; writes rename/assign/unassign/duplicate/delete/restore.
   The trash is listed (GET /api/particles/deleted): Restore is offered on the notice right after a delete AND from the "Deleted" list under the sets, long after. One set belongs to pack(s): the card says
   "used in: A, B" or "stand-alone", never per sticker. */
const SPL={sets:null,busy:false,open:'',detail:{},pick:{},deleted:null,trash:null,poll:0};
const spSetsForget=()=>{SPL.sets=null;SPL.detail={};SPL.open='';SPL.deleted=null;SPL.trash=null};
const spCredits=n=>n==null||+n===0?'nothing spent yet':`about ${+n} credit${+n===1?'':'s'} spent`;
function spSetCard(s){const cells=s.cells||[],picked=cells.filter(c=>c.picked),strip=picked.slice(0,8),used=s.used_in||[],open=SPL.open===s.id;
 return `<div class=ps-card data-ps=${esc(s.id)}>
  <div class=ps-strip>${strip.map(c=>`<span class=ps-cell title="${esc(c.key||('cell '+c.n))}">${c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:'<span class=mut>·</span>'}</span>`).join('')||'<span class=mut>No cells yet</span>'}${picked.length>8?`<span class=ps-more>+${picked.length-8}</span>`:''}</div>
  <div class=ps-main><b>${esc(s.name||s.id)}</b><small class=mut>${esc(s.id)} · ${s.n_cells} cell${s.n_cells===1?'':'s'} · ${picked.length} picked${s.kind?' · '+esc(s.kind):''}</small>
  <div class=ps-used>${used.length?`used in: ${used.map(p=>esc(p.name||p.id)).join(', ')}`:'stand-alone'}</div>
  <div class=ps-cost>${esc(spCredits(s.credits))}</div>
  <div class=ps-act><button class="btn sm" data-act=psopen data-id=${esc(s.id)}>${open?'Close':'Open'}</button><button class="btn sm" data-act=psassign data-id=${esc(s.id)}>Assign</button><button class="btn sm" data-act=psdup data-id=${esc(s.id)}>Duplicate</button><button class="btn sm" data-act=psrename data-id=${esc(s.id)}>Rename</button><button class="btn sm dng" data-act=psdel data-id=${esc(s.id)}>Delete</button></div>
  ${open?spSetDetail(s):''}</div></div>`}
function spSetDetail(s){const d=SPL.detail[s.id],full=d&&d.id===s.id?d:s,cells=full.cells||[],els=full.elements||[],mo=full.motion||{},src=full.source||{},pick=SPL.pick[s.id]||null;
 return `<div class=ps-det>
  ${els.length?`<div class=ps-els>${els.map(x=>`<span class=fx-chip>${esc(x)}</span>`).join('')}</div>`:''}
  ${src&&src.kind?`<div class=mut>from ${esc(src.kind)}${src.effect?` · ${esc(src.effect)}`:''}${src.generation?` · ${esc(src.generation)}`:''}</div>`:''}
  ${mo&&mo.preset?`<div class=mut>motion: ${esc(mo.preset)}</div>`:''}
  ${(full.used_in||[]).map(p=>`<div class=ps-on><span class=mut>on ${esc(p.name||p.id)}</span><button class=link data-act=psunassign data-id=${esc(s.id)} data-p=${esc(p.id)}>take off</button></div>`).join('')}
  ${cells.length?`<div class=ps-cells>${cells.map(c=>{const on=pick?pick.has(c.n):!!c.picked;
   return `<button class="ps-pick${on?' on':''}" data-act=pspickcell data-id=${esc(s.id)} data-n=${c.n} aria-pressed=${on} title="cell ${c.n}${on?' (kept)':' (not kept)'}">${c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:`<span class=mut>${c.missing?'missing':'no file'}</span>`}<span class=ps-tick>${on?'✓':''}</span></button>`}).join('')}</div>
  ${pick?`<div class=row><button class="btn pri sm" data-act=pspicksave data-id=${esc(s.id)}>Keep ${pick.size} picked</button><button class=link data-act=pspickcancel data-id=${esc(s.id)}>cancel</button></div>`:`<div class=mut>Tick the cells to keep.</div>`}`:''}
  ${spMoreHtml(full)}
  ${spBurstHtml(full)}
 </div>`}
function spLibHtml(){const sets=SPL.sets;
 if(!sets)return `<div class=pk-pt-load><div class=spin></div><span class=mut>Reading the particle sets…</span></div>`;
 const del=SPL.deleted?`<div class=ps-del><span>Deleted ${esc(SPL.deleted.name)}: it is in the trash, nothing is destroyed.</span><button class="btn sm" data-act=psrestore data-id=${esc(SPL.deleted.id)}>Restore</button></div>`:'',trash=spTrashHtml(SPL.trash);
 if(!sets.length)return `${del}<div class="card" style="text-align:center;padding:40px"><h2>No particle sets yet</h2><p class=mut>A particle set belongs to a pack: make particles for a pack, then keep them with “Use as particle set”.</p><button class="btn pri" data-act=spopen>${ic('fx')} Make particles</button></div>${trash}`;
 return `${del}<div class=ps-lib>${sets.map(spSetCard).join('')}</div><div class=row><button class="btn pri" data-act=spopen>${ic('fx')} Make particles</button></div>${trash}`}
function spLibRefresh(){if(typeof route_!=='undefined'&&route_==='library'&&typeof LIBTAB!=='undefined'&&LIBTAB==='particles'&&typeof RENDER!=='undefined'&&RENDER.library)RENDER.library();
 if(typeof route_!=='undefined'&&route_==='pack'&&typeof drawPack==='function')drawPack()}
async function spLibSync(force){if(SPL.busy||(SPL.sets&&!force))return;SPL.busy=true;
 try{const r=await api('/api/particles');if(r.ok){SPL.sets=r.j.sets||[];
   for(const s of SPL.sets){const d=SPL.detail[s.id];if(d&&d.n_cells!==s.n_cells)delete SPL.detail[s.id]}          // cells arrived since the card was opened: it is read again
   const t=await api('/api/particles/deleted');if(t.ok)SPL.trash=t.j.sets||[];spLibRefresh();spPoll()}}finally{SPL.busy=false}}
/* a sheet being drawn for a set (Generate more) arrives on its own: while any set is drawing, the list (or the pack's sets) is read again every few seconds */
function spPoll(){clearTimeout(SPL.poll);
 const busy=(SPL.sets||[]).some(s=>s.drawing)||(typeof PKPT!=='undefined'&&Object.values(PKPT.sets||{}).some(l=>(l||[]).some(s=>s&&s.drawing)));
 if(!busy)return;
 SPL.poll=setTimeout(async()=>{if(typeof route_==='undefined')return;
  if(route_==='library'&&typeof LIBTAB!=='undefined'&&LIBTAB==='particles')await spLibSync(true);
  else if(route_==='pack'&&typeof ptCounts==='function'&&typeof PACK_ID!=='undefined'){await ptCounts(PACK_ID);if(PKPT.sets[PACK_ID]&&PKPT.sets[PACK_ID].length)spLibSync(true)}
  spPoll()},2500)}
ACT.psopen=async el=>{const id=el&&el.dataset.id;if(!id){spShowTab();return}SPL.open=SPL.open===id?'':id;
 if(SPL.open&&!SPL.detail[id]){const r=await api('/api/particles/'+id);if(r.ok)SPL.detail[id]=r.j}
 spLibRefresh();if(SPL.open===id){spMoreEstimate(id);spBurstPreview(id)}};
ACT.psassign=el=>{const s=(SPL.sets||[]).find(x=>x.id===el.dataset.id);if(!s)return;const packs=(typeof LIB!=='undefined'&&LIB.packs)||[],have=new Set(s.packs||[]);
 dlg(`<h2>Assign “${esc(s.name||s.id)}”</h2><div class=mut style="margin-bottom:10px">Every sticker of a ticked pack bursts with these particles. Unticking takes the set off the pack: the set stays.</div>
  ${packs.map(p=>`<label class=ps-pack><input type=checkbox data-psapack=${esc(p.id)} ${have.has(p.id)?'checked':''}> ${esc(p.name)} <small class=mut>${p.stickers.length} stickers</small></label>`).join('')||'<div class=mut>No packs yet.</div>'}
  <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=psassignsave data-id=${esc(s.id)}>Save</button></div>`)};
ACT.psassignsave=async el=>{const id=el.dataset.id,add=[...document.querySelectorAll('[data-psapack]')].filter(c=>c.checked).map(c=>c.dataset.psapack),
  cur=(((SPL.sets||[]).find(x=>x.id===id))||{packs:[]}).packs||[],drop=cur.filter(p=>!add.includes(p)),ops=[];
 if(add.length&&add.some(p=>!cur.includes(p)))ops.push(post(`/api/particles/${id}/assign`,{packs:add}));
 if(drop.length)ops.push(post(`/api/particles/${id}/unassign`,{packs:drop}));
 if(!ops.length){closeDlg();return}
 const rs=await Promise.all(ops),bad=rs.find(r=>!r.ok);if(bad)return toast(bad.j.error||'Could not assign',1);
 closeDlg();toast('Assigned');spLibSync(true)};
ACT.psunassign=async el=>{const r=await post(`/api/particles/${el.dataset.id}/unassign`,{packs:[el.dataset.p]});if(!r.ok)return toast(r.j.error||'Could not take it off',1);toast('The set stays: it is only off that pack');spLibSync(true)};
ACT.psdup=async el=>{const r=await post(`/api/particles/${el.dataset.id}/duplicate`,{});if(!r.ok)return toast(r.j.error||'Could not duplicate',1);toast(`Duplicated as ${r.j.id}`);spLibSync(true)};
ACT.psrename=el=>{const s=(SPL.sets||[]).find(x=>x.id===el.dataset.id);askText('Rename particle set',s?(s.name||s.id):'',async n=>{const r=await post(`/api/particles/${el.dataset.id}`,{name:n});if(!r.ok)return toast(r.j.error,1);spLibSync(true)})};
ACT.psdel=el=>{const s=(SPL.sets||[]).find(x=>x.id===el.dataset.id);if(!s)return;
 confirmDlg(`Delete the particle set “${s.name||s.id}”? It moves to the trash: nothing is destroyed, and Restore brings it back.`,()=>spDelGo(s.id,false),'Delete')};
async function spDelGo(id,confirm){const r=await post(`/api/particles/${id}/delete`,confirm?{confirm:true}:{});
 if(!r.ok&&r.status===409){closeDlg();confirmDlg(`${r.j.error||'This set is in use.'} Delete it anyway?`,()=>spDelGo(id,true),'Delete anyway');return}
 if(!r.ok)return toast(r.j.error||'Could not delete',1);
 const s=(SPL.sets||[]).find(x=>x.id===id);SPL.deleted={id,name:s?(s.name||id):id};if(SPL.open===id)SPL.open='';closeDlg();spLibSync(true)}
ACT.psrestore=async el=>{const r=await post(`/api/particles/${el.dataset.id}/restore`,{});if(!r.ok)return toast(r.j.error||'Could not restore',1);SPL.deleted=null;toast(`Restored ${r.j.id||el.dataset.id}`);spLibSync(true)};
ACT.pspickcell=el=>{const id=el.dataset.id,n=+el.dataset.n;let p=SPL.pick[id];
 if(!p){const s=SPL.detail[id]||(SPL.sets||[]).find(x=>x.id===id)||{cells:[]};p=SPL.pick[id]=new Set((s.cells||[]).filter(c=>c.picked).map(c=>c.n))}
 p.has(n)?p.delete(n):p.add(n);spLibRefresh()};
ACT.pspickcancel=el=>{delete SPL.pick[el.dataset.id];spLibRefresh()};
ACT.pspicksave=async el=>{const id=el.dataset.id,pick=[...((SPL.pick[id])||[])];
 const r=await post(`/api/particles/${id}`,{picked});if(!r.ok)return toast(r.j.error||'Could not keep them',1);
 delete SPL.pick[id];SPL.detail[id]=r.j;toast(`Keeping ${pick.length} cells`);spLibSync(true)};
/* ---------- the trash: every deleted set with Restore, long after the delete (nothing is destroyed on a click) */
function spTrashHtml(list){if(!list||!list.length)return '';
 return `<details class=ps-trash><summary>Deleted (${list.length}) · nothing is destroyed: Restore brings a set back</summary>${list.map(s=>{
  const strip=(s.cells||[]).filter(c=>c.picked).slice(0,4),was=(s.used_in||[]).filter(p=>!p.missing);
  return `<div class=ps-trow data-pst=${esc(s.id)}><span class=ps-strip>${strip.map(c=>`<span class=ps-cell>${c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:''}</span>`).join('')}</span>
   <b>${esc(s.name||s.id)}</b><small class=mut>${esc(s.id)} · ${s.n_cells} cell${s.n_cells===1?'':'s'} · ${was.length?`was on ${was.map(p=>esc(p.name||p.id)).join(', ')}`:'was stand-alone'}</small>
   <button class="btn sm" data-act=psrestore data-id=${esc(s.id)}>Restore</button></div>`}).join('')}</details>`}

/* ---------- Generate more (docs/particles_plan.md 4.8): draw another sheet for the set; its cut cells are ADDED, nothing it has is changed.
   POST /api/particles/{id}/more {grid, elements, estimate:true} is the free quote, {grid, elements, go:true} the click. The price is on its own line, never inside the button. */
const SPM={};                                   // set id -> {grid, chosen[], extra[], est{key: {credits, error}}, busy: the key being priced}
const spMoreN=m=>m.grid==='3x3'?9:4;
const spMoreKey=m=>m.grid+'|'+m.chosen.join('|');
function spMoreState(s){let m=SPM[s.id];if(!m)m=SPM[s.id]={grid:'2x2',chosen:null,extra:[],est:{},busy:0};if(m.chosen===null)m.chosen=(s.elements||[]).slice(0,spMoreN(m));return m}
const spMoreNames=(s,m)=>[...new Set([...(s.elements||[]),...m.extra,...m.chosen])];
function spFind(id){const hit=(SPL.detail||{})[id]||(SPL.sets||[]).find(x=>x.id===id);if(hit)return hit;
 if(typeof PKPT!=='undefined')for(const l of Object.values(PKPT.sets||{}))for(const x of l||[])if(x&&x.id===id)return x;return null}
const spSheetWords=sh=>{const n=(sh.appended||[]).length,e=(sh.skipped||[]).length;
 return sh.status==='REQUESTED'?`Waiting for the sheet (${sh.job})…`:sh.status==='DRAWN'?`Cutting the particles (${sh.generation})…`
  :sh.status==='DONE'?`Sheet ${sh.n}: ${n} particle${n===1?'':'s'} added${e?` (${e} cell${e===1?'':'s'} came out empty)`:''}`
  :sh.status==='FAILED'?`Sheet ${sh.n} failed: ${sh.error||'the job failed'}. Draw it again below.`
  :sh.status==='NO_CELLS'?`Sheet ${sh.n} came back with no usable cell. ${sh.error||''}`:`Sheet ${sh.n}: ${String(sh.status||'').toLowerCase()}`};
function spMoreHtml(s){const m=spMoreState(s),N=spMoreN(m),est=m.est[spMoreKey(m)],names=spMoreNames(s,m),busy=!!s.drawing,sheets=(s.sheets||[]).slice().reverse().slice(0,5),ok=!busy&&m.chosen.length&&est&&est.credits!=null;
 return `<div class=ps-gen data-psgen=${esc(s.id)}>
  <div class=ps-genh><b>Generate more</b><span class=mut>Draw another sheet of particles and add its cells to this set. The cells you have stay exactly as they are.</span></div>
  ${sheets.map(sh=>`<div class="ps-sheet ${esc(String(sh.status||'').toLowerCase())}">${['REQUESTED','DRAWN'].includes(sh.status)?'<span class=spin></span> ':''}<span>${esc(spSheetWords(sh))}</span>${sh.status==='NO_CELLS'&&sh.generation?`<button class="btn sm" data-act=openstudio data-gen=${esc(sh.generation)} data-i=1 title="Open the batch in the Studio: a sheet without a green screen has one free “Cut it anyway”">Open ${esc(sh.generation)}</button>`:''}</div>`).join('')}
  <div class=row><span class=mut>Particles on the sheet</span><div class=tabs style="margin:0;gap:6px"><button class="tab${m.grid==='2x2'?' on':''}" data-act=psmoregrid data-id=${esc(s.id)} data-v=2x2>2 x 2 · 4</button><button class="tab${m.grid==='3x3'?' on':''}" data-act=psmoregrid data-id=${esc(s.id)} data-v=3x3>3 x 3 · 9</button></div></div>
  <div class=fx-opts>${names.map(n=>`<button class="fx-opt${m.chosen.includes(n)?' on':''}" data-act=psmorechip data-id=${esc(s.id)} data-v="${esc(n)}" aria-pressed=${m.chosen.includes(n)}>${esc(n)}</button>`).join('')}</div>
  <div class=row><input type=text class=fx-add data-psmoreown=${esc(s.id)} placeholder="add your own" maxlength=40 aria-label="Add your own particle"><button class="btn sm" data-act=psmoreadd data-id=${esc(s.id)}>Add</button><small class=mut>${m.chosen.length} of ${N} chosen${m.chosen.length&&m.chosen.length<N?' · fewer is fine, the sheet repeats them in other sizes and angles':''}</small></div>
  <div class=fx-price data-psmoreprice>${!m.chosen.length?'':est?(est.credits!=null?`about ${est.credits} credit${est.credits===1?'':'s'}`:esc(est.error||'The price is not available.')):'about to be priced…'}</div>
  <div class=row><button class="btn pri" data-act=psmoredraw data-id=${esc(s.id)} ${ok?'':'disabled'}>${ic('fx')} Draw ${N} more particles</button><span class=mut>${busy?'A sheet is being drawn for this set.':'Nothing is spent until you press the button.'}</span></div></div>`}
async function spMoreEstimate(id){const s=spFind(id);if(!s)return;const m=spMoreState(s),k=spMoreKey(m);if(!m.chosen.length||m.est[k]||m.busy===k)return;m.busy=k;
 const r=await post(`/api/particles/${id}/more`,{grid:m.grid,elements:m.chosen,estimate:true});m.busy=0;
 m.est[k]=r.ok?{credits:r.j.credits!=null?r.j.credits:null,error:r.j.cost_error||(r.j.credits==null?'The price is not available.':null)}:{credits:null,error:r.j.error||'The price is not available.'};spLibRefresh()}
ACT.psmoregrid=el=>{const s=spFind(el.dataset.id);if(!s)return;const m=spMoreState(s);m.grid=el.dataset.v==='3x3'?'3x3':'2x2';m.chosen=m.chosen.slice(0,spMoreN(m));spLibRefresh();spMoreEstimate(s.id)};
ACT.psmorechip=el=>{const s=spFind(el.dataset.id);if(!s)return;const m=spMoreState(s),v=el.dataset.v,i=m.chosen.indexOf(v);
 if(i>=0)m.chosen.splice(i,1);else if(m.chosen.length>=spMoreN(m))return toast(`A ${m.grid==='3x3'?'3 x 3':'2 x 2'} sheet holds ${spMoreN(m)}: take one off first`,1);else m.chosen.push(v);
 spLibRefresh();spMoreEstimate(s.id)};
function spMoreAdd(id,v){const s=spFind(id);v=String(v||'').trim().slice(0,40);if(!s||!v)return;const m=spMoreState(s);
 if(!spMoreNames(s,m).includes(v))m.extra.push(v);if(!m.chosen.includes(v)&&m.chosen.length<spMoreN(m))m.chosen.push(v);spLibRefresh();spMoreEstimate(id)}
ACT.psmoreadd=el=>{const i=document.querySelector(`[data-psmoreown="${el.dataset.id}"]`);spMoreAdd(el.dataset.id,i?i.value:'')};
document.addEventListener('keydown',e=>{const t=e.target;if(e.key==='Enter'&&t&&t.dataset&&t.dataset.psmoreown){e.preventDefault();spMoreAdd(t.dataset.psmoreown,t.value)}});
ACT.psmoredraw=async el=>{const id=el.dataset.id,s=spFind(id);if(!s)return;const m=spMoreState(s),est=m.est[spMoreKey(m)];if(!est||est.credits==null||!m.chosen.length)return;el.disabled=true;
 const r=await post(`/api/particles/${id}/more`,{grid:m.grid,elements:m.chosen,go:true});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not start',1)}
 toast(`Drawing ${spMoreN(m)} more particles: ${r.j.estimate!=null?r.j.estimate+' credits':'the price is in your ledger'}`);delete SPL.detail[id];m.est={};spLibSync(true);
 if(typeof route_!=='undefined'&&route_==='pack'&&typeof ptCounts==='function'&&typeof PACK_ID!=='undefined')ptCounts(PACK_ID)};
/* ---------- the burst maker: Motion and Finish of the wizard, for a SET and a PACK (docs/particles_plan.md section 4, docs/particles_plan.md 4.6-4.7).
   ONE preview for the whole pack (not a row per sticker): the five presets, Energy / Float / Swirl (count and spin under Advanced), the particle size, then Render (the final 512 px WebM, checked) and
   Add (an animated sticker of the pack). Everything calls POST /api/particles/{id}/preview | render | add; the same panel sits in the open set card (Library and the pack's studio) and in the wizard
   once the run has been saved as a set. It redraws only itself ([data-psb]), so a slider never moves the rest of the page. A burst is free: there is no price anywhere. */
const SPB={};                                   // set id -> {pack, hint, preset, par{touched sliders only}, shown{what the server used}, pv, size{px,scale}, pvT, busy, again}
const SPBS={};                                  // set id -> the set last drawn, so a partial redraw has it
const spHint=()=>typeof route_!=='undefined'&&route_==='pack'&&typeof PACK_ID!=='undefined'?PACK_ID:'';
function spBurstState(s,hint){let b=SPB[s.id];if(!b)b=SPB[s.id]={pack:'',hint:'',preset:'',par:{},shown:{},pv:'',pvT:0,busy:0,again:0,size:{px:100,scale:1}};
 if(hint&&b.hint!==hint){b.pack=hint;b.hint=hint}else if(!b.pack)b.pack=(s.packs||[])[0]||'';return b}
const spBurstSize=b=>({sprite_px:b.size.px,scale:b.size.scale});
const spPackName=(s,id)=>{const p=typeof packById==='function'?packById(id):null;return p?p.name:((s.used_in||[]).find(x=>x.id===id)||{}).name||id};
function spBSlider(id,b,k){const f=FXSL.find(x=>x[0]===k),v=b.par[k]!==undefined?b.par[k]:b.shown[k];
 return `<label class=fx-sl><span>${f[1]}</span><input type=range min=${f[2]} max=${f[3]} step=${f[4]} value="${v??''}" data-psbp=${k} data-id=${esc(id)} aria-label="${f[1]}"><output>${v??''}</output></label>`}
function spBurstCard(s,b,r){const ok=r.status==='READY'&&!!r.url,ws=(r.warnings||[]).map(fxWords),bl=(r.blocks||[]).map(fxWords),pk=spPackName(s,b.pack);
 return `<div class="ps-br${ok?'':' bad'}" data-psr=${esc(r.id)}><div class=pk-pt-m>${r.url?`<video src="${esc(r.url)}" autoplay loop muted playsinline preload=metadata></video>`:'<span class=mut>no file</span>'}</div>
  <div class=pk-pt-id><b>${esc(r.id)} · ${esc(r.preset||'')}</b><small>${Math.round((r.bytes||0)/1024)} KB · ${esc(String(r.status||'').toLowerCase())}</small></div>
  ${bl.map(w=>`<span class="fx-w bad">${esc(w)}</span>`).join('')}${ws.map(w=>`<span class=fx-w>${esc(w)}</span>`).join('')}
  ${r.added_to?`<small class=mut>in ${esc(spPackName(s,r.added_to))}</small>`:ok?`${ws.length?'<small class=mut>Warnings are only warnings: you decide.</small>':''}<button class="btn sm pri" data-act=psbadd data-id=${esc(s.id)} data-r=${esc(r.id)} data-p=${esc(b.pack)}>${ws.length?'Add anyway':'Add to '+esc(pk)}</button>`:''}</div>`}
function spBurstHtml(s){SPBS[s.id]=s;const b=spBurstState(s,spHint()),own=s.packs||[],kind=(s.source||{}).kind,has=(s.n_picked||0)>0||kind==='stickers',id=esc(s.id);
 const head=`<div class=ps-genh><b>Make a burst</b><span class=mut>What Telegram plays when someone reacts with an emoji of the pack. One preview, for the whole pack.</span></div>`;
 if(!has)return `<div class=ps-burst data-psb=${id}>${head}<div class=mut>This set has no particles yet. Draw some with Generate more above, then give them motion here.</div></div>`;
 const choose=own.length===1?`<b>for ${esc(spPackName(s,own[0]))}</b>`:`<label class=row><span class=mut>for</span><select data-psbpack=${id} aria-label="The pack this burst is for">${b.pack?'':'<option value="" selected>Choose a pack…</option>'}${(own.length?own:((typeof LIB!=='undefined'&&LIB.packs)||[]).map(p=>p.id)).map(pid=>`<option value="${esc(pid)}"${pid===b.pack?' selected':''}>${esc(spPackName(s,pid))}</option>`).join('')}</select></label>`;
 const rs=(Array.isArray(s.renders)?s.renders:[]).filter(r=>r.pack_id===b.pack).slice().reverse();
 return `<div class=ps-burst data-psb=${id}>${head}
  <div class=row>${choose}${kind==='stickers'&&!(s.n_cells>0)?'<span class=mut>the pack’s own stickers fly out as the particles</span>':''}</div>
  <div class=ps-sim><div class=fx-pvbox><img id=psbpv-${id} ${b.pv?`src="${esc(b.pv)}"`:''} alt="">${b.pv?'':'<span class=spin></span>'}<small>${esc(s.name||s.id)}</small></div>
   <div class=fx-ctl><div class=fx-pre>${FXPRESETS.map(n=>`<button class="tab${b.preset===n?' on':''}" data-act=psbpreset data-id=${id} data-n=${n}>${n}</button>`).join('')}<button class=tab data-act=psbshuffle data-id=${id}>shuffle</button></div>
    ${FXMAIN.map(k=>spBSlider(s.id,b,k)).join('')}
    <details class=fx-adv><summary>Advanced: particles, spin</summary>${['count','spin'].map(k=>spBSlider(s.id,b,k)).join('')}</details>
    <details class=fx-adv><summary>Advanced: particle size</summary><div class=fx-size><span class=mut>Particle size</span><label class=fx-px><input type=number min=32 max=512 step=4 value="${b.size.px}" data-psbpx data-id=${id} aria-label="Particle size in pixels"> px</label>
     <div class=tabs style="margin:0;gap:6px">${[1,2,3,4].map(k=>`<button class="tab${b.size.scale===k?' on':''}" data-act=psbscale data-id=${id} data-v=${k} title="${k} times as big">x${k}</button>`).join('')}</div><small class=mut>The particles are fitted to this size before they fly out.</small></div></details>
    <div class=row><button class="btn pri sm" data-act=psbrender data-id=${id}>Render</button><small class=mut>the final 512 px sticker, checked</small></div></div></div>
  ${rs.length?`<div class=ps-brs>${rs.map(r=>spBurstCard(s,b,r)).join('')}</div>`:''}</div>`}
function spBurstRedraw(id){const s=SPBS[id],el=typeof document!=='undefined'&&document.querySelector?document.querySelector(`[data-psb="${id}"]`):null;if(s&&el)el.outerHTML=spBurstHtml(s)}
async function spBurstPreview(id){const s=SPBS[id]||spFind(id);if(!s)return;const b=spBurstState(s,spHint());if(b.busy){b.again=1;return}
 if((s.n_picked||0)<1&&(s.source||{}).kind!=='stickers')return;b.busy=1;
 const r=await post(`/api/particles/${id}/preview`,{...(b.pack?{pack_id:b.pack}:{}),...(b.preset?{preset:b.preset}:{}),params:{...fxClean(b.par),...spBurstSize(b)},size:256});b.busy=0;
 if(r.ok){b.pv=r.j.url;b.shown=fxPick(r.j.params);const img=typeof document!=='undefined'&&document.getElementById?document.getElementById('psbpv-'+id):null;
  if(img){img.src=r.j.url;const sp=img.parentElement&&img.parentElement.querySelector('.spin');if(sp)sp.remove()}
  const root=typeof document!=='undefined'&&document.querySelector?document.querySelector(`[data-psb="${id}"]`):null;
  if(root)for(const [k] of FXSL){const inp=root.querySelector(`[data-psbp=${k}]`);if(inp&&r.j.params[k]!==undefined&&document.activeElement!==inp){inp.value=r.j.params[k];if(inp.nextElementSibling)inp.nextElementSibling.textContent=r.j.params[k]}}}
 else toast(r.j.error||'No preview',1);
 if(b.again){b.again=0;spBurstPreview(id)}}
async function spBurstReload(id){const r=await api('/api/particles/'+id);if(r.ok){SPBS[id]=r.j;if(SPL.detail)SPL.detail[id]=r.j;spBurstRedraw(id)}}
const spBurstSet=el=>{const s=SPBS[el.dataset.id]||spFind(el.dataset.id);return s?[s,spBurstState(s,spHint())]:[null,null]};
ACT.psbpreset=el=>{const [s,b]=spBurstSet(el);if(!s)return;b.preset=el.dataset.n;b.par={};spBurstRedraw(s.id);spBurstPreview(s.id)};
ACT.psbshuffle=el=>{const [s,b]=spBurstSet(el);if(!s)return;b.par.seed=1+Math.floor(Math.random()*9999);b.par.touched=1;spBurstPreview(s.id)};
ACT.psbscale=el=>{const [s,b]=spBurstSet(el);if(!s)return;b.size.scale=Math.max(1,Math.min(4,+el.dataset.v||1));spBurstRedraw(s.id);spBurstPreview(s.id)};
document.addEventListener('input',ev=>{const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.psbp){const [s,b]=spBurstSet({dataset:{id:t.dataset.id}});if(!s)return;b.par[t.dataset.psbp]=+t.value;b.par.touched=1;if(t.nextElementSibling)t.nextElementSibling.textContent=t.value;clearTimeout(b.pvT);b.pvT=setTimeout(()=>spBurstPreview(s.id),220)}
 else if(t.dataset.psbpx!==undefined){const [s,b]=spBurstSet({dataset:{id:t.dataset.id}});if(!s)return;b.size.px=Math.max(32,Math.min(512,Math.round(+t.value)||100));clearTimeout(b.pvT);b.pvT=setTimeout(()=>spBurstPreview(s.id),350)}});
document.addEventListener('change',ev=>{const t=ev.target;if(!t||!t.dataset||t.dataset.psbpack===undefined)return;const [s,b]=spBurstSet({dataset:{id:t.dataset.psbpack}});if(!s)return;b.pack=t.value;spBurstRedraw(s.id);spBurstPreview(s.id)});
ACT.psbrender=async el=>{const [s,b]=spBurstSet(el);if(!s)return;if(!b.pack)return toast('Choose the pack this burst is for',1);
 el.disabled=true;const r=await post(`/api/particles/${s.id}/render`,{pack_id:b.pack,...(b.preset?{preset:b.preset}:{}),params:{...fxClean(b.par),...spBurstSize(b)}});el.disabled=false;
 if(!r.ok)return toast(r.j.error||'Could not render',1);
 await spBurstReload(s.id);if(typeof ptCounts==='function'&&b.pack)ptCounts(b.pack);toast(r.j.status==='READY'?'Rendered: the burst is below':'Rendered, but a Telegram limit is broken: see its checks',r.j.status!=='READY')};
ACT.psbadd=async el=>{const id=el.dataset.id,pk=el.dataset.p,s=SPBS[id]||spFind(id);el.disabled=true;
 const r=await post(`/api/particles/${id}/add`,{renders:[el.dataset.r],pack_id:pk});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not add it',1)}
 toast(`Added to ${s?spPackName(s,pk):'the pack'}: the burst is a sticker of the pack now`);
 if(typeof loadLib==='function')await loadLib();await spBurstReload(id);if(typeof ptCounts==='function')ptCounts(pk);if(typeof ptForget==='function')ptForget()};
/* the wizard's third card: pick a set already saved and put it on this pack (nothing is drawn, nothing is spent) */
function spExistingHtml(S){const sets=SPL.sets;
 if(!sets){spLibSync();return '<div class=fx-job><span class=spin></span> <span class=mut>Reading the particle sets…</span></div>'}
 if(!sets.length)return `<div class=mut>No particle sets yet. Draw some first, then keep them with “Use as particle set”.</div>`;
 return `<div class=ps-pick>${sets.map(s=>{const on=(s.packs||[]).includes(S.pack),strip=(s.cells||[]).filter(c=>c.picked).slice(0,4);
  return `<div class=ps-pickrow><span class=ps-strip>${strip.map(c=>`<span class=ps-cell>${c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:''}</span>`).join('')||'<span class=mut>no cells</span>'}</span>
   <b>${esc(s.name||s.id)}</b><small class=mut>${s.n_picked} picked${(s.used_in||[]).length?` · used in: ${(s.used_in||[]).map(p=>esc(p.name||p.id)).join(', ')}`:''}</small>
   ${on?'<span class=mut>on this pack</span>':`<button class="btn sm pri" data-act=pspickset data-id=${esc(s.id)}>Use this set</button>`}</div>`}).join('')}</div>`}
ACT.pspickset=async el=>{const id=el.dataset.id;if(!SP.pack)return toast('Choose the pack first',1);
 const r=await post(`/api/particles/${id}/assign`,{packs:[SP.pack]});if(!r.ok)return toast(r.j.error||'Could not use it',1);
 toast(`“${r.j.name||id}” is now on this pack`);spLibSync(true);spDraw()};
/* from the pack's particle studio: start the wizard with this pack, or put a saved set on it */
ACT.psmakepack=el=>{SP.pack=el.dataset.p;SP.selFor='';SP.eid='';spSave();if(typeof GS!=='undefined')GS.tab='particles';location.hash='#/generate'};
ACT.pspickpack=el=>{const pid=el.dataset.p,sets=SPL.sets;
 const list=sets===null?'<div class=pk-pt-load><div class=spin></div></div>':sets.length?sets.map(s=>{const on=(s.packs||[]).includes(pid);
  return `<div class=ps-pickrow><b>${esc(s.name||s.id)}</b><small class=mut>${s.n_picked} picked</small>${on?'<span class=mut>on this pack</span>':`<button class="btn sm pri" data-act=pspackassign data-id=${esc(s.id)} data-p=${pid}>Use this set</button>`}</div>`}).join(''):'<div class=mut>No particle sets yet.</div>';
 dlg(`<h2>Use an existing set</h2><div class=mut style="margin-bottom:10px">Put a saved set on this pack. Nothing is drawn and nothing is spent.</div>${list}<div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button></div>`);
 if(sets===null)spLibSync().then(()=>{const d=$('dlg');if(d&&d.classList.contains('on'))ACT.pspickpack(el)})};
ACT.pspackassign=async el=>{const r=await post(`/api/particles/${el.dataset.id}/assign`,{packs:[el.dataset.p]});if(!r.ok)return toast(r.j.error||'Could not use it',1);
 closeDlg();toast(`“${r.j.name||el.dataset.id}” is now on this pack`);spLibSync(true)};
