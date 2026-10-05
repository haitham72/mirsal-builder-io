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
 async function result(r){if(!r.ok){toast(r.j.error||'Import failed',1);return}const j=r.j;
  if(j.duplicate&&j.recoverable&&j.import){dlg(`<h2>This import needs recovery</h2><p>Retry processing the saved batch. No provider job is created.</p><button class=btn data-act=impretry>Retry import</button><button class=btn data-act=dlgx>Close</button>`);return}
  closeDlg();const gid=j.id||+(String(j.generation||'').replace(/^G/i,''));
  if(gid){SES={prompt:IMP.options&&IMP.options.prompt||'',gens:[+gid],off:[],pack:''};saveSes();glast='';GS.tab=j.kind==='video'?'anim':'stickers';location.hash='#/studio';if(route_==='generate')await tick(true);toast(j.duplicate?'Opened the existing batch':'Imported; processing the file');return}
  if(j.effect){location.hash='#/effects/'+j.effect;return}
  toast(j.job?`Already in Queue: ${j.job}${j.recoverable?' (still processing or needs recovery)':''}`:j.task?`Already in the Inbox: task ${j.task}`:'This file is already imported')}
 async function send(retry=false){if(IMP.busy)return;IMP.busy=true;try{const o={...IMP.options,retry};let r;
  if(IMP.job)r=await post('/api/higgsfield/import',{id:IMP.job,...o});
  else{const q=new URLSearchParams();Object.entries({...o,name:IMP.file.name}).forEach(([k,v])=>{if(v!==undefined&&v!=='')q.set(k,String(v))});r=await api('/api/import?'+q,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:IMP.file})}
  await result(r)}finally{IMP.busy=false}}
 ACT.impopen=()=>{IMP={file:null,job:null,options:null,busy:false};dlg(`<h2>Import a sheet or video</h2><p class=mut>A sheet becomes a Studio batch. A video needs an approved video sheet. This is free.</p><input id=imp-file type=file accept=".png,.jpg,.jpeg,.webp,.mp4,.mov,.webm">${form()}<div class=row><button class="btn pri" data-act=impupload>Import</button><button class=btn data-act=dlgx>Cancel</button></div>`)};
 ACT.impupload=()=>{const f=$('imp-file').files[0];if(!f)return toast('Choose a file first',1);IMP.file=f;IMP.options=options();send()};
 ACT.impretry=()=>send(true);
 ACT.imphistory=async()=>{IMP={file:null,job:null,options:null,busy:false};dlg('<h2>Higgsfield history</h2><p>Loading completed jobs…</p>');const r=await api('/api/higgsfield/history');if(!r.ok)return dlg(`<h2>Higgsfield history</h2><p>${esc(r.j.error||'Could not load history')}</p><button class=btn data-act=dlgx>Close</button>`);dlg(`<h2>Higgsfield history</h2><p class=mut>Importing downloads an existing result. No credits are spent.</p>${form()}${IMPV.rows(r.j.jobs)}<button class=btn data-act=dlgx>Close</button>`)};
 ACT.imphf=el=>{IMP.job=el.dataset.id;IMP.options=options();send()};
}
