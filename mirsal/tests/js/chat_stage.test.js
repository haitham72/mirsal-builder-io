// plan.md Step 2: the stage pill's builder (pure half of agent.js). Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const U = require('../../mirsal/console/agent.js');

test('the closed pill shows the current stage and a caret, nothing else', () => {
  const h = U.stageHTML('emojis', false);
  assert.match(h, /data-act=agstage/);
  assert.match(h, />Emojis<i aria-hidden=true>▾<\/i>/);
  assert.match(h, /aria-expanded=false/);
  assert.doesNotMatch(h, /ag-stage-pop/);
});

test('the popover has four one-line choices and only the current one is checked', () => {
  const h = U.stageHTML('animation', true);
  assert.match(h, /aria-expanded=true/);
  const rows = h.match(/class="ag-stage-opt[^"]*"/g);
  assert.equal(rows.length, 4);
  assert.deepEqual([...h.matchAll(/data-v=(\w+)/g)].map(m => m[1]), ['prompt', 'emojis', 'animation', 'export']);
  assert.equal((h.match(/aria-checked=true/g) || []).length, 1);
  assert.match(h, /aria-checked=true class="ag-stage-opt on" data-act=agstagepick data-v=animation tabindex=0>/);
  assert.equal((h.match(/tabindex=0/g) || []).length, 1, 'arrows move inside; Tab leaves the menu');
  assert.match(h, /<b>Prompt<\/b><small>plan only, free<\/small>/);
  assert.match(h, /<b>Export<\/b><small>\+ pack and send<\/small>/);
  assert.equal((h.match(/✓/g) || []).length, 1);
});

test('an unknown stage reads as Emojis, and old creator switches migrate like the server', () => {
  assert.match(U.stageHTML('bogus', false), />Emojis</);
  assert.equal(U.stageOf({ stage: 'prompt' }), 'prompt');
  assert.equal(U.stageOf({}), 'emojis');
  assert.equal(U.stageOf(null), 'emojis');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'video' } }), 'export');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'images' } }), 'emojis');
  assert.equal(U.stageOf({ stage: 'emojis', creator: { on: true, scope: 'video' } }), 'emojis');
});
