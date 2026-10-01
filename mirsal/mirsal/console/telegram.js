/* Send to Telegram (checkpoint 1H): one dialog from a pack. Connect once (bot token + your user id), then one click creates the pack,
   or adds what is new to it. The token is typed here, sent to this PC's server and saved in out/telegram.json; it is never shown again. */
'use strict';
let TG={plan:null,name:'',busy:false,done:null};
const tgKind=k=>k==='video'?'animated':'static';
const tgN=(n,k)=>`${n} ${tgKind(k)} sticker${n===1?'':'s'}`;
async function tgOpen(){TG={plan:null,name:'',busy:false,done:null};const p=packById(PACK_ID);if(!p)return;TG.name=p.name;await tgLoad();tgDraw()}
async function tgLoad(){const r=await api(`/api/packs/${PACK_ID}/telegram?name=${encodeURIComponent(TG.name)}`);if(!r.ok){toast(r.j.error||'Could not read the pack',1);return}TG.plan=r.j}
function tgConnectForm(msg){return`<h3>Connect your Telegram bot</h3>
  <ol class=mut style="margin:6px 0 10px 18px;padding:0"><li>In Telegram, message <b>@BotFather</b>, send <code>/newbot</code>, and copy the token it gives you.</li>
  <li>Open your new bot and press <b>Start</b> (Telegram only lets a bot create packs for people who started it).</li>
  <li>Message <b>@userinfobot</b> to see your numeric user id.</li></ol>
  <div class=fld><label>Bot token</label><input type=text id=tgtok placeholder="123456789:AAH…" autocomplete=off spellcheck=false></div>
  <div class=fld><label>Your Telegram user id</label><input type=text id=tguid placeholder="123456789" inputmode=numeric autocomplete=off></div>
  ${msg?`<div class=warn>${esc(msg)}</div>`:''}
  <div class=mut>Saved on this PC only (<code>out/telegram.json</code>) and sent only to Telegram.</div>
  <div class=row style="justify-content:flex-end"><button class=btn data-act=dlgx>Cancel</button><button class="btn pri" data-act=tgconnect>Connect</button></div>`}
function tgDraw(){const P=TG.plan;if(!P)return;const st=P.status||{};
  if(TG.done){const d=TG.done;
    dlg(`<div class=tgdlg><h2>${ic('check')} Sent to Telegram</h2>${d.sets.map(s=>`<div class=card style="margin:10px 0"><b>${esc(tgN(s.added,s.kind))} added</b> <span class=mut>(${s.total} in this set)</span><br>
      <a href="${esc(s.link)}" target=_blank rel=noopener>${esc(s.link)}</a><div class=row><a class="btn pri sm" href="${esc(s.link)}" target=_blank rel=noopener>Open in Telegram</a><button class="btn sm" data-act=tgcopy data-l="${esc(s.link)}">Copy link</button></div></div>`).join('')}
      ${d.warnings.length?`<div class=warn>${d.warnings.map(esc).join('<br>')}</div>`:''}<div class=row style="justify-content:flex-end"><button class="btn pri" data-act=dlgx>Done</button></div></div>`);return}
  if(!st.configured){dlg(`<div class=tgdlg><h2>${ic('telegram')} Send “${esc(P.pack)}” to Telegram</h2>${tgConnectForm()}</div>`);return}
  const newN=P.sets.reduce((a,s)=>a+s.new.length,0),blocked=P.blocked.length>0;
  dlg(`<div class=tgdlg><h2>${ic('telegram')} Send “${esc(P.pack)}” to Telegram</h2><div class=mut>Connected as <b>@${esc(st.bot||'your bot')}</b>. <button class=link data-act=tgdisconnect>Disconnect</button></div>
    <div class=fld style="margin-top:12px"><label>Pack name on Telegram</label><input type=text id=tgname value="${esc(TG.name)}" maxlength=64></div>
    ${P.sets.map(s=>`<div class=card style="margin:10px 0"><b>${esc(tgN(s.new.length||s.items.length,s.kind))}</b> ${s.exists?`<span class=mut>to the existing set (${s.items.length-s.new.length} already there)</span>`:'<span class=mut>in a new set</span>'}
      <div class=mut style="word-break:break-all">${esc(s.link)}</div></div>`).join('')||'<div class=mut>This pack has no stickers yet.</div>'}
    ${blocked?`<div class=warn style="border-color:var(--bad)"><b>Cannot send yet</b><br>${P.blocked.map(esc).join('<br>')}</div>`:''}
    ${P.warnings.length?`<div class=warn>${P.warnings.map(esc).join('<br>')}</div>`:''}
    <div class=mut style="margin:8px 0">Anyone with the link can add this pack on Telegram.</div>
    <div class=row style="justify-content:space-between"><a class=link href="/api/packs/${PACK_ID}/telegram.zip" download>Download for @stickers instead (zip)</a>
      <span><button class=btn data-act=dlgx>Cancel</button> <button class="btn pri" data-act=tgsendgo ${blocked||!newN||TG.busy?'disabled':''}>${TG.busy?'Sending…':newN&&P.sets.some(s=>s.exists)?`Add ${newN} new`:'Create on Telegram'}</button></span></div></div>`);
  const nm=$('tgname');if(nm)nm.onchange=async()=>{TG.name=nm.value.trim()||TG.name;await tgLoad();tgDraw()}}
ACT.tgsend=()=>tgOpen();
ACT.tgconnect=async()=>{const r=await post('/api/telegram/config',{token:$('tgtok').value,user_id:$('tguid').value});if(!r.ok){$('dlg').querySelector('.tgdlg').innerHTML=`<h2>${ic('telegram')} Connect Telegram</h2>`+tgConnectForm(r.j.error);return}
  toast(`Connected to @${r.j.bot}`);if(route_==='settings')RENDER.settings();if(PACK_ID&&route_==='pack'){await tgLoad();tgDraw()}else closeDlg()};
ACT.tgdisconnect=async()=>{await post('/api/telegram/disconnect');await tgLoad();tgDraw();if(route_==='settings')RENDER.settings()};
ACT.tgsendgo=async()=>{TG.busy=true;tgDraw();const r=await post(`/api/packs/${PACK_ID}/telegram`,{name:TG.name});TG.busy=false;
  if(!r.ok){toast(r.j.error,1);await tgLoad();tgDraw();return}TG.done=r.j;tgDraw()};
ACT.tgcopy=async el=>{try{await navigator.clipboard.writeText(el.dataset.l);toast('Link copied')}catch(e){toast('Copy failed',1)}};
/* Settings card */
async function tgSettingsCard(){const r=await api('/api/telegram');if(!r.ok)return'';const s=r.j;
  return`<div class=card style="margin-top:16px"><h2 style="display:flex;gap:8px;align-items:center">${ic('telegram')} Telegram</h2>
   ${s.configured?`<div class=kv><span>bot</span><span><b>@${esc(s.bot||'?')}</b>${s.from_env?' (from the environment)':''}</span><span>your user id</span><span>${esc(s.user_id)}</span><span>service</span><span>${esc(s.api)}</span></div>
     <div class=row>${s.from_env?'':`<button class="btn sm dng" data-act=tgdisconnect>Disconnect</button>`}<span class=mut>Send a pack from its page: Library → a pack → Send to Telegram.</span></div>`
   :`<div class=mut>Not connected. Stickers can be created on Telegram in one click once you connect a bot.</div><div class=row><button class="btn pri sm" data-act=tgsettings>Connect Telegram</button></div>`}</div>`}
ACT.tgsettings=()=>{TG={plan:{pack:'your stickers',status:{configured:false},sets:[],blocked:[],warnings:[]},name:'',busy:false,done:null};tgDraw()};
