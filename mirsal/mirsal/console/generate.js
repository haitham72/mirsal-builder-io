/* Generate: create {subject} -> create more -> add 1-n.
   A session is the batches (sheets) the user has created for one request. Each batch is a real generation; "Create more" makes the next one on purpose;
   Animate and Add act on every included batch. The review gates are still decided and recorded by the server behind those clicks:
   Generate approves the plan, the x on a tile is a human reject, Add approves what was kept and the pack. */
'use strict';
let GSTALE=false,GAI={configured:false};
const GM=new Map();                       // generation id -> its latest state
let SES={prompt:'',gens:[],off:[],pack:''},bg='checker',glast='',MD=null,VG=null,GINP=[],GHEALTH=null;
const GS={outline:12,tile:220,tab:'stickers'};
let GD=null,GDWORK=false,GDP=null;        // GD: the browser-only pre-batch plan (never a G### nor a member of SES/GM); GDP: the Higgsfield sheet price last read for it {key,c}
try{const d=JSON.parse(localStorage.getItem('mirsal.prompt-draft')||'null');if(d&&d.number==='draft'&&Array.isArray(d.stickers))GD=d}catch(e){}
const ANIM=new Set();                     // batches the user pressed Animate on, until the server reports them animating
try{const o=localStorage.getItem('mirsal.outline');if(o!==null&&!isNaN(+o))GS.outline=[0,4,8,12,16].includes(+o)?+o:(+o>0?12:0);const t=+localStorage.getItem('mirsal.tile');if(t>=130&&t<=420)GS.tile=t;
  const s=JSON.parse(localStorage.getItem('mirsal.session')||'null');if(s&&Array.isArray(s.gens))SES={prompt:s.prompt||'',gens:s.gens.filter(g=>Number.isInteger(g)&&g>0),off:s.off||[],pack:s.pack||''}}catch(e){}      // a saved [null] / NaN (the old hopen clash) must not fire a 400 at every load
const gstore=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const saveSes=()=>gstore('mirsal.session',JSON.stringify(SES));
const wait=ms=>new Promise(f=>setTimeout(f,ms));
const BGS=[['checker','Transparent'],['light','Light'],['dark','Dark'],['wall','Wallpaper']];
const titleCase=s=>s.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());

/* a step that has to wait for a running job waits quietly; it never scolds the user with "busy" */
async function postWait(u,b,label,h){let r=await post(u,b,h);
  for(let n=0;n<180&&!r.ok&&r.status===409&&/busy/i.test(r.j.error||'');n++){say(label||'Waiting for the previous step to finish…');await wait(1000);r=await post(u,b,h)}
  say('');return r}

/* ---------- live preview: the paired 3x3 video is played in the browser and keyed like the stickers, so Animate shows motion at once
   while the real 512x512 WEBMs encode on the server (one hidden video per batch) */
const PVS=new Map(),PVON=new Set();
function pvEnsure(g){let p=PVS.get(g.number);if(p)return p;
  const v=document.createElement('video');v.muted=true;v.loop=true;v.playsInline=true;v.style.cssText='position:fixed;width:1px;height:1px;opacity:0;pointer-events:none';
  v.src=`/src/${g.number}/video`;document.body.appendChild(v);v.play().catch(()=>{});p={v,cal:{},t:-1};PVS.set(g.number,p);return p}
function vcell(g,v,i){const G=g.source.grid,sw=g.source.sheet_size;if(G&&sw){const r=G.rects[i-1],kx=v.videoWidth/sw[0],ky=v.videoHeight/sw[1];return[r[0]*kx,r[1]*ky,r[2]*kx,r[3]*ky]}
  const n=g.grid?g.grid[1]:3,w=v.videoWidth/n,h=v.videoHeight/n;return[((i-1)%n)*w,((i-1)/n|0)*h,w,h]}
function pvCalibrate(g,v,i){const [X,Y,cw,ch]=vcell(g,v,i),S=96,c=document.createElement('canvas');c.width=c.height=S;const x=c.getContext('2d',{willReadFrequently:true});
  x.drawImage(v,X,Y,cw,ch,0,0,S,S);const d=x.getImageData(0,0,S,S).data,D=[];
  for(let y=0;y<S;y++)for(let xx=0;xx<S;xx++){if(y>2&&y<S-3&&xx>2&&xx<S-3)continue;const o=(y*S+xx)*4,r=d[o],gg=d[o+1],b=d[o+2];D.push(gg-Math.max(r,b))}
  D.sort((a,b)=>a-b);return Math.max(.5*D[D.length>>1],8)}
function pvDraw(cv,g,p,i){const v=p.v;if(!v||v.readyState<2||!v.videoWidth)return;
  const t=g.stickers[i-1],m=t.metrics||{},c=m.cell,b=m.bbox,S=cv.width,[X,Y,cw,ch]=vcell(g,v,i);
  let fx=.5,fy=.5,fs=1;if(c&&b&&m.scale){fx=(b[0]+b[2])/2/c[2];fy=(b[1]+b[3])/2/c[3];fs=Math.min(3,(512/m.scale)/c[2])}
  const side=fs*(cw+ch)/2,cx=X+fx*cw,cy=Y+fy*ch;let sx=cx-side/2,sy=cy-side/2,sw=side,sh=side;
  const x0=Math.max(sx,X),y0=Math.max(sy,Y),x1=Math.min(sx+sw,X+cw),y1=Math.min(sy+sh,Y+ch),k=S/side;
  const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,S,S);if(x1<=x0||y1<=y0)return;
  ctx.drawImage(v,x0,y0,x1-x0,y1-y0,(x0-sx)*k,(y0-sy)*k,(x1-x0)*k,(y1-y0)*k);
  if(p.cal[i]===undefined)p.cal[i]=pvCalibrate(g,v,i);const T=p.cal[i],im=ctx.getImageData(0,0,S,S),d=im.data;
  for(let o=0;o<d.length;o+=4){if(!d[o+3])continue;const r=d[o],gg=d[o+1],bb=d[o+2],mx=Math.max(r,bb);let a=2*(T-(gg-mx))/T;a=a<0?0:a>1?1:a;
    if(a<.98&&a>0&&gg>mx)d[o+1]=mx;d[o+3]=d[o+3]*a}
  ctx.putImageData(im,0,0);cv.dataset.d=1}
let PVT=0;
function pvLoop(now){requestAnimationFrame(pvLoop);if(now-PVT<80)return;PVT=now;
  document.querySelectorAll('canvas[data-pv]').forEach(cv=>{const g=GM.get(+cv.dataset.g),p=PVS.get(+cv.dataset.g);if(!g||!p)return;
    const fresh=p.v.currentTime!==p.t;if(fresh||!cv.dataset.d)pvDraw(cv,g,p,+cv.dataset.pv)});
  PVS.forEach(p=>p.t=p.v.currentTime)}
requestAnimationFrame(pvLoop);

/* ---------- state helpers */
const making=g=>['requested','sheet_picked','keyed'].includes(g.stage)&&!g.error;
const animPhase=g=>g.stickers.some(t=>['READY','FAILED'].includes(t.anim_status));
const processing=g=>g.stickers.some(t=>t.anim_status==='PROCESSING');
const isOff=(g,t)=>animPhase(g)&&t.anim_status==='READY'?t.review.anim==='REJECTED':t.review.still==='REJECTED';
const keptStills=g=>g.stickers.filter(t=>t.status==='READY'&&t.review.still!=='REJECTED');
const isOob=t=>t.anim_status==='READY'&&t.review.anim==='BLOCKED';      // made, but the character leaves its cell: blocked for review, kept to look at
const oobNote=t=>{const c=(t.anim_report||[]).find(r=>r.name==='inside_frame');return c?c.detail:'leaves its cell'};
/* ---------- issue colours: ONE colour per kind of problem, the same on the tile, the chip, the marks on the sheets and in the legend.
   [colour, name, text colour on that colour]. DASHED + FADED = will not be exported (never disabled: it stays clickable and can be brought back or allowed); solid = exported, with a check. */
const CAT={bounds:['#f97316','Out of bounds','#fff'],key:['#a855f7','Bad green screen','#fff'],loop:['#eab308','Bad loop','#422006'],look:['#ec4899','Look or motion','#fff'],spec:['#3b82f6','File or Telegram limit','#fff'],bad:['#ef4444','Dropped or blocked','#fff']};
const CATORDER=Object.keys(CAT);
const CATOF={inside_cell:'bounds',inside_slot:'bounds',inside_frame:'bounds',cross_slot:'bounds',edge_trimmed:'bounds',loop_seam:'loop',
  no_spill:'key',chroma_risk:'key',holes:'key',background_is_key:'key',background_flat:'key',alpha_stable:'key',transparent_corners:'key',
  identity_kept:'look',motion_present:'look',single_subject:'look',duplicate_cell:'look',
  sharpness:'look',size_budget:'spec',codec_vp9:'spec',dimensions:'spec',fps:'spec',duration:'spec',no_audio:'spec',alpha_mode_tag:'spec',alpha_decoded:'spec',static_file:'spec',telegram_sticker:'spec',telegram_stroke:'spec'};
/* warnings in plain words: what Python noticed, and what you can do. The sticker stays in your set; nothing is removed for you. */
const WARNWHY={
  duplicate_cell:(t,c)=>`looks almost the same as S${(c&&c.data&&c.data.of)||'another sticker'} (the same pose drawn twice?). Kept: drop one with the x if you do not want both`,
  single_subject:()=>'two separate shapes in this cell (a second character, or a neighbour bleeding in). Kept: look at it and drop it if it is wrong',
  chroma_risk:(t,c)=>`part of the character is close to the green-screen colour${c&&c.value!=null?` (${(c.value*100).toFixed(0)}% of it)`:''}, so some of it may have been cut away. Kept: check the edges`,
  holes:()=>'a hole inside the character, probably a green part that the green-screen cut removed. Kept: check it',
  edge_trimmed:()=>'the trim took off more than the thin rim. Kept: check the edge or lower the trim'};
const plainWarn=(t,w)=>{const c=(t.report||[]).find(r=>r.name===w),f=WARNWHY[w];return f?f(t,c):'kept, check: '+w};
const ANIMWHY={inside_slot:'the character leaves its own slot on the sheet',cross_slot:'the character reaches into a neighbour\'s slot',empty_subject:'nothing was found in its slot',loop_seam:'the loop does not close',size_budget:'the file is over the size limit'};
/* "Use it anyway": a sticker or an animation Python blocked as a judgement call (a character touching its cell, a hole, a slot, a loop) may be allowed by a person, with a click that is recorded
   and can be taken back. Telegram's own limits (format, size, codec) and a cell with no picture stay final. The SERVER says which (`g.allow`, flow/gates.py allow_info): per kind, 'still' | 'animation',
   `can` = may be allowed now, `allowed` = carries a permission, `undo` = the permission may be taken back now, `why` = the plain-words reason of every blocked sticker, `final` = why one cannot be allowed. */
const ALW=(g,kind)=>Object.assign({can:[],allowed:[],undo:[],why:{},final:{}},(g&&g.allow&&g.allow[kind])||{});
const whyOf=(g,t,kind)=>ALW(g,kind).why[t.index];
const canAllow=(g,t,kind='animation')=>ALW(g,kind).can.includes(t.index);
const hasAllowed=(g,t,kind='animation')=>ALW(g,kind).allowed.includes(t.index);
const clickAllow=(g,t,kind='animation')=>canAllow(g,t,kind)||hasAllowed(g,t,kind);
/* ONE decision per cell (the UI/UX spec P1, P2). Every control on a cell is the same control: the sheet's cell, the tile's x / +, Use it anyway, Include anyway, Take it back, Bring back, Drop from the
   set. They all press ACT.gcell, which asks cellOp what to do from the server's word (`g.allow`, flow/gates.py allow_info) and the review state, so the same click sends the same request and leaves
   the same decision row. op: 'allow' | 'unallow' (a Python block that is a judgement call: POST .../allow), 'include' | 'drop' (a human decision on a sticker or animation that is made: POST .../drop;
   out of bounds is OFF by default and 'include' is its "Include anyway", HANDOFF 3 stays), 'none' (final: it says why, it never opens anything). `stage` is 'still' | 'anim'. */
function cellOp(g,t,stage){const kind=stage==='anim'?'animation':'still',A=ALW(g,kind);
  if(canAllow(g,t,kind))return{op:'allow',kind};
  if(hasAllowed(g,t,kind)&&A.undo.includes(t.index))return{op:'unallow',kind};
  if(stage==='still'&&animPhase(g)&&t.anim_status==='READY')return{op:'none',why:'This sticker is animated: decide on its animation.'};
  if(t.status!=='READY')return{op:'none',why:A.final[t.index]||A.why[t.index]||(t.reason?'Blocked: '+String(t.reason).replace(/_/g,' '):'Nothing to change here.')};
  if(stage==='anim'){if(t.anim_status!=='READY')return{op:'none',why:A.final[t.index]||A.why[t.index]||'There is no animation to decide on yet.'};
    return{op:t.review.still==='REJECTED'||['REJECTED','BLOCKED'].includes(t.review.anim)?'include':'drop'}}
  return{op:t.review.still==='REJECTED'?'include':'drop'}}
const cellVerb=(o,t)=>({allow:'Use it anyway',unallow:'Take it back',include:isOob(t)?'Include anyway':'Bring back',drop:'Drop from the set'})[o.op]||'';
const cellTitle=(o,t)=>({allow:'Use it anyway',unallow:'Take it back',include:isOob(t)?'Include this animation anyway':'Bring this one back',drop:'Drop this one from the set'})[o.op]||'';
/* what hovering a cell says it will do, in plain words */
const cellLabel=(o,t)=>({allow:'click to use it anyway',unallow:'click to take the permission back',include:isOob(t)?'click to include it anyway':'click to bring it back',drop:'click to drop it from the set'})[o.op]||o.why||'';
const cellAct=(g,t,stage)=>`data-act=gcell data-g=${g.number} data-i=${t.index} data-stage=${stage}`;
/* the box of a sticker (or an animation) that Python blocked: why in plain words, then 'Use it anyway' when it may be allowed, else why it cannot be */
function blockedBox(g,t,kind){const A=ALW(g,kind),still=kind==='still',why=A.why[t.index]||(still?t.reason||t.status:ANIMWHY[t.anim_reason]||t.anim_reason||'failed');
  return`<div class=gbadmsg><b>${still?'Blocked':'No animation'}</b><div class=mut style="margin:4px 0 8px">${esc(why)}</div>${A.can.includes(t.index)?`<button class="btn sm pri" ${cellAct(g,t,still?'still':'anim')} title="Python's check is a judgement call: you decide. It is recorded, and you can take it back">Use it anyway</button>`:A.final[t.index]?`<div class=mut>${esc(A.final[t.index])}</div>`:''}</div>`}
/* A blocked animation still has a finished clip on disk. Keep that picture in place, dimmed by .gt.nx, and put the reason/action over it. */
function blockedAnimOverlay(g,t){const A=ALW(g,'animation'),why=A.why[t.index]||ANIMWHY[t.anim_reason]||t.anim_reason||'failed';
  return`<div class=gblockover><b>Blocked</b><span>${esc(why)}</span>${A.can.includes(t.index)?`<button class="btn sm pri" ${cellAct(g,t,'anim')} title="Python's check is a judgement call: you decide. It is recorded, and you can take it back">Use it anyway</button>`:A.final[t.index]?`<span>${esc(A.final[t.index])}</span>`:''}</div>`}
/* what is wrong with a sticker at a stage ('still' | 'anim'): hard ones first, then by kind */
function issuesOf(t,stage,g){const out=[],add=(id,text,soft)=>out.push({cat:CATOF[id]||'bad',id,text,soft:!!soft});
  if(stage==='anim'){
    if(t.status!=='READY'||t.review.still==='REJECTED')return out;
    if(t.anim_status==='FAILED')add(t.anim_reason,'no animation: '+(whyOf(g,t,'animation')||ANIMWHY[t.anim_reason]||t.anim_reason||'failed'));
    if(t.anim_status==='READY')(t.anim_report||[]).filter(c=>!c.ok).forEach(c=>add(c.name,c.name==='inside_frame'?oobNote(t):(c.detail||c.name),c.severity==='WARN'));
    if(t.review.anim==='REJECTED')add('dropped','dropped from the set');
  }else{
    if(t.status==='FAILED')add(t.reason,'blocked: '+(whyOf(g,t,'still')||t.reason||'failed'));
    else{(((t.metrics||{}).warnings)||[]).forEach(w=>add(w,plainWarn(t,w),true));
      (t.report||[]).filter(c=>!c.ok&&((t.metrics||{}).waived||[]).includes(c.name)).forEach(c=>add(c.name,c.detail||c.name,true))}
    if(t.review.still==='REJECTED')add('dropped','dropped from the set');
  }
  return out.sort((a,b)=>(a.soft-b.soft)||CATORDER.indexOf(a.cat)-CATORDER.indexOf(b.cat))}
function mark(t,stage,g){const is=issuesOf(t,stage,g);if(!is.length)return null;
  const inSet=stage==='anim'?t.anim_status==='READY'&&!['REJECTED','BLOCKED'].includes(t.review.anim):t.status==='READY'&&t.review.still!=='REJECTED';
  return{cat:is[0].cat,issues:is,accepted:inSet}}
function chip(g,t,stage){const m=mark(t,stage,g),kind=stage==='anim'?'animation':'still',allow=clickAllow(g,t,kind);let cls,title,st='';
  if(m){cls='iss'+(m.accepted?' soft':'');st=` style="--cc:${CAT[m.cat][0]}"`;title=`S${t.index}: ${m.issues.map(i=>CAT[i.cat][1]+' - '+i.text).join('; ')}${m.accepted?'':' (not in the set)'}`}
  else if(stage==='anim'){const c=cellState(t);cls=c;title=`S${t.index}: ${CELLTXT[c]}`}
  else{cls='ok';title=`S${t.index}: accepted`}
  return`<button class="vchip ${cls}"${st} ${allow?cellAct(g,t,stage):`data-act=gopen data-g=${g.number} data-i=${t.index}`} title="${esc(title+(allow?(canAllow(g,t,kind)?' · click to use it anyway':' · click to take the permission back'):''))}">${t.index}</button>`}
function legend(g,stage){const cs=new Set();g.stickers.forEach(t=>{const m=mark(t,stage,g);if(m)m.issues.forEach(i=>cs.add(i.cat))});
  return cs.size?`<div class=lgrow>${CATORDER.filter(c=>cs.has(c)).map(c=>`<span class=lgd style="--cc:${CAT[c][0]}"><i></i>${CAT[c][1]}</span>`).join('')}</div><div class="mut lgnote">dashed and faded = will NOT be exported (click it to allow it when it can be); solid = exported, with a check</div>`:''}
/* the in-place marks on a sheet of size sheet_size: a dashed faded box over every cell that is not in the set, a solid thin outline over one kept with a check.
   Every cell is a full-cell hit area and does exactly one thing (cellOp): allow / take back / include / drop. It never opens a tile (opening belongs to the thumbnail on the right). The hover and the
   label say the reason in plain words, never a raw check id; keyboard: Tab to a cell, Enter to press it (the same actions the tile offers). */
function issueSvg(g,stage,k=1){const W=g.source.sheet_size?g.source.sheet_size[0]:((sheetOf(g)||{}).canvas||[2048])[0],sw=Math.max(2,W/450)*k,kind=stage==='anim'?'animation':'still';let body='';
  g.stickers.forEach(t=>{const c=(stage==='anim'&&layoutOfCell(g,t.index))||(t.metrics||{}).cell;if(!c)return;const m=mark(t,stage,g),o=cellOp(g,t,stage),
    r=`x="${c[0]}" y="${c[1]}" width="${c[2]}" height="${c[3]}"`,act=` ${cellAct(g,t,stage)} style="pointer-events:all;cursor:pointer"`,act2=o.op==='allow'||o.op==='unallow',
    fin=o.op==='none'?(ALW(g,kind).final||{})[t.index]:null;
    let label;
    if(m){const col=CAT[m.cat][0];label=`S${t.index}: ${m.issues.map(i=>CAT[i.cat][1]+' - '+i.text).join('; ')}${m.accepted?'':' (not in the set)'} · ${cellLabel(o,t)}`;
      if(fin&&!label.includes(fin))label+=`. ${fin}`;
      const tip=`<title>${esc(label)}</title>`;
      body+=m.accepted?`<rect ${r} fill="${act2?col:'none'}" fill-opacity="${act2?.06:0}" stroke="${col}" stroke-width="${sw*1.1}"${act} tabindex="0" role="button" aria-label="${esc(label)}">${tip}</rect>`
        :`<rect ${r} fill="#fff" fill-opacity=".34" stroke="${col}" stroke-width="${sw*2}" stroke-dasharray="${W/55} ${W/110}"${act} tabindex="0" role="button" aria-label="${esc(label)}">${tip}</rect>`}
    else{label=`S${t.index}: ${stage==='anim'?CELLTXT[cellState(t)]:'accepted'} · ${cellLabel(o,t)}`;
      body+=`<rect ${r} class=sh-hit${act} tabindex="0" role="button" aria-label="${esc(label)}"><title>${esc(label)}</title></rect>`}});
  return body}
const keptAnim=g=>g.stickers.filter(t=>t.anim_status==='READY'&&t.review.still!=='REJECTED'&&!['REJECTED','BLOCKED'].includes(t.review.anim));
const keptOf=g=>animPhase(g)?keptAnim(g):keptStills(g);
const sheetOf=g=>[...g.video_sheets].reverse().find(v=>v.status!=='REJECTED');
const hasVid=g=>!!(g.source.has_video||(sheetOf(g)&&sheetOf(g).video));
const sessionGens=()=>SES.gens.map(id=>GM.get(id)).filter(Boolean);
const included=()=>sessionGens().filter(g=>!SES.off.includes(g.number));
const nAdded=(g,pid)=>keptOf(g).filter(t=>((g.added||{})[pid]||[]).includes(`${animPhase(g)?'animated':'static'}:${t.index}`)).length;

/* ---------- the screen */
RENDER.generate=async()=>{
  $('s-generate').innerHTML=`<div class=gen2>
   <div class=sh>${ic('gen')} Studio</div>
   <div class=gform>${ic('search')}<input id=prompt type=text placeholder="Describe the stickers, for example: teddy bear for school" autocomplete=off><button id=go class="btn pri gbig" data-act=gprompt>Generate prompt</button></div>
   <div class=gopts><span class=mut>White outline</span><div class=tabs id=opills></div><span class=mut id=ohint></span></div>
   <div id=gsug class=gsug></div><div id=msg class=gmsg></div><div id=ghealth></div><div id=gres></div></div>`;
  $('prompt').value=gdOn()?GD.prompt:SES.prompt||'';$('prompt').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ACT.ggo()}};
  document.documentElement.style.setProperty('--tile',GS.tile+'px');
  drawOutline();glast='';await loadInputs();drawSug();tick(true)};
function drawOutline(){const on=GS.outline>0;$('opills').innerHTML=[[12,'On'],[0,'Off']].map(([px,l])=>`<button class="tab ${(on?12:0)===px?'on':''}" data-act=goutline data-px=${px}>${l}</button>`).join('');
  $('ohint').textContent=on?'white border around each sticker, also on the animation':'stickers are cut out with no border'}
ACT.goutline=el=>{GS.outline=+el.dataset.px;gstore('mirsal.outline',GS.outline);drawOutline();glast='';tick(true)};
/* /api/ai: which engine the AI enhancer would use and what is available (never the key); asked again after the person changes the engine (AIENG, agent.js) */
async function aiRefresh(){const a=await api('/api/ai');if(a.ok){GAI=a.j;if(typeof cpDrawBar==='function')cpDrawBar()}return GAI}          // the chip and the engine control read GAI: redraw when it arrives (the composer can be drawn first)
async function loadInputs(){const r=await api('/api/inputs');if(r.ok)GINP=r.j.inputs;await aiRefresh();const h=await api('/api/generations');if(h.ok)GHEALTH=h.j.health}
function drawSug(){const el=$('gsug');if(!el)return;
  el.innerHTML=GINP.length?`<span class=mut>Prepared sheets:</span>`+GINP.map(s=>`<button class=chip2 data-act=gsug data-s="${esc(s.subject)}">${esc(s.subject.replace(/_/g,' '))} <small>${s.variants.length} ${s.variants.length>1?'sheets':'sheet'}</small></button>`).join(''):''}
ACT.gsug=el=>{$('prompt').value=el.dataset.s.replace(/_/g,' ');ACT.ggo()};

/* a new request starts a session with Batch 1; "Create more" adds the next batch */
async function create(prompt,variant,more){
  say('');const body={prompt,variant:variant||undefined,outline:GS.outline};
  const r=await postWait('/api/generations',body,'Finishing the previous sheet…');
  if(!r.ok){if(r.status===404&&typeof liveOffer==='function'&&liveOffer(prompt)){say('');return false}
  say(`${esc(r.j.error||'Could not start')} ${r.status===404?`<button class="btn sm" data-act=ghiggs>Get the Higgsfield prompt for this</button>`:''}`);return false}
  gdHide();if(more){SES.gens.push(r.j.id)}else{SES={prompt,gens:[r.j.id],off:[],pack:''};for(const p of PVS.values())p.v.remove();PVS.clear();PVON.clear();ANIM.clear()}
  saveSes();glast='';MD=null;tick(true);return true}
ACT.ggo=()=>{const p=$('prompt').value.trim();if(!p){say('Write what you want first, for example <b>teddy bear for school</b>.');return}create(p,0,false)};
function openGen(id){gdHide();SES={prompt:'',gens:[id],off:[],pack:''};saveSes();glast='';MD=null;tick(true)}
ACT.gmore=async()=>{const gs=sessionGens();if(!gs.length)return;const s=gs[0].source.subject,used=new Set(gs.map(g=>String(g.source.subject_id)));
  await loadInputs();const inp=GINP.find(x=>x.subject===s),next=inp&&inp.variants.find(v=>!used.has(String(v.folder)));
  if(!next){toast(`That is every prepared sheet of “${s.replace(/_/g,' ')}”. Put another in Images_gen, or get the Higgsfield prompt to make a new one.`,1);return}
  create(SES.prompt||s.replace(/_/g,' '),next.variant,true)};
ACT.gbdrop=el=>{const id=+el.dataset.g;SES.gens=SES.gens.filter(x=>x!==id);SES.off=SES.off.filter(x=>x!==id);saveSes();glast='';tick(true)};
ACT.ginc=el=>{const id=+el.dataset.g;SES.off=el.checked?SES.off.filter(x=>x!==id):SES.off.concat(id);saveSes();glast='';tick(true)};
document.addEventListener('change',e=>{if(e.target.classList&&e.target.classList.contains('ginc'))ACT.ginc(e.target);
  if(e.target.id==='gbgsel'){bg=e.target.value;glast='';tick(true);if(MD)gmodal()}});
document.addEventListener('input',e=>{if(e.target.id==='gsize'){GS.tile=+e.target.value;document.documentElement.style.setProperty('--tile',GS.tile+'px');gstore('mirsal.tile',GS.tile)}});

/* ---------- the result */
function tileHtml(g,t,mode){const base=`/out/${g.generation_id}/`,anim=mode==='anim',ap=animPhase(g),
    off=anim?(t.review.anim==='REJECTED'||t.review.still==='REJECTED'):t.review.still==='REJECTED',blk=anim&&isOob(t),
    mk=mark(t,anim?'anim':'still',g),hard=mk&&!mk.accepted,kind=anim?'animation':'still',can=canAllow(g,t,kind),allowedNow=hasAllowed(g,t,kind),
    live=anim&&!off&&PVON.has(g.number)&&t.status==='READY'&&g.source.video_path&&!t.webm,blockedClip=anim&&t.webm&&t.anim_status==='FAILED',hasV=t.webm&&(t.anim_status==='READY'||blockedClip);
  let m;
  if(!anim)m=t.png?`<img src="${base+t.png}?e=${t.edited_at||t.rendered_at||0}" loading=lazy>`:t.status==='FAILED'?blockedBox(g,t,'still'):`<div class=gbadmsg>${esc(t.reason||t.status)}</div>`;
  else m=hasV?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:live?`<canvas data-g=${g.number} data-pv=${t.index} width=288 height=288></canvas><span class=livebadge>live preview</span>`
    :t.anim_status==='FAILED'?blockedBox(g,t,'animation'):t.anim_status==='STALE'?`<div class="gbadmsg mut">${esc(t.anim_reason||'Animate again')}</div>`:t.status==='READY'?`<div class="gbadmsg mut">Not animated yet</div>`:t.status==='FAILED'?blockedBox(g,t,'still'):`<div class=gbadmsg>${esc(t.reason||t.status)}</div>`;
  const stg=anim?'anim':'still',op=cellOp(g,t,stg),canX=op.op!=='none'&&(anim?ap:!ap||op.op==='allow'||op.op==='unallow');
  const lines=mk?mk.issues.slice(0,2).map(i=>`<div class=giss style="--cc:${CAT[i.cat][0]}"><i></i>${esc(CAT[i.cat][1])}: ${esc(i.text)}</div>`).join(''):'';
  return`<div class="gt ${off?'off':''} ${off||hard||blk?'nx':''} ${blk?'blk':''} ${hard?'iss':mk?'issw':''}"${mk?` style="--cc:${CAT[mk.cat][0]};--ct:${CAT[mk.cat][2]}"`:''}><div class="gtv bg-${bg}" data-act=gopen data-g=${g.number} data-i=${t.index}>${m}${blockedClip?blockedAnimOverlay(g,t):hard&&!off?`<span class="isstag${can?' clk':''}" ${can?`${cellAct(g,t,stg)} title="Click to use it anyway"`:''}>${esc(CAT[mk.cat][1])}${can?' · click to use it anyway':''}</span>`:''}${off?'<span class="isstag offtag">Not in the set</span>':''}</div><span class=gem>${esc(t.emoji)}</span>
    ${canX?`<button class=gx ${cellAct(g,t,stg)} title="${cellTitle(op,t)}">${['allow','include'].includes(op.op)?ic('plus'):ic('x')}</button>`:''}
    <div class=gcap><b>${esc(t.key.replace(/_/g,' '))}</b>${lines}${blk?`<div class=giss style="--cc:${CAT[mk.cat][0]}">Off by default, not added. <button class="btn sm gincl" ${cellAct(g,t,stg)}>Include anyway</button></div>`:''}${t.edited?'<div class=gwarn style="color:var(--pri-d)">edited</div>':''}${allowedNow?`<div class=gwarn style="color:var(--pri-d)">allowed by you${ALW(g,kind).undo.includes(t.index)?` · <button class=link ${cellAct(g,t,stg)}>Take it back</button>`:''}</div>`:''}${off&&!mk?'<div class=gwarn>Dropped</div>':''}</div></div>`}
function batchHtml(g,k,total,mode){
  const inc=!SES.off.includes(g.number),s=g.source;
  const head=`<div class=gbhead>${total>1?`<label class=gbinc title="Include this batch when you Animate or Add"><input type=checkbox class=ginc data-g=${g.number} ${inc?'checked':''}> <b>Batch ${k+1}</b></label>`:`<b>Batch ${k+1}</b>`}
    <span class=mut>sheet ${s.subject_id} · ${g.generation_id}${hasVid(g)?'':' · no video prepared'}</span>
    ${g.key_colour==='blue'?`<span class=keychip title="This sheet has a blue screen, so it was keyed as blue (and the video sheet is blue too). Nothing to do.">Blue key</span>`:''}
    <span class=gbact>${s.has_video||making(g)||(typeof liveReadyNow==='function'&&liveReadyNow())?'':`<button class="btn sm" data-act=gvideo data-g=${g.number} ${keptStills(g).length?'':'disabled'} title="This sheet has no prepared video: make one from the sheet in your own tool">${ic('film')} Make a video…</button>`}
    <button class="btn sm" data-act=gopenfolder data-g=${g.number} title="Open this batch's folder in the file manager: a properly named folder with the sheet, stickers, animations and prompts">${ic('folder')} Open folder</button>
    ${total>1?`<button class="btn sm" data-act=gbdrop data-g=${g.number} title="Take this batch out of the session">${ic('x')}</button>`:''}</span></div>`;
  if(making(g))return`<section class=gbatch>${head}<div class=gwork><div class=spin></div><b>Making your stickers…</b><div class=mut>${g.stage==='requested'?'Reading the sheet':g.stage==='sheet_picked'?'Removing the background':'Cutting and checking each sticker'}</div></div></section>`;
  const sheetErr=g.stickers.every(t=>t.status==='FAILED')&&(g.verify.sheet||[]).find(c=>!c.ok&&c.severity!=='WARN');
  if(sheetErr){const p=g.problem;      /* the server explains a blocked sheet in words (flow/explain.py): what happened, what was paid, what to do; Python's block stays final */
    return`<section class=gbatch>${head}<div class=gwork><b>${esc(p?p.title:'This sheet cannot be used')}</b><div class=mut>${esc(p?p.why:(sheetErr.detail||sheetErr.name))}</div>
     ${p?`<div class=mut>${esc(p.fix)}</div>${p.received?`<div class=mut>The sheet was received${p.received.job?' ('+esc(p.received.job)+')':''}${p.received.cost?' and paid for ('+p.received.cost+' credits)':''}: nothing is lost, this batch just has no stickers. It stays in History.</div>`:''}
     ${p.cut_anyway?`<button class="btn pri" data-act=gcutany data-g=${g.number} title="Cut the sheet that was received, as it is, for free: you decide on every cell yourself">Cut it anyway</button>`:''}
     <button class="btn${p.cut_anyway?'':' pri'}" data-act=gretrysheet data-g=${g.number}>Try the sheet again</button>`:''}</div></section>`}
  return`<section class="gbatch ${inc?'':'excl'}">${head}${g.error?`<div class=warn>${esc(g.error)}</div>`:''}<div class=gbody>${mode==='anim'?`<div class=gleft>${videoPanel(g)}${sheetPanel(g)}</div>`:sheetPanel(g)}<div class=gtiles>${g.stickers.map(t=>tileHtml(g,t,mode)).join('')}</div></div></section>`}
/* what a set of batches stands at right now: the counts the header and the bottom bar read. One implementation, used by the header and the bottom bar. */
function gstats(gs){const inc=gs.filter(g=>!SES.off.includes(g.number)),n=inc.reduce((a,g)=>a+keptOf(g).length,0),ready=gs.every(g=>!making(g));
  const todoAnim=inc.filter(g=>g.source.has_video&&(!animPhase(g)||g.stickers.some(t=>t.anim_status==='STALE'))&&!processing(g)&&!ANIM.has(g.number)&&keptStills(g).length);
  const busyAnim=gs.some(g=>processing(g)||(ANIM.has(g.number)&&!animPhase(g)));
  const done=inc.reduce((a,g)=>a+g.stickers.filter(t=>['READY','FAILED'].includes(t.anim_status)).length,0),tot=inc.reduce((a,g)=>a+(hasVid(g)?keptStills(g).length:0),0);
  const pk=SES.pack&&packById(SES.pack),added=pk?inc.reduce((a,g)=>a+nAdded(g,SES.pack),0):0;
  return {gs,inc,n,ready,busyAnim,todoAnim,done,tot,pk,added,allAdded:!!(pk&&n>0&&added>=n),kind:inc.some(g=>animPhase(g))?'animated ':''}}
/* the bottom bar (Animate / Add to a pack) */
function barHtml(s){const {n,ready,busyAnim,todoAnim,done,tot,pk,allAdded,kind,inc}=s;
  if(!ready)return`<span class=gstat>Making your stickers…</span>`;
  if(busyAnim)return`<span class=gstat>Animating ${done} of ${tot}…</span><button class="btn pri gbig" disabled>Animating…</button>`;
  if(todoAnim.length)return`<span class=gstat>${n} sticker${n===1?'':'s'} in ${inc.length} batch${inc.length===1?'':'es'}</span><button class=link data-act=gadd ${n?'':'disabled'}>or add the stills</button><button class="btn pri gbig" data-act=ganimate>${ic('play')} Animate${inc.length>1?` ${todoAnim.length} batch${todoAnim.length===1?'':'es'}`:''}</button>`;
  return`<span class=gstat>${n} ${kind}sticker${n===1?'':'s'} in ${inc.length} batch${inc.length===1?'':'es'}${allAdded?` · added to “${esc(pk.name)}”`:''}</span><button class="btn pri gbig" data-act=gadd ${n&&!allAdded?'':'disabled'}>${allAdded?'Added ✓':`Add ${n} to a pack`}</button>${allAdded?`<button class="btn gbig" data-act=gopenpack>Open pack</button>`:''}`}
function gview(){
  if(gdOn())return gdView();
  const gs=sessionGens();if(!gs.length)return'';
  const s=gstats(gs),{pk,allAdded,n}=s;
  return`<div class=ghead><div><h2 style="margin:0">${esc(titleCase(gs[0].source.subject))}</h2><div class=mut>${gs.length} batch${gs.length===1?'':'es'} · ${gs[0].outline_px?gs[0].outline_px+' px outline':'no outline'}</div></div>
    <button class="btn" data-act=gmore ${s.ready&&!s.busyAnim?'':'disabled'} title="Create another sheet of the same subject">${ic('plus')} Create more</button>
    ${gs.length===1?`<button class=btn data-act=ggroup title="Put this batch in the group of another batch: that batch becomes its parent">Add to group</button>`:''}
    ${gs.length===1?`<button class="btn" data-act=tkreport data-k=generation data-id=${esc(gs[0].generation_id)} title="Something wrong with this batch? Send a report">Report</button>`:''}
    <button class="btn dng" data-act=grm title="Move ${gs.length===1?'this batch':'these batches'} to the trash. You can restore ${gs.length===1?'it':'them'} from Removed batches under Earlier batches.">${ic('trash')} Remove batch</button>
    <span style="margin-left:auto" class=gview><label class=mut>Background <select id=gbgsel>${BGS.map(([k,l])=>`<option value=${k} ${bg===k?'selected':''}>${l}</option>`).join('')}</select></label>
    <label class=mut>Size <input type=range id=gsize min=130 max=420 step=10 value=${GS.tile}></label></span></div>
   ${typeof gvarsHtml==='function'?gvarsHtml(gs):''}
   ${stepsHtml(s)}
   ${gbodyHtml(s.gs,{inc:s.inc,todoAnim:s.todoAnim,busyAnim:s.busyAnim,n:s.n})}
   <div class=gbar>${barHtml(s)}</div>`}

/* what the page shows under the header: each step is a real view. */
function gbodyHtml(gs,c){const t=GS.tab;
  if(t==='request')return requestView(gs);
  if(t==='plan')return planView(gs[0]);
  if(t==='anim'&&!gs.some(animPhase)&&!c.busyAnim&&!gs.some(g=>PVON.has(g.number)))return gs.some(g=>g.source.has_video)?animEmpty(gs,c):animCreate(gs);
  return gs.map((g,k)=>batchHtml(g,k,gs.length,t==='anim'?'anim':'still')).join('')}
function animEmpty(gs,c){const hasVid=gs.some(g=>g.source.has_video);   // a prepared video; a Kling video has already produced the animations
  return`<section class=gplan style="text-align:center;padding:44px 16px"><h2 style="margin:0 0 6px">${hasVid?'Animate your stickers':'No video prepared for this sheet'}</h2>
   <div class=mut style="max-width:560px;margin:0 auto 18px">${hasVid?`${c.n} sticker${c.n===1?'':'s'} will be animated from the prepared video. Each animation is checked frame by frame (size, loop, and whether the character stays inside its cell) and shows up here as soon as it is ready.`
     :(typeof liveReadyNow==='function'&&liveReadyNow()?'Generate the animation on the Stickers view: the box under the green screen has the model and the price.':'Make a video from the sheet in your own tool, then add it with “Make a video…” on the Stickers view.')}</div>
   ${hasVid?`<button class="btn pri gbig" data-act=ganimate ${c.todoAnim.length?'':'disabled'}>${ic('play')} Animate</button>`:''}</section>`}

/* The Animation tab before any animation exists (Haitham, 2026-10-04: it said "nothing to see here" while the controls lived on Stickers). Per batch: the video sheet
   that would be sent (the server's preview of the kept stickers), the model and price with Generate (vgenBox, inside the sheet panel), the editable video prompt with the
   same footer as the Prompt tab (Generate video with my prompt), and each kept sticker with motion suggestions that add a phrase to the prompt. Nothing here spends
   without the price shown on the button (rule 13). Pure, except the two live.js helpers it reads when they exist. */
const ANIM_MOTIONS=['bounces','waves','nods','jumps','spins','laughs','leans in','sparkles appear'];
function animCreate(gs){return gs.map(g=>{const kept=keptStills(g),live=typeof liveReadyNow==='function'&&liveReadyNow(),base=`/out/${g.generation_id}/`;
  const prev=kept.length&&typeof previewUrl==='function'&&typeof fillNow==='function'?`<figure class=ganew-prev><img src="${esc(previewUrl(g,fillNow()))}" alt="The video sheet that will be animated" loading=lazy><figcaption class=mut>The video sheet that will be sent: your ${kept.length} kept sticker${kept.length===1?'':'s'}</figcaption></figure>`:'';
  return`<section class=gbatch><div class=gbhead><b>${esc(g.generation_id)}</b><span class=mut>${kept.length?`${kept.length} kept sticker${kept.length===1?'':'s'} to animate`:'Keep at least one sticker on the Stickers view first'}</span>
    ${live?'':`<span class=gbact><button class="btn sm" data-act=gvideo data-g=${g.number} ${kept.length?'':'disabled'} title="Higgsfield is not connected: make the video from the sheet in your own tool">${ic('film')} Make a video…</button></span>`}</div>
   <div class=ganew><div class=ganew-l>${prev}${typeof sheetPanel==='function'?sheetPanel(g):''}</div>
    <div class=ganew-r>${copyBox('Video prompt',pdText(g,'video'),'ap'+g.number,6,{kind:'video',g:g.number,foot:pdFoot(g,'video')})}
     <div class=ganew-sts>${kept.map(t=>`<div class=ganew-st>${t.png?`<img src="${base+t.png}?e=${t.edited_at||t.rendered_at||0}" alt="" loading=lazy>`:''}<div><b>S${t.index} · ${esc(String(t.key||'').replace(/_/g,' '))}</b>
       <div class=ganew-mo>${ANIM_MOTIONS.map(m=>`<button class=ganew-chip data-act=ganmo data-g=${g.number} data-m="${esc('S'+t.index+' '+m)}">${esc(m)}</button>`).join('')}</div></div></div>`).join('')}</div></div></div></section>`}).join('')}
/* a motion suggestion adds "S3 waves" to the batch's video prompt draft (the same draft the Prompt tab edits), so the person sees and can change what is sent */
ACT.ganmo=el=>{const g=GM.get(+el.dataset.g);if(!g)return;const cur=pdText(g,'video')||'';PD[pdKey(g.number,'video')]=(cur.trim()?cur.replace(/\s*$/,'')+'\n':'')+el.dataset.m+'.';glast='';tick(true)};

/* Request: the original request, editable; generating again starts a new session */
function requestView(gs){const g=gs[0],s=g.source,on=GS.outline>0;
  return`<section class=gplan><div class=pcols><div><div class=pbh><b>Your request</b></div>
    <textarea id=greq data-req rows=3 style="width:100%;font:inherit;font-size:15px;background:var(--fill);border:0;border-radius:12px;padding:12px">${esc(SES.prompt||g.prompt||'')}</textarea>
    <div class=row><span class=mut>White outline</span><div class=tabs style="margin:0;gap:6px">${[[12,'On'],[0,'Off']].map(([px,l])=>`<button class="tab ${(on?12:0)===px?'on':''}" data-act=goutline data-px=${px} style="padding:6px 16px;font-size:13px">${l}</button>`).join('')}</div></div>
    <div class=row style="margin-top:12px"><button class="btn pri gbig" data-act=greqgo>Generate again with this request</button></div>
    <div class=mut style="margin-top:6px">This starts a new session. The stickers you have now stay in History.</div></div>
   <ul class=pcells><li><b>Subject</b><div class=mut>${esc(titleCase(s.subject))}</div></li><li><b>Prepared sheets used</b><div class=mut>${gs.map(x=>`sheet ${x.source.subject_id} (${x.generation_id})`).join(', ')}</div></li>
    <li><b>Grid</b><div class=mut>${g.grid[0]}×${g.grid[1]}, ${g.stickers.length} stickers per batch</div></li><li><b>Template</b><div class=mut>${esc(g.template_id||'hand-written plan')}${g.template_version?' v'+g.template_version:''}</div></li>
    <li><b>Edge</b><div class=mut>${g.outline_px?g.outline_px+' px white outline':'no outline'}${g.erode_px?`, ${g.erode_px} px trimmed`:''}</div></li></ul></div></section>`}
/* "Cut it anyway": free, from the sheet already received (pipeline.recut); every cell is judged on its own and you decide at G2 */
ACT.gcutany=async el=>{const r=await post(`/api/generations/${el.dataset.g}/recut`);if(!r.ok)return toast(r.j.error||'Could not cut the sheet',1);toast('Cutting the sheet…');glast='';tick(true)};
ACT.gretrysheet=el=>{const g=GM.get(+el.dataset.g);if(!g)return;$('prompt').value=g.prompt||'';GS.tab='stickers';create(g.prompt||'',0,false)};     /* the same path as Generate: the live price is shown before anything is sent */
ACT.greqgo=el=>{const p=(($('greq')||{}).value||'').trim();
  if(!p){say('Write what you want first.');return}$('prompt').value=p;GS.tab='stickers';create(p,0,false)};

/* ---------- the header: Request > Prompt > Stickers > Animation > Pack (where this request stands, from what the server reports).
   The current step is `GS.tab`. */
function stepsHtml(c){const cur=GS.tab;const {gs,ready,busyAnim,done,tot,pk,allAdded,n}=c,g0=gs[0],cnt=f=>gs.reduce((a,g)=>a+g.stickers.filter(f).length,0);
  const good=cnt(t=>t.status==='READY'),kept=cnt(t=>t.status==='READY'&&t.review.still!=='REJECTED'),dropped=cnt(t=>t.review.still==='REJECTED'),blocked=cnt(t=>t.status==='FAILED'),oobN=cnt(isOob),
    animOk=cnt(t=>t.anim_status==='READY'&&!isOob(t)&&t.review.anim!=='REJECTED'&&t.review.still!=='REJECTED'),aDrop=cnt(t=>t.anim_status==='READY'&&t.review.anim==='REJECTED'&&t.review.still!=='REJECTED'),animFail=cnt(t=>t.anim_status==='FAILED');
  const anim=gs.some(animPhase),hasVid_=gs.some(hasVid);
  const S=[['Request','done',esc(SES.prompt||g0.prompt||''),'request'],
   ['Prompt',g0.sheet_prompt?'done':'todo',`${esc(g0.template_id||'plan')}${g0.template_version?' v'+g0.template_version:''} · tags`,'plan'],
   ['Stickers',ready?(good?'done':'warn'):'run',ready?`${kept} kept${dropped?`, ${dropped} dropped`:''}${blocked?`, ${blocked} blocked`:''}`:'Making…','stickers'],
   ['Animation',busyAnim?'run':anim?(oobN||animFail?'warn':'done'):'todo',busyAnim?`Animating ${done} of ${tot}…`:anim?`${animOk} ready${aDrop?`, ${aDrop} dropped`:''}${oobN?`, ${oobN} out of bounds (off)`:''}${animFail?`, ${animFail} failed`:''}`:hasVid_?'Not started':'No video prepared','anim'],
   ['Pack',allAdded?'done':'todo',allAdded?`Added to “${esc(pk.name)}”`:'Not added yet','pack']];
  const mark=(st,i)=>st==='done'?ic('check'):st==='run'?'<span class=spin></span>':st==='warn'?'!':i+1;
  return`<div class=gsteps>${S.map(([l,st,sub,tab],i)=>`<button class="gst ${st} ${tab===cur?'cur':''}" ${tab==='pack'?`data-act=gadd ${ready&&n?'':'disabled'}`:`data-act=gtab data-t=${tab}`}><span class=gsm>${mark(st,i)}</span><span class=gsl><b>${l}</b><small title="${sub.replace(/<[^>]+>/g,'')}">${sub}</small></span></button>`).join('')}</div>`}

ACT.gopenfolder=async el=>{const r=await post(`/api/generations/${el.dataset.g}/reveal`);if(!r.ok)return toast(r.j.error||'Could not open the folder',1);toast('Opened '+r.j.opened)};

/* ---------- Plan: the prompts the sheet and video were made from, and the 1-5 tags per cell. */
const copyBox=(title,text,id,rows,edit)=>`<div class=pbox><div class=pbh><b>${title}</b><button class="btn sm" data-act=hcopy data-t=${id}>Copy</button></div><textarea ${edit?`data-pd=${edit.kind} data-g=${edit.g}`:'readonly'} id=${id} rows=${rows}>${esc(text||'')}</textarea>${edit?edit.foot:''}</div>`;
/* The Prompt tab writes the prompts too: what is typed here is what is SENT (the server keeps it on the batch: `custom_prompts`, `video_prompt_sent`). Drafts live in PD per batch and kind, so a re-render
   (the page refreshes while a batch works) never loses what was typed; the tick skips its re-render while one of these boxes has the focus. */
const PD={};
if(GD&&GD.edits)Object.assign(PD,GD.edits);
const pdKey=(g,kind)=>`${g}:${kind}`;
const sentVideoPrompt=g=>{const v=(g.video_sheets||[]).slice().reverse().find(x=>x.video_prompt_sent);return v?v.video_prompt_sent:null};
const pdText=(g,kind)=>{const d=PD[pdKey(g.number,kind)];return d!==undefined?d:kind==='sheet'?g.sheet_prompt:(sentVideoPrompt(g)||g.video_prompt)};
const pdBase=(g,kind)=>kind==='sheet'?g.sheet_prompt:(sentVideoPrompt(g)||g.video_prompt);
const pdCustom=(g,kind)=>{const d=PD[pdKey(g.number,kind)];return d!==undefined&&d.trim()!==''&&d!==pdBase(g,kind)};
function pdFoot(g,kind){const custom=pdCustom(g,kind),live=typeof liveReadyNow==='function'&&liveReadyNow();
  if(g.number==='draft')return gdFoot(g,kind);
  const kept=typeof keptStills==='function'?keptStills(g).length:0,sent=(g.video_sheets||[]).some(v=>['VIDEO_RETURNED','SLICED'].includes(v.status));
  const go=kind==='sheet'
    ?`<button class="btn sm pri" data-act=pgsheet data-g=${g.number} ${live?'':'disabled'} title="${live?'Make a NEW sheet from this batch\'s own cells and tags, with this prompt':'Higgsfield is not connected'}">Generate sheet${custom?' with my prompt':''}<span class=lv-vp data-lvprice=image></span></button>`
    :`<button class="btn sm pri" data-act=pgvideo data-g=${g.number} ${live&&kept&&!sent?'':'disabled'} title="${!live?'Higgsfield is not connected':sent?'This sheet already has its video; the engine does not animate a sliced sheet twice. Make a new sheet first.':kept?'Animate the kept stickers with this prompt':'Keep at least one sticker first'}">Generate video${custom?' with my prompt':''}<span class=lv-vp data-lvprice=video></span></button>`;
  return`<div class=pdfoot data-pdfoot=${kind}>${go}<button class="btn sm" data-act=pgreset data-g=${g.number} data-kind=${kind} ${PD[pdKey(g.number,kind)]!==undefined?'':'hidden'}>Reset</button><small class=mut>${custom?'Your text is sent exactly as written.':'This is the template\'s text; edit it to send your own.'} The templates stay as they are.</small></div>`}
function planView(g){const pl=g.reviews&&g.reviews.plan,sv=sentVideoPrompt(g);
  return`<section class=gplan><div class=pcols><div>${copyBox('Sheet prompt',pdText(g,'sheet'),'pp1',11,{kind:'sheet',g:g.number,foot:pdFoot(g,'sheet')})}${copyBox(sv&&PD[pdKey(g.number,'video')]===undefined?'Video prompt (the one sent)':'Video prompt',pdText(g,'video'),'pp2',6,{kind:'video',g:g.number,foot:pdFoot(g,'video')})}
   <p class=mut>Template <b>${esc(g.template_id||'hand-written plan')}</b>${g.template_version?' v'+g.template_version:''} · plan from ${esc(g.plan_source||'')}${pl?` · ${esc(pl.decision.toLowerCase())}d by ${esc(pl.by)}`:''}</p></div>
   <ul class=pcells>${g.stickers.map(t=>`<li><b>${t.index}. ${esc(t.emoji)} ${esc(t.key.replace(/_/g,' '))}</b><div class=mut>${esc(t.prompt)}</div><div class=ptags>${(t.tags||[]).map(x=>`<span>${esc(x)}</span>`).join('')}</div></li>`).join('')}</ul></div></section>`}
document.addEventListener('input',e=>{const t=e.target;if(!t.dataset||t.dataset.pd===undefined)return;
  const g=t.dataset.g==='draft'?GD:GM.get(+t.dataset.g);if(!g)return;PD[pdKey(g.number,t.dataset.pd)]=t.value;if(g===GD)gdSave();
  const foot=t.closest('.pbox').querySelector('[data-pdfoot]');if(foot){const tmp=document.createElement('div');tmp.innerHTML=pdFoot(g,t.dataset.pd);foot.replaceWith(tmp.firstChild);if(typeof fillPrices==='function')fillPrices();if(g===GD)gdPrice()}});
ACT.pgreset=el=>{const n=el.dataset.g==='draft'?'draft':+el.dataset.g;delete PD[pdKey(n,el.dataset.kind)];if(n==='draft')gdSave();glast='';tick(true)};
/* The same Prompt editor, before a sheet exists (docs/engine-and-studio.md, the Generate prompt step). "Generate prompt" is POST /api/plan: no G### is allocated, nothing enters SES or GM, no Higgsfield credit is spent.
   With the AI enhancer On the plan is written through the engine the person chose (ai:true; Local is free, Cloud is one small OpenAI call); a model that fails never blocks, the server answers the built-in plan with expand_error and the step says why.
   "Generate sheet" is the one click that spends: the Higgsfield price sits on its own line above it, the edited text goes to the live sheet route as `sheet_prompt` and the previewed plan (its cells, tags and emoji) as `plan`, which the server re-validates (rule 13). */
const gdOn=()=>!!(GD&&GD.active&&GD.gens===SES.gens.join());      // another batch taking the Studio (an opened batch, a finished sheet) ends this screen; the composer's "Prompt draft" brings it back
function gdSave(){if(GD){GD.edits=Object.fromEntries(Object.entries(PD).filter(([k])=>k.startsWith('draft:')));gstore('mirsal.prompt-draft',JSON.stringify(GD))}}
function gdHide(){if(GD){GD.active=false;gdSave()}}
function gdDrop(){GD=null;GDP=null;delete PD['draft:sheet'];delete PD['draft:video'];try{localStorage.removeItem('mirsal.prompt-draft')}catch(e){}}
const gdKey=()=>{const {model,sel}=lsel('image');return model?model.id+JSON.stringify(sel.options):''};
function gdPriceLine(){if(typeof liveReadyNow!=='function'||!liveReadyNow())return{t:'Higgsfield sheet price: unavailable, Higgsfield is not connected',ok:false};
  if(!GDP||GDP.key!==gdKey())return{t:'Higgsfield sheet price: checking…',ok:false};
  return GDP.c==null?{t:'Higgsfield sheet price: unavailable',ok:false,retry:true}:{t:`Higgsfield sheet price: ◈ ${fcr(GDP.c)} credits`,ok:true}}
function gdFoot(g,kind){const reset=`<button class="btn sm" data-act=pgreset data-g=draft data-kind=${kind} ${PD[pdKey('draft',kind)]!==undefined?'':'hidden'}>Reset</button>`;
  if(kind==='video')return`<div class=pdfoot data-pdfoot=video>${reset}<small class=mut>This video prompt is for later: the animation is made after the sheet and its stickers exist.</small></div>`;
  const P=gdPriceLine(),custom=pdCustom(g,'sheet');
  return`<div class=pdfoot data-pdfoot=sheet><div class=mut id=gdprice>${P.t}</div>${P.retry?'<button class="btn sm" data-act=gdpriceretry>Retry the price</button>':''}<button class="btn sm pri" data-act=gdsheet ${P.ok&&!GDWORK?'':'disabled'} title="Spends the Higgsfield credits shown above">Generate sheet${custom?' with my prompt':''}</button>${reset}<small class=mut>${custom?'Your text is sent exactly as written.':g.expanded_by==='ai'?'The AI enhancer\'s text is sent exactly as shown.':'This is the template\'s text; edit it to send your own.'} Generating the prompt spent no Higgsfield credits; this click is what spends.</small></div>`}
function gdPaint(){const foot=document.querySelector('[data-pdfoot=sheet]');if(!gdOn()||!foot||!foot.querySelector('[data-act=gdsheet]'))return;const tmp=document.createElement('div');tmp.innerHTML=gdFoot(GD,'sheet');foot.replaceWith(tmp.firstChild)}
async function gdPrice(){if(!gdOn()||typeof liveReadyNow!=='function'||!liveReadyNow())return;const key=gdKey();if(GDP&&GDP.key===key)return;
  const c=await lcost('image',true);GDP={key,c};gdPaint()}
function gdView(){const tab=GD.tab==='request'?'request':'plan';
  return`<div class=ghead><div><h2 style="margin:0">Prompt, before the sheet</h2><div class=mut>No batch exists yet · written by ${esc(GD.plan_source||'the free built-in planner')} · ${GD.expanded_by==='ai'?'no Higgsfield credits spent':'nothing spent'}</div></div><button class="btn sm" data-act=gddiscard title="Forget this prompt and its edits. Nothing was created, so nothing is removed">Discard prompt</button></div>
   <div class=gsteps>${[['Request','done',esc(GD.prompt),'request'],['Prompt','todo','editable, nothing spent','plan'],['Stickers','todo','after the sheet'],['Animation','todo','after the stickers'],['Pack','todo','after the stickers']].map(([l,st,sub,t],i)=>`<button class="gst ${st} ${t===tab?'cur':''}" ${t?`data-act=gdtab data-t=${t}`:'disabled'}><span class=gsm>${st==='done'?ic('check'):i+1}</span><span class=gsl><b>${l}</b><small title="${sub.replace(/<[^>]+>/g,'')}">${sub}</small></span></button>`).join('')}</div>
   ${gdNote(GD)}${tab==='request'?`<section class=gplan><p>${esc(GD.prompt)}</p><button class=btn data-act=gdtab data-t=plan>Back to the prompt</button> <small class=mut>To change the request, edit the box above and press Generate prompt again; your edits stay until the new prompt is ready.</small></section>`:planView(GD)}`}
ACT.gdtab=el=>{if(!GD)return;GD.active=true;GD.gens=SES.gens.join();GD.tab=el.dataset.t==='request'?'request':'plan';gdSave();glast='';if(typeof cpDrawBar==='function')cpDrawBar();tick(true)};
ACT.gddiscard=()=>{gdDrop();glast='';if(typeof cpDrawBar==='function')cpDrawBar();tick(true)};
ACT.gdpriceretry=()=>{const {model,sel}=lsel('image');if(model)delete LIVE.est['image'+model.id+JSON.stringify(sel.options)];GDP=null;gdPaint();gdPrice()};
/* Generate prompt: with the AI enhancer On the plan is written by the model the person chose (the same engine control as the AI screen: Auto / Local / Cloud, composer.js); a model that fails never blocks, the server answers the built-in plan with `expand_error` and the step says why */
const gdEngineName=()=>{const g=typeof GAI!=='undefined'?GAI:null;return g&&g.provider&&g.provider!=='none'?`${g.provider==='openai'?'cloud':'local'} · ${String(g.model||'').replace(/:\d+$/,'')}`:''};
ACT.gprompt=()=>gdPlan(typeof aiOn==='function'&&aiOn());
ACT.gpromptfree=()=>gdPlan(false);          // "Use the built-in prompt instead": plans again without the model; the saved enhancer setting is not changed
async function gdPlan(ai){const p=(($('prompt')||{}).value||'').trim();if(!p){say('Write what you want first, for example <b>teddy bear for school</b>.');return}if(GDWORK)return;
  if(typeof CP!=='undefined'&&CP.refs.some(r=>r.busy)){toast('Wait for the reference images to finish uploading',1);return}
  GDWORK=true;const b=$('go');if(b)b.disabled=true;
  if(ai)say(`Asking the AI enhancer${gdEngineName()?` (${esc(gdEngineName())})`:''}… a local model can take a moment.`);
  try{const style=typeof LIVE!=='undefined'?LIVE.style:'flat_vector',loop=!!(typeof LIVE!=='undefined'&&LIVE.loop);
    const r=await post('/api/plan',{prompt:p,grid:'3x3',style_id:style,loop,ai:!!ai});if(!r.ok){say('');toast(r.j.error||'Could not generate the prompt',1);return}
    delete PD['draft:sheet'];delete PD['draft:video'];
    const byAi=r.j.expanded_by==='ai';
    GD={...r.j,number:'draft',prompt:p,ai_asked:!!ai,plan_source:byAi?`the AI enhancer${r.j.expand_model?` (${r.j.expand_model})`:''}`:'the free built-in planner',video_sheets:[],reviews:{},active:true,tab:'plan',gens:SES.gens.join(),style,loop,refs:typeof CP!=='undefined'?CP.refs.filter(x=>x.id).map(x=>x.id):[]};
    say('');gdSave();glast='';await tick(true);
    const gr=$('gres');if(gr&&gr.scrollIntoView)gr.scrollIntoView({behavior:'smooth',block:'start'})          // the step sits below the style tiles: bring it into view so the click visibly does something
  }catch(e){say('');toast(e.message||'Could not generate the prompt',1)}finally{GDWORK=false;if(b)b.disabled=false;if(typeof cpDrawBar==='function')cpDrawBar();gdPrice()}}
/* the one line under the step's title about the enhancer: why the built-in prompt is shown (the model failed or has no key: the server's own reason), or that the model wrote it and how to leave it */
function gdNote(g){if(!g.ai_asked)return'';
  if(g.expand_error)return`<div class="gdnote bad" role=status><span>The AI enhancer did not answer: ${esc(g.expand_error)} This is the built-in prompt instead.</span></div>`;
  if(g.expanded_by==='transformation')return`<div class=gdnote role=status><span>This request changes one character, so the built-in template wrote the cells and the AI enhancer was not asked.</span></div>`;
  if(g.expanded_by==='ai')return`<div class=gdnote role=status><span>Written by the AI enhancer${g.expand_model?` (${esc(g.expand_model)})`:''}.</span><button class="btn sm" data-act=gpromptfree>Use the built-in prompt instead</button></div>`;
  return''}
ACT.gdsheet=async el=>{if(!gdOn()||GDWORK)return;const g=GD,text=(pdText(g,'sheet')||'').trim();if(!text){toast('Write a sheet prompt first',1);return}
  if(typeof liveReadyNow!=='function'||!liveReadyNow()){toast('Connect Higgsfield first',1);return}
  if(!gdPriceLine().ok){toast('The Higgsfield price is not known yet: wait for it or retry it, then generate',1);return}       // never spend against a price the person has not been shown
  GDWORK=true;el.disabled=true;
  try{const ok=await liveStart('sheet',{prompt:g.prompt,ai:false,refs:g.refs||[],style_id:g.style,loop:g.loop,sheet_prompt:(pdCustom(g,'sheet')||g.expanded_by==='ai')?pdText(g,'sheet'):undefined,
    plan:g.slots?{template_id:g.template_id,expanded_by:g.expanded_by,expand_model:g.expand_model,slots:{subject_description:g.slots.subject_description,key_colour:g.slots.key_colour,cells:g.slots.cells}}:undefined});     // the previewed plan goes with the click: the server validates it and builds the batch from the cells the person saw (ai:false: the enhancer is never asked a second time)
    if(ok){gdDrop();glast='';await tick(true)}}
  finally{GDWORK=false;if(GD){gdSave();gdPaint()}if(typeof cpDrawBar==='function')cpDrawBar()}};
ACT.pgsheet=async el=>{const g=GM.get(+el.dataset.g);if(!g||typeof liveStart!=='function')return;el.disabled=true;
  const ok=await liveStart('sheet',{prompt:g.prompt||SES.prompt||'',ai:false,refs:[],from_generation:g.number,sheet_prompt:pdCustom(g,'sheet')?PD[pdKey(g.number,'sheet')]:undefined});
  if(!ok)el.disabled=false;else delete PD[pdKey(g.number,'sheet')];glast='';tick(true)};
ACT.pgvideo=async el=>{const g=GM.get(+el.dataset.g);if(!g||typeof liveStart!=='function')return;el.disabled=true;
  const ok=await liveStart('video',{g:g.number,video_prompt:pdCustom(g,'video')?PD[pdKey(g.number,'video')]:undefined});
  if(!ok)el.disabled=false;else delete PD[pdKey(g.number,'video')];glast='';tick(true)};
/* Remove batch (like Delete pack, but into the trash): says what it does before it does it; stickers already added to a pack are copies and stay in their packs */
const grmText=gs=>`Remove ${gs.map(g=>g.generation_id).join(', ')}? ${gs.length===1?'It moves':'They move'} to the trash, nothing is deleted, and you can restore ${gs.length===1?'it':'them'} from “Removed batches” under Earlier batches. Stickers you already added to a pack stay in their packs.`;
/* Add to group: pick the batch (family) this one joins; the picked one is the parent (flow/groups.py) */
ACT.ggroup=()=>{const g=sessionGens()[0];if(!g)return;const fams=(typeof HB!=='undefined'?HB.items:[]).filter(it=>!(it.variants||[it]).some(v=>v.id===g.number));
  if(!fams.length)return toast('Scroll Earlier batches to load more batches first',1);
  dlg(`<h2>Add ${esc(g.generation_id)} to the group of…</h2><div class=lv-hcol>${fams.map(it=>`<button class=lv-hrow data-act=ggroupgo data-from=${g.number} data-to=${it.id}>${histThumb(it)}<span class=lv-hmeta><b>${histTitle(it)}</b><small>${esc(it.generation_id)}${(it.variants||[]).length>1?` · ${it.variants.length} variations`:''}</small></span></button>`).join('')}</div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button></div>`)};
ACT.ggroupgo=el=>{closeDlg();histJoin(+el.dataset.from,+el.dataset.to)};
ACT.grm=()=>{const gs=sessionGens();if(!gs.length)return;
  confirmDlg(grmText(gs),async()=>{for(const g of gs){const r=await post(`/api/generations/${g.number}/remove`,{});if(!r.ok){toast(r.j.error,1);return}}
    const gone=gs.map(g=>g.number);SES.gens=SES.gens.filter(id=>!gone.includes(id));saveSes();gone.forEach(n=>GM.delete(n));HB.items=HB.items.filter(x=>!gone.includes(x.id));
    glast='';await remLoad();histLoad(false);tick(true)},'Remove')};
ACT.gtab=el=>{if(el.dataset.t==='particles'&&typeof ACT.spopen==='function')return ACT.spopen(el);GS.tab=el.dataset.t;glast='';tick(true)};

/* ---------- Animate, Add: both act on the included batches of the session. */

ACT.ganimate=async el=>{const todo=included().filter(g=>g.source.has_video&&!animPhase(g)&&!processing(g)&&keptStills(g).length);if(!todo.length)return;
  todo.forEach(g=>{ANIM.add(g.number);PVON.add(g.number);if(g.source.video_path)pvEnsure(g)});GS.tab='anim';glast='';tick(true);
  for(const g of todo){const r=await postWait(`/api/generations/${g.number}/animate`,{scope:'pack'},'Waiting for the previous animation…');if(!r.ok){toast(r.j.error,1);ANIM.delete(g.number)}}};
/* Pack: a three-step modal. 1 the pack (and replace-or-add when stills of the same stickers are already in it), 2 how it looks on each
   background, 3 the names the library will show (name, emoji, and the generator's file name, which never changes) */
let PW=null;
const rname=k=>{const t=String(k).replace(/[-_]+/g,' ').trim();return(t.charAt(0).toUpperCase()+t.slice(1)).slice(0,60)};
const PWBG=[['chat','Chat'],['light','Light'],['dark','Dark'],['checker','Transparent'],['wall','Wallpaper']];
ACT.gadd=async el=>{await loadLib();const inc=el&&el.dataset.g?included().filter(g=>spGid(g.generation_id)===spGid(el.dataset.g)):included(),rows=[];
  for(const g of inc)for(const t of keptOf(g))rows.push({g:g.number,gen:g.generation_id,i:t.index,anim:animPhase(g),src:`/out/${g.generation_id}/${animPhase(g)?t.webm:t.png}`,name:rname(t.key),emoji:t.emoji,file:t.name});
  if(!rows.length)return;
  const ps=LIB.packs,def=SES.pack&&packById(SES.pack)?SES.pack:'',base=titleCase(inc[0].source.subject);
  let name=base,k=2;while(ps.some(p=>p.name.toLowerCase()===name.toLowerCase()))name=`${base} ${k++}`;
  PW={rows,anim:rows.some(r=>r.anim)};
  const prev=r=>r.anim?`<video src="${r.src}" autoplay loop muted playsinline></video>`:`<img src="${r.src}">`;
  dlg(`<div class=pw><h2 style="margin:0">Add to a pack</h2><div class=mut>${rows.length} ${PW.anim?'animated stickers':'stickers'} from ${inc.length} batch${inc.length===1?'':'es'}</div>
   <div class=pwgrid><div>
    <div class=pwstep><span class=pwn>1</span><b>Choose the pack</b></div>
    <label class=radio><input type=radio name=gp value=new ${def?'':'checked'}> <b>New pack</b></label>
    <div class=fld><input type=text id=gpname value="${esc(name)}" maxlength=60 placeholder="Pack name" autocomplete=off></div>
    ${ps.length?`<label class=radio><input type=radio name=gp value=old ${def?'checked':''}> <b>An existing pack</b></label>
    <div class=fld><select id=gpold>${ps.map(p=>`<option value="${p.id}" ${p.id===def?'selected':''}>${esc(p.name)} (${p.stickers.length})</option>`).join('')}</select></div>`:''}
    <div id=pwtwins></div>
    <div class=pwstep style="margin-top:16px"><span class=pwn>2</span><b>How it looks</b><select id=pwbg style="width:auto;margin-left:auto;padding:4px 10px">${PWBG.map(([k,l])=>`<option value=${k}>${l}</option>`).join('')}</select></div>
    <div id=pwprev class="pwprev bg-chat">${rows.map(r=>`<div title="${esc(r.name)}">${prev(r)}<span>${esc(r.emoji)}</span></div>`).join('')}</div>
   </div><div>
    <div class=pwstep><span class=pwn>3</span><b>Names in your library</b></div>
    <div class=mut style="margin-bottom:8px">Rename if you like. Telegram needs at least one emoji per sticker. The file name is kept as it came from the generator.</div>
    <div class=pwrows>${rows.map((r,x)=>`<div class=pwrow><div class=pwth>${prev(r)}</div><div style="flex:1;min-width:0"><div class=pwfields><input type=text data-r=${x} data-k=name value="${esc(r.name)}" maxlength=60><input type=text data-r=${x} data-k=emoji value="${esc(r.emoji)}" maxlength=20 class=pwemo></div><small class=mut title="${esc(r.file)}">${esc(r.file)}</small></div></div>`).join('')}</div>
   </div></div>
   <div class=row style="justify-content:flex-end;margin-top:14px"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" id=pwgo data-act=pwgo></button></div></div>`);
  $('pwbg').onchange=e=>{$('pwprev').className='pwprev bg-'+e.target.value};
  const nm=$('gpname'),old=$('gpold');nm.onfocus=()=>{document.querySelector('input[name=gp][value=new]').checked=true;pwSync()};
  if(old){old.onfocus=()=>{document.querySelector('input[name=gp][value=old]').checked=true;pwSync()};old.onchange=pwSync}
  document.querySelectorAll('input[name=gp]').forEach(r=>r.onchange=pwSync);nm.oninput=pwSync;pwSync();if(!def){nm.focus();nm.select()}};
function pwPack(){const mode=(document.querySelector('input[name=gp]:checked')||{}).value||'new';return mode==='old'&&$('gpold')?{old:true,id:$('gpold').value}:{old:false,name:$('gpname').value.trim()}}
/* the pack changed: ask replace-or-add when it already holds the still of an animated sticker, and name the button */
function pwSync(){const p=pwPack(),pk=p.old?packById(p.id):null;
  const twins=!PW.anim||!pk?0:PW.rows.filter(r=>pk.stickers.some(s=>s.type==='static'&&s.source&&s.source.generation===r.gen&&s.source.index===r.i)).length;
  const keep=(document.querySelector('input[name=pwmode]:checked')||{}).value||'replace';
  $('pwtwins').innerHTML=twins?`<div class=pwtw><b>${twins} ${twins===1?'is':'are'} in “${esc(pk.name)}” as ${twins===1?'a still':'stills'} already.</b>
    <label class=radio><input type=radio name=pwmode value=replace ${keep==='replace'?'checked':''}> Replace the ${twins===1?'still':'stills'} with the animated ${twins===1?'one':'ones'}</label>
    <label class=radio><input type=radio name=pwmode value=add ${keep==='add'?'checked':''}> Add next to ${twins===1?'it':'them'}</label></div>`:'';
  $('pwgo').textContent=`Add ${PW.rows.length} to “${p.old?pk.name:(p.name||'new pack')}”`}
ACT.pwgo=async()=>{const p=pwPack();let pid;
  if(p.old)pid=p.id;else{if(!p.name){toast('Give the pack a name',1);return}const r=await post('/api/packs',{name:p.name});if(!r.ok)return toast(r.j.error,1);pid=r.j.id}
  const mode=(document.querySelector('input[name=pwmode]:checked')||{}).value==='add'?'add':'replace',names={};
  document.querySelectorAll('.pwrows input').forEach(i=>{const r=PW.rows[+i.dataset.r];(names[r.g]=names[r.g]||{})[r.i]=Object.assign(names[r.g][r.i]||{},{[i.dataset.k]:i.value.trim()})});
   closeDlg();await gaddrun(pid,mode,names)};
/* the wizard's own rows decide what is added (the included batches of the session) */
async function gaddrun(pid,mode,names){let added=0,replaced=0,err='';const edge=typeof egDirty==='function'&&egDirty()?{outline:egVals().o,erode:egVals().e}:{},
  gens=[...new Set(PW.rows.map(r=>r.g))].map(n=>GM.get(n)).filter(Boolean);
  for(const g of gens){if(!keptOf(g).length)continue;const r=await postWait(`/api/generations/${g.number}/add`,{pack_id:pid,mode,names:(names||{})[g.number]||{}});if(r.ok){added+=r.j.added;replaced+=r.j.replaced||0}else err=r.j.error}
  await loadLib();PW.pid=pid;SES.pack=pid;saveSes();glast='';tick(true);
  if(!err&&typeof spAfterPack==='function')await spAfterPack();
  if(err)toast(err,1);else toast(replaced?`Replaced ${replaced} still${replaced===1?'':'s'} with animated stickers in “${packById(pid).name}”`:added?`Added ${added} to “${packById(pid).name}”`:'Those are already in that pack')}
/* Open the pack this view just added to */
ACT.gopenpack=()=>{const pid=(PW&&PW.pid)||SES.pack;if(pid)location.hash='#/pack/'+pid};

/* ---------- Make a video...: the one multi-step path, for a batch without a prepared video */
ACT.gvideo=async el=>{const id=+el.dataset.g,r=await postWait(`/api/generations/${id}/quick_sheet`);glast='';await tick(true);if(!r.ok&&!sheetOf(GM.get(id)||{video_sheets:[]})){toast(r.j.error,1);return}VG=id;drawVdlg()};
function drawVdlg(){if(VG===null)return;const g=GM.get(VG);if(!g){VG=null;return}const v=sheetOf(g);if(!v){VG=null;closeDlg();return}
  if(v.status==='SLICED'){VG=null;closeDlg();toast('Animations are ready');glast='';return}
  const base=`/out/${g.generation_id}/`,st=v.status,work=st==='VIDEO_RETURNED';
  const row=(n,done,h)=>`<div class=vstep><span class="vn ${done?'ok':''}">${done?ic('check'):n}</span><div style="flex:1">${h}</div></div>`;
  dlg(`<div class=vdlg><h2>Make a video from this sheet</h2>${SR.bulk(g)}<div class=vgrid>${SR.picture(g,v)}
   <div>${row(1,false,`<b>Download the sheet</b><div class=mut>${v.slots.length} of ${g.stickers.length} stickers on a flat green background, no outline.</div><a class="btn sm" href="${base+v.file}" download="${g.generation_id}-${v.id}-sheet.png">${ic('download')} Download sheet</a>`)}
   ${row(2,false,`<b>Animate it in your tool</b><div class=mut>Image to video, sheet as the first frame.</div><button class="btn sm" data-act=gcopyprompt>Copy video prompt</button>`)}
   ${row(3,st==='SLICED',`<b>Upload the video</b><div class=mut>${work?'Python is slicing the video…':st==='VIDEO_BLOCKED'?`<span style="color:var(--bad)">This video was not accepted (${esc(v.block||'')}). Upload a corrected one.</span>`:'It is cut into one animation per sticker.'}</div>
     <input type=file id=gvfile accept="video/*,.mp4,.mov,.webm,.mkv" hidden><button class="btn pri sm" data-act=gpickvideo ${work||v.blocked?'disabled':''}>${ic('plus')} ${st==='VIDEO_BLOCKED'?'Upload another video':'Upload video'}</button>${st==='BUILT'&&!v.blocked?`<button class="btn sm" data-act=gsheetapprove data-g=${g.number}>Approve sheet</button>`:''}`)}</div></div>
   <div class=row style="justify-content:flex-end"><button class=btn data-act=gvclose>Close</button></div></div>`);
  const f=$('gvfile');if(f)f.onchange=async()=>{const file=f.files[0];if(!file)return;const r=await fetch(`/api/generations/${g.number}/video_sheet/${v.id}/video?name=${encodeURIComponent(file.name)}`,{method:'POST',body:file});
    if(!r.ok){let j={};try{j=await r.json()}catch(e){}toast(j.error||'Upload failed',1)}glast='';tick(true)}}
ACT.gpickvideo=()=>{const f=$('gvfile');if(f)f.click()};
ACT.gsheetapprove=async el=>{const r=await postWait(`/api/generations/${+el.dataset.g}/quick_sheet`);if(!r.ok)toast(r.j.error,1);glast='';await tick(true);drawVdlg()};
ACT.gvclose=()=>{VG=null;closeDlg()};
ACT.gcopyprompt=async()=>{const g=GM.get(VG),v=g&&sheetOf(g);try{await navigator.clipboard.writeText((v&&v.video_prompt)||(g&&g.video_prompt)||'');toast('Video prompt copied')}catch(e){toast('Copy failed',1)}};

/* ---------- Green screen & cuts: the raw / keyed sheet, the measured cut lines, each sticker's boundary, and the analysis */
const SV={g:null,view:'raw',lines:true,boxes:true};
/* the measured cut lines (dashed), the cell numbers and each sticker's boundary, as SVG over a sheet of size sheet_size */
function cutSvg(g,lines,boxes,k=1,stage='still'){const s=g.source,[W,H]=s.sheet_size,G=s.grid,sw=Math.max(2,W/450)*k;let svg='';
  if(G&&lines)svg+=G.xs.slice(1,-1).map(x=>`<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#2563eb" stroke-width="${sw}" stroke-dasharray="${W/50} ${W/90}"/>`).join('')+G.ys.slice(1,-1).map(y=>`<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="#2563eb" stroke-width="${sw}" stroke-dasharray="${W/50} ${W/90}"/>`).join('');
  g.stickers.forEach(t=>{const m=t.metrics||{},c=m.cell,b=m.bbox;if(!c)return;
    if(lines)svg+=`<text x="${c[0]+W/90}" y="${c[1]+W/22}" font-size="${W/26}" font-weight="700" fill="#2563eb" stroke="#fff" stroke-width="${W/380}" paint-order="stroke">${t.index}</text>`;
    const mk=boxes&&mark(t,stage,g);
    if(boxes&&b)svg+=`<rect x="${c[0]+b[0]}" y="${c[1]+b[1]}" width="${b[2]-b[0]}" height="${b[3]-b[1]}" fill="none" stroke="${mk&&!mk.accepted?CAT[mk.cat][0]:'#facc15'}" stroke-width="${sw*1.4}"/>`});
  return svg+(boxes?issueSvg(g,stage,k):'')}
/* The Animation view's left panel, the twin of the green-screen panel: the prepared video as one sheet with the same cut lines, a chip per
   cell showing how it came out, and the analysis at a glance; "Full analysis" has every number and every check that did not pass. */
const cellState=t=>t.status!=='READY'?'skip':isOob(t)?'oob':t.anim_status==='READY'?'ok':t.anim_status==='FAILED'?'fail':t.anim_status==='PROCESSING'?'busy':'todo';
const CELLTXT={ok:'ready',oob:'out of bounds',fail:'no animation',busy:'working',todo:'not animated',skip:'no still'};
function vcutSvg(g,k){return cutSvg(g,true,false,k)+issueSvg(g,'anim',k)}
function animStats(g){const S=g.stickers.filter(t=>t.status==='READY'),A=S.filter(t=>t.anim_status==='READY'),kb=A.map(t=>(t.anim_metrics||{}).kb||0);
  return{total:S.length,done:A.length,oob:S.filter(isOob),fail:S.filter(t=>t.anim_status==='FAILED'),avg:kb.length?Math.round(kb.reduce((a,b)=>a+b,0)/kb.length):0,max:Math.max(0,...kb),
    ms:A.filter(t=>(t.anim_metrics||{}).cache!=='hit').reduce((a,t)=>a+(((t.anim_metrics||{}).ms||{}).finish||0),0),cached:A.filter(t=>(t.anim_metrics||{}).cache==='hit').length}}
const LAY=new Map();      // a video sheet's layout.json, fetched once
function layoutOf(g,v){const k=g.number+v.id;if(LAY.has(k))return LAY.get(k);LAY.set(k,null);
  fetch(`/out/${g.generation_id}/${v.layout}`).then(r=>r.json()).then(j=>{LAY.set(k,j);glast='';tick(true)}).catch(()=>{});return null}
function videoBox(g,k){const sz=g.source.sheet_size,v=sheetOf(g);
  if(g.source.video_path&&sz)return`<div class=sbox style="background:#111"><video src="/src/${g.number}/video" autoplay loop muted playsinline style="display:block;width:100%;aspect-ratio:${sz[0]}/${sz[1]};object-fit:fill"></video><svg viewBox="0 0 ${sz[0]} ${sz[1]}" preserveAspectRatio="none">${vcutSvg(g,k)}</svg></div>`;
  if(v&&v.video){const [W,H]=v.canvas||[1,1],lay=layoutOf(g,v),sw=Math.max(2,W/450)*k;
    const rects=lay?lay.slots.map(sl=>`<rect x="${sl.rect[0]}" y="${sl.rect[1]}" width="${sl.rect[2]}" height="${sl.rect[3]}" fill="none" stroke="#2563eb" stroke-width="${sw}" stroke-dasharray="${W/50} ${W/90}" opacity="${sl.sticker?1:.35}"/>`).join(''):'';
    return`<div class=sbox style="background:#111"><video src="/out/${g.generation_id}/${v.preview||v.video}" autoplay loop muted playsinline style="display:block;width:100%;aspect-ratio:${W}/${H};object-fit:fill"></video><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">${rects}${issueSvg(g,'anim',k)}</svg>${SR.controls(g,v)}</div>`}
  if(v)return SR.picture(g,v);
  return`<div class="gbadmsg mut" style="padding:26px 10px">These animations come from pre-sliced clips, so there is no single video sheet for this batch.</div>`}
function videoPanel(g){const s=g.source,vs=sheetOf(g),vi=Object.assign({},vs&&vs.video_info||{},s.video_info||{}),a=animStats(g),bad=a.oob.length+a.fail.length;
  return`<aside class=gsheet><div class=gshead><b>Video sheet</b><span class=gspace></span><span class="gcut ${bad?'warn':'ok'}">${a.done} of ${a.total} animated${a.oob.length?`, ${a.oob.length} out`:''}</span></div>
   ${videoBox(g,2)}
   ${SR.bulk(g)}
   <div class=vchips>${g.stickers.map(t=>chip(g,t,'anim')).join('')}</div>
    ${allowAllRow(g,'animation')}
   <div class="kv vkv"><span>source</span><span>${esc(vi.mode||(s.video_path?'3x3 mp4':vs&&vs.video?'video sheet':'clips'))}${vi.size?' · '+esc(vi.size):vi.width?' · '+vi.width+'×'+vi.height:''}${vi.fps?' · '+vi.fps+' fps':''}</span>
    <span>out of bounds</span><span>${a.oob.length?a.oob.map(t=>'S'+t.index).join(', '):'none'}</span><span>no animation</span><span>${a.fail.length?a.fail.map(t=>'S'+t.index).join(', '):'none'}</span>
    <span>size</span><span>${a.done?`${a.avg} KB average, ${a.max} KB largest`:'-'}</span><span>work</span><span>${a.done?`${(a.ms/1000).toFixed(1)} s${a.cached?` · ${a.cached} from the cache`:''}`:'-'}</span></div>
   <div class=gsfoot><span class=mut>blue = cuts</span><button class="link" data-act=gvsheet data-g=${g.number}>Full analysis</button></div>${legend(g,'anim')}</aside>`}
const AV={g:null};
ACT.gvsheet=el=>{AV.g=+el.dataset.g;animDlg()};
ACT.gaclose=()=>{AV.g=null;closeDlg()};
function animDlg(){const g=GM.get(AV.g);if(!g)return;const s=g.source,vi=s.video_info||{},a=animStats(g);
  const rows=g.stickers.map(t=>{const m=t.anim_metrics||{},ms=m.ms||{},ins=(t.anim_report||[]).find(c=>c.name==='inside_frame'),st=cellState(t),mk=mark(t,'anim',g),col=mk?CAT[mk.cat][0]:st==='ok'?'var(--ok)':'var(--mut)';
    return`<tr><td>${t.index}</td><td style="color:${col}">${mk?esc(CAT[mk.cat][1])+(st==='fail'?': '+esc(t.anim_reason||''):''):CELLTXT[st]}</td><td>${m.frames_out||''}</td><td>${m.fps||''}</td><td>${m.kb||''}</td><td>${m.crf||''}</td>
      <td>${m.loop_seam!==undefined?m.loop_seam+' / '+m.loop_limit:''}</td><td>${ins?ins.value+' px'+(ins.data&&ins.data.frames_over?`, ${ins.data.frames_over} frames`:''):''}</td><td>${m.cache==='hit'?'from the cache':ms.finish!==undefined?(ms.finish/1000).toFixed(1)+' s':''}</td></tr>`}).join('');
  const bad=g.stickers.flatMap(t=>(t.anim_report||[]).filter(c=>!c.ok).map(c=>`<div class=chk><i class=cdot style="--cc:${CAT[CATOF[c.name]||'bad'][0]}"></i><span class="${c.severity==='WARN'?'w':'f'}">S${t.index} ${esc(c.name)}</span> <span class=mut>${esc(c.detail||'')}</span></div>`)).join('');
  dlg(`<div class="sheetdlg animdlg"><div class=mrow><h2 style="margin:0">Video sheet & analysis <span class=mut style="font-weight:500">${g.generation_id} · sheet ${s.subject_id}</span></h2><button class=btn data-act=gaclose>✕</button></div>
   <div class=sgrid><div>${videoBox(g,1.4)}${SR.bulk(g)}<div class=mut style="margin-top:8px">Blue dashed lines: where the video is cut into one animation per sticker.</div>${legend(g,'anim')}</div>
    <div class=sside><h3>Source</h3><div class=kv style="margin:6px 0 12px"><span>mode</span><span>${esc(vi.mode||'')}</span>${vi.file?`<span>file</span><span>${esc(vi.file)}</span><span>video</span><span>${esc(vi.size||'')} · ${vi.fps||''} fps · ${vi.duration||''} s · ${esc(vi.codec||'')}</span>`:`<span>clips</span><span>${esc(vi.clip_format||'')} (one transparent clip per sticker)</span>`}
     <span>animated</span><span>${a.done} of ${a.total}</span><span>work this time</span><span>${(a.ms/1000).toFixed(1)} s${a.cached?` · ${a.cached} read back from the cache`:''}</span></div>
     <h3>Every animation</h3><table class=stbl><tr><th>#</th><th>result</th><th>frames</th><th>fps</th><th>KB</th><th>crf</th><th>loop seam / limit</th><th>on the border</th><th>time</th></tr>${rows}</table>
     <h3 style="margin-top:12px">Checks that did not pass</h3>${bad||'<div class=mut>Every check passed.</div>'}</div></div></div>`)}
/* the same sheet, always on the Generate page beside the stickers (Raw / Keyed per batch) */
const SHK=new Map();      // batch number -> the sheet view the person chose: 'keyed' | 'fixed' (raw is the default)
/* the views of a batch's sheet: the generator's raw sheet, the keyed one, and (after a slice was edited and saved) the sheet rebuilt with that slice fixed, same layout so the same S# */
const sheetViews=g=>{const s=g.source,v=[{id:'raw',file:s.sheet_copy,label:'Raw'}];if(s.keyed)v.push({id:'keyed',file:s.keyed,label:'Keyed'});
  if(s.sheet_fixed)v.push({id:'fixed',file:s.sheet_fixed,label:`Fixed (${(s.sheet_fixed_cells||[]).map(i=>'S'+i).join(', ')})`});return v};
const sheetView=g=>{const vs=sheetViews(g);return vs.find(v=>v.id===SHK.get(g.number))||vs[0]};
function sheetPanel(g){const s=g.source,size=s.sheet_size;if(!size||!s.sheet_copy)return'';
  const cur=sheetView(g),keyed=cur.id==='keyed',base=`/out/${g.generation_id}/`,G=s.grid,[W,H]=size;
  const cut=G?`<span class="gcut ${G.method==='gutter'||G.method==='single'?'ok':'warn'}">${G.method==='gutter'?'cut at gutters':'cut: '+esc(G.method)}</span>`:'';
  return`<aside class=gsheet><div class=gshead><b>${g.key_colour==='blue'?'Blue':'Green'} screen</b><span class=gspace></span><div class=tabs>
    ${sheetViews(g).map(v=>`<button class="tab ${v.id===cur.id?'on':''}" data-act=gshk data-g=${g.number} data-k=${v.id}>${esc(v.label)}</button>`).join('')}</div></div>
   <div class="sbox ${keyed?'bg-'+bg:''}"><img src="${base+cur.file}" alt="${esc(cur.label)}"><svg viewBox="0 0 ${W} ${H}">${cutSvg(g,true,true,2)}</svg></div>
   <div class=vchips>${g.stickers.map(t=>chip(g,t,'still')).join('')}</div>
    ${allowAllRow(g,'still')}
   <div class=gsfoot>${cut}<span class=mut>blue = cuts, yellow = sticker edge</span><button class="link" data-act=gsheet data-g=${g.number}>Full analysis</button></div>${legend(g,'still')}${typeof vgenBox==='function'?vgenBox(g):''}</aside>`}
ACT.gshk=el=>{const n=+el.dataset.g;if(el.dataset.k==='raw')SHK.delete(n);else SHK.set(n,el.dataset.k);glast='';tick(true)};
ACT.gsheet=el=>{SV.g=+el.dataset.g;SV.view='raw';SV.lines=true;SV.boxes=true;sheetDlg()};
function sheetDlg(){const g=GM.get(SV.g);if(!g)return;const s=g.source,base=`/out/${g.generation_id}/`,size=s.sheet_size,G=s.grid;if(!size||!s.sheet_copy)return toast('This sheet has not been read yet',1);
  const [W,H]=size,keyedEv=[...g.events].reverse().find(e=>e.stage==='keyed'&&e.status==='done'),kd=(keyedEv&&keyedEv.detail)||{},th=(kd.threshold||[]).slice().sort((a,b)=>a-b);
  const img=SV.view==='keyed'&&s.keyed?base+s.keyed:base+s.sheet_copy;
  const svg=cutSvg(g,SV.lines,SV.boxes);
  const checks=(g.verify.sheet||[]).map(c=>`<div class=chk><span class="${c.ok?'p':(c.severity==='WARN'?'w':'f')}">${c.ok?'✓':c.severity==='WARN'?'!':'✗'} ${esc(c.name)}</span> <span class=mut>${esc(c.detail||'')}</span></div>`).join('');
  const rows=g.stickers.map(t=>{const m=t.metrics||{};return`<tr><td>${t.index}</td><td>${t.status==='READY'?'<span style="color:var(--ok)">ready</span>':`<span style="color:var(--bad)">${esc(t.reason||t.status)}</span>`}</td><td>${m.fg_px!==undefined?m.fg_px:''}</td><td>${m.threshold!==undefined?m.threshold:''}</td><td>${m.scale||''}</td><td>${esc((m.warnings||[]).join(', '))}</td></tr>`}).join('');
  dlg(`<div class=sheetdlg><div class=mrow><h2 style="margin:0">${g.key_colour==='blue'?'Blue':'Green'} screen & cuts <span class=mut style="font-weight:500">${g.generation_id} · sheet ${s.subject_id} · ${W}×${H}</span></h2><button class=btn data-act=gsclose>✕</button></div>
   <div class=gtoolbar><div class=tabs><button class="tab ${SV.view==='raw'?'on':''}" data-act=gsview data-v=raw>Raw sheet</button><button class="tab ${SV.view==='keyed'?'on':''}" data-act=gsview data-v=keyed ${s.keyed?'':'disabled'}>Background removed</button></div>
    <label class=mut><input type=checkbox data-act=gstog data-k=lines ${SV.lines?'checked':''}> Cut lines</label><label class=mut><input type=checkbox data-act=gstog data-k=boxes ${SV.boxes?'checked':''}> Sticker boundaries</label></div>
   <div class=sgrid><div class="sbox ${SV.view==='keyed'?'bg-'+bg:''}"><img src="${img}" alt="Sheet"><svg viewBox="0 0 ${W} ${H}">${svg}</svg></div>
    <div class=sside><h3>Analysis</h3>${checks||'<div class=mut>No sheet checks recorded.</div>'}
     <div class=kv style="margin:10px 0"><span>background sampled</span><span>${kd.bg?`rgb(${kd.bg.join(', ')})`:'?'}</span><span>key threshold</span><span>${th.length?`${th[0]} to ${th[th.length-1]} (per cell)`:'?'}</span><span>cut</span><span>${esc(kd.cut||(G&&G.method)||'?')}${G&&G.method!=='gutter'&&G.method!=='single'?' (a character may cross a cut)':''}</span><span>grid</span><span>${g.grid[0]}×${g.grid[1]}</span></div>
     <table class=stbl><tr><th>#</th><th>result</th><th>subject px</th><th>threshold</th><th>scale</th><th>warnings</th></tr>${rows}</table>
     <div class=mut style="margin-top:8px">Blue dashed lines: where the sheet is cut (in the gaps between characters). Yellow boxes: each sticker's measured boundary.</div>${legend(g,'still')}</div></div></div>`)}
ACT.gsview=el=>{SV.view=el.dataset.v;sheetDlg()};
ACT.gstog=el=>{SV[el.dataset.k]=el.checked;sheetDlg()};
ACT.gsclose=()=>{SV.g=null;closeDlg()};

/* ---------- "Get the Higgsfield prompt": when nothing prepared matches the request */
ACT.ghiggs=async()=>{const p=$('prompt').value.trim();if(!p)return;
  const r=await post('/api/plan',{prompt:p,grid:'3x3',style_id:(typeof LIVE!=='undefined'&&LIVE.style)||'flat_vector',loop:!!(typeof LIVE!=='undefined'&&LIVE.loop),ai:(typeof aiOn==='function'&&aiOn())});if(!r.ok)return toast(r.j.error,1);
  dlg(`<div class=vdlg><h2>Prompt for Higgsfield</h2><div class=mut>Nothing prepared matches “${esc(p)}”. Generate the sheet, name the folder as shown below, and it appears here.</div>
   <h3>Sheet prompt</h3><textarea readonly rows=9 id=hp1>${esc(r.j.sheet_prompt)}</textarea><div class=row><button class="btn sm" data-act=hcopy data-t=hp1>Copy sheet prompt</button></div>
   <h3>Video prompt</h3><textarea readonly rows=5 id=hp2>${esc(r.j.video_prompt)}</textarea><div class=row><button class="btn sm" data-act=hcopy data-t=hp2>Copy video prompt</button></div>
   <div id=hres></div><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button><button class=btn data-act=hgenop>No prepared sheet: generate it</button><button class="btn pri" data-act=hreserve>Reserve the folder names</button></div></div>`)};
ACT.hcopy=async el=>{try{await navigator.clipboard.writeText($(el.dataset.t).value);toast('Copied')}catch(e){toast('Copy failed',1)}};
ACT.hgenop=async()=>{const p=$('prompt').value.trim();if(!p)return;
  const r=await post('/api/jobs',{kind:'sheet',request:{prompt:p,grid:[3,3]}});if(!r.ok)return toast(r.j.error,1);
  const id=r.j.id,t0=Date.now();
  $('hres').innerHTML=`<div class=card style="margin:10px 0">Job <b>${esc(id)}</b> requested — waiting for the generator (<span id=hjela>0s</span>). The operator claims it, calls Higgsfield, and completes it; the sheet then runs through the stills like a prepared one.</div>`;
  const iv=setInterval(async()=>{const g=await api('/api/jobs/'+id),el=$('hjela');if(!g.ok||!el){clearInterval(iv);return}
    el.textContent=Math.round((Date.now()-t0)/1000)+'s · '+g.j.status;
    if(['DONE','FAILED','TIMEOUT'].includes(g.j.status)){clearInterval(iv);
      if(el&&el.parentElement)el.parentElement.innerHTML+=g.j.status==='DONE'?`<div class=mut>Sheet arrived: <code>${esc(g.j.result.file)}</code> (${Math.round(g.j.result.bytes/1024)} KB).</div>`:JR.controls(g.j)}},5000)};
ACT.hreserve=async()=>{const r=await post('/api/tasks',{prompt:$('prompt').value.trim(),grid:'3x3',style_id:(typeof LIVE!=='undefined'&&LIVE.style)||'flat_vector',loop:!!(typeof LIVE!=='undefined'&&LIVE.loop),ai:(typeof aiOn==='function'&&aiOn())});if(!r.ok)return toast(r.j.error,1);
  $('hres').innerHTML=`<div class=card style="margin:10px 0"><b>Create these two folders and name the downloads into them</b><br><code>${esc(r.j.paths.img)}</code><br><code>${esc(r.j.paths.vid)}</code><div class=mut>The sheet goes in <b>${esc(r.j.folders.img)}</b>, the video in <b>${esc(r.j.folders.vid)}</b>. Then press Generate again.</div></div>`};

/* ---------- one sticker, larger */
function gmodal(){if(!MD)return;const g=GM.get(MD.g);if(!g){MD=null;return}const t=g.stickers[MD.i-1],base=`/out/${g.generation_id}/`,ap=animPhase(g),v=t.edited_at||t.rendered_at||0;
  const still=t.png?`<img src="${base+t.png}?e=${v}">`:`<div class=mut style="padding:12px">${esc(t.status)}${t.reason?': '+esc(t.reason):''}</div>`;
  const vid=t.webm&&t.anim_status==='READY'?`<video src="${base+t.webm}" autoplay loop muted playsinline></video>`:`<div class=mut style="padding:12px">${t.anim_status==='NOT_REQUESTED'?'Not animated yet':esc(t.anim_status)+(t.anim_reason?': '+esc(t.anim_reason):'')}</div>`;
  const rows=cs=>(cs||[]).filter(r=>MD.all||!r.ok).map(r=>`<div class=chk><i class=cdot style="--cc:${r.ok?'#22c55e':CAT[CATOF[r.name]||'bad'][0]}"></i><span class="${r.ok?'p':(r.severity==='WARN'?'w':'f')}">${r.ok?'✓':r.severity==='WARN'?'!':'✗'} ${esc(r.name)}</span> <span class=mut>${esc(r.detail||'')}</span></div>`).join('');
  const mk=mark(t,ap?'anim':'still',g),m=t.metrics||{},am=t.anim_metrics||{},
    meas=[['scale',m.scale],['scale mode',m.scale_mode],['key threshold',m.threshold],['still KB',m.kb],['holes',m.holes],['frames',am.frames_out],['fps',am.fps],['animation KB',am.kb],['crf',am.crf],['loop seam',am.loop_seam!==undefined?am.loop_seam+' / '+am.loop_limit:undefined]].filter(x=>x[1]!==undefined&&x[1]!==null&&x[1]!==''),
    off=ap&&t.anim_status==='READY'?['REJECTED','BLOCKED'].includes(t.review.anim):t.review.still==='REJECTED',
    stg=ap?'anim':'still',op=cellOp(g,t,stg),
    act=op.op==='none'?'':`<button class="btn ${['allow','include'].includes(op.op)?'pri':''}" ${cellAct(g,t,stg)}>${cellVerb(op,t)}</button>`,
    allowAct=op.op==='none'&&op.why?`<span class=mut>${esc(op.why)}</span>`:'',
    path=(t.history||[]).slice().reverse().map(h=>`<div class=hrow><span class=mut>${new Date(h.ts*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</span> <b>${esc(h.stage)}</b> ${esc(h.actor)} ${esc(h.decision)}${h.reason?` <span class=mut>· ${esc(h.reason)}</span>`:''}</div>`).join('');
  const bad=(t.report||[]).concat(t.anim_report||[]).some(r=>!r.ok);
  $('modal').innerHTML=`<div class=mbox style="width:min(900px,96vw)"><div class=mrow><button class="btn nav" data-act=gstep data-d=-1>‹</button>
   <div style="flex:1"><b>${esc(t.emoji)} ${esc(t.key.replace(/_/g,' '))}</b><div class=mut>${esc(t.tags.join(' · '))}</div></div>
   <button class=idtag data-act=copyid data-v="${g.generation_id}/S${t.index}" title="${g.generation_id}/S${t.index} · click to copy the id">${g.generation_id}/S${t.index}</button>
   ${t.status==='READY'?`<button class=btn data-act=gedit title="${t.anim_status==='READY'?'Text, emoji and trim over the animation; one Save updates the image and the animation':'Add text or emoji'}">${ic('edit')} Edit${t.anim_status==='READY'?' (image + animation)':''}</button>`:''}<button class="btn nav" data-act=gstep data-d=1>›</button><button class=btn data-act=gmclose>✕</button></div>
   ${mk?`<div style="margin:6px 0 2px">${mk.issues.map(i=>`<div class=giss style="--cc:${CAT[i.cat][0]}"><i></i>${esc(CAT[i.cat][1])}: ${esc(i.text)}</div>`).join('')}</div>`:''}
   <div class=mpanes><div class=pane><div class=mut>Sticker</div><div class="box bg-${bg}">${still}</div></div><div class=pane><div class=mut>Animation</div><div class="box bg-${bg}">${vid}</div></div></div>
   ${typeof edgeControlsHtml==='function'&&t.status==='READY'?`<div class="lv-edge lv-edge-m"><b>Edge</b>${edgeControlsHtml()}</div>`:''}
   ${act||allowAct?`<div class=row style="margin:8px 0 2px">${act}${allowAct}</div>`:''}
   <details ${bad?'open':''}><summary class=mut>What Python checked</summary>${rows(t.report)}${rows(t.anim_report)||''}${(rows(t.report)||rows(t.anim_report))?'':`<div class=mut>${(t.report||[]).length||(t.anim_report||[]).length?'Every check passed.':'nothing yet'}</div>`}
    <button class=link data-act=gmall>${MD.all?'Show only problems':'Show every check'}</button></details>
   <details><summary class=mut>Path (every decision, newest first)</summary>${path||'<div class=mut>no decisions yet</div>'}</details>
   ${meas.length?`<details><summary class=mut>Measurements</summary><div class="kv vkv">${meas.map(x=>`<span>${x[0]}</span><span>${esc(String(x[1]))}</span>`).join('')}</div></details>`:''}
   <div class=mut style="margin-top:8px">${esc(t.prompt)}</div><div class=mut>← → to browse, Esc to close</div></div>`;
  $('modal').classList.add('on');$('modal').onclick=e=>{if(e.target.id==='modal')ACT.gmclose()};if(typeof egSync==='function'){egSync();applyEdgePreview()}}
ACT.gmall=()=>{MD.all=!MD.all;gmodal()};
ACT.gopen=el=>{MD={g:+el.dataset.g,i:+el.dataset.i,all:!!(MD&&MD.all)};if(typeof egPick==='function')egPick(MD.g,MD.i);gmodal()};
ACT.gmclose=()=>{MD=null;$('modal').classList.remove('on')};
ACT.gstep=el=>{if(!MD)return;const g=GM.get(MD.g),n=g.stickers.length;MD.i=((MD.i-1+(+el.dataset.d)+n)%n)+1;gmodal()};
ACT.gedit=()=>{const g=GM.get(MD.g),t=g.stickers[MD.i-1];ACT.gmclose();return studioEditSticker(g.number,t.index);Ed.openImage(`/out/${g.generation_id}/${t.png}?e=${t.edited_at||0}`,{back:{gen:g.number,index:t.index},outlined:g.outline_px>0,name:t.name,emoji:t.emoji})};
document.addEventListener('keydown',e=>{if(!MD)return;if(e.key==='Escape')ACT.gmclose();if(e.key==='ArrowRight')ACT.gstep({dataset:{d:1}});if(e.key==='ArrowLeft')ACT.gstep({dataset:{d:-1}})});
/* the sheet's cells are SVG rects: Enter or Space on a focused one presses it like a click (a rect answers neither key by itself) */
document.addEventListener('keydown',e=>{const t=e.target;if((e.key==='Enter'||e.key===' ')&&t&&t.dataset&&t.dataset.act&&String(t.tagName||'').toLowerCase()==='rect'){e.preventDefault();const f=ACT[t.dataset.act];if(f)f(t,e)}});

/* animations made before the border check existed have no verdict: judge them once (the server decodes the source cells, no re-encode) */
const RECHK=new Set();
function autoRecheck(g){if(RECHK.has(g.number)||processing(g)||making(g))return;
  const old=t=>t.anim_status==='READY'&&!t.bounds_checked&&!(t.anim_report||[]).some(c=>c.name==='inside_frame'||c.name==='inside_slot')&&(((t.anim_metrics||{}).source||'')==='3x3 mp4'||String((t.anim_metrics||{}).source||'').startsWith('clip:'));
  if(!g.stickers.some(old))return;RECHK.add(g.number);
  post(`/api/generations/${g.number}/recheck`).then(r=>{if(!r.ok&&r.status===409){RECHK.delete(g.number);return}
    if(r.ok&&r.j.flagged.length)toast(`${g.generation_id}: ${r.j.flagged.map(i=>'S'+i).join(', ')} leave${r.j.flagged.length===1?'s':''} the cell and ${r.j.flagged.length===1?'is':'are'} now blocked (checked now, these were made before the check existed)`,1);
    glast='';tick(true)})}

/* ---------- Edit a sticker from the Studio, a pack or the library
   A sticker WITH an animation is edited as layers (text, emoji, stickers, with timing) over its ORIGINAL animation in the video editor; Save to sticker
   exports the layers to the animation AND the image together, and the pack copies follow. A sticker without one is edited in the image editor.
   The edit lives in the Studio (a project); the generator's files stay in source/orig. */
async function studioEditAnim(gnum,index){const r=await postWait(`/api/generations/${gnum}/studio_edit`,{index,action:'open'},'Waiting for the previous step…');if(!r.ok)return toast(r.j.error,1);
  P.studio={gen:gnum,index,project:r.j.project};P.packEdit=null;location.hash='#/prepare/'+r.j.project}
async function studioEditSticker(gnum,index,to){const r=await api('/api/generations/'+gnum);if(!r.ok)return toast('That batch is not available any more',1);const g=r.j,t=g.stickers[index-1],anim=t.anim_status==='READY'&&t.webm;
  if(to!=='agent'&&!SES.gens.includes(g.number)){SES={prompt:g.prompt||'',gens:[g.number],off:[],pack:''};saveSes()}GS.tab=anim?'anim':'stickers';          /* opened from the AI: the Studio's session is left alone */
  if(anim)return studioEditAnim(g.number,index);
  Ed.openImage(`/out/${g.generation_id}/${t.png}?e=${t.edited_at||0}`,{back:{gen:g.number,index,to},outlined:g.outline_px>0,name:t.name,emoji:t.emoji})}
/* send a created sticker back to the Studio: its batch, on the right view */
ACT.openstudio=async el=>{const gid=+String(el.dataset.gen||'').replace(/\D/g,'');const r=await api('/api/generations/'+gid);if(!r.ok)return toast('That batch is not available any more',1);
  const t=r.j.stickers[+el.dataset.i-1];SES={prompt:r.j.prompt||'',gens:[gid],off:[],pack:''};saveSes();GS.tab=el.dataset.view||(t&&t.anim_status==='READY'?'anim':'stickers');glast='';location.hash='#/studio'};
ACT.lcstudioedit=el=>{const s=LCL[LCI];lcClose();studioEditSticker(+String(s.source.generation).replace(/\D/g,''),s.source.index)};
ACT.lcopenstudio=()=>{const s=LCL[LCI];lcClose();ACT.openstudio({dataset:{gen:s.source.generation,i:s.source.index}})};

/* ---------- polling: only while this screen is open */
async function tick(force){try{
  if(route_!=='generate'&&!MD&&VG===null&&SV.g===null)return;
  const h=await api('/api/generations');if(h.ok)GHEALTH=h.j.health;GSTALE=!!(h.ok&&h.j.stale);
  const hh=$('ghealth');if(hh)hh.innerHTML=(GSTALE?'<div class=warn><b>This server is running older code than the files on disk.</b> New buttons may say “not found” and fixes will not apply until you restart it: press Ctrl+C in its terminal, then run <code>python -m mirsal serve</code> from the <code>mirsal</code> folder.</div>':'')+(GHEALTH&&GHEALTH.vp9===false?'<div class=warn>This ffmpeg cannot encode VP9, so animations will fail. Run <code>python -m mirsal doctor</code>.</div>':'');
  let key='';for(const id of SES.gens){const r=await api('/api/generations/'+id);if(r.ok){GM.set(id,r.j);key+=JSON.stringify(r.j);autoRecheck(r.j)}else if(r.status===404){SES.gens=SES.gens.filter(x=>x!==id);saveSes()}}
  for(const id of [...ANIM]){const g=GM.get(id);if(g&&animPhase(g)&&!processing(g))ANIM.delete(id)}
  key+=bg+SES.off.join()+SES.pack+[...ANIM].join()+(LIB.packs||[]).length+JSON.stringify(GD);
  const typing=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.pd!==undefined;
  if(force||(key!==glast&&!typing)){glast=key;const el=$('gres');if(el)el.innerHTML=gview();gdPrice();if(MD)gmodal();drawVdlg();if(SV.g!==null&&document.querySelector('.sheetdlg'))sheetDlg();if(typeof applyEdgePreview==='function')applyEdgePreview();if(typeof hxSync==='function')hxSync()}
}catch(e){const m=$('msg');if(m)m.textContent='Something went wrong: '+e.message}}
setInterval(tick,700);loadLib();

const layoutOfCell=(g,i)=>{const v=sheetOf(g),lay=v&&LAY.get(g.number+v.id);const sl=lay&&lay.slots.find(x=>x.slot===i);return sl?sl.rect:null};
/* "Use it anyway" / "Take it back": POST .../allow {kind, index, allow}. An animation (the default kind) is cut again from the stored video, a still from the stored sheet: free, a few seconds. */
async function allowCall(g,t,kind,allow){const r=await postWait(`/api/generations/${g.number}/allow`,{kind,index:t.index,allow},'Finishing the previous step…');
  if(!r.ok)return toast(r.j.error||'Could not change it',1);
  toast(allow?`S${t.index} is used anyway: cutting its ${kind==='still'?'picture':'animation'} again…`:`S${t.index}: the permission is taken back`);glast='';if(typeof tick==='function')tick(true)}
/* a human decision on a sticker or animation that is made: drop it from the set, or include it / bring it back. Never deletes. POST .../drop {index, dropped} */
async function dropCall(g,t,drop){const r=await postWait(`/api/generations/${g.number}/drop`,{index:t.index,dropped:drop});if(!r.ok)toast(r.j.error,1);
  else if(!drop&&isOob(t))toast(`S${t.index} is included anyway: it will be added with the rest (the marker stays)`);glast='';await tick(true);if(MD)gmodal()}
/* the one handler of every control on a cell */
function cellRun(g,t,stage){const o=cellOp(g,t,stage);
  if(o.op==='allow'||o.op==='unallow')return allowCall(g,t,o.kind,o.op==='allow');
  if(o.op==='include'||o.op==='drop')return dropCall(g,t,o.op==='drop');
  toast(o.why||'Nothing to change here.')}
ACT.gcell=el=>{const g=GM.get(+el.dataset.g),t=g&&g.stickers[+el.dataset.i-1];if(g&&t)return cellRun(g,t,el.dataset.stage==='anim'?'anim':'still')};

/* one bulk control per batch, per kind, above the grid: "Use all anyway (N)" / "Take all back (N)", where N counts what is allow-able NOW, never everything.
   Stills live under the green-screen panel, animations under the video sheet. */
const ALWBUSY=new Set();     // "<batch number>:<kind>" while a bulk allow / take-back is on its way: the buttons wait instead of answering a second click with a "busy" 409
const alwBusy=(g,kind)=>ALWBUSY.has(g.number+':'+kind)||(kind!=='still'&&processing(g));
function allowAllRow(g,kind){const A=ALW(g,kind),a=A.can.length,b=A.undo.length,what=kind==='still'?'sticker':'animation';if(!a&&!b)return'';
  const bz=alwBusy(g,kind),lock=bz?' disabled aria-busy=true':'';
  return`<div class=lv-allow>${a?`<button class="btn sm pri" data-act=gallowall data-g=${g.number} data-kind=${kind} data-allow=1${lock} title="Use every ${what} anyway that Python blocked as a judgement call">${bz?'Cutting again…':`Use all anyway (${a})`}</button>`:''}
   ${b?`<button class="btn sm" data-act=gallowall data-g=${g.number} data-kind=${kind} data-allow=0${lock} title="Block the ${what}s you allowed again">${bz?'Cutting again…':`Take all back (${b})`}</button>`:''}<span class=mut>or click a cell on the sheet</span></div>`}
ACT.gallowall=async el=>{const g=GM.get(+el.dataset.g);if(!g)return;const allow=el.dataset.allow==='1',kind=el.dataset.kind==='still'?'still':'animation',key=g.number+':'+kind;
  if(ALWBUSY.has(key)||el.disabled)return;ALWBUSY.add(key);
  const row=el.closest('.lv-allow');if(row)row.querySelectorAll('button[data-act=gallowall]').forEach(b=>{b.disabled=true;b.setAttribute('aria-busy','true');b.textContent='Cutting again…'});
  try{const r=await postWait(`/api/generations/${g.number}/allow`,{all:true,allow,kind},'Finishing the previous step…');
    if(!r.ok)return toast(r.j.error||'Could not change it',1);
    toast(allow?`Allowed ${r.j.indexes.length}: cutting their ${kind==='still'?'pictures':'animations'}…`:`Took back ${r.j.indexes.length}`);}
  finally{ALWBUSY.delete(key);glast='';if(typeof tick==='function')tick(true)}};
