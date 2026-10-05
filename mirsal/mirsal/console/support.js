/* Help & Support (docs/agent-and-chat.md "Support", docs/design.md §5 Help): one place to describe a problem and follow it. The second column lists the
   person's issues (a state chip each) and their notifications; staff also get the Queue (escalated tickets) and FAQ review. The stage is one conversation:
   the agent's answer with the help entries it read, "Did this solve it?", Send to support, the admin's replies, Reopen. A screenshot can be attached or
   pasted (Ctrl+V) when it helps; the local vision model reads it. Everything is GET/POST /api/support, /api/notifications, /api/faq (console/app.py).
   Top-level names start with SU / SUV / su (the console scripts share one scope); SUV holds the pure builders for node (tests/js/support.test.js). */
'use strict';
const SUV=(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const when=t=>t?new Date(t*1000).toLocaleString([],{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}):'';
  const STATE={answered:'Answered',awaiting_admin:'Waiting for support',admin_replied:'Support replied',resolved:'Resolved',searching:'Looking for an answer…',
    open:'Open',replied:'Replied',fixed:'Resolved',wont_fix:'Closed',pending:'Waiting for review',draft:'Draft',published:'Published',archived:'Archived'};
  const chip=s=>`<span class="su-st ${esc(s)}">${esc(STATE[s]||s)}</span>`;
  const convRow=(c,on)=>`<div class="crow${on?' on':''}" data-act=suopen data-id="${esc(c.id)}"><div style="min-width:0;flex:1"><b class=su-t>${esc(c.title||'Question')}</b><small>${chip(c.status)} ${esc(when(c.updated))}</small></div></div>`;
  const noteRow=n=>`<div class="crow su-note${n.read?'':' unread'}" data-act=sunote data-c="${esc(n.conversation||'')}" data-t="${esc(n.ticket||'')}"><div style="min-width:0"><b>${n.kind==='resolved'?'Resolved':'Support answered'}</b><small>${esc(n.text)}</small></div><span class=meta>${esc(when(n.at))}</span></div>`;
  const short=c=>{const t=String(c.title||'').split(' › ').pop().replace(/\s*\([^)]*`[^)]*\)/g,'').replace(/`/g,'').trim();return t||c.title};
  const cites=m=>(m.cites||[]).length?`<div class=su-cites><span class=mut>From the help:</span>${m.cites.map(c=>c.kind==='faq'?`<button class=su-cite data-act=sucite data-id="${esc(c.id)}">${esc(c.title)}</button>`
    :`<span class="su-cite${c.kind==='code'?' code':''}" title="${esc(c.title)}">${c.kind==='code'?'code: ':''}${esc(short(c))}</span>`).join('')}</div>`:'';
  const msg=(m,staff)=>{const who=m.role==='user'?'out':'in';
    return`<div class="cm c${who}"><div class="bub su-b ${esc(m.role)}">${m.role==='admin'?`<b class=su-who>${esc(m.by_name||'Support')}</b>`:''}<div class=su-x>${esc(m.text)}</div>
      ${m.image?`<a href="${esc(m.image)}" target=_blank rel=noopener><img class=su-img src="${esc(m.image)}" alt="Screenshot"></a>`:''}${staff&&m.seen?`<div class=su-seen><b>Vision model saw:</b> ${esc(m.seen)}</div>`:''}
      ${cites(m)}<span class=tm>${esc(when(m.ts))}${staff&&m.mode?` · ${esc(m.mode)}${m.code_used?' · code':''}`:''}</span></div></div>`};
  /* what the person can do now, from the conversation's state and the agent's last answer */
  const next=(cv,busy)=>{if(busy)return`<div class="su-bar"><span class=spin></span> Looking for an answer…</div>`;
    const last=[...(cv.messages||[])].reverse().find(m=>m.role!=='user')||{};
    if(cv.status==='resolved')return`<div class=su-bar>${chip('resolved')}<span class=mut>Not fixed after all?</span><button class=btn data-act=sureopen>Reopen</button></div>`;
    if(cv.status==='awaiting_admin')return`<div class=su-bar>${chip('awaiting_admin')}<span class=mut>A person will answer here; you get a notification.</span></div>`;
    if(cv.status==='admin_replied')return`<div class=su-bar>${chip('admin_replied')}<span class=mut>Write back below.</span></div>`;
    if(last.need==='screenshot')return`<div class=su-bar><span class=mut>A screenshot would help.</span><button class="btn pri" data-act=sushot>Attach a screenshot</button><button class=link data-act=suesc>Send to support instead</button></div>`;
    if(last.need==='clarify')return'';
    if(last.grounded)return`<div class=su-bar><b>Did this solve it?</b><button class="btn pri" data-act=susolved>Yes, solved</button><button class=btn data-act=suunsolved>No, send to support</button></div>`;
    return`<div class=su-bar><span class=mut>Nothing in the help answers this yet.</span><button class="btn pri" data-act=suesc>Send to support</button></div>`};
  const composer=(cv,img)=>`<div class=su-in>${img?`<div class=su-att><img src="${esc(img)}" alt=""><button class=link data-act=sushotx>remove</button></div>`:''}
    <textarea id=su-text rows=${cv?2:5} placeholder="${cv?(cv.ticket&&cv.status!=='resolved'?'Write to support…':'Add a detail or ask again…'):'Describe the problem in your own words: what you did, what you expected, what happened.'}"></textarea>
    <div class=row><button class="btn sm" data-act=sushot title="Attach a screenshot (or paste one with Ctrl+V)">📎 Screenshot</button><span class=mut style="flex:1">${cv?'':'Paste a screenshot with Ctrl+V; the local AI reads it.'}</span><button class="btn pri" data-act=suask>${cv?'Send':'Ask'}</button></div></div>`;
  const conv=(cv,staff,busy,img)=>`<div class=su-conv><div class=su-head><h2>${esc(cv.title||'Question')}</h2>${chip(busy?'searching':cv.status)}</div>
    <div class=su-msgs id=su-msgs>${(cv.messages||[]).map(m=>msg(m,staff)).join('')}</div>${next(cv,busy)}${composer(cv,img)}</div>`;
  const fresh=(img,busy,pending)=>`<div class=su-conv><div class=su-head><h2>How can we help?</h2></div><p class=mut>The help answers first; if it does not know, a person takes over and you are notified here.</p>${pending?`<div class=su-msgs>${msg({role:'user',text:pending},false)}</div>`:''}${busy?`<div class=su-bar><span class=spin></span> Looking for an answer…</div>`:''}${busy?'':composer(null,img)}</div>`;
  /* staff */
  const queueRow=(t,on)=>`<div class="crow${on?' on':''}" data-act=suq data-id="${esc(t.id)}"><div style="min-width:0;flex:1"><b class=su-t>${esc(t.title||t.summary||t.id)}</b><small>${chip(t.status==='answered'?'open':t.status)} ${esc(t.name||t.user||'')} · ${esc(t.id)}${t.pinged?'':' · not pinged yet'}</small></div></div>`;
  const ticket=(d)=>{const t=d.ticket,cv=d.conversation;
    return`<div class=su-conv><div class=su-head><h2>${esc(t.summary||t.intent||t.id)}</h2>${chip(t.status==='answered'?'open':t.status)}</div>
      <div class=su-meta><span>${esc(t.id)}</span>${t.proposed_fix?`<span><b>Suggested fix:</b> ${esc(t.proposed_fix)}</span>`:''}${t.faq?`<button class=link data-act=sufaq data-id="${esc(t.faq)}">FAQ proposal ${esc(t.faq)}</button>`:''}</div>
      <div class=su-msgs>${cv?(cv.messages||[]).map(m=>msg(m,true)).join(''):`<div class=mut>${esc(t.intent||t.what_happened||'')}</div>${(t.thread||[]).map(m=>msg({...m,by_name:m.by},true)).join('')}`}</div>
      <div class=su-in><textarea id=su-reply rows=3 placeholder="Your answer to the person"></textarea>
      <div class=row style="justify-content:flex-end"><button class=btn data-act=sureply data-id="${esc(t.id)}">Reply</button><button class="btn pri" data-act=suresolve data-id="${esc(t.id)}">${t.status==='fixed'?'Resolved':'Reply and resolve'}</button></div>
      <small class=mut>Reply keeps the issue open. Resolve closes it, notifies the person and proposes an FAQ entry for review.</small></div></div>`};
  const faqRow=(f,on)=>`<div class="crow${on?' on':''}" data-act=sufaq data-id="${esc(f.id)}"><div style="min-width:0;flex:1"><b class=su-t>${esc(f.title||f.question)}</b><small>${chip(f.pending?'pending':f.status)} ${esc(f.category||'')} ${esc(f.id)}</small></div></div>`;
  const faqEdit=f=>{const p=f.pending,src=p||f;
    return`<div class=su-conv><div class=su-head><h2>${esc(f.id)} · ${p?'proposed revision':f.status}</h2>${chip(p?'pending':f.status)}</div>
      ${p&&f.status==='published'?`<div class=su-was><b>Published now (revision ${esc(f.revision)})</b><div>${esc(f.question)}</div><div class=mut>${esc(f.answer)}</div></div>`:''}
      <label>Title<input id=su-ft value="${esc(src.title||'')}"></label><label>Question<input id=su-fq value="${esc(src.question||'')}"></label>
      <label>Answer<textarea id=su-fa rows=7>${esc(src.answer||'')}</textarea></label>
      ${f.looks_like?`<div class=mut><b>Looks like:</b> ${esc(f.looks_like)}</div>`:''}<div class=mut>From ${(f.provenance||[]).map(x=>esc(x.ticket||x.seed||'')).filter(Boolean).join(', ')||'an admin'}</div>
      <div class=row style="justify-content:flex-end">${f.status==='archived'?'':`<button class=btn data-act=sufsave data-id="${esc(f.id)}">Save edits</button>${p||f.status==='draft'?`<button class=btn data-act=sufdisc data-id="${esc(f.id)}">Discard</button><button class="btn pri" data-act=sufpub data-id="${esc(f.id)}">Publish</button>`:''}<button class="btn dng" data-act=sufarch data-id="${esc(f.id)}">Archive</button>`}</div></div>`};
  return {esc,chip,convRow,noteRow,msg,next,conv,fresh,queueRow,ticket,faqRow,faqEdit,STATE};
})();
if(typeof globalThis!=='undefined')globalThis.SUV=SUV;
if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
  const SU={tab:'mine',list:[],cv:null,notes:[],unread:0,busy:false,img:null,queue:[],tk:null,faq:[],fq:null,fall:false,poll:0};
  const suStaff=()=>typeof ME!=='undefined'&&ME&&['owner','admin'].includes(ME.role);
  globalThis.supUnread=()=>SU.unread;
  async function suNotes(){const r=await api('/api/notifications');if(!r.ok)return;const before=SU.unread;SU.notes=r.j.notifications||[];SU.unread=r.j.unread||0;
    if(before!==SU.unread&&typeof drawRail==='function')drawRail();if(route_==='help'&&SU.tab==='mine')suCol()}
  async function suLoad(){const r=await api('/api/support/conversations');SU.list=r.ok?r.j.conversations:[]}
  function suCol(){const el=$('col2');if(!el)return;const tabs=suStaff()?`<div class="tabs su-tabs">${[['mine','My issues'],['queue','Queue'],['faq','FAQ review']].map(([k,l])=>`<button class="tab${SU.tab===k?' on':''}" data-act=sutab data-t=${k}>${l}</button>`).join('')}</div>`:'';
    let body='';
    if(SU.tab==='queue')body=SU.queue.map(t=>SUV.queueRow(t,SU.tk&&SU.tk.ticket.id===t.id)).join('')||'<div class="mut" style="padding:14px">Nobody is waiting.</div>';
    else if(SU.tab==='faq')body=`<div class=row style="padding:0 16px"><button class=link data-act=sufall>${SU.fall?'Waiting for review only':'Show every entry'}</button></div>`+(SU.faq.map(f=>SUV.faqRow(f,SU.fq&&SU.fq.id===f.id)).join('')||'<div class="mut" style="padding:14px">No FAQ entry waits for review.</div>');
    else body=SU.list.map(c=>SUV.convRow(c,SU.cv&&SU.cv.id===c.id)).join('')||'<div class="mut" style="padding:14px">No questions yet.</div>';
    const notes=SU.tab==='mine'&&SU.notes.length?`<div class=su-sh>Notifications${SU.unread?` <span class=su-dot>${SU.unread}</span>`:''}</div>${SU.notes.slice(0,8).map(SUV.noteRow).join('')}`:'';
    el.innerHTML=`<div class=c2h><h1>Help</h1>${SU.tab==='mine'?`<button class=iconbtn data-act=sunew title="New question">${ic('plus')}</button>`:''}</div>${tabs}<div class=c2l>${body}${notes}</div>`}
  globalThis.supCol=suCol;
  function suDraw(){const st=$('s-help');if(!st)return;
    let h;
    if(SU.tab==='queue')h=SU.tk?SUV.ticket(SU.tk):'<div class=su-conv><h2>Queue</h2><p class=mut>Pick an issue on the left.</p></div>';
    else if(SU.tab==='faq')h=SU.fq?SUV.faqEdit(SU.fq):'<div class=su-conv><h2>FAQ review</h2><p class=mut>Proposals from resolved issues and imported entries wait here. Nothing answers people until it is published.</p></div>';
    else h=SU.cv?SUV.conv(SU.cv,suStaff(),SU.busy,SU.img):SUV.fresh(SU.img,SU.busy,SU.busy?SU.pending:null);
    st.innerHTML=`<div class=page>${h}</div>`;const m=$('su-msgs');if(m)m.scrollTop=m.scrollHeight;
    const t=$('su-text');if(t){t.onkeydown=e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();ACT.suask()}};t.onpaste=e=>{const f=[...(e.clipboardData||{}).items||[]].find(i=>i.type&&i.type.startsWith('image/'));if(f){e.preventDefault();suFile(f.getAsFile())}}}}
  function suFile(f){if(!f)return;if(f.size>8*1024*1024)return toast('A screenshot must be under 8 MB',1);const r=new FileReader();r.onload=()=>{SU.img=String(r.result);suDraw()};r.readAsDataURL(f)}
  async function suOpen(id){const r=await api('/api/support/conversations/'+encodeURIComponent(id));if(!r.ok)return toast(r.j.error||'Could not open it',1);SU.cv=r.j;suDraw();suCol();suNotes();suWatch()}
  /* while a person waits for support the open conversation is read again now and then, so an answer shows without a reload */
  function suWatch(){clearTimeout(SU.poll);if(route_!=='help'||!SU.cv||!['awaiting_admin','admin_replied'].includes(SU.cv.status))return;
    SU.poll=setTimeout(async()=>{if(route_!=='help'||!SU.cv||document.hidden)return suWatch();const r=await api('/api/support/conversations/'+SU.cv.id);
      if(r.ok&&JSON.stringify(r.j.messages.length)!==JSON.stringify(SU.cv.messages.length)||r.ok&&r.j.status!==SU.cv.status){SU.cv=r.j;suDraw();await suLoad();suCol()}suWatch()},15000)}
  async function suQueue(){const r=await api('/api/support/queue');SU.queue=r.ok?r.j.tickets:[]}
  async function suFaqs(){const r=await api('/api/faq?status='+(SU.fall?'all':'pending'));SU.faq=r.ok?r.j.faq:[]}
  RENDER.help=async arg=>{const a=String(arg||'');
    if(a.startsWith('queue')&&suStaff()){SU.tab='queue';await suQueue();const id=a.split('/')[1];if(id){const r=await api('/api/support/tickets/'+id);SU.tk=r.ok?r.j:null}}
    else if(a.startsWith('faq')&&suStaff()){SU.tab='faq';await suFaqs();const id=a.split('/')[1];if(id){const r=await api('/api/faq/'+id);SU.fq=r.ok?r.j:null}}
    else{SU.tab='mine';await suLoad();if(/^C\d+$/i.test(a)){await suOpen(a);return}if(!a)SU.cv=null}
    suCol();suDraw()};
  ACT.sutab=el=>{location.hash='#/help'+(el.dataset.t==='mine'?'':'/'+el.dataset.t)};
  ACT.sunew=()=>{SU.cv=null;SU.img=null;location.hash='#/help';suDraw();suCol()};
  ACT.suopen=el=>{location.hash='#/help/'+el.dataset.id};
  ACT.sunote=el=>{if(el.dataset.c)location.hash='#/help/'+el.dataset.c};
  ACT.sushot=()=>{const i=document.createElement('input');i.type='file';i.accept='image/png,image/jpeg,image/webp';i.onchange=()=>suFile(i.files[0]);i.click()};
  ACT.sushotx=()=>{SU.img=null;suDraw()};
  ACT.suask=async()=>{const t=$('su-text'),text=t?t.value.trim():'';if(!text&&!SU.img)return toast('Describe the problem first',1);if(SU.busy)return;
    const cid=SU.cv?SU.cv.id:null,body={text,conversation:cid,client_id:Date.now().toString(36)+Math.random().toString(36).slice(2,6)};if(SU.img)body.image=SU.img;
    if(SU.cv)SU.cv={...SU.cv,messages:[...SU.cv.messages,{role:'user',text:text||'(a screenshot)',ts:Date.now()/1000}]};
    SU.pending=text||'(a screenshot)';SU.busy=true;suDraw();const r=await post('/api/support/ask',body);SU.busy=false;SU.pending=null;
    if(!r.ok){suDraw();const t2=$('su-text');if(t2)t2.value=text;return toast(r.j.error||'Could not send it',1)}SU.img=null;SU.cv=r.j;await suLoad();if(location.hash!=='#/help/'+r.j.id)history.replaceState(null,'','#/help/'+r.j.id);suDraw();suCol();suWatch()};
  const suAct=async(path,body,msg)=>{const r=await post(`/api/support/conversations/${SU.cv.id}/${path}`,body||{});if(!r.ok)return toast(r.j.error||'Could not do that',1);SU.cv=r.j;await suLoad();suDraw();suCol();suWatch();if(msg)toast(msg)};
  ACT.susolved=()=>suAct('feedback',{solved:true},'Glad it is solved');
  ACT.suunsolved=()=>suAct('feedback',{solved:false},'Sent to support: you will be notified here');
  ACT.suesc=()=>suAct('escalate',{},'Sent to support: you will be notified here');
  ACT.sureopen=()=>suAct('reopen',{text:($('su-text')||{}).value||null},'Reopened');
  ACT.sucite=async el=>{const r=await api('/api/faq/'+el.dataset.id);if(!r.ok)return toast('That entry is not available',1);
    dlg(`<h2>${SUV.esc(r.j.title||r.j.question)}</h2><p><b>${SUV.esc(r.j.question)}</b></p><p style="white-space:pre-wrap">${SUV.esc(r.j.answer)}</p><div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button></div>`)};
  ACT.suq=el=>{location.hash='#/help/queue/'+el.dataset.id};
  const suTk=async id=>{const r=await api('/api/support/tickets/'+id);SU.tk=r.ok?r.j:null;await suQueue();suDraw();suCol()};
  ACT.sureply=async el=>{const t=$('su-reply'),text=t?t.value.trim():'';if(!text)return toast('Write the answer first',1);
    const r=await post(`/api/tickets/${el.dataset.id}/reply`,{text,client_id:'r'+Date.now().toString(36)});if(!r.ok)return toast(r.j.error||'Could not reply',1);toast('Sent: the person is notified');suTk(el.dataset.id)};
  ACT.suresolve=async el=>{const t=$('su-reply'),text=t?t.value.trim():'';const r=await post(`/api/tickets/${el.dataset.id}/resolve`,{text:text||null,client_id:text?'s'+Date.now().toString(36):null});
    if(!r.ok)return toast(r.j.error||'Could not resolve it',1);toast('Resolved: an FAQ proposal follows in FAQ review');suTk(el.dataset.id)};
  ACT.sufaq=el=>{location.hash='#/help/faq/'+el.dataset.id};
  ACT.sufall=async()=>{SU.fall=!SU.fall;await suFaqs();suCol()};
  const suF=async(act,body,msg)=>{const id=SU.fq.id,r=await post(`/api/faq/${id}/${act}`,body||{});if(!r.ok)return toast(r.j.error||'Could not do that',1);SU.fq=r.j;await suFaqs();suDraw();suCol();toast(msg)};
  ACT.sufsave=()=>suF('edit',{title:$('su-ft').value,question:$('su-fq').value,answer:$('su-fa').value},'Saved: publish it to answer people');
  ACT.sufpub=()=>suF('publish',{},'Published: the help answers with it now');
  ACT.sufdisc=()=>suF('discard',{},'Discarded');
  ACT.sufarch=()=>confirmDlg('Archive this entry? It stops answering people (it is kept, not deleted).',()=>suF('archive',{},'Archived'),'Archive');
  /* the rail's unread dot: notifications are read every 30 s while the page is open */
  setTimeout(suNotes,1500);setInterval(()=>{if(!document.hidden)suNotes()},30000);
}
