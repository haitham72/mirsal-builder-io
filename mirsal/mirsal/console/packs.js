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
    <button class=btn data-act=pkpreview ${n?'':'disabled'}>${ic('eye')} Preview</button>${n?`<a class=btn href="/api/packs/${p.id}/export.zip" download title="Every sticker file of this pack in one zip: .webm for the animated ones, .png / .webp for the static ones, and a manifest.json">${ic('download')} Download .zip</a>`:`<button class=btn disabled>${ic('download')} Download .zip</button>`}<button class="btn pri" data-act=tgsend ${n?'':'disabled'}>${ic('telegram')} Send to Telegram</button>
    <button class="btn dng" data-act=pkdel>${ic('trash')}</button></div></div></div>
  <div class=row><span class=mut>Click a sticker to view it. Drag to reorder, or drop one on another pack in the Packs column to move it. Tick the square or drag a box to select several (Shift adds, Ctrl un-selects).</span></div>${selBarHtml(n)}
  ${n?`<div class="grid selgrid ${SEL.size?'selmode':''}" id=pkgrid>${p.stickers.map(s=>`<div class="cell ${s.id===p.cover?'cov':''} ${SEL.has(selKey(p.id,s.id))?'sel':''}" draggable=true data-act=stview data-id=${s.id} title="Click to view, drag to reorder"><span class="selbox ${SEL.has(selKey(p.id,s.id))?'on':''}" data-act=lsel data-p=${p.id} data-id=${s.id} title="Select"></span>${s.id===p.cover?'<span class=badge2>cover</span>':''}${ptBadge(p.id,s.id)}${media(s)}
    <div class=hov><button data-act=stview data-id=${s.id} title=Preview>${ic('eye')}</button><button data-act=stedit data-id=${s.id} title="${(s.source&&s.source.generation)?'Edit in the Studio (text, emoji; image and animation together)':s.type==='static'?'Edit a copy in the editor':'Edit: add text or emoji, trim'}">${ic('edit')}</button>${s.type==='animated'?`<button data-act=stanim data-id=${s.id} title="Timeline (trim, frame rate, export)">${ic('play')}</button>`:''}<button data-act=stcover data-id=${s.id} title="Set as cover">${ic('star')}</button><button data-act=stdel data-id=${s.id} title=Delete>${ic('trash')}</button></div>
    <div class=cap data-act=stname data-id=${s.id} title="Rename / change emoji">${esc(s.emoji)} ${esc(s.name)} · ${s.kb}KB</div></div>`).join('')}</div>`
   :`<div class=card style="text-align:center;padding:40px"><h2>This pack is empty</h2><p class=mut>Make stickers in the Studio, or create one from a photo.</p><button class="btn pri" data-act=pkadd>${ic('plus')} Add sticker</button> <button class=btn data-act=nav data-to=generate>${ic('gen')} Generate</button></div>`}</div>`;
 ptCounts(p.id)}
const sOf=id=>packById(PACK_ID).stickers.find(s=>s.id===id);
async function pkUpdate(body,msg){const r=await post('/api/packs/'+PACK_ID,body);if(!r.ok)return toast(r.j.error,1);await loadLib();drawPack();if(msg)toast(msg)}
ACT.pkadd=()=>{Ed.targetPack=PACK_ID;location.hash='#/create'};
ACT.pkrename=()=>askText('Rename pack',packById(PACK_ID).name,n=>pkUpdate({name:n},'Renamed'));
ACT.pkdel=()=>confirmDlg(`Delete pack "${packById(PACK_ID).name}" and its stickers?`,async()=>{const r=await post(`/api/packs/${PACK_ID}/delete`);if(r.ok){await loadLib();location.hash='#/library'}else toast(r.j.error,1)});
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
  <div class=row style="justify-content:center">${s.source&&s.source.generation?`<button class="btn pri" data-act=lcstudioedit>${ic('edit')} Edit in Studio</button><button class=btn data-act=lcopenstudio>${ic('gen')} Open in Studio</button>`:s.type==='static'?`<button class=btn data-act=lcedit>${ic('edit')} Edit a copy</button>`:`<button class=btn data-act=lcedit>${ic('edit')} Edit (text, trim…)</button><button class=btn data-act=lctimeline>${ic('play')} Timeline</button>`}<button class=btn data-act=lcmove>${ic('plus')} Move to pack…</button><button class=btn data-act=lcpack data-id=${s.pack_id}>Open pack</button><button class="btn pri" data-act=lcsend>${ic('chat')} Send to chat</button></div>
  <div id=pk-pt class=pk-pt>${ptHtml(PKPT.d[s.id]||null,s)}</div>
  <div class=thumbs style="justify-content:center;max-height:130px;overflow:auto">${th}</div><div class=mut style="text-align:center">← → to browse, Esc to close</div></div>`;
 $('modal').classList.add('on');ptLoad(s);$('modal').onclick=e=>{if(e.target.id==='modal')lcClose()};
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
const PKPT={d:{},c:{}};          // d: sticker id -> the route's answer; c: pack id -> {sticker id: {created, saved}}
const ptWhy=w=>(typeof FXWHY!=='undefined'&&FXWHY[w])||String(w).replace(/_/g,' ');
const ptKb=b=>b>=1024?Math.round(b/1024)+' KB':(b||0)+' B';
const ptPackName=id=>{const p=typeof packById==='function'?packById(id):null;return p?p.name:'a pack'};
function ptCard(i,s){const ok=i.url&&!i.missing,why=[...(i.warnings||[]),...(i.status==='FAILED'?(i.blocks||[]):[])].map(ptWhy),
  kind=i.mode==='video'?`video, cell ${i.cell}${i.assigned?' (the one this sticker gets)':''} · shared by its group`:'simulated';
 return `<div class="pk-pt-card${i.usable?'':' bad'}"><div class=pk-pt-m>${ok?`<video src="${esc(i.url)}" autoplay loop muted playsinline preload=metadata></video>`:`<span class=mut>${i.status==='FAILED'?'Failed':'File missing'}</span>`}${i.added_to?`<span class=pk-pt-sv>Saved in ${esc(ptPackName(i.added_to))}</span>`:''}</div>
  <div class=pk-pt-id><b>${esc(i.effect)} · ${esc(i.result)}</b><small>${esc(kind)} · ${ptKb(i.bytes)}</small></div>
  ${why.length?`<ul class=pk-pt-w>${why.map(w=>`<li>${esc(w)}</li>`).join('')}</ul>`:''}
  <div class=pk-pt-a>${i.usable&&!i.added_to?`<button class="btn sm pri" data-act=ptadd data-e=${esc(i.effect)} data-r=${esc(i.result)}${s?` data-p=${esc(s.pack_id)} data-s=${esc(s.id)}`:''}>Add to pack</button>`:''}<button class="btn sm" data-act=ptopen data-e=${esc(i.effect)}>Open effect</button></div></div>`}
function ptHtml(j,s){const head=extra=>`<div class=pk-pt-h><b>Particles</b>${extra||''}</div>`;
 if(!j)return head()+`<div class=pk-pt-load><div class=spin></div><span class=mut>Looking for particles…</span></div>`;
 if(j.error)return head()+`<div class=mut>${esc(j.error)}</div>`;
 const made=j.created||[],saved=j.saved||[];
 if(!made.length&&!saved.length)return head()+`<div class=pk-pt-empty><b>No particles yet</b><span class=mut>Make a burst of particles for this sticker, like the effect Telegram plays when you press its emoji.</span>${j.can_make===false?'':`<button class="btn pri" data-act=ptmake data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${ic('fx')} Make particles</button>`}</div>`;
 return head(`<span class=mut>${made.length} made · ${saved.length} saved</span>${j.can_make===false?'':`<button class="btn sm" data-act=ptmake data-p=${esc(s.pack_id)} data-s=${esc(s.id)}>${ic('fx')} Make more</button>`}`)+ptBody(j,s)}
/* the takes of a sticker and the library stickers saved from them (without the heading and without the empty state: the Studio's section draws its own) */
function ptBody(j,s){if(!j)return`<div class=pk-pt-load><div class=spin></div><span class=mut>Looking for particles…</span></div>`;if(j.error)return`<div class=mut>${esc(j.error)}</div>`;
 const made=j.created||[],saved=j.saved||[];
 return(made.length?`<div class=pk-pt-grid>${made.map(x=>ptCard(x,s)).join('')}</div>`:'')
  +(saved.length?`<div class=pk-pt-sh>Saved in the library</div><div class=pk-pt-saved>${saved.map(x=>`<button class=pk-pt-s data-act=ptsaved data-id=${esc(x.pack_id)} title="${esc(x.name)} in ${esc(x.pack)}">${x.missing?'<span class=mut>missing</span>':`<video src="${esc(x.url)}" autoplay loop muted playsinline preload=metadata></video>`}<small>${esc(x.pack)}</small></button>`).join('')}</div>`:'')}
function ptBadge(pid,sid){const c=(PKPT.c[pid]||{})[sid];return c&&c.created+c.saved?`<span class=pk-pt-n title="${c.created} particle${c.created===1?'':'s'} made, ${c.saved} saved">${ic('fx')}${c.created}</span>`:''}
/* a person's change (a take added, particles made) makes what was read stale */
const ptForget=()=>{PKPT.c={};PKPT.d={}};
async function ptLoad(s){const r=await api(`/api/packs/${s.pack_id}/stickers/${s.id}/particles`);PKPT.d[s.id]=r.ok?r.j:{error:r.j.error||'Could not read the particles'};
 const cur=LCI===null?null:LCL[LCI],el=$('pk-pt');if(el&&cur&&cur.id===s.id)el.innerHTML=ptHtml(PKPT.d[s.id],cur)}
async function ptCounts(pid){const r=await api(`/api/packs/${pid}/particles`);if(!r.ok)return;
 if(JSON.stringify(r.j)!==JSON.stringify(PKPT.c[pid]||{})){PKPT.c[pid]=r.j;if(route_==='pack'&&PACK_ID===pid)drawPack()}}
/* "Make particles": in the Studio it opens the Particles tab with this sticker chosen; anywhere else the particle studio (#/effects) */
window.ptMakeFor=(pack,sid)=>{if(route_==='generate'&&typeof spOpenFor==='function')return spOpenFor(pack,sid);if(typeof FX!=='undefined'){FX.pack=pack;FX.sel=new Set([sid]);FX.eid='';FX.rec=null}location.hash='#/effects'};
ACT.ptmake=el=>{lcClose();window.ptMakeFor(el.dataset.p,el.dataset.s)};
ACT.ptopen=el=>{lcClose();location.hash='#/effects/'+el.dataset.e};
ACT.ptsaved=el=>{lcClose();location.hash='#/pack/'+el.dataset.id};
ACT.ptadd=async el=>{const pid=el.dataset.p,sid=el.dataset.s;el.disabled=true;
 const r=await post(`/api/effects/${el.dataset.e}/add`,{results:[el.dataset.r],pack_id:pid,sticker_ids:[sid]});
 if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not add it',1)}
 ptForget();await loadLib();toast('Added to '+ptPackName(pid)+', saved under the sticker');if(route_==='pack')drawPack();else if(route_==='library')RENDER.library();else if(route_==='generate'&&typeof spSecSync==='function')spSecSync(true);
 const cur=LCI===null?null:LCL[LCI];if(cur&&cur.id===sid)ptLoad(cur)};
