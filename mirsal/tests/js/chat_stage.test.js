// The stage control's builder (pure half of agent.js): a pill that opens a panel with the five-stop slider, the chat's models and the options.
// Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const U = require('../../mirsal/console/agent.js');

test('closed it is one pill: a small slider glyph, the current stop and a caret, no slider', () => {
  const h = U.stageHTML('emojis', false);
  assert.match(h, /data-act=agstage aria-haspopup=dialog aria-expanded=false[^>]*><span class=ag-mini aria-hidden=true style="--k:1"><\/span>Stickers<i aria-hidden=true>▾<\/i><\/button>$/);
  assert.doesNotMatch(h, /ag-range|ag-slider|ag-stage-pop/, 'the slider is not on screen until the pill is clicked');
});

test('open, the panel holds a real slider: a range over the five stops, their names under it, what the chosen one does', () => {
  const h = U.stageHTML('animation', true, { grid: '3x3', ask: true, bypass: false, actions: 'predefined' });
  assert.match(h, /aria-expanded=true/);
  assert.match(h, /<input type=range class=ag-range data-agrange min=0 max=4 step=1 value=2 aria-label="How far a new request goes" aria-valuetext="Animation">/);
  assert.equal((h.match(/<i class="on"><\/i>/g) || []).length, 3, 'the ticks up to the thumb are filled');
  assert.deepEqual([...h.matchAll(/class="ag-stop[^"]*" data-act=agstagepick data-v=(\w+)[^>]*>(\w+)</g)].map(m => m[1] + ':' + m[2]),
    ['prompt:Prompt', 'emojis:Stickers', 'animation:Animation', 'export:Telegram', 'api:Export']);
  assert.match(h, /class="ag-stop on" data-act=agstagepick data-v=animation/);
  assert.match(h, /<p class=sp-hint>Animation: \+ animation<\/p>/);
  assert.match(h, /data-act=agsetact data-v=predefined class="on">Predefined/, 'Creative or Predefined: where the stickers come from');
  assert.match(h, /data-act=agcr data-k=bypass role=switch aria-checked=false/, 'from Animation on: approve everything for me');
  assert.match(h, /data-act=agsetask role=switch aria-checked=true/);
  assert.match(h, /data-act=agsetgrid data-v=3x3 class="on"/);
  assert.match(U.stageHTML('api', true), /Export: \+ send to the API/);
  assert.match(U.stageHTML('emojis', true), /data-act=agsetact data-v=creative class="on">Creative/, 'creative by default');
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
