/* Pack manager (DESKTOP_05): metadata, drag-reorder grid, cover, rename, preview, export. */
'use strict';
let DRAG=null;
RENDER.pack=async id=>{await loadLib();PACK_ID=id;drawPack()};
function drawPack(){
 const p=packById(PACK_ID),el=$('s-pack');
 if(!p){el.innerHTML='<div class=card>Pack not found. <a href="#/library">Back to library</a></div>';return}
 const n=p.stickers.length,anim=p.stickers.filter(s=>s.type==='animated').length;
 el.innerHTML=`<div style="max-width:1100px;margin:0 auto">
  <div class=row style="margin-top:0"><button class="btn sm" data-act=nav data-to=library>${ic('back')} Library</button></div>
  <div class=card><div class=phead><div class=cover style="width:84px;height:84px">${coverMedia(p)}</div>
   <div class=pt><h1 style="margin:0">${esc(p.name)}</h1><span class=mut>${n} stickers${anim?` · ${anim} animated`:''} · WhatsApp packs take 3–30 stickers</span></div>
   <div class=pa>
    <button class=btn data-act=pkadd>${ic('plus')} Add sticker</button><button class=btn data-act=pkrename>${ic('edit')} Rename</button>
    <button class=btn data-act=pkpreview ${n?'':'disabled'}>${ic('eye')} Preview</button><button class="btn pri" data-act=pkexport ${n?'':'disabled'}>${ic('download')} Export .wastickers</button>
    <button class="btn dng" data-act=pkdel>${ic('trash')}</button></div></div></div>
  <div class=row><span class=mut>Click a sticker to view it. Drag to reorder, or drop one on another pack in the Packs column to move it. Hover a sticker for preview, edit, cover and delete.</span></div>
  ${n?`<div class=grid id=pkgrid>${p.stickers.map(s=>`<div class="cell ${s.id===p.cover?'cov':''}" draggable=true data-act=stview data-id=${s.id} title="Click to view, drag to reorder">${s.id===p.cover?'<span class=badge2>cover</span>':''}${media(s)}
    <div class=hov><button data-act=stview data-id=${s.id} title=Preview>${ic('eye')}</button>${s.type==='static'?`<button data-act=stedit data-id=${s.id} title="Edit a copy in the editor">${ic('edit')}</button>`:`<button data-act=stanim data-id=${s.id} title="Edit timeline (trim, frame rate, export)">${ic('play')}</button>`}<button data-act=stcover data-id=${s.id} title="Set as cover">${ic('star')}</button><button data-act=stdel data-id=${s.id} title=Delete>${ic('trash')}</button></div>
    <div class=cap data-act=stname data-id=${s.id} title="Rename / change emoji">${esc(s.emoji)} ${esc(s.name)} · ${s.kb}KB</div></div>`).join('')}</div>`
   :`<div class=card style="text-align:center;padding:40px"><h2>This pack is empty</h2><p class=mut>Generate stickers and use "+ Pack", or create one from a photo.</p><button class="btn pri" data-act=pkadd>${ic('plus')} Add sticker</button> <button class=btn data-act=nav data-to=generate>${ic('gen')} Generate</button></div>`}</div>`;
}
const sOf=id=>packById(PACK_ID).stickers.find(s=>s.id===id);
async function pkUpdate(body,msg){const r=await post('/api/packs/'+PACK_ID,body);if(!r.ok)return toast(r.j.error,1);await loadLib();drawPack();if(msg)toast(msg)}
ACT.pkadd=()=>{Ed.targetPack=PACK_ID;location.hash='#/create'};
ACT.pkrename=()=>askText('Rename pack',packById(PACK_ID).name,n=>pkUpdate({name:n},'Renamed'));
ACT.pkdel=()=>confirmDlg(`Delete pack "${packById(PACK_ID).name}" and its stickers?`,async()=>{const r=await post(`/api/packs/${PACK_ID}/delete`);if(r.ok){await loadLib();location.hash='#/library'}else toast(r.j.error,1)});
ACT.stanim=el=>{location.hash=`#/animate/${PACK_ID}/${el.dataset.id}`};
ACT.stcover=el=>pkUpdate({cover:el.dataset.id},'Cover changed');
ACT.stdel=el=>{const s=sOf(el.dataset.id);confirmDlg(`Delete "${s.name}"?`,async()=>{const r=await post(`/api/packs/${PACK_ID}/stickers/${s.id}/delete`);if(r.ok){await loadLib();drawPack()}else toast(r.j.error,1)})};
ACT.stedit=el=>{const s=sOf(el.dataset.id);Ed.openImage('/lib/'+encodeURIComponent(s.file),{outlined:true,name:s.name+' copy',emoji:s.emoji,pack:PACK_ID})};
ACT.stview=el=>{const p=packById(PACK_ID);LCL=p.stickers.map(x=>({...x,pack_id:p.id,pack:p.name}));lcOpen(LCL.findIndex(x=>x.id===el.dataset.id))};
ACT.stname=el=>{const s=sOf(el.dataset.id);dlg(`<h2>Sticker details</h2><div class=fld><label>Name</label><input type=text id=sn value="${esc(s.name)}"></div><div class=fld><label>Emoji tag (at least one is required by Telegram)</label><input type=text id=se value="${esc(s.emoji)}"></div>
  <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=stsave data-id=${s.id}>Save</button></div>`)};
ACT.stsave=async el=>{const r=await post(`/api/packs/${PACK_ID}/stickers/${el.dataset.id}`,{name:$('sn').value,emoji:$('se').value});closeDlg();if(!r.ok)return toast(r.j.error,1);await loadLib();drawPack()};
ACT.pkpreview=()=>{const p=packById(PACK_ID);let b='chat';
 const draw=()=>{dlg(`<h2>${esc(p.name)}</h2><div class=toggles style="margin-bottom:8px">${['chat','light','dark','checker'].map(x=>`<button class="${x===b?'act':''}" data-act=pvbg data-b=${x}>${x}</button>`).join('')}</div>
  <div class="bg-${b}" style="border-radius:14px;padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px">${p.stickers.map(s=>`<div style="aspect-ratio:1">${media(s)}</div>`).join('')}</div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button></div>`);$('dlg').firstChild.style.width='min(760px,94vw)';$('dlg').querySelectorAll('img,video').forEach(m=>{m.style.cssText='width:100%;height:100%;object-fit:contain'})};
 ACT.pvbg=e=>{b=e.dataset.b;draw()};draw()};
ACT.pkexport=async()=>{const p=packById(PACK_ID);toast('Building export…');
 const r=await fetch(`/api/packs/${PACK_ID}/export`);
 if(!r.ok){let m='export failed';try{m=(await r.json()).error}catch(e){}toast(m,1);return}
 let rep={};try{rep=JSON.parse(r.headers.get('X-Export-Report')||'{}')}catch(e){}
 const blob=await r.blob(),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`${p.name}.wastickers`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),4000);toast('');
 dlg(`<h2>${ic('check')} Exported ${esc(p.name)}.wastickers</h2><div class=mut>${rep.stickers||0} static stickers as 512×512 WebP ≤100KB + 96×96 tray icon. Import it with a sticker-import app; official WhatsApp needs a host app (planned).</div>
  ${(rep.skipped_animated||[]).length?`<div class=warn>Skipped ${rep.skipped_animated.length} animated sticker(s): ${esc(rep.skipped_animated.join(', '))}. Animated WebP export is a later step.</div>`:''}
  <div class=kv style="margin:8px 0">${(rep.files||[]).map(f=>`<span>${esc(f.name)}</span><span>${f.kb}KB (q${f.quality})</span>`).join('')}</div><div class=row style="justify-content:flex-end"><button class="btn pri" data-act=dlgx>Done</button></div>`)};
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
  <div class=row style="justify-content:center"><button class=btn data-act=lcedit>${s.type==='static'?ic('edit')+' Edit a copy':ic('play')+' Edit timeline'}</button><button class=btn data-act=lcmove>${ic('plus')} Move to pack…</button><button class=btn data-act=lcpack data-id=${s.pack_id}>Open pack</button><button class="btn pri" data-act=lcsend>${ic('chat')} Send to chat</button></div>
  <div class=thumbs style="justify-content:center;max-height:130px;overflow:auto">${th}</div><div class=mut style="text-align:center">← → to browse, Esc to close</div></div>`;
 $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')lcClose()};
 const on=$('modal').querySelector('.thumb.on');if(on)on.scrollIntoView({block:'nearest',inline:'center'})}
ACT.lcsend=()=>{const s=LCL[LCI];lcClose();CH.pending=s;location.hash='#/chat'};
ACT.lcopen=el=>lcOpen(+el.dataset.i);ACT.lcclose=lcClose;ACT.lcprev=()=>lcStep(-1);ACT.lcnext=()=>lcStep(1);
ACT.lcgo=el=>{LCI=+el.dataset.i;lcDraw()};ACT.lcbg=el=>{LCBG=el.dataset.b;lcDraw()};
ACT.lcpack=el=>{lcClose();location.hash='#/pack/'+el.dataset.id};
ACT.lcedit=()=>{const s=LCL[LCI];lcClose();if(s.type==='static')Ed.openImage('/lib/'+encodeURIComponent(s.file),{outlined:true,name:s.name+' copy',emoji:s.emoji,pack:s.pack_id});else location.hash=`#/animate/${s.pack_id}/${s.id}`};
ACT.lcmove=()=>{const s=LCL[LCI];pickPack(async pid=>{if(pid===s.pack_id)return toast('Already in that pack',1);
 const r=await post(`/api/packs/${s.pack_id}/stickers/${s.id}/move`,{to:pid});if(!r.ok)return toast(r.j.error,1);
 const to=packById(pid)?.name||'pack';await loadLib();lcClose();if(route_==='pack')drawPack();else if(route_==='library')RENDER.library();drawCol2();toast(`Moved to ${to}`)},'Move to pack')};
document.addEventListener('keydown',e=>{if(LCI===null||$('dlg').classList.contains('on'))return;if(e.key==='Escape')lcClose();if(e.key==='ArrowRight')lcStep(1);if(e.key==='ArrowLeft')lcStep(-1)});
