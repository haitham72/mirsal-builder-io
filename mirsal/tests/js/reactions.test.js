// reactions.js: Reaction effects (#/reactions), the emoji bank ONLY. Search + two rows of small emojis, the picked one in one editor card, then only the created reactions as cards.
// The whole file runs in a vm with the few globals it uses stubbed (console_vm.js), so the markup and the posts are checked for real. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConsole } = require('./console_vm');

const BANK = "[{token:'kiss',emoji:'😘',preset:'burst',motion:'hearts pop'},{token:'cry',emoji:'😭',preset:'rain',motion:'tears fall'},{token:'school',emoji:'🏫',preset:'burst',motion:''}]";
const MADE = "[{id:'L002',token:'cry',emoji:'😭',preset:'rain',params:{size_in_dur:0,size_out_dur:0.4,hue_var:0},url:'/out/particles/emoji/cry/renders/L002.lottie.json',preview:'/out/particles/emoji/cry/renders/L002.webp'}," +
  "{id:'L001',token:'kiss',emoji:'😘',preset:'vortex',params:{size_in_dur:0.2,size_out_dur:0.6,hue_var:50,particle_size:2,size_min:0.05,size_max:0.15},url:'/out/particles/emoji/kiss/renders/L001.lottie.json',preview:null}]";
const J = (r, code) => JSON.parse(r(`JSON.stringify(${code})`));

test('the screen: search, small emojis only, no thumbnail cards of the bank, and only the created reactions as cards', () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=${MADE}`);
  const h = r('rxHtml()');
  assert.match(h, /data-rxq placeholder="Search 3 emoji"/);
  assert.equal((h.match(/class="rx-e/g) || []).length, 3, 'one small tile per emoji');
  assert.doesNotMatch(h.split('rx-made')[0], /<img|<video|<b>kiss<\/b>|burst/, 'the emoji rows are glyphs only: no names, no presets, nothing playing');
  assert.equal((h.match(/<article class=rx-card /g) || []).length, 2, 'one card per created reaction');
  assert.match(h, /Your reactions <small class=mut>2<\/small>/);
  assert.match(h, /<img src="\/out\/particles\/emoji\/cry\/renders\/L002.webp"/, 'a card plays its own loop');
  assert.match(h, /data-act=rxdl data-u="\/out\/particles\/emoji\/kiss\/renders\/L001.lottie.json" data-n="kiss L001"/);
  assert.match(h, /data-act=rxedit data-t="cry" data-id="L002"/);
  assert.doesNotMatch(h, /pack|sticker|Kling|Generate more|data-rxed/i, 'no pack, sticker or Kling; no editor until an emoji is picked');
  r('RXS.made=[]');
  assert.match(r('rxHtml()'), /Nothing created yet: pick an emoji above\./);
  r('RXQ.q="tear"');
  assert.deepEqual(J(r, 'rxList().map(m=>m.token)'), ['cry'], 'search reads the token, the glyph and the motion sentence');
  r('RXQ.q=""');
  assert.equal(r('RXN'), 48, 'never the whole bank: a few rows of tiles, two shown');
});

test('picking opens ONE editor card with honest defaults, and Create posts the token and the options, then shows its card', async () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=[]`);
  r("POSTREPLIES.push({ok:true,j:{url:'/out/particles/emoji/kiss/previews/a-256.webp'}})");
  await r("ACT.rxpick({dataset:{t:'kiss'}})");
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-preview', { token: 'kiss', particle_size: 1, size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 25, size: 256 }]],
    'Size variation is left out: the motion keeps its own range until the person moves it');
  const h = r('rxHtml()');
  assert.match(h, /data-rxed/);
  assert.match(h, /src="\/out\/particles\/emoji\/kiss\/previews\/a-256.webp"/, 'the reaction plays in the editor');
  assert.match(h, /<option value="" selected>its own · burst<\/option>/);
  const [sim, shape] = h.split('<b>Shape</b>');
  assert.match(sim, /<b>Simulation<\/b>/);
  for (const k of ['magnitude', 'gravity', 'vortex', 'spin', 'count', 'spread']) assert.match(sim, new RegExp(`data-rxo=${k}`), `Simulation has ${k}`);
  for (const k of ['particle_size', 'size_var', 'size_in_dur', 'size_out_dur', 'hue_var']) assert.match(shape, new RegExp(`data-rxo=${k}`), `Shape has ${k}`);
  assert.equal((h.match(/type=range/g) || []).length, 11, 'six Simulation sliders and five Shape sliders');
  assert.match(shape, /<span class=mut>Size<\/span>.*?<output>×1<\/output>/s);
  assert.match(sim, /data-rxo=magnitude[^>]*><output>…<\/output>/, "the motion's own speed is not known until the server answers: never a made-up number");
  assert.match(h, /Hue 0 keeps the emoji's own colours/);
  assert.match(h, /data-act=rxcreate/);

  r("POSTS.length=0;RXS.ek.preset='vortex';RXS.ek.hue_var=0;RXS.ek.particle_size=1.5;RXS.ek.size_var=0");
  r("POSTREPLIES.push({ok:true,j:{id:'L003',token:'kiss',emoji:'😘',preset:'vortex',params:{},url:'/out/particles/emoji/kiss/renders/L003.lottie.json',preview:'/out/particles/emoji/kiss/renders/L003.webp'}})");
  await r('ACT.rxcreate()');
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-lottie', { token: 'kiss', particle_size: 1.5, size_var: 0, size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 0, preset: 'vortex' }]]);
  assert.equal(r('RXS.ek'), null, 'the editor closes');
  assert.deepEqual(J(r, 'RXS.made.map(x=>x.id)'), ['L003'], 'the new reaction is the first card');
});

test('Edit reopens a card with its own options; Download fetches the stored file', () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=${MADE}`);
  r("ACT.rxedit({dataset:{t:'kiss',id:'L001'}})");
  assert.deepEqual(J(r, '{t:RXS.ek.token,p:RXS.ek.preset,i:RXS.ek.size_in_dur,o:RXS.ek.size_out_dur,h:RXS.ek.hue_var,s:RXS.ek.particle_size,v:RXS.ek.size_var}'), { t: 'kiss', p: 'vortex', i: 0.2, o: 0.6, h: 50, s: 2, v: 0.5 },
    'Edit restores Size and the exact size range of the card (0.05-0.15 is 50% around 0.10)');
  r("ACT.rxedit({dataset:{t:'cry',id:'L002'}})");
  assert.equal(r('RXS.ek.preset'), '', "rain is cry's own motion: no override");
  r("var DL=[];document.createElement=()=>({click(){DL.push(this.href+'|'+this.download)},remove(){}});document.body={appendChild(){}}");
  r("ACT.rxdl({dataset:{u:'/out/particles/emoji/cry/renders/L002.lottie.json',n:'cry L002'}})");
  assert.deepEqual(J(r, 'DL'), ['/out/particles/emoji/cry/renders/L002.lottie.json|cry L002.lottie.json']);
  r('ACT.rxclose()');
  assert.equal(r('RXS.ek'), null);
});

test('Simulation shows the motion values, sends only what was moved, and Reset / another motion go back to the motion', async () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=[]`);
  r("POSTREPLIES.push({ok:true,j:{url:'/a.webp',params:{magnitude:0.8,gravity:0.5,vortex:0,spin:1,count:28,spread:360,size_min:0.1,size_max:0.22}}})");
  await r("ACT.rxpick({dataset:{t:'kiss'}})");
  const h = r('rxEditor()');
  assert.match(h, /data-rxo=magnitude[^>]*><output>×0.8<\/output>/, 'its own speed');
  assert.match(h, /data-rxo=count[^>]*><output>28<\/output>/);
  assert.match(h, /data-rxo=spread[^>]*><output>360°<\/output>/);
  assert.match(h, /data-rxo=size_var[^>]*><output>38%<\/output>/, 'its own size range, 0.10-0.22');
  assert.match(h, /data-act=rxreset data-g=sim disabled/, 'nothing to reset yet');
  r("POSTS.length=0;RXS.ek.sim.magnitude=2;RXS.ek.sim.count=12");
  r("POSTREPLIES.push({ok:true,j:{url:'/b.webp',params:{}}})");
  await r("rxPlay('kiss')");
  assert.deepEqual(J(r, 'POSTS[0][1]'), { token: 'kiss', magnitude: 2, count: 12, particle_size: 1, size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 25, size: 256 }, 'only the moved settings go to the server');
  r("POSTS.length=0;POSTREPLIES.push({ok:true,j:{url:'/c.webp',params:{}}})");
  await r("ACT.rxreset({dataset:{g:'sim'}})");
  assert.deepEqual(J(r, 'RXS.ek.sim'), {});
  r("RXS.ek.sim.spin=3;RXS.ek.particle_size=2");
  await r("ACT.rxreset({dataset:{g:'shape'}})");
  assert.deepEqual(J(r, '[RXS.ek.sim,RXS.ek.particle_size,RXS.ek.hue_var]'), [{ spin: 3 }, 1, 25], 'Shape reset leaves Simulation alone');
  const before = r('POSTS.length');
  r("RXS.ek.preset='vortex';RXS.ek.sim={};");
  assert.equal(r('Object.keys(RXS.ek.sim).length'), 0, 'another motion starts from its own simulation');
  assert.ok(before >= 1);
});

test('Edit restores the Simulation of a created reaction', () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=[{id:'L004',token:'kiss',emoji:'😘',preset:'burst',params:{magnitude:2.5,gravity:-1,vortex:0.5,spin:0,count:40,spread:180,particle_size:1,size_min:0.1,size_max:0.22},url:'/x.json',preview:null}]`);
  r("ACT.rxedit({dataset:{t:'kiss',id:'L004'}})");
  assert.deepEqual(J(r, 'RXS.ek.sim'), { magnitude: 2.5, gravity: -1, vortex: 0.5, spin: 0, count: 40, spread: 180 });
});

test('Select several: clicks tick emojis instead of opening one, and one Create makes them all with each emoji\'s own look or a saved preset', async () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=[];RXS.presets=[{id:'preset01',name:'Preset 01',settings:{preset:'vortex'}}]`);
  r('ACT.rxmulti()');
  assert.equal(r('RXS.multi'), true);
  r("ACT.rxpick({dataset:{t:'kiss'}});ACT.rxpick({dataset:{t:'cry'}});ACT.rxpick({dataset:{t:'school'}});ACT.rxpick({dataset:{t:'school'}})");
  assert.deepEqual(J(r, '[...RXS.sel]'), ['kiss', 'cry'], 'a second click unticks');
  assert.equal(r('RXS.ek'), null, 'nothing opens in the editor while ticking');
  const h = r('rxPick()');
  assert.match(h, /data-act=rxmulti aria-pressed=true/);
  assert.match(h, /<b>2<\/b> <span class=rx-many-g>😘😭<\/span>/);
  assert.match(h, /<option value="" selected>Each emoji's own<\/option><option value="preset01">Preset 01<\/option>/);
  assert.match(h, /data-act=rxmany >Create 2 reactions/);
  assert.equal((h.match(/class=rx-tick/g) || []).length, 2, 'ticked tiles carry a check');
  r("POSTREPLIES.push({ok:true,j:{reactions:[{id:'L001',token:'kiss',emoji:'😘',preset:'vortex',params:{}},{id:'L001',token:'cry',emoji:'😭',preset:'vortex',params:{}}],errors:[]}})");
  r("RXS.apply='preset01'");
  await r('ACT.rxmany({})');
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-lottie/batch', { tokens: ['kiss', 'cry'], preset_id: 'preset01' }]]);
  assert.deepEqual(J(r, 'RXS.made.map(x=>x.token)'), ['cry', 'kiss'], 'their cards come first, newest first');
  assert.equal(r('RXS.sel.size'), 0);
  r("POSTS.length=0;RXS.apply='';RXS.sel.add('cry');POSTREPLIES.push({ok:true,j:{reactions:[],errors:[{token:'cry',error:'x'}]}})");
  await r('ACT.rxmany({})');
  assert.deepEqual(J(r, 'POSTS[0][1]'), { tokens: ['cry'] }, "each emoji's own: no preset is sent");
  r("RXS.sel=new Set(Array.from({length:24},(_,i)=>'t'+i))");
  r("ACT.rxpick({dataset:{t:'kiss'}})");
  assert.equal(r('RXS.sel.size'), 24, 'at most 24 at once');
  r('ACT.rxmulti()');
  assert.deepEqual(J(r, '[RXS.multi,RXS.sel.size]'), [false, 0], 'leaving Select several clears the ticks');
});

test('Save preset keeps the editor settings without the emoji; the hover reaction is 64 px from the tile right edge', async () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=[];RXS.presets=[]`);
  r("RXS.ek=rxNew('kiss');RXS.ek.preset='rain';RXS.ek.sim.count=12;RXS.ek.hue_var=0");
  assert.match(r('rxEditor()'), /data-act=rxcreate[^>]*>Create reaction<\/button><button class=btn data-act=rxsave/);
  r("POSTREPLIES.push({ok:true,j:{id:'preset01',name:'Preset 01',settings:{}}})");
  await r('ACT.rxsave()');
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-presets', { settings: { count: 12, particle_size: 1, size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 0, preset: 'rain' } }]]);
  assert.deepEqual(J(r, 'RXS.presets.map(p=>p.name)'), ['Preset 01']);
  r("RXS.ek=null;RXS.hover='cry';const k=rxKey(rxFor('cry'));RXS.pv[k]='/r.webp';RXS.par[k]={origin:[0.5,0.1]}");
  const t = r("rxTile(rxRow('cry'))");
  assert.match(t, /class=rx-fx src="\/r.webp" style="width:64px;height:64px;left:calc\(100% - 32px\);top:calc\(50% - 6px\)"/,
    "the rain's origin (top centre) sits on the tile's right edge");
});
