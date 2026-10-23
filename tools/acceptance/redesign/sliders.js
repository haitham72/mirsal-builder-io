async page => {
 const path = 'G:/Haitham/VsCode/Mirsal-Builder/docs/uiux_review/redesign-shots/';
 const rows=[]; const requests=[]; const responses=[]; const errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>{if(r.method()==='POST'&&/\/(position|video_size)$/.test(r.url()))requests.push({url:r.url(),body:r.postDataJSON(),time:Date.now()})});
 page.on('response',r=>{if(/\/(position|video_size)$/.test(r.url()))responses.push({url:r.url(),status:r.status()})});
 const check=(x,m)=>{if(!x)throw new Error(m)};
 const idle=async()=>{await page.waitForFunction(()=>vslBusy.size===0);for(let i=0;i<180;i++){const r=await page.request.get('http://127.0.0.1:8797/api/generations');if(!(await r.json()).busy)break;await page.waitForTimeout(500)}await page.waitForTimeout(800)};
 for(const g of [146,156])for(const w of [1440,390])for(const theme of ['dark','light']){
  const row={g,w,theme}; let start,rs;
  try {
   await page.setViewportSize({width:w,height:900});
   await idle();
   await page.evaluate(async ({g,theme})=>{wlClose();thmSet(theme);await histReload();ACT.hopen({dataset:{id:String(g)}});GS.tab='anim';glast='';await tick(true)}, {g,theme});
   const adjust=page.locator(`[data-act=vslopen][data-g="${g}"][data-i="1"]`);
   await adjust.waitFor(); if(await adjust.getAttribute('aria-expanded')!=='true')await adjust.click();
   const selector=`.vsl[data-g="${g}"][data-i="1"] input[data-k=dx]`;
   let input=page.locator(selector); await page.waitForTimeout(800);await input.evaluate(e=>e.scrollIntoView({behavior:'instant',block:'center'}));
   start=requests.length;rs=responses.length;
   // Native pointer drag: readout changes before release, then force a poll redraw.
   const b=await input.boundingBox(); const before=await input.inputValue();
   const x=b.x+b.width*.63,y=b.y+b.height/2;
   const current=+before;const thumb=b.x+8+(b.width-16)*(current+50)/100;
   await page.mouse.move(thumb,y);await page.mouse.down();await page.mouse.move(x,y,{steps:8});
   const during=await input.inputValue();row.dragReadout=await input.locator('..').locator('b').innerText();check(during!==before,'drag did not change value');
   check(row.dragReadout.includes(during.replace(/^0$/,'0')),'readout mismatch');
   check(requests.length===start,'POST before release');
   await page.evaluate(async()=>{glast='';await tick(true)});
   input=page.locator(selector);check(await input.inputValue()===during,'pending lost during redraw');row.pendingRedraw=true;
   await page.mouse.up();
   await page.waitForFunction(()=>Object.keys(vslPend).length===0&&vslBusy.size===0,{},{timeout:30000});await idle();
   const first=requests.slice(start);check(first.filter(r=>r.body.reslice).length===1,'release must request one cut');row.releaseCuts=1;
   const count=requests.length;await input.dispatchEvent('change');await page.waitForTimeout(700);check(requests.length===count,'untouched release posted');row.untouchedPosts=0;
   row.shot=`slider-G${g}-${w===390?'phone':'desktop'}-${theme}.png`;
   await input.evaluate(e=>e.scrollIntoView({behavior:'instant',block:'center'}));await page.screenshot({path:path+row.shot});
   const reset=page.locator(`[data-act=vslreset][data-g="${g}"][data-i="1"]`);
   const resetStart=requests.length;await reset.click();await idle();
   const resets=requests.slice(resetStart);check(resets.length===2,'reset request count');
   check(resets[0].url.endsWith('/position')&&resets[0].body.offset===null&&resets[0].body.reslice===false,'reset position contract');
   check(resets[1].url.endsWith('/video_size')&&resets[1].body.scale===null&&resets[1].body.reslice===true,'reset scale contract');row.resetCuts=1;
   row.frameEditor=await page.locator(`[data-act=vzedit][data-g="${g}"]`).count();check(row.frameEditor>0,'frame editor missing');
   row.responses=responses.slice(rs);row.pass=true;
  }catch(e){row.pass=false;row.error=String(e);await page.screenshot({path:path+`failure-G${g}-${w}-${theme}.png`});}
  rows.push(row);await page.evaluate(data=>{window.__slider=data;localStorage.setItem('acceptance.sliders',JSON.stringify(data))},{rows,errors,requests,responses});
 }
 return {rows,errors};
}
