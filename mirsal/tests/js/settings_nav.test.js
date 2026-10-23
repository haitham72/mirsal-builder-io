const {readRawConsoleFile}=require('./console_source');
const {readConsoleFile,statement:consoleStatement}=require('./console_source');
// F-26/F-27 (T-072): the Settings bar is built from a registry and rebuilt
// after the render wrappers mount, so it only offers mounted cards: no dead
// Account shortcut off the LAN, and a Tickets shortcut where its card mounted.
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),vm=require('node:vm'),fs=require('node:fs');
const src=readConsoleFile(path.join(__dirname,'../../mirsal/console/settings.js'),'utf8');
function statement(marker){return consoleStatement(src,marker);}
function rig(present){
  const presentSet=new Set(present);
  const ctx=vm.createContext({
    document:{
      querySelector:()=>null,
      getElementById(id){return presentSet.has(id)?{id}:null;},
    },
  });
  // stub querySelector to return a mutable nav holder
  vm.runInContext('let __nav=null;document.querySelector=()=>__nav;',ctx);
  const run=s=>vm.runInContext(s,ctx);
  run(statement('let SET_SECTIONS='));
  run(statement('function setNavHtml('));
  run(statement('function setNavSync('));
  return run;
}

test('the registry holds every section including Tickets, with stable ids and actions',()=>{
  const run=rig([]);
  const html=run(`setNavHtml([['set-appear','Appearance'],['au-me','Account'],['tk-box','Tickets'],['trx-box','Trash']])`);
  assert.match(html,/<nav class="gseg set-nav" aria-label="Settings sections">/);
  for(const id of ['set-appear','au-me','tk-box','trx-box'])
    assert.match(html,new RegExp(`<button type=button data-act=setgo data-id=${id}>`));
  assert.match(src,/\['tk-box','Tickets'\]/,'Tickets is in the registry');
  assert.match(src,/ACT\.setgo=el=>/,'the section action is unchanged');
});

test('the bar keeps only mounted cards: LAN Account stays, local Account and foreign Tickets go',()=>{
  let run=rig(['set-appear','au-me','set-health','set-ai','set-tg','tk-box','trx-box']);
  run(`SET_SECTIONS=[['set-appear','A'],['au-me','Account'],['tk-box','Tickets'],['trx-box','Trash']];__nav={outerHTML:''};setNavSync();`);
  let html=run('__nav.outerHTML');
  assert.match(html,/data-id=au-me/,'LAN keeps Account');
  assert.match(html,/data-id=tk-box/,'mounted Tickets stays');
  run=rig(['set-appear','set-health','set-ai','set-tg','trx-box']);
  run(`SET_SECTIONS=[['set-appear','A'],['au-me','Account'],['tk-box','Tickets'],['trx-box','Trash']];__nav={outerHTML:''};setNavSync();`);
  html=run('__nav.outerHTML');
  assert.doesNotMatch(html,/data-id=au-me/,'no dead Account shortcut off the LAN');
  assert.doesNotMatch(html,/data-id=tk-box/,'no Tickets shortcut where its card never mounted');
  assert.match(html,/data-id=trx-box/,'Trash stays');
});

test('the auth, tickets and trash wrappers rebuild the bar after mounting',()=>{
  for(const f of ['auth.js','tickets.js','trash.js']){
    const s=readRawConsoleFile(path.join(__dirname,'../../mirsal/console',f),'utf8');
    assert.match(s,/if\(typeof setNavSync==='function'\)setNavSync\(\);/,`${f} rebuilds the bar`);
  }
});
