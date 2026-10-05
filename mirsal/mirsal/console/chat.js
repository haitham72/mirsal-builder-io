/* Local Echo contact: replies/reactions test the sent sticker's current assigned particle settings.
   Messages live in this browser. Preview selection and rendering belong to the engine. */
'use strict';
if(typeof ICONS!=='undefined'){ICONS.phone='<rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/>';
 ICONS.desktop='<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M9 20h6M12 16v4"/>'}
const CH={msgs:[],tray:false,pk:null,typing:false,draft:'',pending:null,epoch:0,seq:0,play:{},requests:{},view:'desktop'};
try{if(localStorage.getItem('mirsal.chat.view')==='mobile')CH.view='mobile'}catch(e){}   /* a per-browser look: the chat as on a phone, or full width */
try{CH.msgs=JSON.parse(localStorage.getItem('mirsal.chat')||'[]')}catch(e){}
if(!Array.isArray(CH.msgs))CH.msgs=[];
const chSave=()=>{try{localStorage.setItem('mirsal.chat',JSON.stringify(CH.msgs.slice(-200)))}catch(e){}};
const hm=t=>new Date(t).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
const chPreview=m=>!m?'No messages yet':m.kind==='sticker'?'Sticker':esc(m.text);
const chSticker=(s,pack_id)=>({id:s.id,pack_id:s.pack_id||pack_id,type:s.type,file:s.file,name:s.name});
const chParticleH=m=>{const p=CH.play[m.id];return p?`<img class=ch-particle src="${esc(p.url)}" alt="" aria-hidden=true data-particle-set="${esc(p.set)}">`:''};     /* centred on the reaction badge (bottom-left), spilling over the bubble, as Telegram plays a reaction's effect (studio.css .ch-particle) */
const chReactionH=m=>!m.react?'':m.kind==='sticker'&&m.from==='out'&&m.s&&m.s.id&&m.s.pack_id?`<button type=button class=react data-act=chreplay data-id="${esc(m.id)}" title="Replay reaction" aria-label="Replay reaction">${esc(m.react)}</button>`:`<span class=react>${esc(m.react)}</span>`;
function chList(){const m=CH.msgs[CH.msgs.length-1];
 $('col2').innerHTML=`<div class=c2h><h1>Chats</h1></div><div class=c2s><input type=search placeholder="Search chats…" disabled></div>
  <div class=c2l><div class="crow on"><div class="cv chav">M</div><div style="min-width:0"><b>Mirsal Echo</b><small>${m&&m.from==='out'?'You: ':''}${chPreview(m)}</small></div><span class=meta>${m?hm(m.t):''}</span></div></div>`}
const chMsgH=m=>{const t=`<span class=tm>${hm(m.t)}${m.from==='out'?' ✓✓':''}</span>`;
 return m.kind==='sticker'?`<div class="cm c${m.from}" data-chmsg="${esc(m.id)}"><div class="bub stk">${media(m.s)}${chParticleH(m)}${chReactionH(m)}${t}</div></div>`
  :`<div class="cm c${m.from}"><div class=bub>${esc(m.text)}${chReactionH(m)}${t}</div></div>`};
function chTrayH(){const ps=LIB.packs.filter(p=>p.stickers.length);if(!ps.length)return`<div class=chtray><span class=mut>No stickers yet.</span> <button class="btn sm" data-act=nav data-to=create>${ic('create')} Create one</button></div>`;
 const cur=ps.find(p=>p.id===CH.pk)||ps[0];CH.pk=cur.id;
 return`<div class=chtray><div class=tabs style="margin:0 0 8px">${ps.map(p=>`<button class="tab ${p.id===cur.id?'on':''}" data-act=chpack data-id=${p.id}>${esc(p.name)}</button>`).join('')}</div>
  <div class=trgrid>${cur.stickers.map(s=>`<div class=trs data-act=chpick data-id=${s.id} title="${esc(s.name)}">${media(s)}</div>`).join('')}</div></div>`}
function chDraw(){if(route_!=='chat')return;const el=$('s-chat'),inp=$('chin');if(inp)CH.draft=inp.value;
 el.innerHTML=`<div class="chat${CH.view==='mobile'?' mobile':''}"><div class=chh><div class="cv chav">M</div><div style="flex:1"><b>Mirsal Echo</b><small>${CH.typing?'typing…':'online'}</small></div><button class=iconbtn data-act=chview title="${CH.view==='mobile'?'Desktop view':'Mobile view'}" aria-label="${CH.view==='mobile'?'Switch to desktop view':'Switch to mobile view'}">${ic(CH.view==='mobile'?'desktop':'phone')}</button><button class=iconbtn data-act=chclear title="Clear chat">${ic('trash')}</button></div>
  <div class=chm id=chm>${CH.msgs.map(chMsgH).join('')||'<div class="mut chempty">Say hi or send a sticker. It comes back to you and your message gets a like.</div>'}${CH.typing?'<div class="cm in"><div class="bub typing"><i></i><i></i><i></i></div></div>':''}</div>
  ${CH.tray?chTrayH():''}
  <div class=chc><button class="iconbtn ${CH.tray?'on':''}" data-act=chtray title=Stickers>${ic('sticker')}</button><input type=text id=chin placeholder="Type a message" autocomplete=off value="${esc(CH.draft)}"><button class="btn pri" data-act=chsend>${ic('chat')} Send</button></div></div>`;
 const m=$('chm');m.scrollTop=m.scrollHeight;const i=$('chin');i.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ACT.chsend()}};i.focus();i.setSelectionRange(i.value.length,i.value.length);drawCol2()}
async function chPlay(id){const m=CH.msgs.find(x=>x.id===id&&x.from==='out');if(!m||m.kind!=='sticker'||!m.s||!m.s.id||!m.s.pack_id)return;
 const epoch=CH.epoch,token=(CH.requests[id]||0)+1;CH.requests[id]=token;
 delete CH.play[id];chDraw();
 let r;try{r=await api(`/api/packs/${encodeURIComponent(m.s.pack_id)}/stickers/${encodeURIComponent(m.s.id)}/particle-preview`)}catch(e){return}
 if(epoch!==CH.epoch||CH.requests[id]!==token||!CH.msgs.includes(m)||route_!=='chat'||!r.ok||!r.j.set||!r.j.url)return;
 const url=String(r.j.url),sep=url.includes('?')?'&':'?';CH.play[id]={set:r.j.set,url:url+sep+'echo='+encodeURIComponent(id+'-'+token)};chDraw();
 setTimeout(()=>{if(epoch===CH.epoch&&CH.requests[id]===token){delete CH.play[id];chDraw()}},3200)}
function chSend(m){const o={id:Date.now().toString(36)+'-'+(++CH.seq),t:Date.now(),from:'out',...m},epoch=CH.epoch;CH.msgs.push(o);chSave();chDraw();
 setTimeout(()=>{if(epoch!==CH.epoch||!CH.msgs.includes(o))return;CH.typing=true;chDraw()},450);
 setTimeout(()=>{if(epoch!==CH.epoch||!CH.msgs.includes(o))return;CH.typing=false;o.react=o.kind==='sticker'?'❤️':'👍';CH.msgs.push({...o,id:o.id+'e',reply_to:o.id,t:Date.now(),from:'in',react:undefined});chSave();chDraw();if(o.kind==='sticker')chPlay(o.id)},1500)}
RENDER.chat=async()=>{await loadLib();chDraw();if(CH.pending){const s=CH.pending;CH.pending=null;chSend({kind:'sticker',s:chSticker(s)})}};
ACT.chsend=()=>{const i=$('chin'),v=i.value.trim();if(!v)return;CH.draft='';i.value='';chSend({kind:'text',text:v})};
ACT.chtray=()=>{CH.tray=!CH.tray;chDraw()};ACT.chpack=el=>{CH.pk=el.dataset.id;chDraw()};
ACT.chpick=el=>{const p=packById(CH.pk),s=p&&p.stickers.find(x=>x.id===el.dataset.id);if(s)chSend({kind:'sticker',s:chSticker(s,p.id)})};
ACT.chreplay=el=>chPlay(el.dataset.id);
ACT.chview=()=>{CH.view=CH.view==='mobile'?'desktop':'mobile';try{localStorage.setItem('mirsal.chat.view',CH.view)}catch(e){}chDraw()};
function chClear(){CH.epoch++;CH.msgs=[];CH.play={};CH.requests={};CH.typing=false;CH.pending=null;chSave();chDraw()}
ACT.chclear=()=>confirmDlg('Clear this chat?',chClear);
