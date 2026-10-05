/* Free sheet/video uploads and Higgsfield history. Processing stays in flow/imports.py. */
'use strict';
const IMPV=(()=>{
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const rows=jobs=>jobs.map(j=>`<div class=row><span><b>${esc(j.kind)}</b> · ${esc(j.model||'')}<br><small>${esc(j.prompt||j.id)}</small></span><button class=btn data-act=imphf data-id="${esc(j.id)}" ${j.known||j.status==='completed'?'':'disabled'}>${j.known?'Open existing':'Import'}</button></div>`).join('')||'<p class=mut>No jobs found.</p>';
 return {rows};
})();
if(typeof globalThis!=='undefined')globalThis.IMPV=IMPV;
if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
 let IMP={file:null,job:null,options:null,busy:false};
 const owner=()=>typeof ME==='undefined'||!ME||ME.role==='owner';
 globalThis.impButtons=()=>owner()?'<button class="btn sm" data-act=impopen>Use my own sheet</button><button class="btn sm" data-act=imphistory>Import from Higgsfield</button>':'';
 const options=()=>({prompt:($('imp-prompt')||{}).value||'',generation:($('imp-generation')||{}).value||undefined,sheet:($('imp-sheet')||{}).value||undefined});
 const form=()=>`<div class=fld><label>Description (optional)</label><input id=imp-prompt maxlength=2000 value="${esc(($('prompt')||{}).value||'')}"></div><div class=fld><label>Destination batch for a video</label><input id=imp-generation placeholder="G104" value="${SES.gens.length?'G'+String(SES.gens[0]).padStart(3,'0'):''}"></div><div class=fld><label>Video sheet (optional)</label><input id=imp-sheet placeholder="First approved sheet"></div>`;
  async function result(r){if(!r.ok){if(r.j&&r.j.candidates&&r.j.candidates.length>1){chooseDlg(r.j.candidates);return}toast(r.j.error||'Import failed',1);return}const j=r.j;
  if(j.duplicate&&j.recoverable&&j.import){dlg(`<h2>This import needs recovery</h2><p>Retry processing the saved batch. No provider job is created.</p><button class=btn data-act=impretry>Retry import</button><button class=btn data-act=dlgx>Close</button>`);return}
  closeDlg();const gid=j.id||+(String(j.generation||'').replace(/^G/i,''));
  if(gid){SES={prompt:IMP.options&&IMP.options.prompt||'',gens:[+gid],off:[],pack:''};saveSes();glast='';GS.tab=j.kind==='video'?'anim':'stickers';location.hash='#/studio';if(route_==='generate')await tick(true);toast(j.recovered?`Recovered ${j.job||''}: linked to the failed job, no second charge`:(j.duplicate?'Opened the existing batch':'Imported; processing the file'));return}
  if(j.effect){location.hash='#/effects/'+j.effect;return}
  toast(j.job?`Already in Queue: ${j.job}${j.recoverable?' (still processing or needs recovery)':''}`:j.task?`Already in the Inbox: task ${j.task}`:'This file is already imported')}
  async function send(retry=false){if(IMP.busy)return;IMP.busy=true;try{const o={...IMP.options,retry};let r;
  if(IMP.localJob){if(IMP.job)o.local_job=IMP.localJob}
  if(IMP.job)r=await post('/api/higgsfield/import',{id:IMP.job,...o});
  else{const q=new URLSearchParams();Object.entries({...o,name:IMP.file.name}).forEach(([k,v])=>{if(v!==undefined&&v!=='')q.set(k,String(v))});if(IMP.localJob)q.set('job',IMP.localJob);if(IMP.asNew)q.set('as_new','1');r=await api('/api/import?'+q,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:IMP.file})}
  await result(r)}finally{IMP.busy=false}}
  const TICKET_RX=/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  const chooseDlg=(cs,preview)=>dlg(`<h2>Is this the result of …?</h2><p class=mut>This file names a provider job that matches ${cs.length} of your failed jobs. Pick the one it completes (no second charge), or import it as a new batch.</p>${cs.map(c=>`<button class=row data-act=impchoose data-j="${esc(c.job)}" style="width:100%;text-align:left;gap:10px">${c.thumb?`<img src="${esc(c.thumb)}" style="width:72px;height:72px;object-fit:cover" alt="">`:preview?`<img src="${esc(preview)}" style="width:72px;height:72px;object-fit:cover" alt="">`:''}<span><b>${esc(c.job)} · ${esc(c.kind||'')}</b><br><small>${esc(c.prompt||'no description')}${c.at?' · '+new Date(c.at*1000).toLocaleString():''}${c.generation?' · '+esc(c.generation):''}</small></span></button>`).join('')}<div class=row><button class=btn data-act=impnew>Import as a new batch</button><button class=btn data-act=dlgx>Cancel</button></div>`);
  ACT.impopen=()=>{IMP={file:null,job:null,options:null,busy:false,localJob:null,asNew:false};dlg(`<h2>Import a sheet or video</h2><p class=mut>A sheet becomes a Studio batch. A video needs an approved video sheet. This is free.</p><input id=imp-file type=file accept=".png,.jpg,.jpeg,.webp,.mp4,.mov,.webm">${form()}<div class=row><button class="btn pri" data-act=impupload>Import</button><button class=btn data-act=dlgx>Cancel</button></div>`)};
  ACT.impupload=async()=>{const f=$('imp-file').files[0];if(!f)return toast('Choose a file first',1);IMP.file=f;IMP.options=options();IMP.localJob=null;IMP.asNew=false;
    const m=(f.name||'').match(TICKET_RX);
    if(m&&!IMP.options.generation&&!IMP.options.sheet){const r=await api('/api/imports/candidates?ticket='+encodeURIComponent(m[0].toLowerCase()));const cs=r.ok?(r.j.candidates||[]):[];
      if(cs.length>1){chooseDlg(cs);return}}
    send()};
  ACT.impchoose=el=>{IMP.localJob=el.dataset.j;send()};
  ACT.impnew=()=>{IMP.asNew=true;IMP.localJob=null;send()};
 ACT.impretry=()=>send(true);
   ACT.imphistory=async()=>{IMP={file:null,job:null,options:null,busy:false,localJob:null,asNew:false};dlg('<h2>Higgsfield history</h2><p>Loading completed jobs…</p>');const r=await api('/api/higgsfield/history');if(!r.ok)return dlg(`<h2>Higgsfield history</h2><p>${esc(r.j.error||'Could not load history')}</p><button class=btn data-act=dlgx>Close</button>`);dlg(`<h2>Higgsfield history</h2><p class=mut>Importing downloads an existing result. No credits are spent.</p>${form()}${IMPV.rows(r.j.jobs)}<button class=btn data-act=dlgx>Close</button>`)};
 ACT.imphf=el=>{IMP.job=el.dataset.id;IMP.options=options();send()};
}
