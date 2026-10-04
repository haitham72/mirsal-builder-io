/* Trending (docs/api.md, Office accounts on the LAN): shared packs, Higgsfield-style, in the Library's Trending tab (a member, who has no library, gets it as their Library).
   Cards: the cover, the name, likes and comments; Trending / New / Most liked; a card opens the pack with its stickers, its comments and Use in my workflow.
   The owner and admins Share a pack from its page (trShareBtn). Everything is GET/POST /api/trending (console/app.py). Top-level names start with TR / tr;
   TRV holds the pure builders for node. */
'use strict';
const TRV=(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fileUrl=(pid,sid)=>`/api/trending/${encodeURIComponent(pid)}/file/${encodeURIComponent(sid)}`;
  const pic=(pid,s)=>!s?'<span class=mut>no stickers</span>':s.type==='animated'?`<video src="${fileUrl(pid,s.id)}" autoplay loop muted playsinline preload=metadata></video>`:`<img src="${fileUrl(pid,s.id)}" alt="" loading=lazy>`;
  const ORDERS=[['trending','Trending'],['new','New'],['liked','Most liked']];
  const card=p=>`<div class=tr-card><button class=tr-open data-act=tropen data-id="${esc(p.pack_id)}" title="Open ${esc(p.name)}"><span class=tr-cover>${pic(p.pack_id,p.cover)}</span><b>${esc(p.name)}</b><small class=mut>${p.stickers} sticker${p.stickers===1?'':'s'}</small></button>
    <div class=tr-meta><button class="tr-like${p.liked?' on':''}" data-act=trlike data-id="${esc(p.pack_id)}" aria-pressed=${!!p.liked} title="${p.liked?'Unlike':'Like'}">♥ ${p.likes}</button><span class=mut>💬 ${p.comments}</span></div></div>`;
  const list=(packs,order)=>`<div class=tabs style="margin:0 0 12px">${ORDERS.map(([v,l])=>`<button class="tab${order===v?' on':''}" data-act=trorder data-v=${v}>${l}</button>`).join('')}</div>`+
    (packs.length?`<div class=tr-grid>${packs.map(card).join('')}</div>`:'<div class=mut>Nothing shared yet. The owner shares a pack from its page (Share to Trending).</div>');
  const detail=(d,me,canShare)=>`<h2>${esc(d.name)}</h2><div class=row><button class="btn${d.liked?' pri':''}" data-act=trlike data-id="${esc(d.pack_id)}" aria-pressed=${!!d.liked}>♥ ${d.likes}</button>
     <button class="btn pri" data-act=truse data-id="${esc(d.pack_id)}" title="Make it yours: a copy in your library, or a new batch in this style">Use in my workflow</button>${canShare?`<button class="btn sm" data-act=trunshare data-id="${esc(d.pack_id)}">Stop sharing</button>`:''}</div>
    <div class=tr-sts>${d.stickers.map(s=>`<span class=tr-st title="${esc(s.name||'')}">${pic(d.pack_id,s)}</span>`).join('')}</div>
    <div class=tr-cm>${d.comments.map(c=>`<div class=tr-c><b>${esc(c.name)}</b> ${esc(c.text)}${me&&(c.user===me.id||canShare)?` <button class=link data-act=truncomment data-id="${esc(d.pack_id)}" data-c="${esc(c.id)}">delete</button>`:''}</div>`).join('')||'<div class=mut>No comments yet.</div>'}
     <div class=row><input id=tr-text maxlength=500 placeholder="Say something about this pack" style="flex:1"><button class=btn data-act=trcomment data-id="${esc(d.pack_id)}">Comment</button></div></div>
    <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Close</button></div>`;
  return {esc,card,list,detail,fileUrl};
})();
if(typeof globalThis!=='undefined')globalThis.TRV=TRV;
if(typeof document!=='undefined'&&typeof ACT!=='undefined'){
  const TR={order:'trending',packs:[],canShare:false,shared:null,open:null};
  const me=()=>typeof ME!=='undefined'?ME:null;
  async function trLoad(){const r=await api('/api/trending?order='+TR.order);if(!r.ok)return;TR.packs=r.j.packs;TR.canShare=r.j.can_share;TR.shared=new Set(TR.packs.map(p=>p.pack_id));
    const el=document.getElementById('tr-box');if(el)el.innerHTML=TRV.list(TR.packs,TR.order)}
  globalThis.trLoad=trLoad;
  async function trOpen(id){TR.open=id;const r=await api('/api/trending/'+encodeURIComponent(id));if(!r.ok)return toast(r.j.error||'Could not open it',1);dlg(TRV.detail(r.j,me(),TR.canShare))}
  ACT.trorder=el=>{TR.order=el.dataset.v;trLoad()};
  ACT.tropen=el=>trOpen(el.dataset.id);
  ACT.trlike=async el=>{const on=el.getAttribute('aria-pressed')!=='true',r=await post(`/api/trending/${encodeURIComponent(el.dataset.id)}/${on?'like':'unlike'}`,{});if(!r.ok)return toast(r.j.error||'Could not',1);
    await trLoad();if(TR.open===el.dataset.id&&document.querySelector('#dlg.on .tr-cm'))trOpen(el.dataset.id)};
  ACT.trcomment=async el=>{const i=document.getElementById('tr-text'),text=i?i.value.trim():'';if(!text)return;const r=await post(`/api/trending/${encodeURIComponent(el.dataset.id)}/comments`,{text});
    if(!r.ok)return toast(r.j.error||'Could not comment',1);trOpen(el.dataset.id);trLoad()};
  ACT.truncomment=async el=>{const r=await post(`/api/trending/${encodeURIComponent(el.dataset.id)}/comments/${encodeURIComponent(el.dataset.c)}/delete`,{});if(!r.ok)return toast(r.j.error||'Could not',1);trOpen(el.dataset.id);trLoad()};
  ACT.truse=async el=>{const r=await post(`/api/trending/${encodeURIComponent(el.dataset.id)}/use`,{});if(!r.ok)return toast(r.j.error||'Could not use it',1);closeDlg();
    if(r.j.copied){toast(`Copied to your library as “${r.j.copied.name}”`);if(typeof loadLib==='function')await loadLib();location.hash='#/pack/'+r.j.copied.pack_id;return}
    if(typeof CP!=='undefined'){CP.refs=(r.j.refs||[]).map(x=>({...x}));}location.hash='#/studio';setTimeout(()=>{const p=document.getElementById('prompt');if(p){p.value=r.j.prompt;p.dispatchEvent(new Event('input'))}if(typeof composerDraw==='function')composerDraw();
      toast('Ready in the Studio: this pack\'s subject and its cover as a reference. Change it, then Generate.')},300)};
  ACT.trunshare=async el=>{const r=await post(`/api/trending/${encodeURIComponent(el.dataset.id)}/unshare`,{});if(!r.ok)return toast(r.j.error||'Could not',1);closeDlg();toast('No longer shared');trLoad()};
  ACT.trshare=async el=>{const on=el.dataset.on!=='1',r=await post(`/api/trending/${encodeURIComponent(el.dataset.p)}/${on?'share':'unshare'}`,{});if(!r.ok)return toast(r.j.error||'Could not',1);
    toast(on?'Shared: it is in Trending for everyone signed in':'No longer shared');await trLoad();if(typeof drawPack==='function')drawPack()};
  globalThis.trShareBtn=pid=>{const m=me();if(m&&!['owner','admin'].includes(m.role))return '';if(TR.shared===null){TR.shared=new Set();trLoad().then(()=>{if(typeof drawPack==='function')drawPack()})}
    const on=TR.shared.has(pid);return `<button class=btn data-act=trshare data-p="${TRV.esc(pid)}" data-on=${on?1:0} title="${on?'Take it out of Trending':'Everyone signed in can see, like, comment on and use it'}">${on?'♥ Shared':'Share to Trending'}</button>`};
  const trLib=RENDER.library;
  RENDER.library=async(...a)=>{const m=me();
    if(m&&m.id!=='local'&&m.role!=='owner'){$('s-library').innerHTML='<div class=page><div class=ph><h1>Trending</h1></div><div id=tr-box></div></div>';return trLoad()}
    return trLib(...a)};
}
