async page=>{
 const rows=[],responses=[];
 page.on('response',r=>{if(r.request().method()==='POST'&&r.url().endsWith('/position'))responses.push({status:r.status(),body:r.request().postDataJSON(),url:r.url()})});
 const idle=async()=>{for(let i=0;i<180;i++){if(!(await (await page.request.get('http://127.0.0.1:8797/api/generations')).json()).busy)return;await page.waitForTimeout(500)}throw Error('writer still busy')};
 for(const g of [146,156])for(const w of [1440,390])for(const theme of ['dark','light']){
  const row={g,w,theme};try{
   await idle();await page.setViewportSize({width:w,height:900});
   await page.goto('http://127.0.0.1:8797/#/studio');
   await page.evaluate(async({g,theme})=>{thmSet(theme);await histReload();ACT.hopen({dataset:{id:String(g)}});GS.tab='anim';glast='';await tick(true)},{g,theme});await page.waitForTimeout(700);
   const a=page.locator(`[data-act=vslopen][data-g="${g}"][data-i="1"]`);if(await a.getAttribute('aria-expanded')!=='true')await a.click();
   const input=page.locator(`.vsl[data-g="${g}"][data-i="1"] input[data-k=dx]`);await input.evaluate(e=>e.scrollIntoView({behavior:'instant',block:'center'}));
   const from=responses.length;
   await input.focus();await page.keyboard.press('ArrowRight');
   await page.waitForFunction(()=>vslBusy.size===0&&Object.keys(vslPend).length===0,{},{timeout:30000});
   await input.focus();await page.keyboard.press('ArrowRight');
   await page.waitForFunction(()=>vslBusy.size===0&&Object.keys(vslT).every(k=>!vslBusy.has(k)),{},{timeout:30000});
   await page.waitForTimeout(15000);
   row.responses=responses.slice(from);row.busyRetries=row.responses.filter(r=>r.status===409).length;
   row.pass=row.busyRetries>0&&row.responses.filter(r=>r.status===200).length>0;
  }catch(e){row.pass=false;row.error=String(e)}rows.push(row);await page.evaluate(rows=>localStorage.setItem('acceptance.retry',JSON.stringify(rows)),rows);
 }
 return {rows};
}
