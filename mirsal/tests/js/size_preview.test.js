const {readConsoleFile,statement:consoleStatement}=require('./console_source');
// Motion size (Resize box + frame editor, built 2026-10-15; T-001 Keep approved size
// is retired): the Resize toggle and the Size stepper stage into a one-frame test
// preview (vzPreview, GET anim_preview); Apply sends the stored change once;
// Cancel sends nothing. Run: node --test tests/js
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const src=readConsoleFile(path.join(__dirname,'../../mirsal/console/studio-core.js'),'utf8');
function statement(marker){return consoleStatement(src,marker);}

test('the Resize toggle stages into the one-frame preview, never a stored POST',()=>{
  const h=statement('ACT.gresize=');
  assert.match(h,/VZ\.resize\s*=/,'click flips the staged resize flag');
  assert.match(h,/vzPreview\(\)/,'click re-cuts the one test frame on the fly');
  assert.doesNotMatch(h,/post\s*\(/,'no stored POST before Apply');
});

test('the batch Size stepper stages too; Apply sends video_size once',()=>{
  const size=statement('ACT.gvsize=');
  assert.match(size,/VZ\.scale\s*=/,'click stages the scale');
  assert.doesNotMatch(size,/post\s*\(/,'no stored POST before Apply');
  const apply=statement('ACT.vzapply=');
  assert.match(apply,/\/video_size/,'Apply stores the batch size');
});

test('the sticker editor Applies one position POST with offset and scale; Cancel sends nothing',()=>{
  const apply=statement('ACT.vzapply=');
  assert.match(apply,/\/position/,'Apply stores position');
  assert.match(apply,/offset/,'with the offset');
  assert.match(apply,/scale/,'with the scale');
  const cancel=statement('ACT.vzcancel=');
  assert.match(cancel,/vzClear\(\)/,'Cancel drops the staged preview');
  assert.doesNotMatch(cancel,/post\s*\(/,'Cancel makes zero mutation calls');
});
