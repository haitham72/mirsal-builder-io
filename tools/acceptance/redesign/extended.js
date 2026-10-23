async page=>{
 const path='G:/Haitham/VsCode/Mirsal-Builder/docs/uiux_review/redesign-shots/';
 const rows=[],errors=[],bad=[];const check=(x,m)=>{if(!x)throw Error(m)};
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('/position'))bad.push({url:r.url(),status:r.status()})});
 for(const w of [1440])for(const theme of ['dark']){
  const row={w,theme,opened:[],hovered:0};try{
   await page.setViewportSize({width:w,height:900});
   // Delay the real response, leave its route while in flight, then return.
   await page.goto('http://127.0.0.1:8797/#/reactions');await page.evaluate(t=>{wlClose();thmSet(t)},theme);
   await page.locator('#s-reactions [data-act=rxstyle][data-s=packs]').click();
   await page.waitForFunction(()=>!SPL.busy);
   let delayed=false;
   await page.route('**/api/particles',async route=>{if(route.request().method()!=='GET')return route.continue();delayed=true;const response=await route.fetch();await new Promise(r=>setTimeout(r,1800));await route.fulfill({response})});
   await page.evaluate(()=>{SPL.sets=null;spLibSync(true)});
   await page.waitForTimeout(150);await page.goto('http://127.0.0.1:8797/#/home');await page.waitForTimeout(2200);
   await page.goto('http://127.0.0.1:8797/#/reactions');await page.waitForSelector('#s-reactions [data-ps]');
   check(delayed,'delay did not engage');check(await page.evaluate(()=>!SPL.busy&&RXS.tab==='packs'),'stuck loading or lost tab');row.offRoute=true;
   await page.unroute('**/api/particles');
   await page.locator('#s-reactions [data-act=psopen]').first().click();row.opened.push('Packs set detail');
   const menu=page.locator('#s-reactions details.gh-more summary').first();await menu.click();row.opened.push('Packs set options');await menu.click();
   await page.locator('#s-reactions [data-act=rxstyle][data-s=emoji]').click();
   for(const motion of ['burst','fountain','vortex','rain','confetti']){
    const btn=page.locator(`#s-reactions [data-act=rxmotion][data-m=${motion}]`);if(await btn.getAttribute('aria-expanded')!=='true')await btn.click();row.opened.push('Emoji '+motion);
   }
   const cards=page.locator('#s-reactions [data-act=rxpopen]');const n=await cards.count();
   for(let i=0;i<n;i++){await cards.nth(i).hover();row.hovered++}
   await cards.first().click();const adv=page.locator('#s-reactions [data-rxadvanced]');await adv.locator('summary').click();
   check(await adv.evaluate(e=>e.open),'advanced did not open');row.opened.push('Emoji Motion / Size / Advanced');
   await page.locator('#s-reactions [data-rxed]').evaluate(e=>e.scrollIntoView({behavior:'instant',block:'start'}));
   await page.screenshot({path:path+`extended-emoji-${w}-${theme}.png`});
   await page.locator('#s-reactions [data-act=rxstyle][data-s=lottie]').click();await page.waitForSelector('#s-reactions [data-act=lspick]');
   const files=page.locator('#s-reactions [data-act=lspick]');const count=await files.count();
   for(let i=0;i<count;i++){await files.nth(i).hover();row.hovered++;await files.nth(i).click();await page.waitForSelector('#s-reactions [data-lsed]');row.opened.push('Lottie file '+i)}
   for(const name of ['Emitter','Particle','Physics','Morph','Aux system']){const d=page.locator(`#s-reactions [data-lsg="${name}"]`);if(!await d.evaluate(e=>e.open))await d.locator('summary').click();row.opened.push('Lottie '+name)}
   await page.screenshot({path:path+`extended-lottie-${w}-${theme}.png`});
   // A long pre-existing synthetic session respects the no-real-chat-copy rule.
   await page.goto('http://127.0.0.1:8797/#/agent/S001');await page.waitForSelector('#ai-msgs');
   const sc=page.locator('#ai-scroll');await sc.evaluate(e=>e.scrollTop=e.scrollHeight*.35);
   const before=await sc.evaluate(e=>({top:e.scrollTop,height:e.scrollHeight,count:document.querySelector('#ai-msgs').children.length}));
   await page.waitForTimeout(3500);
   const after=await sc.evaluate(e=>({top:e.scrollTop,height:e.scrollHeight,count:document.querySelector('#ai-msgs').children.length}));
   check(before.count>=400,'history fixture not loaded');check(Math.abs(before.top-after.top)<3,'poll moved history scroll');check(before.count===after.count,'poll duplicated messages');row.history={before,after};
   await page.screenshot({path:path+`extended-chat-${w}-${theme}.png`});row.pass=true;
  }catch(e){row.pass=false;row.error=String(e)}
  rows.push(row);await page.evaluate(data=>localStorage.setItem('acceptance.extended',JSON.stringify(data)),{rows,errors,bad});
 }
 return {rows,errors,bad};
}
