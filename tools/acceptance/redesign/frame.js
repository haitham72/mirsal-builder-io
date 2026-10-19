async page=>{
 const rows=[],writes=[];page.on('request',r=>{if(r.method()==='POST'&&/\/(position|video_size)$/.test(r.url()))writes.push(r.url())});
 for(const w of [1440,390])for(const theme of ['dark','light']){
  const row={w,theme};try{
   await page.setViewportSize({width:w,height:900});await page.goto('http://127.0.0.1:8797/#/studio');
   await page.evaluate(async theme=>{thmSet(theme);await histReload();ACT.hopen({dataset:{id:'146'}});GS.tab='anim';glast='';await tick(true)},theme);await page.waitForTimeout(800);
   const button=page.locator('[data-act=vzedit][data-g="146"][data-i="1"]');await button.evaluate(e=>e.scrollIntoView({behavior:'instant',block:'center'}));await button.click();
   await page.waitForFunction(()=>VZ.meta&&document.querySelector('#vzcard img').complete);
   await page.locator('#vzcard input[aria-label=Frame]').focus();await page.keyboard.press('ArrowRight');
   await page.locator('#vzcard [data-act=vzgrid]').click();await page.waitForTimeout(400);
   const box=await page.locator('#vzcard').boundingBox();row.bounds=box;row.inViewport=box.x>=0&&box.y>=0&&box.x+box.width<=w+1&&box.y+box.height<=901;
   row.frame=await page.locator('#vzcard .vzframe small').innerText();
   await page.screenshot({path:`G:/Haitham/VsCode/Mirsal-Builder/docs/uiux_review/redesign-shots/frame-${w}-${theme}.png`});
   const before=writes.length;await page.locator('#vzcard [data-act=vzcancel]').click();row.cancelPosts=writes.length-before;
   row.pass=row.inViewport&&row.cancelPosts===0;
  }catch(e){row.pass=false;row.error=String(e)}rows.push(row);
 }return rows;
}
