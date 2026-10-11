// The stage control's builder (pure half of agent.js): a pill that opens a panel with the five-stop slider, the chat's models and the options.
// Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const U = require('../../mirsal/console/agent.js');

test('closed it is one pill: the current stop and a caret, no slider', () => {
  const h = U.stageHTML('emojis', false);
  assert.match(h, /data-act=agstage aria-haspopup=dialog aria-expanded=false[^>]*>Stickers<i aria-hidden=true>▾<\/i><\/button>$/);
  assert.doesNotMatch(h, /ag-stop|ag-slider|ag-stage-pop/, 'the slider is not on screen until the pill is clicked');
});

test('open, the panel holds the slider: five named stops, the current one checked, the ones before it filled', () => {
  const h = U.stageHTML('animation', true, { grid: '3x3', ask: true, bypass: false });
  assert.match(h, /aria-expanded=true/);
  assert.deepEqual([...h.matchAll(/class="ag-stop[^"]*" data-act=agstagepick data-v=(\w+)/g)].map(m => m[1]), ['prompt', 'emojis', 'animation', 'export', 'api']);
  assert.deepEqual([...h.matchAll(/<span>(\w+)<\/span><\/button>/g)].map(m => m[1]), ['Prompt', 'Stickers', 'Animation', 'Telegram', 'Export']);
  assert.equal((h.match(/aria-checked=true class="ag-stop/g) || []).length, 1);
  assert.match(h, /class="ag-stop on" data-act=agstagepick data-v=animation tabindex=0/);
  assert.match(h, /class="ag-stop done" data-act=agstagepick data-v=emojis/);
  assert.equal((h.match(/class="ag-stop[^"]*"[^>]*tabindex=0/g) || []).length, 1, 'arrows move along the slider; Tab leaves it');
  assert.match(h, /style="--k:2"/);
  assert.match(h, /<p class=sp-hint>Animation: \+ animation<\/p>/);
  assert.match(h, /data-act=agcr data-k=bypass role=switch aria-checked=false/, 'from Animation on: approve everything for me');
  assert.match(h, /data-act=agsetask role=switch aria-checked=true/);
  assert.match(h, /data-act=agsetgrid data-v=3x3 class="on"/);
  assert.match(U.stageHTML('api', true), /Export: \+ send to the API/);
});

test('the models: Default first, the chat\'s pick selected; video only from Animation on', () => {
  const models = { image: { list: [{ id: 'nano_banana_flash', label: 'Nano Banana 2' }, { id: 'nano_banana_pro', label: 'Nano Banana Pro' }], cur: 'nano_banana_pro', def: 'Nano Banana 2' },
    video: { list: [{ id: 'kling3', label: 'Kling 3.0' }], cur: '', def: 'Kling 3.0' }, ai: null };
  const still = U.stageHTML('emojis', true, { models });
  assert.match(still, /<select data-agm=image aria-label="Stickers model"><option value="">Default · Nano Banana 2<\/option><option value="nano_banana_flash">Nano Banana 2<\/option><option value="nano_banana_pro" selected>/);
  assert.doesNotMatch(still, /data-agm=video/, 'no video model before the Animation stage');
  assert.doesNotMatch(still, /data-agm=ai/, 'no chat model when the local server lists none');
  assert.doesNotMatch(still, /data-k=bypass/);
  const anim = U.stageHTML('animation', true, { models });
  assert.match(anim, /<select data-agm=video aria-label="Video model"><option value="" selected>Default · Kling 3.0<\/option>/);
});

test('an unknown stage reads as Stickers, and old creator switches migrate like the server', () => {
  assert.match(U.stageHTML('bogus', false), />Stickers<i aria-hidden=true>▾/);
  assert.equal(U.stageOf({ stage: 'prompt' }), 'prompt');
  assert.equal(U.stageOf({ stage: 'api' }), 'api');
  assert.equal(U.stageOf({}), 'emojis');
  assert.equal(U.stageOf(null), 'emojis');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'video' } }), 'export');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'images' } }), 'emojis');
  assert.equal(U.stageOf({ stage: 'emojis', creator: { on: true, scope: 'video' } }), 'emojis');
});
