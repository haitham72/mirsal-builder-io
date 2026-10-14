const {readConsoleFile,statement:consoleStatement}=require('./console_source');
// F-01 (T-001): Keep approved size is a staged preview until Apply. Only one
// ACT.gkeepsize definition may exist: the staged one that flips VZ.keep and
// re-cuts on the fly (vzPreview), with no keep_size/video_size POST. Apply
// (ACT.vzapply) sends the stored change once; Cancel (ACT.vzcancel) sends none.
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const src=readConsoleFile(path.join(__dirname,'../../mirsal/console/studio-core.js'),'utf8');
function statement(marker){return consoleStatement(src,marker);}

test('exactly one Keep approved size handler exists, and it stages instead of storing',()=>{
  const defs=src.match(/ACT\.gkeepsize\s*=/g)||[];
  assert.equal(defs.length,1,'the late immediate POST assignment is gone; the staged one stays');
  const h=statement('ACT.gkeepsize=');
  assert.match(h,/VZ\.keep\s*=\s*!vzKeep\(g\)/,'click flips the staged keep flag');
  assert.match(h,/vzPreview\(\)/,'click re-cuts the one test sticker on the fly');
  assert.doesNotMatch(h,/post\s*\(/,'no stored POST before Apply (reading g.keep_size to compare is fine)');
});

test('Apply sends the staged change once; Cancel sends nothing',()=>{
  const apply=statement('ACT.vzapply=');
  assert.match(apply,/vzSend\(g,/,'Apply goes through the single send path');
  const cancel=statement('ACT.vzcancel=');
  assert.match(cancel,/vzClear\(\)/,'Cancel drops the staged preview');
  assert.doesNotMatch(cancel,/post\(/,'Cancel makes zero mutation calls');
});
