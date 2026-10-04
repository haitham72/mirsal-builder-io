/* Particles in the Studio (docs/effects.md): the batch the Studio presents gets two things, both from this file.
   1. The Particles TAB next to Stickers and Animation: a small guided flow. Pick a pack and how the particles are made (the pack's own stickers: free; drawn by an AI: credits, the price on the button;
      a Kling video: credits), then the stickers burst with them, with live sliders, and Add puts the results into the pack. It is the particle studio's own flow (effects.js: state SP here, FX there;
      every effect function is shared), only smaller; "Open in the particle studio" opens the same effect there (#/effects/E###).
   2. The Particles SECTION under the batch (drawn into #gpart): for each sticker of the batch that is in a library pack, what was made and saved for it (the gallery of the library's sticker view),
      and one line for the stickers that are not in a pack yet. Every particle made is stored in its effect and therefore appears here, "saved under the sticker".
   Nothing is decided here: the engine does it behind /api/effects and /api/packs/{id}/particles. Top-level names in this file start with SP / sp (the scripts share ONE global scope). */
'use strict';
const SPKINDS=[['pack','Sprites from the sticker','Free'],['drawn','AI image sprites','Credits'],['video','Kling animated · from scratch','Credits']];
const SPMAX=24;                       // a run takes at most this many stickers (flow/effects.MAX_STICKERS)
const SP=Object.assign(fxNew('sp'),{kind:'pack',src:'own',mode:'sim',selFor:'',t:0});
FXS.sp=SP;
SP.root=()=>$('sp-root');SP.alive=()=>((route_==='generate'&&GS.tab==='particles')||route_==='effects')&&!!$('sp-root');SP.draw=()=>spDraw();
/* the three choices: the pack stickers and the drawn sheet are simulations (mode sim), the video is Kling (mode video, pro studio only); src says where the burst's particles come from */
function spKind(k){SP.kind=k;SP.mode=k==='video'?'video':'sim';SP.src=k==='pack'?'own':k==='drawn'?'drawn':k==='existing'?'existing':'video'}
let spLast=null;
try{spLast=JSON.parse(localStorage.getItem('mirsal.sp')||'null')}catch(e){}
SP.scope=null;
const spScopeKey=s=>JSON.stringify(s||null);
const spSave=()=>{if(!SP.scope)return;try{localStorage.setItem('mirsal.sp',JSON.stringify({eid:SP.eid,scope:SP.scope,kind:SP.kind,grid:SP.grid}))}catch(e){}};
const spScopeStickers=(scope,packs)=>{if(!scope)return [];
 return (packs||[]).flatMap(p=>(p.stickers||[]).filter(st=>
  scope.sticker_ids?scope.sticker_ids.includes(st.id):scope.sticker_id?st.id===scope.sticker_id:scope.generation?spGid((st.source||{}).generation)===spGid(scope.generation)&&(!scope.index||+scope.index===+(st.source||{}).index):p.id===scope.pack_id
 ).map(st=>({pack_id:p.id,sticker:st})));};
function spEnter(scope){SP.entry=(SP.entry||0)+1;fxReset(SP);SP.eid='';SP.scope=scope||null;SP.target='';SP.importing='';SP.importError='';SP.note='';SP.grid='2x2';SP.addOpen=false;
 const rows=spScopeStickers(scope,LIB.packs);SP.pack=(rows[0]||{}).pack_id||'';SP.sel=new Set(rows.map(r=>r.sticker.id));SP.selFor=SP.pack;
 if(route_==='generate')spShowTab();else{location.hash='#/effects';if(route_==='effects'&&typeof RENDER.effects==='function')RENDER.effects('')}
 return rows}
ACT.spcontinue=()=>{if(!spLast||spScopeKey(spLast.scope)!==spScopeKey(SP.scope))return;SP.eid=spLast.eid||'';spKind(spLast.kind);SP.grid=spLast.grid;spDraw();if(SP.eid)fxLoad(SP).then(spDraw)};
ACT.spscope=el=>spEnter(el.dataset.g?{generation:spGid(el.dataset.g)}:{pack_id:el.dataset.p,sticker_id:el.dataset.s||undefined});
const spApproveHtml=scope=>`<div class=sp-line><span class=mut>Approve this batch as a pack first, so the particles have a sticker to live in</span><button class="btn pri" data-act=spapprove data-g=${esc(scope.generation)}>Approve as a pack</button></div>`;
ACT.spapprove=async el=>{SP.pendingScope={generation:spGid(el.dataset.g)};await ACT.gadd({dataset:{g:el.dataset.g}})};
async function spAfterPack(){if(!SP.pendingScope)return;const scope=SP.pendingScope;SP.pendingScope=null;await loadLib();spEnter(scope)}
function spScopePicker(){return `<h2>Particles for which sticker?</h2><div class=fx-packs>${(LIB.packs||[]).flatMap(p=>p.stickers.map(st=>`<button class=fx-pack data-act=spscope data-p=${esc(p.id)} data-s=${esc(st.id)}>${media(st)}<b>${esc(st.name)}</b><small>${esc(p.name)}</small></button>`)).join('')}</div>`}

/* ---------- which library stickers came from a batch (pure): the pack sticker of cell `index` of batch `gid`, a still preferred to an animated one */
const spGid=v=>{const m=String(v==null?'':v).toUpperCase().match(/^G?(\d+)$/);return m?'G'+m[1].padStart(3,'0'):''};
function spLinkIndex(packs,gid){const out={},want=spGid(gid);if(!want)return out;
 for(const p of packs||[])for(const s of p.stickers||[]){const src=s.source||{};if(spGid(src.generation)!==want||!src.index)continue;
  const cur=out[src.index];if(!cur||(cur.sticker.type==='animated'&&s.type!=='animated'))out[src.index]={pack_id:p.id,pack:p.name,sticker:s}}
 return out}
const spHere=(p,gids)=>p.stickers.filter(s=>(gids||[]).includes(spGid((s.source||{}).generation))).length;
const spGids=gs=>gs.map(g=>spGid(g.generation_id));

/* ---------- the tab: setup (pure builder) */
const spOwners=S=>spScopeStickers(S.scope,LIB.packs).filter(r=>S.sel.has(r.sticker.id)).map(r=>({pack_id:r.pack_id,sticker_id:r.sticker.id}));
const spSlices=S=>spScopeStickers(S.scope,LIB.packs).filter(r=>S.sel.has(r.sticker.id)).map(r=>r.sticker.source||{}).filter(src=>src.generation&&src.index).map(src=>({generation:src.generation,index:src.index}));
const spKindChip=s=>{const kind=(s.source||{}).kind||s.kind,video=(s.cells||[]).some(c=>c.clip_url&&c.job);return video&&kind!=='video'?'Mixed sprites · Kling':({drawn:'From AI sheet',video:'From Kling video',stickers:'From sprites'}[kind]||'Particles')};
function spSliceSheet(S){const rows=spScopeStickers(S.scope,LIB.packs),gid=spGid(S.scope.generation||(rows[0]||{}).sticker?.source?.generation),g=typeof GM!=='undefined'?GM.get(+gid.slice(1)):null;
 if(!g||!g.source||!g.source.sheet_copy)return '';const sz=g.source.sheet_size||[512,512],rects=(g.source.grid||{}).rects||[];
 return `<svg class=sp-slice-sheet viewBox="0 0 ${sz[0]} ${sz[1]}" aria-label="Select slices as sprites"><image href="/out/${esc(gid)}/${esc(g.source.sheet_copy)}" width=${sz[0]} height=${sz[1]} />${rows.map(r=>{const st=r.sticker,box=rects[(st.source||{}).index-1];if(!box)return '';return `<rect x=${box[0]} y=${box[1]} width=${box[2]} height=${box[3]} fill="${S.sel.has(st.id)?'rgba(100,80,220,.3)':'transparent'}" class=sp-slice-hit data-act=spst data-id=${esc(st.id)} tabindex=0 role=button aria-pressed=${S.sel.has(st.id)} aria-label="Select S${st.source.index} as a sprite"><title>S${st.source.index} · select as sprite</title></rect>`}).join('')}</svg>`}
const spPromptElements=(prompt,grid)=>String(prompt||'').split(/[,;\n]/).map(x=>x.trim()).filter(Boolean).slice(0,fxCols(grid));
function spSetupHtml(S,packs,gids){if(!S.scope)return spScopePicker();
 const rows=spScopeStickers(S.scope,packs),n=S.sel.size,ai=S.kind==='drawn'||S.kind==='video';
 return `<div class=sp-modes>${SPKINDS.map(([k,l,tag])=>`<button class="sp-mode${S.kind===k?' on':''}" data-act=spkind data-v=${k} aria-pressed=${S.kind===k}><b>${l}</b><em>${tag}</em></button>`).join('')}</div>
 ${ai?`<label class=sp-prompt>Particle prompt<input type=text data-spprompt value="${esc(S.note||'')}" placeholder="Gold sparks, stars, diamonds" maxlength=300></label>
 <div class=row>${['2x2','3x3'].map(grid=>`<button class="tab${S.grid===grid?' on':''}" data-act=spgrid data-v=${grid}>${grid.replace('x',' × ')}</button>`).join('')}${S.kind==='video'&&S.grid==='3x3'?'<span class=fx-warn>3×3 may spill between cells. Use it anyway.</span>':''}</div>`:''}
 ${S.kind==='pack'?spSliceSheet(S):''}<div class=fx-sts>${rows.map(r=>{const st=r.sticker;return `<button class="fx-st${S.sel.has(st.id)?' on':''}" data-act=spst data-id=${esc(st.id)} title="${esc(st.name)}" aria-pressed=${S.sel.has(st.id)}>${media(st)}<span>${esc(st.name||'S'+(st.source||{}).index)}</span></button>`}).join('')}</div>
 ${S.kind==='existing'?spExistingHtml(S):`<button class="btn pri" data-act=spstart ${n?'':'disabled'}>${S.kind==='pack'?'Use selected · free':'Get price'}</button>`}
 <button class=link data-act=spkind data-v=existing>Use another sticker’s particles</button>`}
const spSetup=gs=>{const ids=new Set(spScopeStickers(SP.scope,LIB.packs).map(r=>r.sticker.id));return spSetupHtml(SP,LIB.packs.map(p=>({...p,stickers:p.stickers.filter(st=>ids.has(st.id))})).filter(p=>p.stickers.length),spGids(gs))};
ACT.sppack=el=>{spEnter({pack_id:el.dataset.id});spDraw()};
ACT.spkind=el=>{spKind(el.dataset.v);spSave();spDraw()};
ACT.spgrid=el=>{SP.grid=el.dataset.v;spSave();spDraw()};
ACT.spst=el=>{const i=el.dataset.id;SP.sel.has(i)?SP.sel.delete(i):SP.sel.add(i);spDraw()};
document.addEventListener('keydown',ev=>{const t=ev.target;if(t&&t.classList&&t.classList.contains('sp-slice-hit')&&['Enter',' '].includes(ev.key)){ev.preventDefault();ACT.spst(t)}});
ACT.spall=el=>{SP.sel=el.dataset.v==='1'?new Set(spScopeStickers(SP.scope,LIB.packs).map(r=>r.sticker.id)):new Set();spDraw()};
/* the vision model looks at pictures only with the person's yes (asked once, like everywhere): the pack stickers need none */
ACT.spstart=()=>{const prompt=SP.root()&&SP.root().querySelector('[data-spprompt]');if(prompt)SP.note=prompt.value;spStart()};
ACT.spnovlm=()=>{vlmSet('0');closeDlg();spStart()};
async function spStart(){const entry=SP.entry,k=SP.kind,owners=spOwners(SP);if(!owners.length)return;
 if(k==='pack'){const slices=spSlices(SP),animated=spScopeStickers(SP.scope,LIB.packs).some(r=>SP.sel.has(r.sticker.id)&&r.sticker.type==='animated'),r=await post('/api/particles',animated?{from_stickers:owners.map(o=>o.sticker_id),parent_pack_id:SP.pack,owners,target:SP.target||undefined}:slices.length?{from_slices:slices,owners,target:SP.target||undefined}:{from_stickers:owners.map(o=>o.sticker_id),parent_pack_id:SP.pack,owners,target:SP.target||undefined});
  if(SP.entry!==entry)return;if(!r.ok)return toast(r.j.error||'Could not use the slices',1);SP.set=r.j;SP.target=r.j.id;SPL.detail[r.j.id]=r.j;spBurstState(r.j,SP.pack);spDraw();spBurstPreview(r.j.id);return}
 const r=await post('/api/effects',{pack_id:SP.pack,sticker_ids:owners.filter(o=>o.pack_id===SP.pack).map(o=>o.sticker_id),mode:k==='video'?'video':'sim',grid:SP.grid,note:SP.note||'',allow_vlm:false});
 if(SP.entry!==entry)return;if(!r.ok)return toast(r.j.error||'Could not start',1);
 fxReset(SP);SP.eid=r.j.id;spSave();await fxLoad(SP);spDraw()}
ACT.spreset=()=>{fxReset(SP);SP.eid='';spSave();spDraw()};

/* ---------- the tab: the effect in progress */
const spKindName=k=>(SPKINDS.find(x=>x[0]===k)||[,'Particles'])[1];
function spHead(e){return `<div class=sp-eh><b>${esc(e.pack_name||'Particles')}</b><div class=sp-ea><button class=link data-act=spreset>Back</button><details><summary>Details</summary><a class=link href="#/effects/${esc(e.id)}">Original run · ${esc(e.id)}</a></details></div></div>`}
function spRunHtml(e){if(e.status==='NEW')return '<div class=fx-job><span class=spin></span> Preparing sprites…</div>';
 if(e.status==='ERROR')return `<div class=warn>${esc(e.error||'Could not prepare sprites')}<button class=btn data-act=spreset>Back</button></div>`;
 if(e.mode==='video')return (e.groups||[]).map(g=>{const v=(e.video||{})[g.id]||{},j=v.live||{},est=SP.est[g.id+e.grid.join('x')];
  if(v.status==='REQUESTED'&&!fxJobBad(j))return `<div class=fx-job><span class=spin></span> Generating animated sprites <small>${esc(v.job||'')} · ${esc(j.stage||j.status||'waiting')}</small></div>`;
  if(v.status==='DONE')return '<div class=fx-job><span class=spin></span> Slicing animated sprites…</div>';
  return `${fxJobBad(j)?`<div class=warn>${esc(j.error||'The video failed')}</div>`:''}<div class=fx-price data-fxest=${esc(g.id)}>${est&&est.credits!=null?est.credits+' credits':est?'Price unavailable':'Getting price…'}</div>${est&&est.credits==null?`<button class=link data-act=fxprice data-g=${esc(g.id)}>Retry price</button>`:''}<button class="btn pri" data-act=fxvideo data-g=${esc(g.id)} ${est&&est.credits!=null?'':'disabled'}>Generate animated sprites</button>`}).join('');
 const st=fxDrState(SP,e),sheet=fxSet(e)||{},j=sheet.live||{},d=SP.dr,est=d.est[fxDrKey(d)];
 if(['wait','cut'].includes(st))return `<div class=fx-job><span class=spin></span> ${st==='cut'?'Slicing sprites':'Generating image sprites'} <small>${esc(sheet.job||'')} · ${esc(j.stage||j.status||'')}</small></div>`;
 if(st==='failed')return `<div class=warn>${esc(j.error||sheet.error||'The sheet failed')}<button class=btn data-act=spreset>Back</button></div>`;
 if(['pick','done'].includes(st))return fxReady(SP,fxSetGen(e)).length?'<div class=fx-job><span class=spin></span> Opening simulator…</div>':fxDrCells(SP,e,'');
 return `<div class=fx-price>${est&&est.credits!=null?est.credits+' credits':est?'Price unavailable':'Getting price…'}</div>${est&&est.credits==null?'<button class=link data-act=spprice>Retry price</button>':''}<button class="btn pri" data-act=fxddraw ${est&&est.credits!=null&&d.chosen.length?'':'disabled'}>Generate image sprites</button>`}
function spEditorCells(s){const pick=SPL.pick[s.id];return `<div class=ps-cells>${(s.cells||[]).map(c=>{const on=pick?pick.has(c.n):!!c.picked;return `<div class=sp-sprite><button class="ps-pick${on?' on':''}" data-act=pspickcell data-id=${esc(s.id)} data-n=${c.n} aria-pressed=${on} title="${esc(c.key||'Sprite '+c.n)}">${spCellMedia(c)}<span class=ps-tick>${on?'✓':''}</span></button>${(c.warnings||[]).map(w=>`<small class=fx-w>${esc(fxWords(w))}</small>`).join('')}</div>`}).join('')}</div>${pick?`<button class="btn sm pri" data-act=pspicksave data-id=${esc(s.id)}>Use selected${(s.cells||[]).some(c=>pick.has(c.n)&&(c.warnings||[]).length)?' anyway':''}</button>`:''}`}
function spBody(gs){if(!SP.scope)return spScopePicker();if(SP.scope.generation&&!spScopeStickers(SP.scope,LIB.packs).length)return spApproveHtml(SP.scope);
 const rows=spScopeStickers(SP.scope,LIB.packs),heading=`<div class=sp-h><h2>Particles</h2><span class=sp-target>${rows.slice(0,4).map(r=>media(r.sticker)).join('')}<b>${rows.length===1?esc(rows[0].sticker.name):rows.length+' stickers'}</b></span></div>`;
 if(SP.set&&!SP.eid){const s=SP.set;return `${heading}<div class=row><span class=fx-chip>${spKindChip(s)}</span><span class=mut>${spSaved(s)?'Saved row':'Draft · not saved yet'}</span><button class=link data-act=spfresh>New version</button></div>${spEditorCells(s)}<details class=sp-add data-spadd ${SP.addOpen?'open':''}><summary>Add more</summary>${spMoreHtml(s)}</details>${spBurstHtml(s)}`}
 return heading+(SP.importError?`<div class=warn>${esc(SP.importError)}<button class=btn data-act=spimportretry>Retry</button></div>`:'')+(SP.eid?(SP.rec?spHead(SP.rec)+spRunHtml(SP.rec):'<div class=fx-job><span class=spin></span> Loading…</div>'):spSetup(gs))}
document.addEventListener('toggle',ev=>{if(ev.target&&ev.target.dataset&&ev.target.dataset.spadd!==undefined)SP.addOpen=ev.target.open},true);
ACT.spimportretry=()=>{SP.importError='';spAfterDraw()};
ACT.spprice=()=>{delete SP.dr.est[fxDrKey(SP.dr)];spAfterDraw()};
async function spImport(e){const token=SP.entry,eid=SP.eid;if(SP.importing===eid)return;SP.importing=eid;
 const selected=e.mode==='video'?(e.results||[]).filter(r=>r.file).map(r=>r.cell):SP.dr.picked===e.id+':'+fxSetGen(e)?fxTicked(SP,e):fxReady(SP,fxSetGen(e)).map(c=>c.index);
 const r=await post('/api/particles',{from_effect:eid,owners:spOwners(SP),target:SP.target||undefined,picked:selected});
 if(SP.entry!==token||SP.eid!==eid)return;SP.importing='';if(!r.ok){SP.importError=r.j.error||'Could not open simulator';return spDraw()}
 SP.set=r.j;SP.target=r.j.id;SP.eid='';SP.importError='';spSave();SPL.detail[r.j.id]=r.j;spBurstState(r.j,SP.pack);spDraw();spBurstPreview(r.j.id)}
async function spAfterDraw(){const e=SP.rec;if(!SP.eid||!e||!['READY','RESULTS','VIDEO_REQUESTED','DONE'].includes(e.status))return;
 if(SP.importError)return;
 if(e.mode==='video'){if((e.results||[]).some(r=>r.mode==='video'&&r.file)&&!Object.values(e.video||{}).some(v=>v.status==='REQUESTED'&&!fxJobBad(v.live)))return spImport(e);for(const g of e.groups||[])fxEstimate(SP,g.id);return}
 const st=fxDrState(SP,e);if(['pick','done'].includes(st)&&(fxReady(SP,fxSetGen(e)).length||(SP.dr.picked===e.id+':'+fxSetGen(e)&&fxTicked(SP,e).length)))return spImport(e);
 if(st==='make'){const d=SP.dr;if(!d.chosen.length)d.chosen=spPromptElements(SP.note,SP.grid);if(!d.chosen.length)d.chosen=(e.groups||[]).flatMap(g=>g.elements||[]).slice(0,fxCols(SP.grid));d.grid=SP.grid;await fxDrEstimate(SP);spDrawPrice()}}
function spDrawPrice(){const root=SP.root();if(root&&SP.rec&&!SP.set){root.innerHTML=spBody(sessionGens())}}
const spCellMedia=c=>c.clip_url?`<video src="${esc(c.clip_url)}"${c.url?` poster="${esc(c.url)}"`:''} autoplay loop muted playsinline preload=metadata></video>`:c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:'<span class=mut>No sprite</span>';
ACT.spfresh=()=>{SP.entry=(SP.entry||0)+1;fxReset(SP);SP.eid='';SP.target='';spDraw()};
function spDraw(){const el=$('sp-root');if(!el)return;el.innerHTML=spBody(sessionGens());SP.last=fxSig(SP);spAfterDraw()}
function spView(gs){if(SP.eid&&Date.now()-SP.t>3000){SP.t=Date.now();fxLoad(SP).then(()=>{if(SP.alive()&&fxSig(SP)!==SP.last)SP.draw()})}
 const cont=spLast&&spLast.eid&&spScopeKey(spLast.scope)===spScopeKey(SP.scope)?'<button class=link data-act=spcontinue>Continue the last run</button>':'';
 return `<section class="gplan sp fx" id=sp-root data-fxx=sp>${cont}${spBody(gs)}</section>`}
const spEffectsRender=RENDER.effects;
RENDER.effects=arg=>{if(arg)return spEffectsRender(arg);$('s-effects').innerHTML=spView([]);spAfterDraw()};
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
function spOpenFor(pack,sid){return spEnter({pack_id:pack,sticker_id:sid||undefined})}
ACT.spopen=el=>{const ds=(el&&el.dataset)||{};const gs=route_==='generate'?sessionGens():[];
 return spEnter(ds.g?{generation:spGid(ds.g)}:gs.length?{generation:spGid(gs[gs.length-1].generation_id)}:null)};
ACT.spmake=el=>spOpenFor(el.dataset.p,el.dataset.s);

/* ---------- the section under the batch: the particles of each of its stickers that is in a pack (pure builder + a loader) */
const SPS={batches:{},sig:'',busy:false,html:'',el:null,loaded:false};
const spThumb=(gid,c)=>c.png?`<img src="/out/${esc(gid)}/${esc(c.png)}" alt="" loading=lazy>`:'';
/* b: {gid, cells: [{index, key, png, link: {pack_id, pack, sticker} | null, n: particles made + saved, det: the sticker's answer | null}]} */
/* a particle set owned by several stickers of the batch is ONE row, drawn once above them; each sticker's block keeps only its own rows (pure) */
function spSecShared(b){const by=new Map();for(const c of b.cells)if(c.link&&c.det)for(const r of [...(c.det.rows||[]),...(c.det.drafts||[])]){const e=by.get(r.id)||{row:r,cells:[]};if(!e.cells.includes(c))e.cells.push(c);by.set(r.id,e)}
 return [...by.values()].filter(e=>e.cells.length>1)}
const spSecOwn=(c,shared)=>{if(!c.det)return c;const ids=new Set(shared.map(e=>e.row.id)),det={...c.det,rows:(c.det.rows||[]).filter(r=>!ids.has(r.id)),drafts:(c.det.drafts||[]).filter(r=>!ids.has(r.id)),sets:(c.det.sets||[]).filter(x=>!ids.has(x.id))};
 return {...c,det,n:typeof ptCount==='function'?ptCount(det):c.n}};
function spSecBatchHtml(b,many){const free=b.cells.filter(c=>!c.link),shared=spSecShared(b),own=b.cells.filter(c=>c.link).map(c=>spSecOwn(c,shared));
 return `<div class=sp-bt>${many?`<div class=sp-bh><b>${esc(b.gid)}</b></div>`:''}
 ${shared.map(e=>{const c=e.cells[0];return `<div class="sp-st sp-shared"><div class=sp-sth><b>Shared by ${e.cells.map(x=>'S'+x.index).join(', ')}</b></div><div class=pk-rows>${ptRow(e.row,{id:c.link.sticker.id,pack_id:c.link.pack_id},!e.row.saved)}</div></div>`}).join('')}
 ${own.map(c=>`<div class=sp-st><div class=sp-sth><span class=sp-th>${spThumb(b.gid,c)}</span><b>S${c.index}${c.key?' · '+esc(String(c.key).replace(/_/g,' ')):''}</b><span class=mut>in <button class=link data-act=ptsaved data-id=${esc(c.link.pack_id)}>${esc(c.link.pack)}</button></span><button class="btn sm" data-act=spmake data-p=${esc(c.link.pack_id)} data-s=${esc(c.link.sticker.id)}>${c.n?'New version':'Create particles'}</button></div>${c.n?ptBody(c.det,{id:c.link.sticker.id,pack_id:c.link.pack_id}):shared.some(e=>e.cells.includes(b.cells.find(x=>x.index===c.index)))?'<span class=mut>Uses the shared particles above</span>':'<span class=mut>No particles yet</span>'}</div>`).join('')}
 ${free.length?spApproveHtml({generation:b.gid}):''}</div>`}
const spSecHtml=bs=>bs.length?`<section class=sp-sec><div class=sp-sech><h2>${ic('fx')} Particles</h2><span class=mut>Particles — made for each sticker of this batch. Adding a burst to the pack affirms it.</span><button class="btn sm pri" data-act=spopen>${ic('fx')} Create particles</button></div>${bs.map(b=>spSecBatchHtml(b,bs.length>1)).join('')}</section>`:'';
function spSecData(){const out=[];for(const id of SES.gens){const g=GM.get(id);if(!g)continue;const gid=spGid(g.generation_id),ix=spLinkIndex(LIB.packs,gid),batch=SPS.batches[gid];
 out.push({gid,cells:g.stickers.filter(t=>t.status==='READY'&&t.png&&(t.review||{}).still!=='REJECTED').map(t=>{const det=batch?(batch.cells||[]).find(c=>c.index===t.index):null,l=det?det.link:ix[t.index]||null,fallback=l?PKPT.d[l.sticker.id]:null,d=det||fallback,c=l?(PKPT.c[l.pack_id]||{})[l.sticker.id]:null;
 return{index:t.index,key:t.key,png:t.png,link:l,n:d?(d.sets||[]).length+(d.created||[]).length+(d.saved||[]).length:c?c.created+c.saved:0,det:d||null}})})}return out}
function spSecDraw(){const el=$('gpart');if(!el)return;const html=spSecHtml(spSecData());if(html!==SPS.html||el!==SPS.el){SPS.html=html;SPS.el=el;el.innerHTML=html}}
async function spSecSync(force){if(SPS.busy||!$('gpart'))return;SPS.busy=true;
 try{for(const b of spSecData()){const r=await api(`/api/generations/${b.gid}/particles`);if(r.ok)SPS.batches[b.gid]=r.j}SPS.loaded=true;spSecDraw()}
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
  <div class=ps-strip>${strip.map(c=>`<span class=ps-cell title="${esc(c.key||('cell '+c.n))}">${spCellMedia(c)}</span>`).join('')||'<span class=mut>No cells yet</span>'}${picked.length>8?`<span class=ps-more>+${picked.length-8}</span>`:''}</div>
  <div class=ps-main><b>${esc(s.name||s.id)}</b><small class=mut>${esc(s.id)} · ${s.n_cells} cell${s.n_cells===1?'':'s'} · ${picked.length} picked${s.kind?' · '+esc(spKindChip(s)):''}</small>
  <div class=ps-used>${(s.owner||[]).length?`made for ${(s.owner||[]).length} sticker${s.owner.length===1?'':'s'}`:'Detached · attach to a sticker'}</div>
  <div class=ps-cost>${esc(spCredits(s.credits))}${(s.source||{}).job?' · '+esc(s.source.job):''}</div>
  <div class=ps-act><button class="btn sm" data-act=psopen data-id=${esc(s.id)}>${open?'Close':'Open'}</button><button class="btn sm" data-act=psassign data-id=${esc(s.id)}>Attach to stickers</button><button class="btn sm" data-act=psdup data-id=${esc(s.id)}>Duplicate</button><button class="btn sm" data-act=psrename data-id=${esc(s.id)}>Rename</button><button class="btn sm dng" data-act=psdel data-id=${esc(s.id)}>Delete</button></div>
  ${open?spSetDetail(s):''}</div></div>`}
function spSetDetail(s){const d=SPL.detail[s.id],full=d&&d.id===s.id?d:s,cells=full.cells||[],els=full.elements||[],mo=full.motion||{},src=full.source||{},pick=SPL.pick[s.id]||null;
 return `<div class=ps-det>
  ${els.length?`<div class=ps-els>${els.map(x=>`<span class=fx-chip>${esc(x)}</span>`).join('')}</div>`:''}
  ${src&&src.kind?`<div class=mut>from ${esc(src.kind)}${src.effect?` · ${esc(src.effect)}`:''}${src.generation?` · ${esc(src.generation)}`:''}</div>`:''}
  ${mo&&mo.preset?`<div class=mut>motion: ${esc(mo.preset)}</div>`:''}
  ${(full.owner||[]).map(o=>`<div class=ps-on><span class=mut>sticker ${esc(o.sticker_id)}</span><button class=link data-act=psunassign data-id=${esc(s.id)} data-s=${esc(o.sticker_id)}>unlink</button></div>`).join('')}
  ${cells.length?`<div class=ps-cells>${cells.map(c=>{const on=pick?pick.has(c.n):!!c.picked;
   return `<button class="ps-pick${on?' on':''}" data-act=pspickcell data-id=${esc(s.id)} data-n=${c.n} aria-pressed=${on} title="cell ${c.n}${on?' (kept)':' (not kept)'}">${spCellMedia(c)}<span class=ps-tick>${on?'✓':''}</span></button>`}).join('')}</div>
  ${pick?`<div class=row><button class="btn pri sm" data-act=pspicksave data-id=${esc(s.id)}>Keep ${pick.size} picked</button><button class=link data-act=pspickcancel data-id=${esc(s.id)}>cancel</button></div>`:`<div class=mut>Tick the cells to keep.</div>`}`:''}
  ${spMoreHtml(full)}
  ${spBurstHtml(full)}
 </div>`}
function spLibHtml(){const sets=SPL.sets;
 if(!sets)return `<div class=pk-pt-load><div class=spin></div><span class=mut>Reading the particle sets…</span></div>`;
 const del=SPL.deleted?`<div class=ps-del><span>Deleted ${esc(SPL.deleted.name)}: it is in the trash, nothing is destroyed.</span><button class="btn sm" data-act=psrestore data-id=${esc(SPL.deleted.id)}>Restore</button></div>`:'',trash=spTrashHtml(SPL.trash);
 if(!sets.length)return `${del}<div class="card" style="text-align:center;padding:40px"><h2>No particle sets yet</h2><p class=mut>Particles live in stickers. Choose a sticker to create its particles.</p><button class="btn pri" data-act=spopen>${ic('fx')} Make particles</button></div>${trash}`;
 return `${del}<div class=ps-lib>${sets.map(spSetCard).join('')}</div><div class=row><button class="btn pri" data-act=spopen>${ic('fx')} Make particles</button></div>${trash}`}
function spLibRefresh(){if(SP.set&&!SP.eid&&SP.alive())spDraw();if(typeof route_!=='undefined'&&route_==='library'&&typeof LIBTAB!=='undefined'&&LIBTAB==='particles'&&typeof RENDER!=='undefined'&&RENDER.library)RENDER.library();
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
ACT.psassign=el=>{const s=spFind(el.dataset.id);if(!s)return;const have=new Set((s.owner||[]).map(o=>o.sticker_id));
 dlg(`<h2>Assign particles</h2>${(LIB.packs||[]).flatMap(p=>p.stickers.map(st=>`<label class=ps-pack><input type=checkbox data-psasticker=${esc(st.id)} ${have.has(st.id)?'checked':''}> ${esc(st.name)} <small class=mut>${esc(p.name)}</small></label>`)).join('')}<div class=row><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=psassignsave data-id=${esc(s.id)}>Assign</button></div>`)};
ACT.psassignsave=async el=>{const id=el.dataset.id,add=[...document.querySelectorAll('[data-psasticker]')].filter(c=>c.checked).map(c=>c.dataset.psasticker),cur=((spFind(id)||{}).owner||[]).map(o=>o.sticker_id),drop=cur.filter(x=>!add.includes(x));
 const a=await post(`/api/particles/${id}/link`,{sticker_ids:add});if(!a.ok)return toast(a.j.error,1);
 let saved=a.j;if(drop.length){const d=await post(`/api/particles/${id}/unlink`,{sticker_ids:drop});if(!d.ok)return toast(d.j.error,1);saved=d.j}if(SP.set&&SP.set.id===id)SP.set=saved;SPL.detail[id]=saved;closeDlg();await loadLib();spLibRefresh();spLibSync(true)};
ACT.psunassign=async el=>{const r=await post(`/api/particles/${el.dataset.id}/unlink`,{sticker_ids:[el.dataset.s]});if(!r.ok)return toast(r.j.error||'Could not unlink',1);toast('Unlinked; the set stays');await loadLib();spLibSync(true)};
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
 const r=await post(`/api/particles/${id}`,{picked:pick});if(!r.ok)return toast(r.j.error||'Could not keep them',1);
 delete SPL.pick[id];SPL.detail[id]=r.j;if(SP.set&&SP.set.id===id)SP.set=r.j;toast(`Keeping ${pick.length} cells`);spLibRefresh();spBurstPreview(id);spLibSync(true)};
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
const spMoreKey=m=>m.mode+'|'+m.grid+'|'+(m.prompt||'')+'|'+m.chosen.join('|');
function spMoreState(s){let m=SPM[s.id];if(!m)m=SPM[s.id]={mode:(s.source||{}).kind==='video'?'video':'drawn',prompt:(s.elements||[]).join(', '),grid:'2x2',chosen:null,extra:[],est:{},busy:0};if(m.chosen===null)m.chosen=(s.elements||[]).slice(0,spMoreN(m));return m}
const spMoreNames=(s,m)=>[...new Set([...(s.elements||[]),...m.extra,...m.chosen])];
function spFind(id){const hit=(SP.set&&SP.set.id===id?SP.set:null)||(SPL.detail||{})[id]||(SPL.sets||[]).find(x=>x.id===id);if(hit)return hit;
 if(typeof PKPT!=='undefined')for(const l of Object.values(PKPT.sets||{}))for(const x of l||[])if(x&&x.id===id)return x;return null}
const spSheetWords=sh=>{const n=(sh.appended||[]).length,e=(sh.skipped||[]).length;
 return sh.status==='REQUESTED'?`Waiting for the sheet (${sh.job})…`:sh.status==='DRAWN'?`Cutting the particles (${sh.generation})…`
  :sh.status==='DONE'?`Sheet ${sh.n}: ${n} particle${n===1?'':'s'} added${e?` (${e} cell${e===1?'':'s'} came out empty)`:''}`
  :sh.status==='FAILED'?`Sheet ${sh.n} failed: ${sh.error||'the job failed'}. Draw it again below.`
  :sh.status==='NO_CELLS'?`Sheet ${sh.n} came back with no usable cell. ${sh.error||''}`:`Sheet ${sh.n}: ${String(sh.status||'').toLowerCase()}`};
function spMoreHtml(s){const m=spMoreState(s),est=m.est[spMoreKey(m)],ok=!s.drawing&&m.chosen.length&&est&&est.credits!=null;
 return `<div class=ps-gen data-psgen=${esc(s.id)}>
 <div class=sp-modes><button class="sp-mode on" aria-pressed=true><b>Create with AI</b><em>Credits</em></button><button class=sp-mode data-act=psmoreexisting data-id=${esc(s.id)}><b>Use existing sprites</b><em>Free</em></button></div>
 <div class=tabs>${[['drawn','Image sprites'],['video','Animated sprites · Kling']].map(([mode,label])=>`<button class="tab${m.mode===mode?' on':''}" data-act=psmoremode data-id=${esc(s.id)} data-v=${mode}>${label}</button>`).join('')}</div>
 <label class=sp-prompt>Particle prompt<input type=text data-psmoreprompt=${esc(s.id)} value="${esc(m.prompt)}" placeholder="Gold sparks, stars, diamonds" maxlength=300></label>
 <div class=row>${['2x2','3x3'].map(grid=>`<button class="tab${m.grid===grid?' on':''}" data-act=psmoregrid data-id=${esc(s.id)} data-v=${grid}>${grid.replace('x',' × ')}</button>`).join('')}${m.mode==='video'&&m.grid==='3x3'?'<span class=fx-warn>3×3 may spill between cells. Use it anyway.</span>':''}</div>
 ${(s.sheets||[]).slice().reverse().slice(0,5).map(sh=>`<div class=ps-sheet>${['REQUESTED','DRAWN'].includes(sh.status)?'<span class=spin></span> ':''}${esc(spSheetWords(sh))}${sh.status==='NO_CELLS'&&sh.generation?`<button class="btn sm" data-act=openstudio data-gen=${esc(sh.generation)} data-i=1>Open ${esc(sh.generation)}</button>`:''}</div>`).join('')}
 <div class=fx-price data-psmoreprice>${!m.chosen.length?'Enter a particle prompt':est?est.credits!=null?est.credits+' credits':esc(est.error||'Price unavailable'):'Getting price…'}</div>${est&&est.credits==null?`<button class=link data-act=psmoreprice data-id=${esc(s.id)}>Retry price</button>`:''}
 <button class="btn pri" data-act=psmoredraw data-id=${esc(s.id)} ${ok?'':'disabled'}>Generate ${m.mode==='video'?'animated':'image'} sprites</button></div>`}
function spMoreRefresh(id){const s=spFind(id),root=document.querySelector&&document.querySelector(`[data-psgen="${id}"]`);if(!s||!root)return spLibRefresh();const active=document.activeElement,focused=active&&active.dataset&&active.dataset.psmoreprompt===id,start=focused?active.selectionStart:null,end=focused?active.selectionEnd:null;root.outerHTML=spMoreHtml(s);if(focused){const next=document.querySelector(`[data-psmoreprompt="${id}"]`);if(next){next.focus();next.setSelectionRange(start,end)}}}
ACT.psmoremode=el=>{const s=spFind(el.dataset.id);if(!s)return;spMoreState(s).mode=el.dataset.v;spMoreRefresh(s.id);spMoreEstimate(s.id)};
ACT.psmoreprice=el=>{const s=spFind(el.dataset.id);if(!s)return;const m=spMoreState(s);delete m.est[spMoreKey(m)];spMoreRefresh(s.id);spMoreEstimate(s.id)};
ACT.psmoreexisting=el=>{const s=spFind(el.dataset.id);if(!s)return;const owners=s.owner||[];if(!SP.scope||SP.target!==s.id){spEnter({pack_id:(owners[0]||{}).pack_id,sticker_ids:owners.map(o=>o.sticker_id)});SP.entry=(SP.entry||0)+1}SP.set=null;SP.target=s.id;SP.eid='';spKind('pack');spDraw()};
document.addEventListener('input',ev=>{const t=ev.target;if(t&&t.dataset&&t.dataset.spprompt!==undefined)SP.note=t.value;
 if(t&&t.dataset&&t.dataset.psmoreprompt){const s=spFind(t.dataset.psmoreprompt);if(!s)return;const m=spMoreState(s);m.prompt=t.value;m.chosen=spPromptElements(t.value,m.grid);clearTimeout(m.timer);m.timer=setTimeout(()=>{spMoreRefresh(s.id);spMoreEstimate(s.id)},500)}});
async function spMoreEstimate(id){const s=spFind(id);if(!s)return;const m=spMoreState(s),k=spMoreKey(m);if(!m.chosen.length||m.est[k]||m.busy===k)return;m.busy=k;
 const r=await post(`/api/particles/${id}/more`,{mode:m.mode,grid:m.grid,elements:m.chosen,prompt:m.prompt,estimate:true});m.busy=0;
 m.est[k]=r.ok?{effect:r.j.effect,credits:r.j.credits!=null?r.j.credits:null,error:r.j.cost_error||(r.j.credits==null?'The price is not available.':null)}:{credits:null,error:r.j.error||'The price is not available.'};spMoreRefresh(id)}
ACT.psmoregrid=el=>{const s=spFind(el.dataset.id);if(!s)return;const m=spMoreState(s);m.grid=el.dataset.v==='3x3'?'3x3':'2x2';m.chosen=spPromptElements(m.prompt,m.grid);spMoreRefresh(s.id);spMoreEstimate(s.id)};
ACT.psmorechip=el=>{const s=spFind(el.dataset.id);if(!s)return;const m=spMoreState(s),v=el.dataset.v,i=m.chosen.indexOf(v);
 if(i>=0)m.chosen.splice(i,1);else if(m.chosen.length>=spMoreN(m))return toast(`A ${m.grid==='3x3'?'3 x 3':'2 x 2'} sheet holds ${spMoreN(m)}: take one off first`,1);else m.chosen.push(v);
 spLibRefresh();spMoreEstimate(s.id)};
function spMoreAdd(id,v){const s=spFind(id);v=String(v||'').trim().slice(0,40);if(!s||!v)return;const m=spMoreState(s);
 if(!spMoreNames(s,m).includes(v))m.extra.push(v);if(!m.chosen.includes(v)&&m.chosen.length<spMoreN(m))m.chosen.push(v);spLibRefresh();spMoreEstimate(id)}
ACT.psmoreadd=el=>{const i=document.querySelector(`[data-psmoreown="${el.dataset.id}"]`);spMoreAdd(el.dataset.id,i?i.value:'')};
document.addEventListener('keydown',e=>{const t=e.target;if(e.key==='Enter'&&t&&t.dataset&&t.dataset.psmoreown){e.preventDefault();spMoreAdd(t.dataset.psmoreown,t.value)}});
ACT.psmoredraw=async el=>{const id=el.dataset.id,s=spFind(id);if(!s)return;const m=spMoreState(s),est=m.est[spMoreKey(m)];if(!est||est.credits==null||!m.chosen.length)return;el.disabled=true;
 const r=await post(`/api/particles/${id}/more`,{mode:m.mode,grid:m.grid,elements:m.chosen,prompt:m.prompt,...(est.effect?{effect:est.effect}:{}),go:true});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not start',1)}
 toast('Generating sprites');delete SPL.detail[id];m.est={};if(r.j.id&&/^E/.test(r.j.id)&&SP.target===id){SP.eid=r.j.id;SP.set=null;spKind(m.mode);spSave();await fxLoad(SP);spDraw()}else spLibSync(true);
 if(typeof route_!=='undefined'&&route_==='pack'&&typeof ptCounts==='function'&&typeof PACK_ID!=='undefined')ptCounts(PACK_ID)};
/* ---------- the burst maker: Motion and Finish of the wizard, for a SET and a PACK (docs/particles_plan.md section 4, docs/particles_plan.md 4.6-4.7).
   ONE preview for the whole pack (not a row per sticker): the five presets, Energy / Float / Swirl (count and spin under Advanced), the particle size, then Render (the final 512 px WebM, checked) and
   Add (an animated sticker of the pack). Everything calls POST /api/particles/{id}/preview | render | add; the same panel sits in the open set card (Library and the pack's studio) and in the wizard
   once the run has been saved as a set. It redraws only itself ([data-psb]), so a slider never moves the rest of the page. A burst is free: there is no price anywhere. */
const SPB={};                                   // set id -> {pack, hint, preset, par{touched sliders only}, shown{what the server used}, pv, size{px,scale}, pvT, busy, again}
const SPBS={};                                  // set id -> the set last drawn, so a partial redraw has it
const spHint=()=>typeof route_!=='undefined'&&route_==='pack'&&typeof PACK_ID!=='undefined'?PACK_ID:'';
function spBurstState(s,hint){let b=SPB[s.id];if(!b)b=SPB[s.id]={pack:'',hint:'',preset:'',par:{},shown:{},pv:'',pvT:0,busy:0,again:0,size:{px:(s.motion&&s.motion.params&&s.motion.params.sprite_px)||100,scale:(s.motion&&s.motion.params&&s.motion.params.scale)||1}};
 if(hint&&b.hint!==hint){b.pack=hint;b.hint=hint}else if(!b.pack)b.pack=(s.packs||[])[0]||'';return b}
/* the preset the server will use when none was picked: the set's own default motion, else burst (particle_sets._burst), so a preset is always lit */
const spPresetOf=(s,b)=>b.preset||(s.motion&&s.motion.preset)||'burst';
const spBurstSize=b=>({sprite_px:b.size.px,scale:b.size.scale});
const spPackName=(s,id)=>{const p=typeof packById==='function'?packById(id):null;return p?p.name:((s.used_in||[]).find(x=>x.id===id)||{}).name||id};
function spBSlider(id,b,k){const f=FXSL.find(x=>x[0]===k),v=b.par[k]!==undefined?b.par[k]:b.shown[k];
 return `<label class=fx-sl><span>${f[1]}</span><input type=range min=${f[2]} max=${f[3]} step=${f[4]} value="${v??''}" data-psbp=${k} data-id=${esc(id)} aria-label="${f[1]}"><output>${v??''}</output></label>`}
function spBurstCard(s,b,r){const ok=r.status==='READY'&&!!r.url,ws=(r.warnings||[]).map(fxWords),bl=(r.blocks||[]).map(fxWords),pk=spPackName(s,b.pack);
 return `<div class="ps-br${ok?'':' bad'}" data-psr=${esc(r.id)}><div class=pk-pt-m>${r.url?`<video src="${esc(r.url)}" autoplay loop muted playsinline preload=metadata></video>`:'<span class=mut>no file</span>'}</div>
  <div class=pk-pt-id><b>${esc(r.id)} · ${esc(r.preset||'')}</b><small>${Math.round((r.bytes||0)/1024)} KB · ${esc(String(r.status||'').toLowerCase())}</small></div>
  ${bl.map(w=>`<span class="fx-w bad">${esc(w)}</span>`).join('')}${ws.map(w=>`<span class=fx-w>${esc(w)}</span>`).join('')}
  ${r.added_to?`<small class=mut>In pack ✓</small>`:ok?`<button class="btn sm pri" data-act=psbadd data-id=${esc(s.id)} data-r=${esc(r.id)} data-p=${esc(b.pack)}>${ws.length?'Use it anyway · Add':'Add to pack'}</button>`:''}</div>`}
function spBurstHtml(s){SPBS[s.id]=s;const b=spBurstState(s,spHint()),own=s.packs||[],kind=(s.source||{}).kind,has=(s.n_picked||0)>0||kind==='stickers',id=esc(s.id);
 const head=`<div class=ps-genh><b>Motion</b></div>`;
 if(!has)return `<div class=ps-burst data-psb=${id}>${head}<div class=mut>Add sprites to preview.</div></div>`;
 const choose=own.length===1?`<b>for ${esc(spPackName(s,own[0]))}</b>`:`<label class=row><span class=mut>for</span><select data-psbpack=${id} aria-label="The pack this burst is for">${b.pack?'':'<option value="" selected>Choose a pack…</option>'}${(own.length?own:((typeof LIB!=='undefined'&&LIB.packs)||[]).map(p=>p.id)).map(pid=>`<option value="${esc(pid)}"${pid===b.pack?' selected':''}>${esc(spPackName(s,pid))}</option>`).join('')}</select></label>`;
 const rs=(Array.isArray(s.renders)?s.renders:[]).filter(r=>r.pack_id===b.pack).slice().reverse();
 return `<div class=ps-burst data-psb=${id}>${head}
  <div class=row>${choose}${kind==='stickers'&&!(s.n_cells>0)?'<span class=mut>the pack’s own stickers fly out as the particles</span>':''}</div>
  <div class=ps-sim><div class=fx-pvbox><img id=psbpv-${id} ${b.pv?`src="${esc(b.pv)}"`:''} alt="">${b.pv?'':'<span class=spin></span>'}<small>${esc(s.name||s.id)}</small></div>
   <div class=fx-ctl><div class=fx-pre>${FXPRESETS.map(n=>`<button class="tab${spPresetOf(s,b)===n?' on':''}" data-act=psbpreset data-id=${id} data-n=${n}>${n}</button>`).join('')}<button class=tab data-act=psbshuffle data-id=${id}>shuffle</button></div>
    ${FXMAIN.map(k=>spBSlider(s.id,b,k)).join('')}
    <details class=fx-adv><summary>Advanced: particles, spin</summary>${['count','spin'].map(k=>spBSlider(s.id,b,k)).join('')}</details>
    <details class=fx-adv><summary>Advanced: sprite resolution</summary><div class=fx-size><span class=mut>Sprite resolution</span><label class=fx-px><input type=number min=32 max=512 step=4 value="${b.size.px}" data-psbpx data-id=${id} aria-label="Sprite resolution in pixels"> px</label><small class=mut>sharpness of each sprite; Size changes how big they look</small></div></details>
    <div class=row><button class="btn pri sm" data-act=psbrender data-id=${id}>Render</button><button class="btn sm${spSaved(s)?'':' pri'}" data-act=psbsave data-id=${id}>${spSaved(s)?'Save':'Save as a row'}</button>${spSaved(s)?`<button class=link data-act=psbsaveas data-id=${id}>Save as new</button>`:''}<button class=link data-act=psassign data-id=${id}>Assign to stickers</button><button class=link data-act=pschat data-id=${id}>Test in chat</button></div></div></div>
  ${rs.length?`<div class=ps-brs>${rs.map(r=>spBurstCard(s,b,r)).join('')}</div>`:''}</div>`}
function spBurstRedraw(id){const s=SPBS[id],el=typeof document!=='undefined'&&document.querySelector?document.querySelector(`[data-psb="${id}"]`):null;if(s&&el)el.outerHTML=spBurstHtml(s)}
const spBurstPreviewKey=b=>JSON.stringify([b.pack,b.preset,fxClean(b.par),spBurstSize(b)]);
async function spBurstPreview(id){const s=SPBS[id]||spFind(id);if(!s)return;const b=spBurstState(s,spHint());if(b.busy){b.again=1;return}
 if((s.n_picked||0)<1&&(s.source||{}).kind!=='stickers')return;b.busy=1;
 const request=spBurstPreviewKey(b);
 const r=await post(`/api/particles/${id}/preview`,{...(b.pack?{pack_id:b.pack}:{}),...(b.preset?{preset:b.preset}:{}),params:{...fxClean(b.par),...spBurstSize(b)},size:256});b.busy=0;
 if(request!==spBurstPreviewKey(b))b.again=1;
 else if(r.ok){b.pv=r.j.url;b.shown=fxPick(r.j.params);const img=typeof document!=='undefined'&&document.getElementById?document.getElementById('psbpv-'+id):null;
  if(img){img.src=r.j.url;const sp=img.parentElement&&img.parentElement.querySelector('.spin');if(sp)sp.remove()}
  const root=typeof document!=='undefined'&&document.querySelector?document.querySelector(`[data-psb="${id}"]`):null;
  if(root)for(const [k] of FXSL){const inp=root.querySelector(`[data-psbp=${k}]`);if(inp&&r.j.params[k]!==undefined&&document.activeElement!==inp){inp.value=r.j.params[k];if(inp.nextElementSibling)inp.nextElementSibling.textContent=r.j.params[k]}}}
 else toast(r.j.error||'No preview',1);
 if(b.again){b.again=0;return spBurstPreview(id)}}
async function spBurstReload(id){const r=await api('/api/particles/'+id);if(r.ok){if(SP.set&&SP.set.id===id)SP.set=r.j;SPBS[id]=r.j;if(SPL.detail)SPL.detail[id]=r.j;spBurstRedraw(id)}}
const spBurstSet=el=>{const s=SPBS[el.dataset.id]||spFind(el.dataset.id);return s?[s,spBurstState(s,spHint())]:[null,null]};
ACT.psbpreset=el=>{const [s,b]=spBurstSet(el);if(!s)return;b.preset=el.dataset.n;b.par={};b.shown={};spBurstRedraw(s.id);spBurstPreview(s.id)};
ACT.psbshuffle=el=>{const [s,b]=spBurstSet(el);if(!s)return;b.par.seed=1+Math.floor(Math.random()*9999);b.par.touched=1;spBurstPreview(s.id)};
document.addEventListener('input',ev=>{const t=ev.target;if(!t||!t.dataset)return;
 if(t.dataset.psbp){const [s,b]=spBurstSet({dataset:{id:t.dataset.id}});if(!s)return;b.par[t.dataset.psbp]=+t.value;b.par.touched=1;if(t.nextElementSibling)t.nextElementSibling.textContent=t.value;clearTimeout(b.pvT);b.pvT=setTimeout(()=>spBurstPreview(s.id),220)}
 else if(t.dataset.psbpx!==undefined){const [s,b]=spBurstSet({dataset:{id:t.dataset.id}});if(!s)return;b.size.px=Math.max(32,Math.min(512,Math.round(+t.value)||100));clearTimeout(b.pvT);b.pvT=setTimeout(()=>spBurstPreview(s.id),350)}});
document.addEventListener('change',ev=>{const t=ev.target;if(!t||!t.dataset||t.dataset.psbpack===undefined)return;const [s,b]=spBurstSet({dataset:{id:t.dataset.psbpack}});if(!s)return;b.pack=t.value;spBurstRedraw(s.id);spBurstPreview(s.id)});
const spSavedMotion=(s,b)=>({preset:spPresetOf(s,b),params:{...fxClean(b.shown),...fxClean(b.par),...spBurstSize(b)}});
const spSaved=s=>!!s&&(!('saved_at' in s)||s.saved_at!=null);
const spSavedDone=()=>{if(typeof ptForget==='function')ptForget();if(typeof LCI!=='undefined'&&LCI!==null&&typeof ptLoad==='function'){const cur=LCL[LCI];if(cur)ptLoad(cur)}};
ACT.psbsave=async el=>{const [s,b]=spBurstSet(el);if(!s)return;const was=spSaved(s),r=await post(`/api/particles/${s.id}`,{motion:spSavedMotion(s,b),save:true});if(!r.ok)return toast(r.j.error||'Could not save particles',1);if(SP.set&&SP.set.id===s.id)SP.set=r.j;SPL.detail[s.id]=r.j;SPBS[s.id]=r.j;spLibRefresh();spBurstRedraw(s.id);spSavedDone();toast(was?'Saved: this row now has the new motion':'Saved as a new row under the sticker')};
ACT.psbsaveas=async el=>{const [s,b]=spBurstSet(el);if(!s)return;const r=await post(`/api/particles/${s.id}/save-as-new`,{motion:spSavedMotion(s,b)});if(!r.ok)return toast(r.j.error||'Could not save a new row',1);SP.entry=(SP.entry||0)+1;SP.set=r.j;SP.target=r.j.id;SP.eid='';SPL.detail[r.j.id]=r.j;if(SPL.sets)SPL.sets.push(r.j);spBurstState(r.j,SP.pack);spDraw();spBurstPreview(r.j.id);spSavedDone();toast('Saved as a new row; the first one is unchanged')};
ACT.pschat=async el=>{const [s,b]=spBurstSet(el);if(!s)return;const saved=await post(`/api/particles/${s.id}`,{motion:spSavedMotion(s,b)});if(!saved.ok)return toast(saved.j.error||'Could not save particles',1);if(SP.set&&SP.set.id===s.id)SP.set=saved.j;SPL.detail[s.id]=saved.j;
 const owners=saved.j.owner||[];let target;for(const o of owners){const p=packById(o.pack_id),st=p&&(p.stickers||[]).find(x=>x.id===o.sticker_id);if(st){target={...st,pack_id:p.id};break}}if(!target)return ACT.psassign({dataset:{id:s.id}});CH.pending=target;location.hash='#/chat'};
ACT.psbrender=async el=>{const [s,b]=spBurstSet(el);if(!s)return;if(!b.pack)return toast('Choose the pack this burst is for',1);
 el.disabled=true;const r=await post(`/api/particles/${s.id}/render`,{pack_id:b.pack,...(b.preset?{preset:b.preset}:{}),params:{...fxClean(b.par),...spBurstSize(b)}});el.disabled=false;
 if(!r.ok)return toast(r.j.error||'Could not render',1);
 await spBurstReload(s.id);if(typeof ptCounts==='function'&&b.pack)ptCounts(b.pack);toast(r.j.status==='READY'?'Rendered: the burst is below':'Rendered, but a Telegram limit is broken: see its checks',r.j.status!=='READY')};
ACT.psbadd=async el=>{const id=el.dataset.id,pk=el.dataset.p,s=SPBS[id]||spFind(id);el.disabled=true;
 const sid=el.dataset.s||((SP.scope||{}).sticker_id)||undefined,r=await post(`/api/particles/${id}/add`,{renders:[el.dataset.r],pack_id:pk,...(sid?{sticker_id:sid}:{})});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not add it',1)}
 toast(`Added to ${s?spPackName(s,pk):'the pack'}: the burst is a sticker of the pack now`);
 if(typeof loadLib==='function')await loadLib();await spBurstReload(id);if(typeof ptCounts==='function')ptCounts(pk);if(typeof ptForget==='function')ptForget()};
/* the wizard's third card: pick a set already saved and put it on this pack (nothing is drawn, nothing is spent) */
function spExistingHtml(S){const sets=SPL.sets;
 if(!sets){spLibSync();return '<div class=fx-job><span class=spin></span> <span class=mut>Reading the particle sets…</span></div>'}
 if(!sets.length)return `<div class=mut>No saved particles yet.</div>`;
 return `<div class=ps-pick>${sets.map(s=>{const on=(s.owner||[]).some(o=>S.sel.has(o.sticker_id)),strip=(s.cells||[]).filter(c=>c.picked).slice(0,4);
  return `<div class=ps-pickrow><span class=ps-strip>${strip.map(c=>`<span class=ps-cell>${c.url?`<img src="${esc(c.url)}" alt="" loading=lazy>`:''}</span>`).join('')||'<span class=mut>no cells</span>'}</span>
   <b>${esc(s.name||s.id)}</b><small class=mut>${s.n_picked} picked${(s.used_in||[]).length?` · used in: ${(s.used_in||[]).map(p=>esc(p.name||p.id)).join(', ')}`:''}</small>
   ${on?'<span class=mut>linked to these stickers</span>':`<button class="btn sm pri" data-act=pspickset data-id=${esc(s.id)}>Use this set</button>`}</div>`}).join('')}</div>`}
ACT.pspickset=async el=>{const r=await post(`/api/particles/${el.dataset.id}/link`,{sticker_ids:spOwners(SP)});if(!r.ok)return toast(r.j.error||'Could not link it',1);SP.set=r.j;SP.target=r.j.id;SP.eid='';spDraw();spBurstPreview(r.j.id)};
/* from the pack's particle studio: start the wizard with this pack, or put a saved set on it */
ACT.psmakepack=el=>spEnter({pack_id:el.dataset.p});
ACT.pspickpack=el=>{spEnter({pack_id:el.dataset.p});spKind('existing');spDraw()};
ACT.pspackassign=el=>{spEnter({pack_id:el.dataset.p});return ACT.pspickset(el)};

ACT.agpscope=async el=>{spEnter({pack_id:el.dataset.p});spKind(el.dataset.k);if(el.dataset.id){SP.entry=(SP.entry||0)+1;const r=await api('/api/particles/'+el.dataset.id);if(r.ok){SP.set=r.j;SP.target=r.j.id;SP.eid=''}}spDraw()};
ACT.agpapprove=async el=>{const n=+String(el.dataset.g).replace(/\D/g,'');const r=await api('/api/generations/'+n);if(!r.ok)return toast(r.j.error,1);GM.set(n,r.j);SES={prompt:r.j.prompt||'',gens:[n],off:[],pack:''};saveSes();location.hash='#/studio';await RENDER.generate();await ACT.spapprove({dataset:{g:el.dataset.g}})};

ACT.psrecover=el=>{const parents=(LIB.packs||[]).filter(p=>p.id!==el.dataset.p&&p.stickers.length);dlg(`<h2>Use as particle pack</h2><label>Parent pack <select id=psrecoverparent data-psrecoverparent><option value="">Select parent pack</option>${parents.map(p=>`<option value=${esc(p.id)}>${esc(p.name)}</option>`).join('')}</select></label><div id=psrecovertargets></div><label class=ps-pack><input type=checkbox id=psrecoverall> All stickers in this pack</label><div class=row><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=psrecovergo data-p=${esc(el.dataset.p)} data-s=${esc(el.dataset.s)}>Use as particles · free</button></div>${parents.length?'':'<p class=mut>Add or approve the parent stickers as a pack first.</p><button class=btn data-act=psrecovercreate>Create parent stickers</button>'}`)};
ACT.psrecovercreate=()=>{closeDlg();if(typeof lcClose==='function')lcClose();location.hash='#/studio'};
document.addEventListener('change',ev=>{const t=ev.target;if(!t||!t.dataset||t.dataset.psrecoverparent===undefined)return;const p=packById(t.value),root=$('psrecovertargets');if(root)root.innerHTML=p?`<span class=mut>Target stickers</span>${p.stickers.map(st=>`<label class=ps-pack><input type=checkbox data-psrecoverowner=${esc(st.id)} checked>${media(st)} ${esc(st.name)}</label>`).join('')}`:''});
ACT.psrecovergo=async el=>{const pid=$('psrecoverparent').value;if(!pid)return toast('Select the parent pack',1);const source=(LIB.packs||[]).find(p=>p.id===el.dataset.p),ids=$('psrecoverall').checked?(source.stickers||[]).map(st=>st.id):[el.dataset.s],owners=[...document.querySelectorAll('[data-psrecoverowner]')].filter(c=>c.checked).map(c=>({pack_id:pid,sticker_id:c.dataset.psrecoverowner}));if(!owners.length)return toast('Select a target sticker',1);
 const parent=packById(pid),links=owners.map(o=>((parent.stickers.find(st=>st.id===o.sticker_id)||{}).particles||[]).slice(-1)[0]),target=links.every(Boolean)&&new Set(links).size===1?links[0]:undefined;el.disabled=true;
 const r=await post('/api/particles',{from_stickers:ids,parent_pack_id:pid,owners,target,...(!target?{name:(source.name||'Recovered')+' particles'}:{})});el.disabled=false;if(!r.ok)return toast(r.j.error,1);closeDlg();if(typeof lcClose==='function')lcClose();await loadLib();spSetsForget();spEnter({pack_id:pid,sticker_ids:owners.map(o=>o.sticker_id)});SP.entry=(SP.entry||0)+1;SP.set=r.j;SP.target=r.j.id;SP.eid='';SPL.detail[r.j.id]=r.j;spDraw();spBurstPreview(r.j.id)};
