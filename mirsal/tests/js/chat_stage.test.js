// The stage slider's builder (pure half of agent.js): five stops, the current one named, details with the stops, the chat's models and the options.
// Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const U = require('../../mirsal/console/agent.js');

test('the closed slider has five stops, the current one checked and named, and a details button', () => {
  const h = U.stageHTML('emojis', false);
  assert.deepEqual([...h.matchAll(/class="ag-stop[^"]*" data-act=agstagepick data-v=(\w+)/g)].map(m => m[1]), ['prompt', 'emojis', 'animation', 'export', 'api']);
  assert.equal((h.match(/aria-checked=true/g) || []).length, 1);
  assert.match(h, /aria-checked=true class="ag-stop on" data-act=agstagepick data-v=emojis tabindex=0/);
  assert.equal((h.match(/tabindex=0/g) || []).length, 1, 'arrows move along the slider; Tab leaves it');
  assert.match(h, /class="ag-stop done" data-act=agstagepick data-v=prompt/, 'the stops before the current one are filled');
  assert.match(h, /<span class=ag-stage-lab>Stickers<\/span>/);
  assert.match(h, /style="--k:1"/);
  assert.match(h, /data-act=agstage aria-haspopup=dialog aria-expanded=false/);
  assert.doesNotMatch(h, /ag-stage-pop/);
});

test('the details list the five stops with what each does, and only the current one is checked', () => {
  const h = U.stageHTML('api', true, { grid: '3x3', ask: true, bypass: false });
  const pop = h.slice(h.indexOf('ag-stage-pop'));
  assert.deepEqual([...pop.matchAll(/class="ag-stage-opt[^"]*" data-act=agstagepick data-v=(\w+)/g)].map(m => m[1]), ['prompt', 'emojis', 'animation', 'export', 'api']);
  assert.match(pop, /<b>Telegram<\/b><small>\+ pack and Telegram<\/small>/);
  assert.match(pop, /<b>Export<\/b><small>\+ send to the API<\/small>/);
  assert.equal((pop.match(/✓/g) || []).length, 1);
  assert.match(pop, /data-act=agcr data-k=bypass role=switch aria-checked=false/, 'from Animation on: approve everything for me');
  assert.match(pop, /data-act=agsetask role=switch aria-checked=true/);
  assert.match(pop, /data-act=agsetgrid data-v=3x3 class="on"/);
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
  assert.match(U.stageHTML('bogus', false), /ag-stage-lab>Stickers</);
  assert.equal(U.stageOf({ stage: 'prompt' }), 'prompt');
  assert.equal(U.stageOf({ stage: 'api' }), 'api');
  assert.equal(U.stageOf({}), 'emojis');
  assert.equal(U.stageOf(null), 'emojis');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'video' } }), 'export');
  assert.equal(U.stageOf({ creator: { on: true, scope: 'images' } }), 'emojis');
  assert.equal(U.stageOf({ stage: 'emojis', creator: { on: true, scope: 'video' } }), 'emojis');
});
