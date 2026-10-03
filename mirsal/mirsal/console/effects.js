/* Particle effects (#/effects, a tool of Create): the burst Telegram plays when you press an emoji, made for a PACK. docs/effects.md.
   Pick a pack and its stickers, see what bursts out of each (a vision model or a built-in table; every piece is editable), then make the burst:
   Simulate (free: gravity / explosion / vortex sliders with a live preview rendered by the engine) or Video (a text-only Kling clip, the price is shown first and the click is the go-ahead).
   Results are 3-second Telegram stickers; Add puts them into the pack tagged with the source emoji. Everything here calls /api/effects; nothing is decided in the browser. */
'use strict';
ICONS.fx='<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/><circle cx="12" cy="12" r="1.8"/>';
const FX={pack:'',sel:new Set(),mode:'video',grid:'2x2',note:'',eid:'',rec:null,past:[],par:{},pv:{},est:{},pick:new Set(),timer:0,pvT:{},busy:{},pgrid:'2x2',pest:{},gen:{},sig:{}};
const FXSL=[['magnitude','Explosion',0,3,.05],['gravity','Gravity',-2,3,.05],['vortex','Vortex',-2,2,.05],['count','Pieces',4,80,1],['spin','Spin',0,3,.05]];
const FXPRESETS=['burst','fountain','vortex','rain','confetti'];
const FXWHY={effect_tail_faded:'Pieces were still on screen at the end, so the last frames were faded out to end empty, like a Telegram effect.',effect_empty_start:'Something is on screen in the first frames.',
 effect_empty_end:'Something is still on screen in the last frames.',effect_has_burst:'Hardly anything bursts: the effect is nearly empty.',effect_not_a_still:'Nothing moves.',effect_inside_cell:'Pieces leave their cell.',
 size_budget:'Over Telegram’s size limit.',codec_vp9:'Not VP9.',dimensions:'Not 512 x 512.',fps:'Not 30 fps.',duration:'Longer than 3 seconds.',alpha_decoded:'No transparency came out.',cell_unreadable:'This cell could not be read.'};

RENDER.effects=async arg=>{await loadLib();clearTimeout(FX.timer);
 if(arg&&/^E\d+$/i.test(arg)){FX.eid=arg.toUpperCase();await fxLoad()}else{FX.eid='';FX.rec=null;const r=await api('/api/effects');FX.past=r.ok?r.j.effects.slice(-8).reverse():[]}
 fxDraw()};
ACT.fxopen=()=>{location.hash='#/effects'};
ACT.fxback=()=>{FX.eid='';FX.rec=null;location.hash='#/effects'};
async function fxLoad(){const r=await api('/api/effects/'+FX.eid);if(!r.ok){toast(r.j.error||'No such effect',1);FX.eid='';FX.rec=null;return}
 FX.rec=r.j;const e=r.j;for(const g of e.groups||[]){const v=(e.video||{})[g.id];if(v&&v.status==='REQUESTED'&&v.job){const j=await api('/api/jobs/'+v.job);if(j.ok)v.live=j.j}
  const pc=g.pieces;if(pc&&pc.status==='REQUESTED'&&pc.job){const j=await api('/api/jobs/'+pc.job);if(j.ok)pc.live=j.j}
  const n=e.mode==='sim'?fxGn(g):0;if(n){const q=await api('/api/generations/'+n);if(q.ok)FX.gen[n]=q.j}
  const sig=g.id+':'+n+':'+(n?fxReady(n).length:0);if(FX.sig[g.id]!==sig){FX.sig[g.id]=sig;for(const sid of g.stickers)delete FX.pv[sid]}}      /* the pieces changed: the previews are drawn again from them */
 const live=['NEW'].includes(e.status)||Object.values(e.video||{}).some(v=>v.status==='REQUESTED'&&v.live&&!['FAILED','DONE'].includes(v.live.status))||(e.groups||[]).some(fxPiecesBusy);
 clearTimeout(FX.timer);if(live&&route_==='effects')FX.timer=setTimeout(async()=>{await fxLoad();if(route_==='effects')fxDraw()},2200)}

/* ---------- the drawn pieces of a group: the job, then the cells of the batch it became */
const fxGn=g=>{const s=g&&g.sprites;return s&&typeof s==='object'&&s.generation!=null?+String(s.generation).replace(/\D/g,'')||0:0};
const fxReady=n=>{const r=FX.gen[n];return r?(r.stickers||[]).filter(s=>s.status==='READY'&&s.png&&(s.review||{}).still!=='REJECTED'):[]};
function fxPiecesBusy(g){const pc=g.pieces;if(!pc)return false;
 if(pc.status==='REQUESTED')return !['FAILED','TIMEOUT'].includes((pc.live||{}).status);
 const n=fxGn(g);if(!n||pc.generation!==n)return false;const r=FX.gen[n];return !r||(!r.error&&(r.stage!=='sliced'||!!r.busy))}

/* ---------- setup: a pack, its stickers, how */
const fxPackOf=()=>packById(FX.pack);
function fxSetup(){const p=fxPackOf(),packs=LIB.packs.filter(x=>x.stickers.length);
 return `<div class=ph><h1>Particle effects</h1></div><div class=mut>Pick an emoji pack. Each sticker gets a 3-second burst of related pieces, like the effect Telegram plays when you press the emoji: Batman bursts bat signals, a jewelry sticker gold bars and diamonds. It starts from nothing and ends with nothing.</div>
  ${FX.past.length?`<div class=fx-past><span class=mut>Earlier</span>${FX.past.map(x=>`<a href="#/effects/${x.id}">${esc(x.id)} · ${esc(x.pack_name||'')} <small>${esc(String(x.status||'').toLowerCase())}</small></a>`).join('')}</div>`:''}
  <div class=sh style="margin-top:18px">1 · Choose the pack</div>
  <div class=fx-packs>${packs.map(x=>`<button class="fx-pack${x.id===FX.pack?' on':''}" data-act=fxpack data-id=${x.id}><span class=fx-cv>${coverMedia(x)}</span><b>${esc(x.name)}</b><small>${x.stickers.length} stickers</small></button>`).join('')||'<div class=mut>Make a pack first (Library).</div>'}</div>
  ${p?`<div class=sh style="margin-top:18px">2 · Which stickers <button class="link" data-act=fxall data-v=1>all</button><button class=link data-act=fxall data-v=0>none</button></div>
  <div class=fx-sts>${p.stickers.map(s=>`<button class="fx-st${FX.sel.has(s.id)?' on':''}" data-act=fxst data-id=${s.id} title="${esc(s.name)}">${media(s)}<span>${esc(s.emoji||'')}</span></button>`).join('')}</div>
  <div class=sh style="margin-top:18px">3 · How is the burst made</div>
  <div class=fx-modes><label class="fx-mode${FX.mode==='sim'?' on':''}"><input type=radio name=fxm ${FX.mode==='sim'?'checked':''} data-act=fxmode data-v=sim><b>Simulate</b><small>Free. The pieces fly by gravity, explosion and vortex sliders you move, with a live preview. The pieces are drawn for you by AI (a sheet of different small pieces, a few credits once), or they are the stickers themselves.</small></label>
   <label class="fx-mode${FX.mode==='video'?' on':''}"><input type=radio name=fxm ${FX.mode==='video'?'checked':''} data-act=fxmode data-v=video><b>Video from scratch</b><small>Kling draws the burst from text only, on an empty screen. About 4.5 credits for a clip of 4 cells (2x2); the price is shown before anything is spent.</small></label></div>
  ${FX.mode==='video'?`<div class=row><span class=mut>Cells in one clip</span><div class=tabs style="margin:0;gap:6px"><button class="tab${FX.grid==='2x2'?' on':''}" data-act=fxgrid data-v=2x2>2 x 2</button><button class="tab${FX.grid==='3x3'?' on':''}" data-act=fxgrid data-v=3x3>3 x 3</button></div>${FX.grid==='3x3'?'<span class=fx-warn>3 x 3 was measured poor: pieces cross cells and nothing ends empty.</span>':''}</div>`:''}
  <div class=row><input id=fxnote type=text placeholder="Your own pieces? e.g. pieces: gold bars, diamonds (optional)" value="${esc(FX.note)}" style="flex:1;min-width:260px"></div>
  <div class=row><button class="btn pri gbig" data-act=fxgo ${FX.sel.size?'':'disabled'}>${ic('fx')} Look at ${FX.sel.size} sticker${FX.sel.size===1?'':'s'}</button><span class=mut>A vision model looks at them if you allow it (asked once); otherwise a built-in table decides.</span></div>`:''}`}
ACT.fxpack=el=>{FX.pack=el.dataset.id;FX.sel=new Set((fxPackOf()||{stickers:[]}).stickers.map(s=>s.id));fxDraw()};
ACT.fxst=el=>{const i=el.dataset.id;FX.sel.has(i)?FX.sel.delete(i):FX.sel.add(i);fxDraw()};
ACT.fxall=el=>{const p=fxPackOf();FX.sel=el.dataset.v==='1'&&p?new Set(p.stickers.map(s=>s.id)):new Set();fxDraw()};
ACT.fxmode=el=>{FX.mode=el.dataset.v;fxDraw()};
ACT.fxgrid=el=>{FX.grid=el.dataset.v;fxDraw()};
ACT.fxgo=()=>{const n=$('fxnote');FX.note=n?n.value:FX.note;
 if(vlmState()===null){HX.vlmThen=()=>fxStart();return dlg(`<h2>Allow AI vision of your stickers?</h2><p class=mut>To choose what bursts out of each sticker, the pictures are sent to the vision model: the local one (LM Studio) when it is running, otherwise the cloud one if you set it up. You are asked once. Without it a built-in table of common emoji decides.</p>
   <div class=row style="justify-content:flex-end"><button class=btn data-act=fxnovlm>Use the table</button><button class="btn pri" data-act=vlmyes>Allow</button></div>`)}
 fxStart()};
ACT.fxnovlm=()=>{vlmSet('0');closeDlg();fxStart()};
async function fxStart(){const r=await post('/api/effects',{pack_id:FX.pack,sticker_ids:[...FX.sel],mode:FX.mode,grid:FX.grid,note:FX.note,allow_vlm:vlmState()==='1'});
 if(!r.ok)return toast(r.j.error||'Could not start',1);FX.eid=r.j.id;location.hash='#/effects/'+FX.eid}

/* ---------- one effect */
const fxEmoji=(e,sid)=>((e.stickers||[]).find(s=>s.sticker_id===sid)||{}).emoji||'';
const fxSticker=(e,sid)=>{const p=packById(e.pack_id),s=p&&p.stickers.find(x=>x.id===sid);return s||null};
function fxPieces(g){return `<div class=fx-pieces>${g.elements.map((x,i)=>`<span class=fx-chip>${esc(x)}<button data-act=fxdelpiece data-g=${g.id} data-i=${i} aria-label="Remove ${esc(x)}">${ic('x')}</button></span>`).join('')}
 <input class=fx-add id=fxadd-${g.id} type=text placeholder="add a piece" data-fxadd=${g.id}><button class="btn sm" data-act=fxaddpiece data-g=${g.id}>Add</button></div>`}
function fxVideoPanel(e,g){const v=(e.video||{})[g.id]||{},est=FX.est[g.id+e.grid.join('x')];
 if(v.status==='REQUESTED'){const j=v.live||{};return `<div class=fx-job>${j.status==='FAILED'?`<b class=bad>The video failed</b><div class=mut>${esc(j.error||'')}</div><button class="btn" data-act=fxvideo data-g=${g.id}>Try again</button>`:`<span class=spin></span> <b>Making the video</b> <span class=mut>${esc(v.job||'')} · ${esc(j.stage||j.status||'waiting')}</span>`}</div>`}
 return `<div class=fx-job><span class=mut>${e.grid[0]} x ${e.grid[1]} cells, screen ${esc(g.key)}, Kling pro 3 s, no start image.</span>
  <button class="btn pri" data-act=fxvideo data-g=${g.id}>${ic('film')} Make the video${est&&est.credits!=null?` · ${est.credits} credits`:''}</button>${v.status==='DONE'?`<small class=mut>Made (${v.cells} cells, ${v.cost!=null?v.cost+' credits':''}). Make another to get more takes.</small>`:''}</div>`}
function fxSimRow(e,g,sid){const s=fxSticker(e,sid),p=FX.par[sid]||{},u=FX.pv[sid];
 return `<div class=fx-sim data-sid=${sid}><div class=fx-pvbox><img id=fxpv-${sid} ${u?`src="${esc(u)}"`:''} alt="">${!u?'<span class="spin"></span>':''}<small>${esc(s?s.name:sid)} ${esc(fxEmoji(e,sid))}</small></div>
  <div class=fx-ctl><div class=fx-pre>${FXPRESETS.map(n=>`<button class="tab${(g.preset||{})[sid]===n&&!FX.par[sid]?.touched?' on':''}" data-act=fxpreset data-sid=${sid} data-n=${n}>${n}</button>`).join('')}<button class=tab data-act=fxshuffle data-sid=${sid}>shuffle</button></div>
   ${FXSL.map(([k,l,a,b,st])=>`<label class=fx-sl><span>${l}</span><input type=range min=${a} max=${b} step=${st} value="${p[k]??''}" data-fxp=${k} data-sid=${sid}><output>${p[k]??''}</output></label>`).join('')}
   <div class=row><button class="btn pri sm" data-act=fxrender data-sid=${sid}>Render</button><small class=mut>the final 512 px sticker, checked</small></div></div></div>`}
function fxPiecesPanel(e,g){const pc=g.pieces||{},n=fxGn(g),grid=FX.pgrid,k=g.id+grid,est=FX.pest[k],cells=grid==='3x3'?9:4,src=n?'gen':'own';
 const drawn=n?fxReady(n):[],r=n?FX.gen[n]:null;
 let state='';
 if(pc.status==='REQUESTED'){const j=pc.live||{};
  state=j.status==='FAILED'||j.status==='TIMEOUT'?`<div class=fx-pc-st><b class=bad>The pieces sheet failed</b><span class=mut>${esc(j.error||j.status)}</span></div>`
   :`<div class=fx-pc-st><span class=spin></span> <b>Drawing the pieces</b> <span class=mut>${esc(pc.job||'')} · ${esc(j.stage||j.status||'waiting')}</span></div>`}
 else if(n){
  state=!r&&pc.generation!==n?`<div class=fx-warn>There is no batch G${String(n).padStart(3,'0')}.</div>`:!r||fxPiecesBusy(g)?`<div class=fx-pc-st><span class=spin></span> <b>Cutting the pieces</b> <span class=mut>G${String(n).padStart(3,'0')}</span></div>`
   :`<div class=fx-pc-st><b>${drawn.length} of ${(r.stickers||[]).length} pieces ready</b> <span class=mut>G${String(n).padStart(3,'0')} · the burst uses these</span></div>
     <div class=fx-pc-ths>${drawn.map(s=>`<span class=fx-pc-th title="${esc(s.key||'')}"><img src="/out/${esc(r.generation_id)}/${esc(s.png)}" alt="${esc(s.key||'')}" loading=lazy></span>`).join('')}</div>
     ${drawn.length?'':'<div class=fx-warn>None of the cells is usable: draw again, or use the stickers themselves.</div>'}`}
 const busy=pc.status==='REQUESTED'&&!['FAILED','TIMEOUT'].includes((pc.live||{}).status);
 return `<div class=fx-pc><div class=fx-pc-h><b>Pieces that burst</b><span class=mut>an AI-drawn sheet of ${esc(g.elements.join(', '))}: one different piece per cell</span></div>
  <div class=fx-pc-draw><div class=tabs style="margin:0;gap:6px"><button class="tab${grid==='2x2'?' on':''}" data-act=fxpgrid data-v=2x2 ${busy?'disabled':''}>2 x 2</button><button class="tab${grid==='3x3'?' on':''}" data-act=fxpgrid data-v=3x3 ${busy?'disabled':''}>3 x 3</button></div>
   <button class="btn pri" data-act=fxpieces data-g=${g.id} ${busy?'disabled':''}>${ic('fx')} ${n&&pc.generation===n?`Draw ${cells} pieces again`:`Draw ${cells} pieces with AI`}${est&&est.credits!=null?` · ${est.credits} credits`:''}</button></div>
  ${state}
  <div class=fx-pc-alt><span class=mut>or use</span><label><input type=radio name=fxs-${g.id} ${src==='own'?'checked':''} data-act=fxsprites data-g=${g.id} data-v=own> the stickers themselves</label>
   <label><input type=radio name=fxs-${g.id} ${src==='gen'?'checked':''} data-act=fxsprites data-g=${g.id} data-v=gen> a batch I already made, G<input type=number id=fxgen-${g.id} min=1 style="width:70px" value="${n||''}"></label></div></div>`}
function fxSimPanel(e,g){
 return `<div class=fx-job>${fxPiecesPanel(e,g)}${g.stickers.map(sid=>fxSimRow(e,g,sid)).join('')}</div>`}
function fxResults(e){const rs=e.results||[];if(!rs.length)return '';const n=FX.pick.size;
 return `<div class=sh style="margin-top:22px">Results <button class=link data-act=fxpickall>select all that can be added</button></div><div class=fx-res>${rs.map(r=>{
  const ok=r.status==='READY',ws=(r.checks||[]).filter(c=>c.verdict==='WARN'),bl=(r.checks||[]).filter(c=>c.verdict==='BLOCK');
  return `<div class="fx-r${FX.pick.has(r.id)?' on':''}${ok?'':' bad'}"><div class=fx-rv>${r.file?`<video src="/out/effects/${e.id}/${r.file}" autoplay loop muted playsinline></video>`:'<span class=mut>no file</span>'}</div>
   <div class=fx-rm><b>${esc(r.id)} · ${r.mode==='video'?'cell '+r.cell:esc((fxSticker(e,r.sticker_id)||{}).name||'')}</b><small>${Math.round((r.bytes||0)/1024)} KB · ${esc(String(r.status).toLowerCase())}</small>
   ${bl.map(c=>`<span class="fx-w bad" title="${esc(c.detail||'')}">${esc(FXWHY[c.id]||c.id)}</span>`).join('')}${ws.map(c=>`<span class=fx-w title="${esc(c.detail||'')}">${esc(FXWHY[c.id]||c.id)}</span>`).join('')}
   ${r.added_to?'<small class=mut>added to the pack</small>':''}${ok?`<button class="btn sm${FX.pick.has(r.id)?' pri':''}" data-act=fxpick data-id=${r.id}>${FX.pick.has(r.id)?'Selected':'Select'}</button>`:''}</div></div>`}).join('')}</div>
  <div class=row><button class="btn pri gbig" data-act=fxadd ${n?'':'disabled'}>Add ${n||''} to ${esc(e.pack_name||'the pack')}</button><span class=mut>Warnings are only warnings: you decide. The effect sticker keeps the emoji of its source.</span></div>`}
function fxRecord(){const e=FX.rec;if(!e)return '';
 const head=`<div class=ph><h1>${esc(e.title||e.id)}</h1><small class=mut>${esc(e.id)} · ${e.mode==='sim'?'simulated':'video from scratch'}</small></div><button class=link data-act=fxback>${ic('back')} all effects</button>`;
 if(e.status==='NEW')return head+`<div class=fx-job style="margin-top:16px"><span class=spin></span> <b>Looking at your stickers…</b> <span class=mut>choosing what bursts out of each</span></div>`;
 if(e.status==='ERROR')return head+`<div class=warn>${esc(e.error||'The analysis failed')} <button class=btn data-act=fxback>Back</button></div>`;
 return head+(e.notes||[]).map(n=>`<div class=mut style="margin-top:6px">${esc(n)}</div>`).join('')+(e.groups||[]).map(g=>`<section class=fx-g><header><b>${esc(g.subject)}</b><span class="fx-key ${esc(g.key)}">screen ${esc(g.key)}</span><small class=mut>pieces chosen by ${g.by==='vlm'?'the vision model':g.by==='you'?'you':'the built-in table'}</small></header>
  ${fxPieces(g)}<div class=fx-gst>${g.stickers.map(sid=>{const s=fxSticker(e,sid);return s?`<span class=fx-th title="${esc(s.name)}">${media(s)}</span>`:''}).join('')}</div>${e.mode==='sim'?fxSimPanel(e,g):fxVideoPanel(e,g)}</section>`).join('')+fxResults(e)}
function fxDraw(){const el=$('s-effects');if(!el)return;el.innerHTML=`<div class="page fx">${FX.eid?fxRecord():fxSetup()}</div>`;
 if(FX.rec&&FX.rec.status==='READY'||FX.rec&&FX.rec.status==='RESULTS'||FX.rec&&FX.rec.status==='VIDEO_REQUESTED'||FX.rec&&FX.rec.status==='DONE'){
  if(FX.rec.mode==='sim')for(const g of FX.rec.groups){fxPiecesEstimate(g.id);const n=fxGn(g);if(n&&!fxReady(n).length)continue;for(const sid of g.stickers)if(!FX.pv[sid])fxPreview(sid,true)}
  if(FX.rec.mode==='video')for(const g of FX.rec.groups)fxEstimate(g.id)}}
async function fxEstimate(gid){const e=FX.rec,k=gid+e.grid.join('x');if(FX.est[k]||FX.busy[k])return;FX.busy[k]=1;
 const r=await api(`/api/effects/${e.id}/estimate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({group:gid})});FX.busy[k]=0;
 FX.est[k]=r.ok?r.j:{credits:null};if(route_==='effects'&&FX.rec&&FX.rec.id===e.id){const b=document.querySelector(`[data-act=fxvideo][data-g=${gid}]`);if(b&&r.ok&&r.j.credits!=null)b.innerHTML=`${ic('film')} Make the video · ${r.j.credits} credits`}}

async function fxPiecesEstimate(gid){const e=FX.rec,k=gid+FX.pgrid;if(FX.pest[k]||FX.busy['pe'+k])return;FX.busy['pe'+k]=1;
 const r=await post(`/api/effects/${e.id}/pieces_estimate`,{group:gid,grid:FX.pgrid});FX.busy['pe'+k]=0;
 FX.pest[k]=r.ok?r.j:{credits:null};if(route_==='effects'&&FX.rec&&FX.rec.id===e.id&&k===gid+FX.pgrid){const b=document.querySelector(`[data-act=fxpieces][data-g=${gid}]`);if(b&&r.ok&&r.j.credits!=null&&!/credits/.test(b.textContent))b.innerHTML=b.innerHTML+` · ${r.j.credits} credits`}}
ACT.fxpgrid=el=>{FX.pgrid=el.dataset.v;fxDraw()};
ACT.fxpieces=async el=>{const g=el.dataset.g;el.disabled=true;
 const r=await post(`/api/effects/${FX.eid}/pieces`,{group:g,grid:FX.pgrid,go:true});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not start',1)}
 toast(`Drawing ${FX.pgrid==='3x3'?9:4} pieces: ${r.j.estimate!=null?r.j.estimate+' credits':'the price is shown in your ledger'}`);await fxLoad();fxDraw()};

/* ---------- editing the pieces and the video */
async function fxPlan(body){const r=await post(`/api/effects/${FX.eid}/plan`,body);if(!r.ok)return toast(r.j.error||'Not possible',1);FX.rec=r.j;FX.est={};FX.pest={};FX.pv={};await fxLoad();fxDraw()}
ACT.fxdelpiece=el=>{const g=FX.rec.groups.find(x=>x.id===el.dataset.g);if(!g)return;const els=g.elements.filter((_,i)=>i!==+el.dataset.i);if(!els.length)return toast('Keep at least one piece',1);fxPlan({group:g.id,elements:els})};
ACT.fxaddpiece=el=>{const g=FX.rec.groups.find(x=>x.id===el.dataset.g),i=$('fxadd-'+el.dataset.g),v=i?i.value.trim():'';if(!g||!v)return;fxPlan({group:g.id,elements:g.elements.concat(v)})};
document.addEventListener('keydown',e=>{const t=e.target;if(e.key==='Enter'&&t&&t.dataset&&t.dataset.fxadd){e.preventDefault();ACT.fxaddpiece({dataset:{g:t.dataset.fxadd}})}});
ACT.fxsprites=el=>{const g=el.dataset.g;if(el.dataset.v==='own')return fxPlan({group:g,sprites:'own'});const n=+($('fxgen-'+g)||{}).value;if(!n)return toast('Type the batch number',1);fxPlan({group:g,sprites:{generation:n}})};
ACT.fxvideo=async el=>{const g=el.dataset.g,k=g+FX.rec.grid.join('x'),est=FX.est[k];el.disabled=true;
 const r=await post(`/api/effects/${FX.eid}/video`,{group:g,go:true});if(!r.ok){el.disabled=false;return toast(r.j.error||'Could not start',1)}
 toast(`Started: ${r.j.estimate!=null?r.j.estimate+' credits':'the price is shown in your ledger'}`);await fxLoad();fxDraw()};

/* ---------- the simulated burst: sliders -> a live preview rendered by the engine */
async function fxPreview(sid,first){const e=FX.rec;if(!e||FX.busy['p'+sid])return;FX.busy['p'+sid]=1;
 const r=await post(`/api/effects/${e.id}/preview`,{sticker_id:sid,params:first&&!FX.par[sid]?{}:fxClean(FX.par[sid]),size:256});FX.busy['p'+sid]=0;
 if(!r.ok)return toast(r.j.error||'No preview',1);FX.pv[sid]=r.j.url;if(!FX.par[sid])FX.par[sid]=fxPick(r.j.params);
 const img=$('fxpv-'+sid);if(img){img.src=r.j.url;const sp=img.parentElement.querySelector('.spin');if(sp)sp.remove()}
 for(const [k,,,,] of FXSL){const inp=document.querySelector(`[data-fxp=${k}][data-sid="${sid}"]`);if(inp&&r.j.params[k]!==undefined){inp.value=r.j.params[k];if(inp.nextElementSibling)inp.nextElementSibling.textContent=r.j.params[k]}}}
const fxPick=p=>{const o={seed:p.seed};FXSL.forEach(([k])=>o[k]=p[k]);return o};
const fxClean=p=>{const o={};if(p)Object.entries(p).forEach(([k,v])=>{if(k!=='touched'&&v!==''&&v!==undefined)o[k]=+v});return o};
document.addEventListener('input',ev=>{const t=ev.target;if(!t.dataset||!t.dataset.fxp)return;const sid=t.dataset.sid,p=FX.par[sid]=FX.par[sid]||{};p[t.dataset.fxp]=+t.value;p.touched=1;
 if(t.nextElementSibling)t.nextElementSibling.textContent=t.value;clearTimeout(FX.pvT[sid]);FX.pvT[sid]=setTimeout(()=>fxPreview(sid),220)});
ACT.fxpreset=async el=>{const sid=el.dataset.sid;FX.par[sid]=undefined;const e=FX.rec,g=e.groups.find(x=>x.stickers.includes(sid));g.preset[sid]=el.dataset.n;
 const r=await post(`/api/effects/${e.id}/preview`,{sticker_id:sid,params:{...PRESETVALS(el.dataset.n)},size:256});if(!r.ok)return toast(r.j.error,1);FX.par[sid]=fxPick(r.j.params);FX.pv[sid]=r.j.url;fxDraw()};
const PRESETVALS=n=>({burst:{},fountain:{spread:70,magnitude:1.9,gravity:1.3,count:36,spin:1.5},vortex:{vortex:1.1,gravity:.35,magnitude:.8,spin:2,count:40},rain:{gravity:.9,magnitude:.45,count:50,spin:.6},confetti:{count:64,spin:3,gravity:.7,magnitude:1.5,spread:140}})[n]||{};
ACT.fxshuffle=el=>{const sid=el.dataset.sid,p=FX.par[sid]=FX.par[sid]||{};p.seed=1+Math.floor(Math.random()*9999);fxPreview(sid)};
ACT.fxrender=async el=>{const sid=el.dataset.sid;el.disabled=true;const r=await post(`/api/effects/${FX.eid}/render`,{sticker_id:sid,params:fxClean(FX.par[sid])});el.disabled=false;
 if(!r.ok)return toast(r.j.error||'Could not render',1);await fxLoad();FX.pick.add(r.j.id);fxDraw();toast(r.j.status==='READY'?'Rendered':'Rendered, with a Telegram limit broken: see its checks',r.j.status!=='READY')};

/* ---------- results -> the pack */
ACT.fxpick=el=>{const i=el.dataset.id;FX.pick.has(i)?FX.pick.delete(i):FX.pick.add(i);fxDraw()};
ACT.fxpickall=()=>{(FX.rec.results||[]).filter(r=>r.status==='READY'&&!r.added_to).forEach(r=>FX.pick.add(r.id));fxDraw()};
ACT.fxadd=async()=>{const r=await post(`/api/effects/${FX.eid}/add`,{results:[...FX.pick]});if(!r.ok)return toast(r.j.error||'Could not add',1);
 toast(`Added ${r.j.added.length} effect sticker${r.j.added.length===1?'':'s'} to the pack`);FX.pick.clear();await loadLib();await fxLoad();fxDraw()};
