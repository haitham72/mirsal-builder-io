/* Tickets (docs/tickets_plan.md): Settings > Tickets lists every report and every failure the server caught (GET /api/tickets), each with what happened,
   what the person meant, the AI's summary and proposed fix, and 2-4 small questions answered with one click (POST /api/tickets/{id}/answer). Report (any
   screen: data-act=tkreport data-k=<kind> data-id=<id>) opens one dialog and POSTs /api/tickets. Questions never block anything. Top-level names start
   with TK / tk (the console scripts share one global scope); TKV holds the pure builders for node. */
'use strict';
const TKV=(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const when=t=>t?new Date(t*1000).toLocaleString():'';
  const ISSUE={wrong_result:'Wrong result',crash:'Crash',stuck_job:'Stuck or failed job',duplicate:'Duplicate',ui:'Screen',slow:'Slow',spend:'Credits',other:'Other'};
  const STATUS={open:'Open',answered:'Answered',fixed:'Fixed',wont_fix:'Won’t fix'};
  const SRC={report:'reported',crash:'server error',job:'failed job',telegram:'Telegram'};
  const row=(t,open)=>`<div class="tk-row${open?' on':''}" data-tk=${esc(t.id)}><button class=tk-head data-act=tkopen data-id=${esc(t.id)} aria-expanded=${!!open}>
      <b>${esc(t.id)}</b><span class="tk-st ${esc(t.status)}">${esc(STATUS[t.status]||t.status)}</span><span>${esc(ISSUE[t.issue]||t.issue)}</span>
      <span class=mut>${esc(t.summary||'')}</span><small class=mut>${esc(SRC[t.source]||t.source)}${t.count>1?` · ${t.count} times`:''} · ${esc(when(t.last_at||t.at))}${t.open_questions?` · ${t.open_questions} question${t.open_questions===1?'':'s'}`:''}</small></button></div>`;
  const detail=(t,owner)=>{const ans=q=>(t.answers||[]).find(a=>a.question===q);
    return `<div class=tk-det>
      ${t.intent?`<div><b>You said</b><div>${esc(t.intent)}</div></div>`:''}
      <div><b>What happened</b><div class=mut>${esc(t.what_happened||'')}</div></div>
      ${t.proposed_fix?`<div><b>Proposed fix</b><div>${esc(t.proposed_fix)}</div></div>`:''}
      ${(t.questions||[]).map((q,i)=>{const a=ans(i);return `<div class=tk-q><b>${esc(q.text)}</b><div class=tk-ch>${q.choices.map(c=>`<button class="ganew-chip${a&&a.choice===c?' on':''}" data-act=tkans data-id=${esc(t.id)} data-q=${i} data-c="${esc(c)}" aria-pressed=${!!(a&&a.choice===c)}>${esc(c)}</button>`).join('')}${q.allow_other?`<button class=link data-act=tkother data-id=${esc(t.id)} data-q=${i}>${a&&a.text?esc(a.text):'something else…'}</button>`:''}</div></div>`}).join('')}
      ${owner?`<div class=row>${['open','fixed','wont_fix'].map(s=>`<button class="btn sm${t.status===s?' pri':''}" data-act=tkstatus data-id=${esc(t.id)} data-s=${s}>${esc(STATUS[s])}</button>`).join('')}<small class=mut>drafted by ${esc(t.drafted_by||'preset')}</small></div>`:''}</div>`};
  const list=(rows,openId,openT,owner,filter)=>`<div class=tabs style="margin:0 0 8px">${[['open','Open'],['','All']].map(([v,l])=>`<button class="tab${filter===v?' on':''}" data-act=tkfilter data-v="${v}">${l}</button>`).join('')}</div>`+
    (rows.length?rows.map(t=>row(t,t.id===openId)+(t.id===openId&&openT?detail(openT,owner):'')).join(''):'<div class=mut>No tickets. A failure the server catches or a Report you send shows up here.</div>');
  const reportDlg=(k,id)=>`<h2>Report a problem</h2><p class=mut>What went wrong${id?` with ${esc(id)}`:''}? A ticket keeps what happened around it; you get a few one-click questions after.</p>
    <textarea id=tk-text rows=4 style="width:100%" placeholder="For example: the particles play twice, or the button does nothing"></textarea>
    <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=tksend data-k="${esc(k||'other')}" data-id="${esc(id||'')}">Send</button></div>`;
  return {esc,row,detail,list,reportDlg,ISSUE,STATUS};
})();
if(typeof globalThis!=='undefined')globalThis.TKV=TKV;
if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
  const TK={rows:[],open:null,t:null,filter:'open'};
  const tkOwner=()=>typeof ME==='undefined'||!ME||ME.role==='owner';
  async function tkLoad(){const r=await api('/api/tickets'+(TK.filter?'?status='+TK.filter:''));TK.rows=r.ok?r.j.tickets:[];tkDraw()}
  async function tkOpen(id){TK.open=id;const r=await api('/api/tickets/'+id);TK.t=r.ok?r.j:null;tkDraw()}
  function tkDraw(){const el=document.getElementById('tk-box');if(el)el.innerHTML=TKV.list(TK.rows,TK.open,TK.t,tkOwner(),TK.filter)}
  ACT.tkopen=el=>{if(TK.open===el.dataset.id){TK.open=null;TK.t=null;tkDraw()}else tkOpen(el.dataset.id)};
  ACT.tkfilter=el=>{TK.filter=el.dataset.v;TK.open=null;tkLoad()};
  ACT.tkans=async el=>{const r=await post(`/api/tickets/${el.dataset.id}/answer`,{question:+el.dataset.q,choice:el.dataset.c});if(!r.ok)return toast(r.j.error||'Could not save the answer',1);TK.t=r.j;tkDraw();tkLoad()};
  ACT.tkother=el=>{const v=prompt('Your answer');if(!v||!v.trim())return;post(`/api/tickets/${el.dataset.id}/answer`,{question:+el.dataset.q,text:v.trim()}).then(r=>{if(!r.ok)return toast(r.j.error||'Could not save the answer',1);TK.t=r.j;tkDraw()})};
  ACT.tkstatus=async el=>{const r=await post(`/api/tickets/${el.dataset.id}/status`,{status:el.dataset.s});if(!r.ok)return toast(r.j.error||'Could not change it',1);TK.t=r.j;tkLoad()};
  ACT.tkreport=el=>dlg(TKV.reportDlg(el.dataset.k,el.dataset.id));
  ACT.tksend=async el=>{const i=document.getElementById('tk-text'),text=i?i.value.trim():'';if(!text)return toast('Say what went wrong first',1);
    const k=el.dataset.k,id=el.dataset.id||null,sticker=el.dataset.s||null;el.disabled=true;
    const r=await post('/api/tickets',{text,target:{kind:k,id,...(sticker?{sticker}:{})}});el.disabled=false;
    if(!r.ok)return toast(r.j.error||'Could not send the report',1);closeDlg();toast(`Reported as ${r.j.id}: a few questions wait in Settings > Tickets`)};
  ACT.tkrefresh=()=>tkLoad();
  const tkOrig=RENDER.settings;
  RENDER.settings=async(...a)=>{const r=await tkOrig(...a);const page=document.querySelector('#s-settings .page');
    if(page&&!document.getElementById('tk-box')){const c=document.createElement('div');c.className='card';c.style.marginTop='16px';
      c.innerHTML='<div class=row style="justify-content:space-between"><h2 style="margin:0">Tickets</h2><button class="btn sm" data-act=tkrefresh>Refresh</button></div><div id=tk-box></div>';page.appendChild(c);tkLoad()}
    return r};
}
