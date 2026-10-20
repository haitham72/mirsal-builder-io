/* Users: the people of this Mirsal and what each one made and spent (docs/api.md "Users", docs/design.md §5 Users). The owner and admins get the roster in the second column
   (filters by status and role) and, on the stage, the totals or one person: identity, credits, the 30-day spend and batches, jobs that worked or failed with cost against the
   estimate, the ledger, storage, and their batches by family with prompts and media. People management (add, approve, roles, passwords, credits) lives here, moved from Settings.
   A member opening Users sees only "My usage" (GET /api/users/me): the server never answers anyone else's page to them. The graphs are hand-drawn SVG on the shared tokens (no library).
   UV holds the pure builders (node tests: tests/js/users.test.js); names start with US / UV / us so no other script's top-level name is shadowed. */
const UV=(()=>{
  const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>Math.round((+v||0)*100)/100;
  const bytes=b=>{b=+b||0;const u=['B','KB','MB','GB','TB'];let i=0;while(b>=1024&&i<u.length-1){b/=1024;i++}return`${i?(b<10?b.toFixed(1).replace(/\.0$/,''):Math.round(b)):b} ${u[i]}`};
  const when=ts=>ts?new Date(ts*1000).toLocaleDateString(undefined,{day:'numeric',month:'short',year:'numeric'}):'never';
  /* one bar per day; the tallest is the full height; a day with nothing is a 1px hairline so the axis reads */
  const bars=(values,days,label,cls)=>{const v=(values||[]).map(x=>+x||0),max=Math.max(1e-9,...v),w=300,h=64,n=v.length||1,bw=w/n;
    return`<figure class="us-chart ${cls||''}"><figcaption>${esc(label)}</figcaption><svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" role=img aria-label="${esc(label)}">${v.map((x,i)=>{const bh=x?Math.max(2,x/max*(h-4)):1;
      return`<rect x="${(i*bw+bw*0.15).toFixed(2)}" y="${(h-bh).toFixed(2)}" width="${(bw*0.7).toFixed(2)}" height="${bh.toFixed(2)}" rx="1.5"><title>${esc((days||[])[i]||'')}: ${num(x)}</title></rect>`}).join('')}</svg>
      <div class=us-axis><span>${esc(((days||[])[0]||'').slice(5))}</span><span>${esc(((days||[]).slice(-1)[0]||'').slice(5))}</span></div></figure>`};
  /* worked vs failed jobs as one split bar */
  const split=(ok,bad)=>{ok=+ok||0;bad=+bad||0;const t=ok+bad;return`<div class=us-split title="${ok} worked, ${bad} failed"><i style="width:${t?ok/t*100:0}%"></i><b style="width:${t?bad/t*100:0}%"></b></div>
    <div class=us-legend><span class=ok>${ok} worked</span><span class=bad>${bad} failed</span></div>`};
  const STATUS={pending:'Waiting',active:'Active',rejected:'Rejected',disabled:'Disabled'};
  const roster=(users,f,sel)=>{f=f||{};const rows=(users||[]).filter(u=>(!f.status||(u.status||'active')===f.status)&&(!f.role||u.role===f.role));
    return rows.length?rows.map(u=>`<button class="us-row${sel===u.id?' on':''}" data-act=usopen data-id="${esc(u.id)}"><span class=us-av>${esc((u.name||u.email||'?').trim().slice(0,1).toUpperCase())}</span>
      <span class=us-rmeta><b>${esc(u.name||u.email||u.id)}</b><small>${esc(u.role||'')} · ${esc(STATUS[u.status]||u.status||'Active')} · ${num(u.spent)} cr spent · ${u.batches||0} batches</small></span></button>`).join('')
      :'<div class=mut style="padding:12px">Nobody matches these filters.</div>'};
  const filters=f=>{f=f||{};const opt=(k,v,l)=>`<button class="chip2${(f[k]||'')===v?' on':''}" data-act=usfilter data-k=${k} data-v="${v}">${l}</button>`;
    return`<div class=us-filters>${opt('status','','All')}${opt('status','active','Active')}${opt('status','pending','Waiting')}${opt('status','disabled','Disabled')}</div>
      <div class=us-filters>${opt('role','','Any role')}${opt('role','owner','Owner')}${opt('role','admin','Admin')}${opt('role','member','Member')}</div>`};
  const stat=(v,l)=>`<div class=us-stat><b>${v}</b><small>${esc(l)}</small></div>`;
  const totals=t=>{t=t||{};const s=t.series||{};return`<div class=us-stats>${stat(t.batches||0,'batches')}${stat(t.stickers||0,'stickers')}${stat(num(t.spent),'credits spent')}${stat(bytes(t.bytes),'on disk')}</div>
    <div class=us-charts>${bars(s.spend,s.days,'Credits spent per day, last 30 days')}${bars(s.batches,s.days,'Batches made per day','alt')}</div><div class=card style="margin-top:12px"><h2>Jobs</h2>${split(t.jobs_ok,t.jobs_failed)}</div>`};
  const job=j=>{const over=j.cost!=null&&j.estimate!=null&&+j.cost>+j.estimate;return`<tr><td>${esc(j.id)}</td><td>${esc(j.kind)}</td><td class="st-${esc(String(j.status||'').toLowerCase())}">${esc(j.status)}</td>
    <td>${esc(j.label||j.generation||'')}</td><td class=num>${j.estimate==null?'–':num(j.estimate)}</td><td class="num${over?' over':''}">${j.cost==null?'–':num(j.cost)}</td><td>${when(j.created)}</td></tr>`};
  const batch=b=>`<div class=us-batch><div class=us-bh><b>${esc(b.id)}</b><small>${when(b.created)} · ${esc(b.stage||'')}${b.kind&&b.kind!=='stickers'?' · '+esc(b.kind):''}</small></div>
    <div class=us-prompt>${esc(b.prompt||'')}</div>
    ${b.sheet_prompt||b.video_prompt?`<details><summary>Prompts</summary>${b.sheet_prompt?`<p><small>Sheet</small><br>${esc(b.sheet_prompt)}</p>`:''}${b.video_prompt?`<p><small>Video</small><br>${esc(b.video_prompt)}</p>`:''}</details>`:''}
    <div class=us-media>${(b.stickers||[]).filter(s=>s.png).slice(0,9).map(s=>`<a class=us-th href="${esc(s.webm||s.png)}" target=_blank rel=noopener title="S${s.index}${s.webm?' · animated':''}"><img src="${esc(s.png)}" loading=lazy alt="">${s.webm?'<i>▶</i>':''}</a>`).join('')||'<span class=mut>no picture yet</span>'}</div></div>`;
  /* one person's page; `staff` adds the management row (AUV.person's buttons, auth.js) */
  const page=(d,staff,manage)=>{d=d||{};const u=d.user||{},s=d.summary||{},se=d.series||{};
    return`<div class=page><div class=ph><h1>${staff?esc(u.name||u.email||u.id):'My usage'}</h1><span class=mut>${esc(u.email||'')}${u.role?' · '+esc(u.role):''}</span></div>
      ${manage||''}
      <div class=us-stats>${stat(u.credits_left==null?'–':num(u.credits_left),'credits left')}${stat(num(s.spent),'credits spent')}${stat(s.batches||0,'batches')}${stat(s.stickers||0,'stickers')}${stat(s.animated||0,'animated')}${stat(bytes(s.bytes),'on disk')}</div>
      <div class=us-charts>${bars(se.spend,se.days,'Credits spent per day, last 30 days')}${bars(se.batches,se.days,'Batches made per day','alt')}</div>
      <div class=card style="margin-top:12px"><h2>Jobs</h2>${split(s.jobs_ok,s.jobs_failed)}
        ${(d.jobs||[]).length?`<div class=us-tbl><table><thead><tr><th>Job</th><th>Kind</th><th>Status</th><th>For</th><th class=num>Estimate</th><th class=num>Cost</th><th>When</th></tr></thead><tbody>${d.jobs.map(job).join('')}</tbody></table></div>`:'<div class=mut>No paid jobs yet.</div>'}</div>
      ${(d.ledger||[]).length?`<details class=card style="margin-top:12px"><summary><b>Ledger</b> <small>${d.ledger.length} paid call${d.ledger.length===1?'':'s'}</small></summary><div class=us-tbl><table><tbody>${d.ledger.map(l=>`<tr><td>${when(l.ts)}</td><td>${esc(l.kind)}</td><td>${esc(l.model)}</td><td>${esc(l.job)}</td><td>${esc(l.status)}</td><td class=num>${l.cost==null?'–':num(l.cost)}</td></tr>`).join('')}</tbody></table></div></details>`:''}
      <h2 style="margin:20px 0 8px">Their work</h2>${(d.families||[]).length?d.families.map(f=>`<div class="card us-fam"><div class=us-fh>Family of <b>${esc(f.root)}</b> <small>${f.batches.length} batch${f.batches.length===1?'':'es'}</small></div>${f.batches.map(batch).join('')}</div>`).join(''):'<div class=mut>No batches yet.</div>'}</div>`};
  return {esc,bytes,bars,split,roster,filters,totals,page,num};
})();
if(typeof globalThis!=='undefined')globalThis.UV=UV;

if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
  const US={over:null,f:{},sel:null};
  const usStaff=()=>typeof AUV==='undefined'||AUV.staff(typeof ME==='undefined'?null:ME);
  async function usLoad(){const r=await api('/api/users/overview');US.over=r.ok?r.j:{users:[],totals:{},error:r.j.error};return US.over}
  globalThis.usCol=async function(){const el=$('col2');if(!usStaff()){el.innerHTML=`<div class=c2h><h1>Users</h1></div><div class=us-roster><button class="us-row on"><span class=us-av>${UV.esc(((typeof ME!=='undefined'&&ME&&ME.name)||'M').slice(0,1).toUpperCase())}</span><span class=us-rmeta><b>My usage</b><small>what you made and spent</small></span></button></div>`;return}
    if(!US.over)await usLoad();el.innerHTML=`<div class=c2h><h1>Users</h1><button class=iconbtn data-act=usall title="Everyone: the totals">${ic('chart')}</button></div>${UV.filters(US.f)}<div class=us-roster>${UV.roster(US.over.users,US.f,US.sel)}</div>`};
  async function usManage(uid){const r=await api('/api/people');if(!r.ok)return'';const p=(r.j.people||[]).find(x=>x.id===uid);const reqs=(r.j.requests||[]).filter(x=>x.user===uid);
    return p?`<div class="card us-manage">${AUV.requests(reqs)}${AUV.person(p)}</div>`:''}
  RENDER.users=async arg=>{const st=$('s-users');
    if(!usStaff()){const r=await api('/api/users/me');st.innerHTML=r.ok?UV.page(r.j,false):`<div class=page><div class=mut>${UV.esc(r.j.error||'')}</div></div>`;return}
    US.sel=arg||null;await usLoad();usCol();
    if(!US.sel){const pr=await api('/api/people');st.innerHTML=`<div class=page><div class=ph><h1>Users</h1><span class=mut>${(US.over.users||[]).length} people</span></div>${UV.totals(US.over.totals)}
      <div class=card style="margin-top:16px"><h2>People</h2><div id=au-people>${pr.ok?AUV.people(pr.j.people,pr.j.requests,pr.j.recent):UV.esc(pr.j.error||'')}</div></div></div>`;return}
    const r=await api('/api/users/'+encodeURIComponent(US.sel));st.innerHTML=r.ok?UV.page(r.j,true,await usManage(US.sel)):`<div class=page><div class=mut>${UV.esc(r.j.error||'Not found')}</div></div>`};
  ACT.usopen=el=>{location.hash='#users/'+el.dataset.id};
  ACT.usall=()=>{location.hash='#users'};
  ACT.usfilter=el=>{US.f[el.dataset.k]=el.dataset.v;usCol()};
}
