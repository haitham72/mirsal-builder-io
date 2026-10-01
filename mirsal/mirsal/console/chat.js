/* Chat (desktop): a local echo contact. Send a sticker (or text), it is echoed back and your message gets liked.
   Messages live in this browser (localStorage) until Phase 5 puts a real Mirsal chat backend behind the same UI. */
'use strict';
const CH={msgs:[],tray:false,pk:null,typing:false,draft:'',pending:null};
try{CH.msgs=JSON.parse(localStorage.getItem('mirsal.chat')||'[]')}catch(e){}
const chSave=()=>{try{localStorage.setItem('mirsal.chat',JSON.stringify(CH.msgs.slice(-200)))}catch(e){}};
const hm=t=>new Date(t).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
const chPreview=m=>!m?'No messages yet':m.kind==='sticker'?'Sticker':esc(m.text);
function chList(){const m=CH.msgs[CH.msgs.length-1];
 $('col2').innerHTML=`<div class=c2h><h1>Chats</h1></div><div class=c2s><input type=search placeholder="Search chats…" disabled></div>
  <div class=c2l><div class="crow on"><div class="cv chav">M</div><div style="min-width:0"><b>Mirsal Echo</b><small>${m&&m.from==='out'?'You: ':''}${chPreview(m)}</small></div><span class=meta>${m?hm(m.t):''}</span></div></div>`}
const chMsgH=m=>{const t=`<span class=tm>${hm(m.t)}${m.from==='out'?' ✓✓':''}</span>`;
 return m.kind==='sticker'?`<div class="cm c${m.from}"><div class="bub stk">${media(m.s)}${m.react?`<span class=react>${m.react}</span>`:''}${t}</div></div>`
  :`<div class="cm c${m.from}"><div class=bub>${esc(m.text)}${m.react?`<span class=react>${m.react}</span>`:''}${t}</div></div>`};
function chTrayH(){const ps=LIB.packs.filter(p=>p.stickers.length);if(!ps.length)return`<div class=chtray><span class=mut>No stickers yet.</span> <button class="btn sm" data-act=nav data-to=create>${ic('create')} Create one</button></div>`;
 const cur=ps.find(p=>p.id===CH.pk)||ps[0];CH.pk=cur.id;
 return`<div class=chtray><div class=tabs style="margin:0 0 8px">${ps.map(p=>`<button class="tab ${p.id===cur.id?'on':''}" data-act=chpack data-id=${p.id}>${esc(p.name)}</button>`).join('')}</div>
  <div class=trgrid>${cur.stickers.map(s=>`<div class=trs data-act=chpick data-id=${s.id} title="${esc(s.name)}">${media(s)}</div>`).join('')}</div></div>`}
function chDraw(){if(route_!=='chat')return;const el=$('s-chat'),inp=$('chin');if(inp)CH.draft=inp.value;
 el.innerHTML=`<div class=chat><div class=chh><div class="cv chav">M</div><div style="flex:1"><b>Mirsal Echo</b><small>${CH.typing?'typing…':'online'}</small></div><button class=iconbtn data-act=chclear title="Clear chat">${ic('trash')}</button></div>
  <div class=chm id=chm>${CH.msgs.map(chMsgH).join('')||'<div class="mut chempty">Say hi or send a sticker. It comes back to you and your message gets a like.</div>'}${CH.typing?'<div class="cm in"><div class="bub typing"><i></i><i></i><i></i></div></div>':''}</div>
  ${CH.tray?chTrayH():''}
  <div class=chc><button class="iconbtn ${CH.tray?'on':''}" data-act=chtray title=Stickers>${ic('sticker')}</button><input type=text id=chin placeholder="Type a message" autocomplete=off value="${esc(CH.draft)}"><button class="btn pri" data-act=chsend>${ic('chat')} Send</button></div></div>`;
 const m=$('chm');m.scrollTop=m.scrollHeight;const i=$('chin');i.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ACT.chsend()}};i.focus();i.setSelectionRange(i.value.length,i.value.length);drawCol2()}
function chSend(m){const o={id:Date.now().toString(36),t:Date.now(),from:'out',...m};CH.msgs.push(o);chSave();chDraw();
 setTimeout(()=>{CH.typing=true;chDraw()},450);
 setTimeout(()=>{CH.typing=false;o.react=o.kind==='sticker'?'❤️':'👍';CH.msgs.push({...o,id:o.id+'e',t:Date.now(),from:'in',react:undefined});chSave();chDraw()},1500)}
RENDER.chat=async()=>{await loadLib();chDraw();if(CH.pending){const s=CH.pending;CH.pending=null;chSend({kind:'sticker',s:{type:s.type,file:s.file,name:s.name}})}};
ACT.chsend=()=>{const i=$('chin'),v=i.value.trim();if(!v)return;CH.draft='';i.value='';chSend({kind:'text',text:v})};
ACT.chtray=()=>{CH.tray=!CH.tray;chDraw()};ACT.chpack=el=>{CH.pk=el.dataset.id;chDraw()};
ACT.chpick=el=>{const s=packById(CH.pk).stickers.find(x=>x.id===el.dataset.id);chSend({kind:'sticker',s:{type:s.type,file:s.file,name:s.name}})};
ACT.chclear=()=>confirmDlg('Clear this chat?',()=>{CH.msgs=[];chSave();chDraw()});
