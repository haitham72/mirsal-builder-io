// reactions.js: Reaction effects (#/reactions), the emoji bank ONLY (Haitham, 2026-10-14): the whole wall with Done / Not done, an emoji opens at its
// newest SAVED reaction, the start look for the rest, Presets ▾ (save, update, load, remove) filed by motion, Animation presets with a random preset
// of each emoji's own motion, batch create in the background (emoji-batches) and Export All | Selected.
// The whole file runs in a vm with the few globals it uses stubbed (console_vm.js), so the markup and the posts are checked for real. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConsole } = require('./console_vm');

const BANK = "[{token:'kiss',emoji:'😘',preset:'burst',motion:'hearts pop'},{token:'cry',emoji:'😭',preset:'rain',motion:'tears fall'},{token:'school',emoji:'🏫',preset:'burst',motion:''}]";
const MADE = "[{id:'L002',token:'cry',emoji:'😭',preset:'rain',params:{},settings:{magnitude:1.2,gravity:1,vortex:0,spin:1,count:20,spread:360,particle_size:0.5,size_var:0.2,size_in_dur:0,size_out_dur:0.4,hue_var:0},url:'/out/particles/emoji/cry/renders/L002.lottie.json',preview:'/x.webp',created:2}," +
  "{id:'L001',token:'kiss',emoji:'😘',preset:'vortex',params:{magnitude:2,size_in_dur:0.2,size_out_dur:0.6,hue_var:50,particle_size:2,size_min:0.05,size_max:0.15},url:'/out/particles/emoji/kiss/renders/L001.lottie.json',preview:null,created:1}]";
const START = { magnitude: 0.7, gravity: 1, vortex: 0, spin: 1, count: 28, spread: 360, particle_size: 0.3, size_var: 0.38, size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 25 };
const J = (r, code) => JSON.parse(r(`JSON.stringify(${code})`));
const screen = () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=${MADE};RXS.presets=[];globalThis.confirmDlg=(t,f)=>{globalThis.CONF=t;f()}`);
  return r;
};

test('the wall is every emoji, with Done / Not done, the count, and a dot on the done ones', () => {
  const r = screen();
  const h = r('rxHtml()');
  assert.match(h, /<b>2<\/b>\/3 done/);
  assert.equal((h.match(/class="rx-e/g) || []).length, 3, 'every bank emoji, no two-row clip');
  assert.equal((h.match(/class=rx-dot/g) || []).length, 2);
  r("RXQ.f='todo'");
  assert.deepEqual(J(r, 'rxList().map(m=>m.token)'), ['school']);
  r("RXQ.f='done'");
  assert.deepEqual(J(r, 'rxList().map(m=>m.token)'), ['kiss', 'cry']);
  assert.match(h, /data-act=rxzip data-w=all/);
  assert.doesNotMatch(h, /Your reactions/, 'the separate list of created reactions is gone');
});

test('an emoji opens at its newest saved reaction (Saved: v...), one never made at the start look', () => {
  const r = screen();
  r("ACT.rxpick({dataset:{t:'cry'}})");
  assert.equal(r('RXS.ek.ver'), 'L002');
  assert.deepEqual(J(r, 'rxSettings(RXS.ek)'), { magnitude: 1.2, gravity: 1, vortex: 0, spin: 1, count: 20, spread: 360, particle_size: 0.5, size_var: 0.2, size_in_dur: 0, size_out_dur: 0.4, hue_var: 0 });
  assert.match(r('rxEditor()'), /data-rxver[\s\S]*v1 ·/);
  r("ACT.rxpick({dataset:{t:'school'}})");
  assert.deepEqual(J(r, 'rxSettings(RXS.ek)'), START, 'the start look, the motion its own');
  r("ACT.rxpick({dataset:{t:'kiss'}})");
  const k = J(r, 'RXS.ek');
  assert.equal(k.preset, 'vortex', 'a reaction saved before settings were kept is read back from its params');
  assert.equal(k.sim.magnitude, 2);
  assert.equal(k.particle_size, 2);
});

test('Create reaction saves a new version and the editor stays on it; Reset goes back to the start look', async () => {
  const r = screen();
  r("ACT.rxpick({dataset:{t:'school'}});RXS.ek.sim.count=12");
  r("POSTREPLIES.push({ok:true,j:{id:'L001',token:'school',emoji:'🏫',preset:'burst',params:{},settings:{},url:'/s.json',preview:'/s.webp'}})");
  await r('ACT.rxcreate()');
  const [url, body] = J(r, 'POSTS.at(-1)');
  assert.equal(url, '/api/particles/emoji-lottie');
  assert.equal(body.count, 12);
  assert.equal(r('RXS.ek.ver'), 'L001');
  assert.equal(r("rxDone().has('school')"), true);
  r("ACT.rxreset({dataset:{g:'sim'}});ACT.rxreset({dataset:{g:'shape'}})");
  assert.deepEqual(J(r, 'rxSettings(RXS.ek)'), START);
});

test('Presets ▾: Save as new carries the emoji (its motion files it), Update changes the loaded one, Load puts its settings in the editor', async () => {
  const r = screen();
  r("ACT.rxpick({dataset:{t:'school'}})");
  const ed = r('rxEditor()');
  assert.match(ed, /data-act=rxcreate[^>]*>Create reaction<\/button>.*<span class=sp><\/span><details class="gh-more rx-pmenu">/s, 'Create left, Presets right');
  r("POSTREPLIES.push({ok:true,j:{id:'preset01',name:'Preset 01',motion:'burst',token:'school',settings:{count:9}}})");
  await r('ACT.rxsave()');
  assert.deepEqual(J(r, "POSTS.find(p=>p[0]==='/api/particles/emoji-presets')"), ['/api/particles/emoji-presets', { settings: START, token: 'school' }]);
  assert.equal(r('RXS.ek.presetId'), 'preset01');
  assert.match(r('rxEditor()'), /data-act=rxpupd data-id="preset01">Update “Preset 01”<\/button><button class="btn dng" data-act=rxpdel data-id="preset01">Remove “Preset 01”/);
  assert.match(r('rxEditor()'), /data-act=rxcreate[^>]*>Create reaction<\/button><span class=rx-chips><button class="btn sm rx-chip on" data-act=rxpload data-id="preset01"/, 'Create reaction | the presets as chips | Presets ▾');
  r("RXS.ek.sim.count=40;POSTREPLIES.push({ok:true,j:{id:'preset01',name:'Preset 01',motion:'burst',token:'school',settings:{count:40}}})");
  await r("ACT.rxpupd({dataset:{id:'preset01'}})");
  assert.ok(J(r, "POSTS.some(p=>p[0]==='/api/particles/emoji-presets/preset01')"), 'Update posts to the preset itself');
  r("ACT.rxpick({dataset:{t:'kiss'}});ACT.rxpload({dataset:{id:'preset01'}})");
  assert.equal(r('RXS.ek.sim.count'), 40);
  assert.equal(r('RXS.ek.token'), 'kiss');
});

test('Select: Shift-click ticks the range; Create N and the random presets run as one background batch', async () => {
  const r = screen();
  r("RXS.presets=[{id:'preset01',name:'Soft',motion:'burst',token:'kiss',settings:{}}];ACT.rxmulti()");
  r("ACT.rxpick({dataset:{t:'kiss'}},{});ACT.rxpick({dataset:{t:'school'}},{shiftKey:true})");
  assert.deepEqual(J(r, '[...RXS.sel]'), ['kiss', 'cry', 'school']);
  r("RXS.apply='*random';POSTREPLIES.push({ok:true,j:{id:'Babc',state:'running',total:3,done:0,made:[],errors:[]}})");
  await r('ACT.rxmany()');
  assert.deepEqual(J(r, 'POSTS.at(-1)'), ['/api/particles/emoji-batches', { tokens: ['kiss', 'cry', 'school'], mode: 'random' }]);
  assert.match(r('rxRunHtml()'), /Creating <b>0<\/b> of 3/);
  r("RXS.run=null;POSTREPLIES.push({ok:true,j:{id:'Bdef',state:'running',total:1,done:0,made:[],errors:[]}})");
  await r("ACT.rxbatch({dataset:{w:'todo',m:'random'}})");
  assert.deepEqual(J(r, 'POSTS.at(-1)'), ['/api/particles/emoji-batches', { mode: 'random', only_missing: true }]);
  assert.match(r('CONF'), /Create 1 reaction, each with a random preset of its own motion/);
});

test('the hover reaction is 64 px from the tile right edge, and plays the newest saved look of a done emoji', async () => {
  const r = screen();
  r("RXS.ek=null;RXS.hover='cry';const k=rxHovKey('cry');RXS.pv[k]='/r.webp';RXS.par[k]={origin:[0.5,0.1]}");
  const t = r("rxTile(rxRow('cry'))");
  assert.match(t, /class=rx-fx src="\/r.webp" style="width:64px;height:64px;left:calc\(90% - 32px\);top:calc\(90% - 6px\)"/,
    "the rain's origin (top centre) sits on the sticker's bottom-right, 90% / 90%, as Telegram plays it");
  assert.equal(J(r, "rxFor('cry')").magnitude, 1.2, 'its saved look, not the start look');
});

test('a pack sticker finds its predefined emoji (the longest match) and asks for the same fit preview as the bank hover', async () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=[{token:'heart',emoji:'❤️'},{token:'heart_on_fire',emoji:'❤️‍🔥'},{token:'laugh',emoji:'🤣'}];RXS.made=[];RXS.presets=[]`);
  assert.equal(r("rxTokenOf('🤣')"), 'laugh');
  assert.equal(r("rxTokenOf('❤️‍🔥')"), 'heart_on_fire', 'the longest bank emoji the glyph starts with');
  assert.equal(r("rxTokenOf('❤')"), 'heart', 'with or without the variation selector');
  assert.equal(r("rxTokenOf('🐪')"), '', 'not a predefined emoji: no reaction');
  r("POSTREPLIES.push({ok:true,j:{url:'/l.webp',params:{origin:[0.5,0.5]}}})");
  const pv = JSON.parse(await r("rxHovPreview('laugh').then(JSON.stringify)"));
  assert.equal(pv.url, '/l.webp');
  const [[url, body]] = J(r, 'POSTS');
  assert.equal(url, '/api/particles/emoji-preview');
  assert.equal(body.fit, true);
  assert.equal(r("RXS.pv[rxHovKey('laugh')]"), '/l.webp', 'one cache shared with the Reaction effects tiles');
});

test('the wall draws one page at a time (Load more), and Select all ticks the whole list without drawing it', () => {
  const r = loadConsole(['reactions.js']);
  r("RXS.bank=Array.from({length:250},(_,i)=>({token:'e'+i,emoji:'🙂',preset:'burst',motion:''}));RXS.made=[];RXS.presets=[]");
  const h = r('rxHtml()');
  assert.equal((h.match(/class="rx-e/g) || []).length, 120, 'one page, not 250');
  assert.match(h, /data-act=rxmore>Load more<\/button><small class=mut>120 of 250 shown · 130 more/);
  r('ACT.rxmore()');
  assert.equal(r('RXS.shown'), 240);
  r('RXS.multi=true;ACT.rxselall()');
  assert.equal(r('RXS.sel.size'), 250, 'every emoji of the list, drawn or not');
  r("RXQ.q='e1';ACT.rxfilter({dataset:{f:'all'}})");
  assert.equal(r('RXS.shown'), 120, 'a new search or filter starts at the first page again');
});
