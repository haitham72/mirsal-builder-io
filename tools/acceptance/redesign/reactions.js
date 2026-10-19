async page=>{
 const path='G:/Haitham/VsCode/Mirsal-Builder/docs/uiux_review/redesign-shots/';
 const rows=[],errors=[],bad=[],endpoints=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('response',r=>{if(r.status()>=400)bad.push({url:r.url(),status:r.status()})});
 const check=(x,m)=>{if(!x)throw Error(m)};
 for(const [route,key] of [['particles','sets'],['particles/bank','bank'],['particles/emoji-lottie','reactions'],['particles/lottie-reactions','files']]){
  const r=await page.request.get('http://127.0.0.1:8797/api/'+route),j=await r.json();endpoints.push({route,status:r.status(),count:(j[key]||[]).length});check(r.status()===200&&j[key].length>0,'empty endpoint '+route);
 }
 const ids=(await (await page.request.get('http://127.0.0.1:8797/api/particles')).json()).sets.map(x=>x.id).sort();
 for(const w of [1440,390])for(const theme of ['dark','light']){
  const row={w,theme,states:[]};
  try{
   await page.setViewportSize({width:w,height:900});
   await page.goto('http://127.0.0.1:8797/#/reactions');await page.evaluate(t=>{wlClose();thmSet(t)},theme);
   for(const tab of ['emoji','lottie','packs']){
    const state={tab};
    await page.locator(`#s-reactions [data-act=rxstyle][data-s=${tab}]`).click();
    await page.waitForTimeout(900);
    check(await page.locator(`#s-reactions [data-act=rxstyle][data-s=${tab}]`).getAttribute('aria-selected')==='true','Create selected');
    if(tab==='packs'){await page.waitForSelector('#s-reactions [data-ps]');check(JSON.stringify(await page.locator('#s-reactions [data-ps]').evaluateAll(es=>es.map(e=>e.dataset.ps).sort()))===JSON.stringify(ids),'Create Packs differs from server');}
    state.create=`reactions-${tab}-${w===390?'phone':'desktop'}-${theme}.png`;
    await page.screenshot({path:path+state.create});
    await page.goto('http://127.0.0.1:8797/#/library');
    await page.locator('[data-act=libtab][data-t=particles]').click();await page.waitForTimeout(900);
    const selected=page.locator(`#s-library [data-act=rxstyle][data-s=${tab}]`);
    check(await selected.getAttribute('aria-selected')==='true','Library lost shared tab');
    if(tab==='packs')check(JSON.stringify(await page.locator('#s-library [data-ps]').evaluateAll(es=>es.map(e=>e.dataset.ps).sort()))===JSON.stringify(ids),'Library Packs differs from server');
    state.library=`library-reactions-${tab}-${w===390?'phone':'desktop'}-${theme}.png`;
    await page.screenshot({path:path+state.library});
    // Keyboard activation on Library must update Create's selected tab too.
    const next=['emoji','lottie','packs'][(['emoji','lottie','packs'].indexOf(tab)+1)%3];
    await selected.focus();await page.keyboard.press('Tab');
    if(tab!=='packs')check(await page.evaluate(()=>document.activeElement.dataset.act)==='rxstyle','next tab not keyboard reachable');
    await page.locator(`#s-library [data-act=rxstyle][data-s=${next}]`).focus();await page.keyboard.press('Enter');
    await page.goto('http://127.0.0.1:8797/#/reactions');await page.waitForTimeout(500);
    check(await page.locator(`#s-reactions [data-act=rxstyle][data-s=${next}]`).getAttribute('aria-selected')==='true','Create lost Library keyboard change');
    state.bothWays=true;state.keyboard=true;row.states.push(state);
   }
   row.pass=true;
  }catch(e){row.pass=false;row.error=String(e)}
  rows.push(row);await page.evaluate(data=>localStorage.setItem('acceptance.reactions',JSON.stringify(data)),{rows,endpoints,errors,bad});
 }
 return {rows,endpoints,errors,bad};
}
