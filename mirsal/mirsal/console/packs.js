/* Pack manager (DESKTOP_05): metadata, drag-reorder grid, cover, rename, preview, export. */
'use strict';
let DRAG=null;
RENDER.pack=async id=>{await loadLib();PACK_ID=id;drawCol2();drawPack()};
function drawPack(){
 const p=packById(PACK_ID),el=$('s-pack');
 if(!p){el.innerHTML='<div class=card>Pack not found. <a href="#/library">Back to library</a></div>';return}
 const n=p.stickers.length,anim=p.stickers.filter(s=>s.type==='animated').length;
 el.innerHTML=`<div class=page>
  <div class=row style="margin-top:0"><button class="btn sm" data-act=nav data-to=library>${ic('back')} Library</button></div>
  <div class=card><div class=phead><div class=cover style="width:84px;height:84px">${coverMedia(p)}</div>
   <div class=pt><h1 style="margin:0">${esc(p.name)}</h1><span class=mut>${n} stickers${anim?` · ${anim} animated`:''} · a Telegram set takes up to 120</span></div>
   <div class=pa>
    <button class=btn data-act=pkadd>${ic('plus')} Add sticker</button><button class=btn data-act=pkrename>${ic('edit')} Rename</button>
    <button class=btn data-act=pkpreview ${n?'':'disabled'}>${ic('eye')} Preview</button>${n&&typeof trShareBtn==='function'?trShareBtn(p.id):''}${n?`<a class=btn href="/api/packs/${p.id}/export.zip" download title="Every sticker file of this pack in one zip: .webm for the animated ones, .png / .webp for the static ones, and a manifest.json">${ic('download')} Download .zip</a>`:`<button class=btn disabled>${ic('download')} Download .zip</button>`}${typeof ME==='undefined'||!ME||ME.role==='owner'?`<button class="btn pri" data-act=tgsend ${n?'':'disabled'}>${ic('telegram')} Send to Telegram</button>`:''}
    <button class="btn dng" data-act=pkdel title="Move this pack to the trash. You can restore it, or delete it for good, from Settings, Trash.">${ic('trash')} Delete pack</button></div></div></div>
  <div class=row><span class=mut>Click a sticker to view it. Drag to reorder, or drop one on another pack in the Packs column to move it. Tick the square or drag a box to select several (Shift adds, Ctrl un-selects).</span></div>${selBarHtml(n)}
   ${n?`<div class="grid selgrid ${SEL.size?'selmode':''}" id=pkgrid>${p.stickers.map(s=>`<div class="cell ${s.id===p.cover?'cov':''} ${SEL.has(selKey(p.id,s.id))?'sel':''}" draggable=true data-act=stview data-id=${s.id} title="Click to view, drag to reorder"><span class="selbox ${SEL.has(selKey(p.id,s.id))?'on':''}" data-act=lsel data-p=${p.id} data-id=${s.id} title="Select"></span>${s.id===p.cover?'<span class=badge2>cover</span>':''}${ptBadge(p.id,s.id)}${media(s)}
    <div class=hov><button data-act=stview data-id=${s.id} title=Preview>${ic('eye')}</button><button data-act=stedit data-id=${s.id} title="${(s.source&&s.source.generation)?'Edit in the Studio (text, emoji; image and animation together)':s.type==='static'?'Edit a copy in the editor':'Edit: add text or emoji, trim'}">${ic('edit')}</button>${s.type==='animated'?`<button data-act=stanim data-id=${s.id} title="Timeline (trim, frame rate, export)">${ic('play')}</button>`:''}<button data-act=stcover data-id=${s.id} title="Set as cover">${ic('star')}</button><button data-act=stdel data-id=${s.id} title=Delete>${ic('trash')}</button></div>
    <div class=cap data-act=stname data-id=${s.id} title="Rename / change emoji">${esc(s.emoji)} ${esc(s.name)} · ${s.kb}KB</div></div>`).join('')}</div>`
   :`<div class=card style="text-align:center;padding:40px"><h2>This pack is empty</h2><p class=mut>Make stickers in the Studio, or create one from a photo.</p><button class="btn pri" data-act=pkadd>${ic('plus')} Add sticker</button> <button class=btn data-act=nav data-to=generate>${ic('gen')} Generate</button></div>`}
  ${pkPsHtml(p)}</div>`;
 ptCounts(p.id)}
const sOf=id=>packById(PACK_ID).stickers.find(s=>s.id===id);
async function pkUpdate(body,msg){const r=await post('/api/packs/'+PACK_ID,body);if(!r.ok)return toast(r.j.error,1);await loadLib();drawPack();if(msg)toast(msg)}
ACT.pkadd=()=>{Ed.targetPack=PACK_ID;location.hash='#/create'};
ACT.pkrename=()=>askText('Rename pack',packById(PACK_ID).name,n=>pkUpdate({name:n},'Renamed'));
/* what Delete pack will do, said before it is done (plain text: confirmDlg escapes it): the pack goes to the TRASH with its stickers and files untouched (Settings > Trash restores it or deletes it for good, flow/purge.py); the stickers that came from a batch also stay in that batch */
function pkDelText(p){const sts=p.stickers||[],gens=[...new Set(sts.map(s=>(s.source||{}).generation).filter(Boolean))].sort(),back=sts.filter(s=>(s.source||{}).generation).length,only=sts.length-back;
 if(!sts.length)return `Delete the pack “${p.name}”? It has no stickers. It goes to the trash and you can restore it from Settings, Trash. Its particle sets stay in the Library.`;
 return `Delete the pack “${p.name}”? It goes to the trash with its ${sts.length} sticker${sts.length===1?'':'s'}: nothing is deleted yet, and you can restore it, or delete it for good, from Settings, Trash. ${back?`${back} of its stickers came from batches (${gens.join(', ')}), which keep their own copies. `:''}${only?`${only} exist only in this pack. `:''}Its particle sets stay in the Library.`}
ACT.pkdel=()=>confirmDlg(pkDelText(packById(PACK_ID)),async()=>{const r=await post(`/api/packs/${PACK_ID}/delete`);if(r.ok){await loadLib();location.hash='#/library'}else toast(r.j.error,1)});
ACT.stanim=el=>{location.hash=`#/animate/${PACK_ID}/${el.dataset.id}`};
ACT.stcover=el=>pkUpdate({cover:el.dataset.id},'Cover changed');
ACT.stdel=el=>{const s=sOf(el.dataset.id);confirmDlg(`Delete "${s.name}"?`,async()=>{const r=await post(`/api/packs/${PACK_ID}/stickers/${s.id}/delete`);if(r.ok){await loadLib();drawPack()}else toast(r.j.error,1)})};
ACT.stedit=el=>{const s=sOf(el.dataset.id);if(s.source&&s.source.generation)return studioEditSticker(+String(s.source.generation).replace(/\D/g,''),s.source.index);
  if(s.type==='animated')return editAnimatedSticker(PACK_ID,s.id);Ed.openImage('/lib/'+encodeURIComponent(s.file),{outlined:true,name:s.name+' copy',emoji:s.emoji,pack:PACK_ID})};
ACT.stview=el=>{const p=packById(PACK_ID);LCL=p.stickers.map(x=>({...x,pack_id:p.id,pack:p.name}));lcOpen(LCL.findIndex(x=>x.id===el.dataset.id))};
ACT.stname=el=>{const s=sOf(el.dataset.id);dlg(`<h2>Sticker details</h2><div class=fld><label>Name</label><input type=text id=sn value="${esc(s.name)}"></div><div class=fld><label>Emoji tag (at least one is required by Telegram)</label><input type=text id=se value="${esc(s.emoji)}"></div>
  <div class=fld><label>File name${s.file_name?' (from the generator)':''}</label><input type=text readonly value="${esc(s.file_name||s.file)}" onfocus="this.select()"><div class=mut style="margin-top:3px">${s.file_name?`stored as ${esc(s.file)}`:''}</div></div>
  <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=stsave data-id=${s.id}>Save</button></div>`)};
ACT.stsave=async el=>{const r=await post(`/api/packs/${PACK_ID}/stickers/${el.dataset.id}`,{name:$('sn').value,emoji:$('se').value});closeDlg();if(!r.ok)return toast(r.j.error,1);await loadLib();drawPack()};
ACT.pkpreview=()=>{const p=packById(PACK_ID);let b='chat';
 const draw=()=>{dlg(`<h2>${esc(p.name)}</h2><div class=toggles style="margin-bottom:8px">${['chat','light','dark','checker'].map(x=>`<button class="${x===b?'act':''}" data-act=pvbg data-b=${x}>${x}</button>`).join('')}</div>
  <div class="bg-${b}" style="border-radius:14px;padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px">${p.stickers.map(s=>`<div style="aspect-ratio:1">${media(s)}</div>`).join('')}</div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button></div>`);$('dlg').firstChild.style.width='min(760px,94vw)';$('dlg').querySelectorAll('img,video').forEach(m=>{m.style.cssText='width:100%;height:100%;object-fit:contain'})};
 ACT.pvbg=e=>{b=e.dataset.b;draw()};draw()};
/* drag reorder (HTML5 DnD, delegated) */
const S_PACK=$('s-pack');
S_PACK.addEventListener('dragstart',e=>{const c=e.target.closest('.cell[data-id]');if(!c)return;DRAG=c.dataset.id;e.dataTransfer.effectAllowed='move';e.dataTransfer.setData('text/plain',DRAG)});
S_PACK.addEventListener('dragover',e=>{const c=e.target.closest('.cell[data-id]');if(!c||!DRAG)return;e.preventDefault();S_PACK.querySelectorAll('.over').forEach(x=>x.classList.remove('over'));c.classList.add('over')});
S_PACK.addEventListener('drop',e=>{const c=e.target.closest('.cell[data-id]');if(!c||!DRAG)return;e.preventDefault();const from=DRAG;DRAG=null;if(from===c.dataset.id)return drawPack();
 const all=packById(PACK_ID).stickers.map(s=>s.id),fi=all.indexOf(from),ti=all.indexOf(c.dataset.id),ids=all.filter(i=>i!==from),at=ids.indexOf(c.dataset.id)+(fi<ti?1:0);ids.splice(at,0,from);pkUpdate({order:ids},'Order saved')});
S_PACK.addEventListener('dragend',()=>{DRAG=null;S_PACK.querySelectorAll('.over').forEach(x=>x.classList.remove('over'))});

/* drop a sticker on a pack row in the Packs column = move it to that pack */
const C2=$('col2');
C2.addEventListener('dragover',e=>{const r=e.target.closest('.crow');if(!r||!DRAG||r.dataset.id===PACK_ID)return;e.preventDefault();C2.querySelectorAll('.over').forEach(x=>x.classList.remove('over'));r.classList.add('over')});
C2.addEventListener('dragleave',e=>{const r=e.target.closest('.crow');if(r)r.classList.remove('over')});
C2.addEventListener('drop',async e=>{const r=e.target.closest('.crow');if(!r||!DRAG||r.dataset.id===PACK_ID)return;e.preventDefault();const sid=DRAG;DRAG=null;
 if(SEL.size>1&&SEL.has(selKey(PACK_ID,sid)))return moveSelection(r.dataset.id);          // dragging one of several selected stickers carries the whole selection
 const res=await post(`/api/packs/${PACK_ID}/stickers/${sid}/move`,{to:r.dataset.id});if(!res.ok)return toast(res.j.error,1);
 const to=packById(r.dataset.id).name;await loadLib();drawPack();drawCol2();toast(`Moved to ${to}`)});

/* Library carousel: big view of the current list (Recent / My Stickers / a pack) with prev/next, thumbnails, arrow keys */
function lcOpen(i){LCI=Math.max(0,i);lcDraw()}
function lcClose(){LCI=null;$('modal').classList.remove('on')}
function lcStep(d){if(LCL.length){LCI=(LCI+d+LCL.length)%LCL.length;lcDraw()}}
let LCBG='checker';
function lcDraw(){const s=LCL[LCI];if(!s)return lcClose();
 const bgs=['checker','light','dark','wall'].map(x=>`<button class="${x===LCBG?'act':''}" data-act=lcbg data-b=${x}>${x}</button>`).join('');
 const th=LCL.map((x,k)=>`<div class="thumb ${k===LCI?'on':''}" data-act=lcgo data-i=${k} title="${esc(x.name)}">${media(x)}</div>`).join('');
 $('modal').innerHTML=`<div class=mbox style="width:min(760px,96vw)"><div class=mrow><button class="btn nav" data-act=lcprev>‹</button>
  <div style="flex:1;min-width:0"><b>${esc(s.emoji)} ${esc(s.name)}</b><div class=mut>${LCI+1}/${LCL.length} · in <a href="#/pack/${s.pack_id}" data-act=lcpack data-id=${s.pack_id}>${esc(s.pack)}</a> · ${s.type} · ${s.w}×${s.h} · ${s.kb}KB</div></div>
  <div class=toggles>${bgs}</div><button class="btn nav" data-act=lcnext>›</button><button class=btn data-act=lcclose>✕</button></div>
  <div class="pvbox bg-${LCBG}" style="margin-top:10px;min-height:0">${media(s)}</div>
  <div class=row style="justify-content:center">${s.source&&s.source.generation?`<button class="btn pri" data-act=lcstudioedit>${ic('edit')} Edit in Studio</button><button class=btn data-act=lcopenstudio>${ic('gen')} Open in Studio</button>`:s.type==='static'?`<button class=btn data-act=lcedit>${ic('edit')} Edit a copy</button>`:`<button class=btn data-act=lcedit>${ic('edit')} Edit (text, trim…)</button><button class=btn data-act=lctimeline>${ic('play')} Timeline</button>`}<button class=btn data-act=psrecover data-p=${s.pack_id} data-s=${s.id}>Use as particle pack</button><button class=btn data-act=lcmove>${ic('plus')} Move to pack…</button><button class=btn data-act=lcpack data-id=${s.pack_id}>Open pack</button><button class="btn pri" data-act=lcsend>${ic('chat')} Send to chat</button></div>
  <div id=pk-psline class=pk-psline>${pkStickerLine(s)}</div>
  <div class=thumbs style="justify-content:center;max-height:130px;overflow:auto">${th}</div><div class=mut style="text-align:center">← → to browse, Esc to close</div></div>`;
 $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')lcClose()};
 const on=$('modal').querySelector('.thumb.on');if(on)on.scrollIntoView({block:'nearest',inline:'center'})}
ACT.lcsend=()=>{const s=LCL[LCI];lcClose();CH.pending=s;location.hash='#/chat'};
ACT.lcopen=el=>lcOpen(+el.dataset.i);ACT.lcclose=lcClose;ACT.lcprev=()=>lcStep(-1);ACT.lcnext=()=>lcStep(1);
ACT.lcgo=el=>{LCI=+el.dataset.i;lcDraw()};ACT.lcbg=el=>{LCBG=el.dataset.b;lcDraw()};
ACT.lcpack=el=>{lcClose();location.hash='#/pack/'+el.dataset.id};
ACT.lcedit=()=>{const s=LCL[LCI];lcClose();if(s.type==='static')Ed.openImage('/lib/'+encodeURIComponent(s.file),{outlined:true,name:s.name+' copy',emoji:s.emoji,pack:s.pack_id});else editAnimatedSticker(s.pack_id,s.id)};
ACT.lctimeline=()=>{const s=LCL[LCI];lcClose();location.hash=`#/animate/${s.pack_id}/${s.id}`};
ACT.lcmove=()=>{const s=LCL[LCI];pickPack(async pid=>{if(pid===s.pack_id)return toast('Already in that pack',1);
 const r=await post(`/api/packs/${s.pack_id}/stickers/${s.id}/move`,{to:pid});if(!r.ok)return toast(r.j.error,1);
 const to=packById(pid)?.name||'pack';await loadLib();lcClose();if(route_==='pack')drawPack();else if(route_==='library')RENDER.library();drawCol2();toast(`Moved to ${to}`)},'Move to pack')};
document.addEventListener('keydown',e=>{if(LCI===null||$('dlg').classList.contains('on'))return;if(e.key==='Escape')lcClose();if(e.key==='ArrowRight')lcStep(1);if(e.key==='ArrowLeft')lcStep(-1)});

/* ---------- Particles of a sticker (docs/effects.md): what was created for it and what was saved, under the big preview and, for the stickers of the open batch, in the Studio (particles.js).
   The data is GET /api/packs/{id}/stickers/{sid}/particles (an engine function, flow/effects.for_sticker); the pack grid's little counter is ONE request for the whole pack,
   GET /api/packs/{id}/particles. ptHtml/ptBody/ptCard are pure (tests/js); every button carries its pack and sticker (data-p, data-s), so it works wherever the gallery is drawn. */
const PKPT={d:{},c:{},sets:{},bursts:{}};          // d: sticker id -> the route's answer; c: pack id -> {sticker id: {created, saved}}; sets/bursts: the pack's particle studio
const ptWhy=w=>(typeof FXWHY!=='undefined'&&FXWHY[w])||String(w).replace(/_/g,' ');
const ptKb=b=>b>=1024?Math.round(b/1024)+' KB':(b||0)+' B';
const ptPackName=id=>{const p=typeof packById==='function'?packById(id):null;return p?p.name:'a pack'};
function ptCard(i,s){const ok=i.url&&!i.missing,why=[...(i.warnings||[]),...(i.status==='FAILED'?(i.blocks||[]):[])].map(ptWhy),
  kind=i.mode==='video'?`video, cell ${i.cell}${i.assigned?' (the one this sticker gets)':''} · shared by its group`:'simulated';
 return `<div class="pk-pt-card${i.usable?'':' bad'}"><div class=pk-pt-m>${ok?`<video src="${esc(i.url)}" autoplay loop muted playsinline preload=metadata></video>`:`<span class=mut>${i.status==='FAILED'?'Failed':'File missing'}</span>`}${i.added_to?`<span class=pk-pt-sv>Saved in ${esc(ptPackName(i.added_to))}</span>`:''}</div>
  <div class=pk-pt-id><b>${esc(i.effect)} · ${esc(i.result)}</b><small>${esc(kind)} · ${ptKb(i.bytes)}</small></div>
  ${why.length?`<ul class=pk-pt-w>${why.map(w=>`<li>${esc(w)}</li>`).join('')}</ul>`:''}
  <div class=pk-pt-a>${i.usable&&!i.added_to?`<button class="btn sm pri" data-act=ptadd data-e=${esc(i.effect)} data-r=${esc(i.result)}${s?` data-p=${esc(s.pack_id)} data-s=${esc(s.id)}`:''}>Add to pack</button>`:''}<button class="btn sm" data-act=ptopen data-e=${esc(i.effect)}>Open effect</button></div></div>`}
function ptGroupRuns(j){const sets=j.sets||[],groups=new Map();
 const imported=effect=>!effect?[]:sets.filter(x=>(x.source||{}).effect===effect||(x.imports||[]).some(v=>String(v).startsWith(effect+'/'))||(x.cells||[]).some(c=>String(c.import||'').startsWith(effect+'/'))).map(x=>x.id);
 if(Array.isArray(j.runs)){for(const r of j.runs)groups.set(r.effect,{...r,cells:r.cells||[],saved:r.saved||[],imported_as:[...new Set([...(r.imported_as||[]),...imported(r.effect)])]})}
 else{for(const c of j.created||[]){const key=c.effect||'unknown';if(!groups.has(key))groups.set(key,{effect:c.effect,mode:c.mode,cells:[],saved:[],imported_as:imported(c.effect)});groups.get(key).cells.push(c)}
  for(const c of j.saved||[]){const key=c.effect||'saved:'+c.pack_id;if(!groups.has(key))groups.set(key,{effect:c.effect,mode:'video',cells:[],saved:[],imported_as:imported(c.effect)});groups.get(key).saved.push(c)}}
 return [...groups.values()].filter(r=>!r.imported_as.length)}
function ptRunCard(run,s){const cells=run.cells||[],saved=run.saved||[],sprites=cells.length?cells:saved,available=sprites.some(c=>c.url&&!c.missing),why=[...new Set(cells.flatMap(c=>[...(c.warnings||[]),...(c.status==='FAILED'?(c.blocks||[]):[])]))],label=run.name||(run.mode==='video'?'Animated sprites':'Image sprites');
 return `<div class="pk-pt-card pk-pt-run" data-particle-run=${esc(run.effect||'saved')}><b>${esc(label)}</b><small>${sprites.length} sprite${sprites.length===1?'':'s'}${run.effect?' · '+esc(run.effect):''}</small><div class=ps-strip>${sprites.slice(0,8).map(c=>`<span class=ps-cell>${c.url&&!c.missing?`<video src="${esc(c.url)}" autoplay loop muted playsinline preload=metadata></video>`:'<span class=mut>Missing</span>'}</span>`).join('')}</div>
 ${available&&run.effect?`<button class="btn sm pri" data-act=ptrunsim data-e=${esc(run.effect)} data-mode=${esc(run.mode||'sim')} data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${why.length?'Use it anyway · Simulator':'Use in simulator · free'}</button>`:!available?'<span class=mut>No readable sprites. Open the original run to recover its media.</span>':''}
 <details><summary>Original sprite clips${saved.length?' · '+saved.length+' added to library':''}</summary>${cells.map(c=>ptCard(c,s)).join('')}${saved.length?`<div class=pk-pt-saved>${saved.map(c=>`<button class=pk-pt-s data-act=ptsaved data-id=${esc(c.pack_id)} title="${esc(c.name)} in ${esc(c.pack)}">${c.url&&!c.missing?`<video src="${esc(c.url)}" autoplay loop muted playsinline preload=metadata></video>`:'<span class=mut>missing</span>'}<small>${esc(c.name)}</small></button>`).join('')}</div>`:''}${run.effect?`<button class=link data-act=ptopen data-e=${esc(run.effect)}>Open original run</button>`:''}</details></div>`}
function ptRowMedia(r){if(r.preview)return `<video src="${esc(r.preview)}" autoplay loop muted playsinline preload=metadata></video>`;
 const sp=(r.sprites||[]).filter(c=>!c.missing).slice(0,4);return sp.length?`<span class=pk-row-strip>${sp.map(c=>c.clip_url?`<video src="${esc(c.clip_url)}" autoplay loop muted playsinline preload=metadata></video>`:`<img src="${esc(c.url)}" alt="" loading=lazy>`).join('')}</span>`:'<span class=mut>No picture</span>'}
function ptRow(r,s,draft){const inPack=(r.in_pack||[]).length,a=r.addable,meta=[r.n_sprites?`${r.n_sprites} sprite${r.n_sprites===1?'':'s'}`:'',r.credits?spCredits(r.credits):'free',r.job,r.shared_with?`shared with ${r.shared_with} other sticker${r.shared_with===1?'':'s'}`:''].filter(Boolean);
 return `<div class="pk-row${draft?' draft':''}" data-particle-row=${esc(r.id)}><span class=pk-row-v>${draft?'Draft':'v'+r.version}</span><div class=pk-pt-m>${ptRowMedia(r)}</div>
  <div class=pk-row-id><b>${esc(r.label)}</b><small>${esc(meta.join(' · '))}</small></div>
  <div class=pk-row-a><button class="btn sm" data-act=psshow data-id=${esc(r.id)} data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>Open</button><button class=link data-act=tkreport data-k=particle_set data-id=${esc(r.id)} title="Something wrong with these particles? Send a report">Report</button>
  ${inPack?'<small class=mut>In pack ✓</small>':a&&!draft?`<button class="btn sm pri" data-act=psbadd data-id=${esc(r.id)} data-r=${esc(a.render)} data-p=${esc(a.pack_id||s.pack_id)} data-s=${esc(s.id)}>Add to pack</button>`:''}</div></div>`}
function ptRowsHtml(j,s){const rows=j.rows||[],drafts=j.drafts||[],runs=ptGroupRuns(j);
 return `<div class=pk-rows>${rows.map(r=>ptRow(r,s,false)).join('')}${drafts.map(r=>ptRow(r,s,true)).join('')}${runs.map(r=>ptRunCard(r,s)).join('')}</div>`}
const ptCount=j=>(j.rows||[]).length+(j.drafts||[]).length+ptGroupRuns(j).length;
function ptHtml(j,s){const head=extra=>`<div class=pk-pt-h><b>Particles</b>${extra||''}</div>`;
 if(!j)return head()+`<div class=pk-pt-load><div class=spin></div><span class=mut>Looking for particles…</span></div>`;
 if(j.error)return head()+`<div class=mut>${esc(j.error)}</div>`;
 const make=label=>j.can_make===false?'':`<button class="btn sm pri" data-act=ptmake data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${ic('fx')} ${label}</button>`;
 if(!ptCount(j))return head()+`<div class=pk-pt-empty><b>No particles yet</b>${make('Make particles')}</div>`;
 return head(`<span class=mut>${(j.rows||[]).length} saved</span>${make('New version')}`)+ptBody(j,s)}
function ptBody(j,s){if(!j)return`<div class=pk-pt-load><div class=spin></div><span class=mut>Looking for particles…</span></div>`;if(j.error)return`<div class=mut>${esc(j.error)}</div>`;
 return ptCount(j)?ptRowsHtml(j,s):''}
function ptBadge(pid,sid){const c=(PKPT.c[pid]||{})[sid];return c&&c.created+c.saved?`<span class=pk-pt-n title="${c.created} particle${c.created===1?'':'s'} made, ${c.saved} saved">${ic('fx')}${c.created+c.saved}</span>`:''}
/* a person's change (a take added, particles made) makes what was read stale */
const ptForget=()=>{PKPT.c={};PKPT.d={}};
async function ptLoad(s){const r=await api(`/api/packs/${s.pack_id}/stickers/${s.id}/particles`);PKPT.d[s.id]=r.ok?r.j:{error:r.j.error||'Could not read the particles'};
 const cur=LCI===null?null:LCL[LCI],el=$('pk-psline');if(el&&cur&&cur.id===s.id)el.innerHTML=pkStickerLine(cur)}
async function ptCounts(pid){const r=await api(`/api/packs/${pid}/particles`);
 if(!r.ok){if(PKPT.sets[pid]==null){PKPT.sets[pid]=[];PKPT.bursts[pid]=[];if(route_==='pack'&&PACK_ID===pid)drawPack()}return}     /* an error ends the wait too (it used to spin for ever) */
 const j={counts:r.j.counts||{},sets:r.j.sets||[],bursts:r.j.bursts||[]},old={counts:PKPT.c[pid]||{},sets:PKPT.sets[pid]||[],bursts:PKPT.bursts[pid]||[]};
 if(PKPT.sets[pid]==null||JSON.stringify(j)!==JSON.stringify(old)){     /* never read before: store it even when it is empty (an empty pack used to stay "Reading…" for ever) */PKPT.c[pid]=j.counts;PKPT.sets[pid]=j.sets;PKPT.bursts[pid]=j.bursts;if(route_==='pack'&&PACK_ID===pid)drawPack()}}
/* "Make particles": in the Studio it opens the Particles tab with this sticker chosen; anywhere else the particle studio (#/effects) */
window.ptMakeFor=(pack,sid)=>spOpenFor(pack,sid);
ACT.ptmake=el=>{lcClose();window.ptMakeFor(el.dataset.p,el.dataset.s)};
ACT.ptrunsim=async el=>{lcClose();spOpenFor(el.dataset.p,el.dataset.s);SP.entry=(SP.entry||0)+1;SP.eid=el.dataset.e;spKind(el.dataset.mode==='video'?'video':'drawn');spSave();const eid=SP.eid;await fxLoad(SP);if(SP.eid===eid){spDraw();spAfterDraw()}};
ACT.ptopen=el=>{lcClose();location.hash='#/effects/'+el.dataset.e};
ACT.ptsaved=el=>{lcClose();location.hash='#/pack/'+el.dataset.id};
ACT.ptadd=async el=>{const pid=el.dataset.p,sid=el.dataset.s;el.disabled=true;
 const r=await post(`/api/effects/${el.dataset.e}/add`,{results:[el.dataset.r],pack_id:pid,sticker_ids:[sid]});
 if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not add it',1)}
 ptForget();await loadLib();toast('Added to '+ptPackName(pid)+', saved under the sticker');if(route_==='pack')drawPack();else if(route_==='library')RENDER.library();else if(route_==='generate'&&typeof spSecSync==='function')spSecSync(true);
   const cur=LCI===null?null:LCL[LCI];if(cur&&cur.id===sid)ptLoad(cur)};

/* ---------- the pack's particle studio (docs/particles.md 5): the sets assigned to this pack and the bursts rendered for it. One set belongs to
   the pack: a sticker shows one line linking here (pkStickerLine), never a gallery of its own. The set cards are shared with the Library (particles.js).
   The bursts rendered FOR this pack are listed with Add (POST /api/particles/{id}/add, the same handler as the set card's burst maker: particles.js psbadd); making one is in the set's card. */
function pkPsHtml(p){const sets=PKPT.sets[p.id];
 if(sets===undefined||sets===null)return `<section class=pk-ps><div class=pk-ps-h><h2>${ic('fx')} Particle studio</h2></div><div class=pk-pt-load><div class=spin></div><span class=mut>Reading the pack's particle sets…</span></div></section>`;
 const bursts=PKPT.bursts[p.id]||[];
 return `<section class=pk-ps><div class=pk-ps-h><h2>${ic('fx')} Particle studio</h2><span class=mut>particles made for the stickers in this pack</span><span class=gspace></span>
  <button class="btn sm pri" data-act=psmakepack data-p=${p.id}>Make particles for this pack</button><button class="btn sm" data-act=pspickpack data-p=${p.id}>Use particles of another sticker</button></div>
  ${sets.length?sets.map(s=>typeof spSetCard==='function'?spSetCard(s):'').join(''):`<div class=mut>No particles made for these stickers yet.</div>`}
  ${bursts.length?`<div class=pk-ps-sh>Bursts rendered for this pack</div><div class=pk-ps-bursts>${bursts.map(b=>pkBurst(b,p.id)).join('')}</div>`:''}</section>`}
function pkBurst(b,pid){const ws=b.warnings||[],bl=b.blocks||[],ok=b.status==='READY'&&b.url&&!b.missing;
 return `<div class=pk-ps-b><div class=pk-pt-m>${b.url&&!b.missing?`<video src="${esc(b.url)}" autoplay loop muted playsinline preload=metadata></video>`:'<span class=mut>file missing</span>'}</div>
  <div class=pk-pt-id><b>${esc(b.set_name||b.set||'')}</b><small>${esc(b.preset||'')} · ${esc(String(b.status||'').toLowerCase())}${b.added_to?` · in ${esc(ptPackName(b.added_to))}`:''}</small></div>
  ${ws.length||bl.length?`<ul class=pk-pt-w>${[...bl,...ws].map(w=>`<li>${esc(ptWhy(w))}</li>`).join('')}</ul>`:''}
  ${!b.added_to&&ok?`<button class="btn sm pri" data-act=psbadd data-id=${esc(b.set)} data-r=${esc(b.id)} data-p=${esc(pid||'')}>${ws.length?'Add anyway':'Add to this pack'}</button>`:''}</div>`}
/* one line on the sticker, linking to the pack's particle studio (the gallery lives there now) */
function pkStickerLine(s){if(!s.pack_id)return '<span class=mut>No pack.</span>';
 const sets=PKPT.sets[s.pack_id];if(!sets){ptCounts(s.pack_id);return '<span class=mut>Reading the sticker’s particles…</span>'}
 const mine=sets.filter(x=>(x.owner||[]).some(o=>o.sticker_id===s.id));PKPT.d=PKPT.d||{};const detail=PKPT.d[s.id];if(!detail&&typeof ptLoad==='function'){PKPT.d[s.id]={loading:true};ptLoad(s)}
 if(!detail||detail.loading)return `<span class=mut>${mine.length?'Reading the sticker’s particles…':'No particles yet'}</span> <button class=link data-act=ptmake data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${mine.length?'New version':'Create particles'}</button>`;
 if(detail.error)return `<span class=mut>${esc(detail.error)}</span>`;
 const n=(detail.rows||[]).length,count=ptCount(detail);
 return `<span>${count?`Particles · ${n} saved version${n===1?'':'s'}`:'No particles yet'}</span> <button class=link data-act=ptmake data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${count?'New version':'Create particles'}</button>${count?ptBody(detail,s):''}`};
ACT.psshow=async el=>{spOpenFor(el.dataset.p,el.dataset.s);const r=await api('/api/particles/'+el.dataset.id);if(r.ok){SP.entry=(SP.entry||0)+1;SP.set=r.j;SP.target=r.j.id;SP.eid='';spDraw();spBurstPreview(r.j.id)}};
