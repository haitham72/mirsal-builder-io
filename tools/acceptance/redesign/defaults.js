async page=>{
 await page.evaluate(()=>localStorage.removeItem('mirsal.live'));
 await page.reload();await page.goto('http://127.0.0.1:8797/#/studio');
 const studio=await page.evaluate(()=>cpGrid());
 const p=await page.request.post('http://127.0.0.1:8797/api/plan',{data:{prompt:'generic emojis',ai:false}});const plan=await p.json();
 const c=await page.request.post('http://127.0.0.1:8797/api/chat/sessions',{data:{title:'2x2 default acceptance'}});const chat=await c.json();
 const old=[];for(const n of [146,156]){const g=await (await page.request.get(`http://127.0.0.1:8797/api/generations/${n}`)).json();old.push({n,grid:g.grid,cells:g.stickers.length})}
 if(studio!=='2x2'||chat.settings.grid!=='2x2'||plan.stickers.length!==4||plan.grid.join('x')!=='2x2'||old.some(g=>g.cells!==9))throw Error('default/preservation regression');
 return {studio,chat:chat.settings.grid,planGrid:plan.grid,cells:plan.stickers.length,videoTemplate:plan.slots.video_template,spatialLines:plan.video_prompt.split('\n').filter(s=>s.includes('): State:')),old};
}
