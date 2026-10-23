async page=>{
 const rows=[];
 const ratio=async el=>el.evaluate(e=>{const c=getComputedStyle(e);const lum=s=>{const v=s.match(/[\d.]+/g).slice(0,3).map(Number).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return v[0]*.2126+v[1]*.7152+v[2]*.0722};const a=lum(c.color),b=lum(c.backgroundColor);return {fg:c.color,bg:c.backgroundColor,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}});
 for(const w of [1440,390])for(const theme of ['dark','light']){
  await page.setViewportSize({width:w,height:900});await page.goto('http://127.0.0.1:8797/#/reactions');await page.evaluate(t=>thmSet(t),theme);
  await page.locator('#s-reactions [data-act=rxstyle][data-s=packs]').click();const tab=page.locator('#s-reactions [data-act=rxstyle][data-s=packs]');await tab.hover();await page.waitForTimeout(250);
  const v=await ratio(tab);rows.push({w,theme,...v});
 }
 if(rows.some(r=>r.ratio<4.5))throw Error('Hovered selected-tab contrast <4.5: '+JSON.stringify(rows));
 return rows;
}
