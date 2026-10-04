/* Office accounts (docs/api.md, Office accounts on the LAN): on the LAN a browser signs in with an @nadi.ae account. GET /api/auth/me decides: signed out ->
   the sign-in card (Sign in / Create account / Forgot password); `pending` -> Waiting for approval; must_change_password -> a new password first. On this
   machine (not the LAN) the owner is signed in already and nothing shows. Settings gets "Signed in as" (Sign out, Request credits) and, for the owner and
   admins, People: add people (passwords shown once), approve, reject, roles, new password, credits. Top-level names start with AU / au; AUV holds the pure
   builders for node. */
'use strict';
const AUV=(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const field=(id,label,type,ac)=>`<label class=au-f><span>${label}</span><input id=${id} type=${type} autocomplete=${ac}></label>`;
  const gate=(mode,msg)=>`<div class=au-card role=dialog aria-modal=true aria-labelledby=au-t><img class=au-logo src=/assets/brand/mirsal-logo.png alt=""><h2 id=au-t>${mode==='signup'?'Create your account':mode==='forgot'?'Forgot password':'Sign in to Mirsal'}</h2>
    ${msg?`<div class=au-msg>${esc(msg)}</div>`:''}
    ${mode==='signup'?field('au-name','Name','text','name'):''}${field('au-email','Email (@nadi.ae)','email','username')}${mode==='forgot'?'':field('au-pw','Password','password',mode==='signup'?'new-password':'current-password')}
    <button class="btn pri au-go" ${mode==='signup'?'data-act=ausignup':mode==='forgot'?'data-act=auforgot':'data-act=ausignin'}>${mode==='signup'?'Create account':mode==='forgot'?'Ask for a new password':'Sign in'}</button>
    <div class=au-links>${mode!=='signin'?'<button class=link data-act=aumode data-v=signin>Sign in</button>':''}${mode!=='signup'?'<button class=link data-act=aumode data-v=signup>Create account</button>':''}${mode!=='forgot'?'<button class=link data-act=aumode data-v=forgot>Forgot password</button>':''}</div></div>`;
  const waiting=u=>`<div class=au-card role=dialog aria-modal=true><img class=au-logo src=/assets/brand/mirsal-logo.png alt=""><h2>Waiting for approval</h2>
    <p class=mut>Thanks, ${esc(u.name||u.email)}. Haitham will approve your account; this page opens by itself once he has.</p><button class=btn data-act=aulogout>Sign out</button></div>`;
  const change=u=>`<div class=au-card role=dialog aria-modal=true><h2>Choose your own password</h2><p class=mut>${esc(u.email)} was given a password to start with.</p>
    ${field('au-old','The password you were given','password','current-password')}${field('au-new','Your new password (8 characters or more)','password','new-password')}
    <button class="btn pri au-go" data-act=auchange>Save</button></div>`;
  const STATUS={pending:'Waiting',active:'Active',rejected:'Rejected',disabled:'Disabled'};
  const person=p=>{const pend=p.status==='pending';
    return `<div class=au-p data-uid=${esc(p.id)}><div><b>${esc(p.name)}</b><small class=mut>${esc(p.email||p.id)} · ${esc(p.role)} · ${esc(STATUS[p.status]||p.status||'token')}${p.credits_left!=null?` · ${p.credits_left} credits left, ${p.credits_spent||0} spent`:''}</small></div>
      <div class=row>${pend?`<button class="btn sm pri" data-act=aupeople data-id=${esc(p.id)} data-a=approve>Approve</button><button class="btn sm" data-act=aupeople data-id=${esc(p.id)} data-a=reject>Reject</button>`:''}
      ${p.role!=='owner'&&p.email?`${p.role==='admin'?`<button class="btn sm" data-act=aupeople data-id=${esc(p.id)} data-a=member>Make member</button>`:`<button class="btn sm" data-act=aupeople data-id=${esc(p.id)} data-a=admin>Make admin</button>`}
        <button class="btn sm" data-act=aupeople data-id=${esc(p.id)} data-a=password>New password</button><button class="btn sm" data-act=aucredits data-id=${esc(p.id)}>Give credits</button>
        ${p.status==='disabled'?`<button class="btn sm" data-act=aupeople data-id=${esc(p.id)} data-a=enable>Enable</button>`:pend?'':`<button class="btn sm dng" data-act=aupeople data-id=${esc(p.id)} data-a=disable>Disable</button>`}`:''}</div></div>`};
  const people=(list,reqs)=>{const waitingIds=new Set((reqs||[]).filter(r=>r.kind!=='signup').map(r=>r.user));
    return `<div class=row><textarea id=au-add rows=2 placeholder="name@nadi.ae, one per line" style="flex:1"></textarea><button class="btn pri" data-act=auadd>Add people</button></div>
      ${(reqs||[]).filter(r=>r.kind!=='signup').map(r=>`<div class=au-req>${esc(r.name||r.email)} asks for ${r.kind==='credits'?'more credits':'a new password'}${r.reason?`: “${esc(r.reason)}”`:''}
        <button class="btn sm pri" data-act=aupeople data-id=${esc(r.user)} data-a=${r.kind==='credits'?'credits':'password'} data-n=10>${r.kind==='credits'?'Give 10':'New password'}</button><button class="btn sm" data-act=auignore data-id=${esc(r.user)} data-r=${esc(r.id)}>Ignore</button></div>`).join('')}
      ${(list||[]).map(person).join('')||'<div class=mut>Nobody yet.</div>'}`};
  const me=u=>u&&u.id!=='local'?`<div class=row style="justify-content:space-between"><span>Signed in as <b>${esc(u.name)}</b> <span class=mut>${esc(u.email||'')}${u.credits_left!=null?` · ${u.credits_left} credits left`:''}</span></span>
    <span class=row><button class="btn sm" data-act=aucreditask>Request credits</button><button class="btn sm" data-act=aulogout>Sign out</button></span></div>`:'';
  const reshow=(shown,mode)=>shown!==mode;   /* a background 401 must not wipe the card: re-show only a mode that is not already up (typed text and error messages survive the polls) */
  return {esc,gate,waiting,change,people,person,me,reshow};
})();
if(typeof globalThis!=='undefined')globalThis.AUV=AUV;
if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
  const AU={me:null,mode:'signin',lan:false,shown:null};
  const auVal=id=>{const e=document.getElementById(id);return e?e.value.trim():''};
  function auShow(html,key){const k=key||AU.mode;if(!AUV.reshow(AU.shown,k))return;let o=document.getElementById('au-gate');if(!o){o=document.createElement('div');o.id='au-gate';document.body.appendChild(o)}o.innerHTML=html;o.classList.add('on');AU.shown=k;
    const f=o.querySelector('input');if(f)f.focus()}
  function auHide(){const o=document.getElementById('au-gate');if(o)o.classList.remove('on');AU.shown=null}
  async function auCheck(){const r=await api('/api/auth/me');
    if(r.status===401){AU.me=null;AU.lan=!!r.j.lan;return auShow(AUV.gate(AU.mode))}
    if(!r.ok)return;AU.me=r.j.user;AU.lan=!!r.j.lan;globalThis.ME=AU.me;
    if(AU.me.status==='pending'){auShow(AUV.waiting(AU.me),'waiting');setTimeout(auCheck,15000);return}
    if(AU.me.must_change_password)return auShow(AUV.change(AU.me),'change');
    auHide()}
  const auPost=async(u,b)=>{const r=await post(u,b);if(!r.ok){const m=r.j.error||'Something went wrong';const box=document.querySelector('#au-gate .au-card');
    if(box){let el=box.querySelector('.au-msg');if(!el){el=document.createElement('div');el.className='au-msg';box.insertBefore(el,box.querySelector('label'))}el.textContent=m}else toast(m,1)}return r};
  ACT.aumode=el=>{AU.mode=el.dataset.v;auShow(AUV.gate(AU.mode))};
  ACT.ausignin=async()=>{const r=await auPost('/api/auth/login',{email:auVal('au-email'),password:auVal('au-pw')});if(r.ok)location.reload()};
  ACT.ausignup=async()=>{const r=await auPost('/api/auth/signup',{email:auVal('au-email'),name:auVal('au-name'),password:auVal('au-pw')});if(r.ok)auCheck()};
  ACT.auforgot=async()=>{const r=await auPost('/api/auth/forgot',{email:auVal('au-email')});if(r.ok){AU.mode='signin';auShow(AUV.gate('signin',r.j.message))}};
  ACT.auchange=async()=>{const r=await auPost('/api/auth/password',{old:auVal('au-old'),new:auVal('au-new')});if(r.ok){toast('Password saved');auCheck()}};
  ACT.aulogout=async()=>{await post('/api/auth/logout',{});location.reload()};
  ACT.aucreditask=async()=>{const reason=prompt('More credits: what are they for? (optional)');if(reason===null)return;const r=await post('/api/auth/credits',{reason});
    toast(r.ok?'Asked: Haitham decides in Telegram or Settings':(r.j.error||'Could not ask'),!r.ok)};
  async function auPeople(){const el=document.getElementById('au-people');if(!el)return;const r=await api('/api/people');el.innerHTML=r.ok?AUV.people(r.j.people,r.j.requests):`<div class=mut>${AUV.esc(r.j.error||'')}</div>`}
  ACT.auadd=async()=>{const emails=auVal('au-add').split(/[\s,;]+/).filter(Boolean);if(!emails.length)return;const r=await post('/api/people',{emails});if(!r.ok)return toast(r.j.error||'Could not add them',1);
    dlg(`<h2>Send these passwords yourself</h2><p class=mut>They are shown once. Each person chooses their own at the first sign-in.</p>${r.j.people.map(p=>`<div class=au-pw><b>${AUV.esc(p.email)}</b> <code>${AUV.esc(p.password)}</code></div>`).join('')}<div class=row style="justify-content:flex-end"><button class="btn pri" data-act=dlgx>Done</button></div>`);auPeople()};
  ACT.aupeople=async el=>{const r=await post('/api/people/'+el.dataset.id,{action:el.dataset.a,...(el.dataset.n?{credits:+el.dataset.n}:{}) });if(!r.ok)return toast(r.j.error||'Could not change it',1);
    if(r.j.password)dlg(`<h2>New password</h2><p class=mut>Shown once: send it to ${AUV.esc(r.j.user.email)} yourself. They choose their own at the next sign-in.</p><code class=au-pw>${AUV.esc(r.j.password)}</code><div class=row style="justify-content:flex-end"><button class="btn pri" data-act=dlgx>Done</button></div>`);
    else toast('Saved');auPeople()};
  ACT.aucredits=async el=>{const n=prompt('How many credits to give?','10');if(!n||!(+n>0))return;const r=await post('/api/people/'+el.dataset.id,{action:'credits',credits:Math.round(+n)});toast(r.ok?'Given':(r.j.error||'Could not'),!r.ok);auPeople()};
  ACT.auignore=async el=>{const r=await post('/api/people/'+el.dataset.id,{action:'ignore'});toast(r.ok?'Ignored':(r.j.error||'Could not'),!r.ok);auPeople()};
  const realFetch=window.fetch.bind(window);
  window.fetch=async(...a)=>{const r=await realFetch(...a);const u=String(a[0]||'');if(r.status===401&&u.startsWith('/api/')&&!u.startsWith('/api/auth/')&&AU.shown===null)auCheck();return r};
  document.addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target&&e.target.closest&&e.target.closest('#au-gate')){const b=document.querySelector('#au-gate .au-go');if(b)b.click()}});
  const auOrig=RENDER.settings;
  RENDER.settings=async(...a)=>{const r=await auOrig(...a);const page=document.querySelector('#s-settings .page');
    if(page&&!document.getElementById('au-me')){const c=document.createElement('div');c.className='card';c.id='au-me';c.style.marginTop='16px';c.innerHTML=AUV.me(AU.me);if(c.innerHTML)page.insertBefore(c,page.firstChild)}
    if(page&&!document.getElementById('au-people')&&(!AU.me||['owner','admin'].includes(AU.me.role))){const c=document.createElement('div');c.className='card';c.style.marginTop='16px';
      c.innerHTML='<div class=row style="justify-content:space-between"><h2 style="margin:0">People</h2></div><div id=au-people></div>';page.appendChild(c);auPeople()}
    return r};
  auCheck();
}
