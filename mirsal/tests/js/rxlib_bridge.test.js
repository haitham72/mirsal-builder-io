// The bridge between Reaction effects (#/reactions) and the Sticker Library's Reactions tab (Haitham, 2026-10-15:
// the two screens looked completely different and disconnected). Runs in the console vm (console_vm.js). Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConsole } = require('./console_vm');

test('#/reactions links to Library Reactions and lands on its tab', () => {
  const r = loadConsole(['reactions.js', 'lottiestyle.js'], { extra: 'var LIBTAB="recent";var location={hash:""};' });
  assert.match(r('rxStyleBar()'), /data-act=rxgolib/, 'the style bar carries the bridge');
  r('ACT.rxgolib()');
  assert.equal(r('LIBTAB'), 'particles');
  assert.equal(r('location.hash'), '#/library');
});

test('Library Reactions lists the reactions made in Reaction effects and links back', () => {
  const run = loadConsole(['effects.js', 'particles.js'], { studio: true });
  run("SPL.sets=[];SPL.made=[{id:'L001',token:'kiss',emoji:'😘',preset:'burst_01',url:'/out/particles/emoji/kiss/renders/L001.lottie.json',preview:'/out/particles/emoji/kiss/renders/L001.webp'}]");
  const h = run('spLibHtml()');
  assert.match(h, /Made in Reaction effects/, 'the created section shows');
  assert.match(h, /L001\.lottie\.json/, 'the download goes to the stored file');
  assert.match(h, /href="#\/reactions"/, 'and back');
  assert.match(run('spLibHead()'), /href="#\/reactions"/, 'the header links too');
});

test('an empty library still shows the made section once it loads', () => {
  const run = loadConsole(['effects.js', 'particles.js'], { studio: true });
  run('SPL.sets=[];SPL.made=[]');
  assert.match(run('spLibHtml()'), /none yet/, 'no sets but the bridge is visible');
});
