// reactions.js: Reaction effects (#/reactions), the emoji bank ONLY. Search + two rows of small emojis, the picked one in one editor card, then only the created reactions as cards.
// The whole file runs in a vm with the few globals it uses stubbed (console_vm.js), so the markup and the posts are checked for real. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConsole } = require('./console_vm');

const BANK = "[{token:'kiss',emoji:'😘',preset:'burst',motion:'hearts pop'},{token:'cry',emoji:'😭',preset:'rain',motion:'tears fall'},{token:'school',emoji:'🏫',preset:'burst',motion:''}]";
const MADE = "[{id:'L002',token:'cry',emoji:'😭',preset:'rain',params:{size_in_dur:0,size_out_dur:0.4,hue_var:0},url:'/out/particles/emoji/cry/renders/L002.lottie.json',preview:'/out/particles/emoji/cry/renders/L002.webp'}," +
  "{id:'L001',token:'kiss',emoji:'😘',preset:'vortex',params:{size_in_dur:0.2,size_out_dur:0.6,hue_var:50},url:'/out/particles/emoji/kiss/renders/L001.lottie.json',preview:null}]";
const J = (r, code) => JSON.parse(r(`JSON.stringify(${code})`));

test('the screen: search, small emojis only, no thumbnail cards of the bank, and only the created reactions as cards', () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=${MADE}`);
  const h = r('rxHtml()');
  assert.match(h, /data-rxq placeholder="Search 3 emoji"/);
  assert.equal((h.match(/class="rx-e/g) || []).length, 3, 'one small tile per emoji');
  assert.doesNotMatch(h.split('rx-made')[0], /<img|<video|<b>kiss<\/b>|burst/, 'the emoji rows are glyphs only: no names, no presets, nothing playing');
  assert.equal((h.match(/<article class=rx-card>/g) || []).length, 2, 'one card per created reaction');
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
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-preview', { token: 'kiss', size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 25, size: 256 }]]);
  const h = r('rxHtml()');
  assert.match(h, /data-rxed/);
  assert.match(h, /src="\/out\/particles\/emoji\/kiss\/previews\/a-256.webp"/, 'the reaction plays in the editor');
  assert.match(h, /<option value="" selected>its own · burst<\/option>/);
  for (const k of ['size_in_dur', 'size_out_dur', 'hue_var']) assert.match(h, new RegExp(`data-rxo=${k}`));
  assert.equal((h.match(/type=range/g) || []).length, 3, 'three sliders, nothing else to tune');
  assert.match(h, /Hue 0 keeps the emoji's own colours/);
  assert.match(h, /data-act=rxcreate/);

  r("POSTS.length=0;RXS.ek.preset='vortex';RXS.ek.hue_var=0");
  r("POSTREPLIES.push({ok:true,j:{id:'L003',token:'kiss',emoji:'😘',preset:'vortex',params:{},url:'/out/particles/emoji/kiss/renders/L003.lottie.json',preview:'/out/particles/emoji/kiss/renders/L003.webp'}})");
  await r('ACT.rxcreate()');
  assert.deepEqual(J(r, 'POSTS'), [['/api/particles/emoji-lottie', { token: 'kiss', size_in_dur: 0.4, size_out_dur: 0.4, hue_var: 0, preset: 'vortex' }]]);
  assert.equal(r('RXS.ek'), null, 'the editor closes');
  assert.deepEqual(J(r, 'RXS.made.map(x=>x.id)'), ['L003'], 'the new reaction is the first card');
});

test('Edit reopens a card with its own options; Download fetches the stored file', () => {
  const r = loadConsole(['reactions.js']);
  r(`RXS.bank=${BANK};RXS.made=${MADE}`);
  r("ACT.rxedit({dataset:{t:'kiss',id:'L001'}})");
  assert.deepEqual(J(r, '{t:RXS.ek.token,p:RXS.ek.preset,i:RXS.ek.size_in_dur,o:RXS.ek.size_out_dur,h:RXS.ek.hue_var}'), { t: 'kiss', p: 'vortex', i: 0.2, o: 0.6, h: 50 });
  r("ACT.rxedit({dataset:{t:'cry',id:'L002'}})");
  assert.equal(r('RXS.ek.preset'), '', "rain is cry's own motion: no override");
  r("var DL=[];document.createElement=()=>({click(){DL.push(this.href+'|'+this.download)},remove(){}});document.body={appendChild(){}}");
  r("ACT.rxdl({dataset:{u:'/out/particles/emoji/cry/renders/L002.lottie.json',n:'cry L002'}})");
  assert.deepEqual(J(r, 'DL'), ['/out/particles/emoji/cry/renders/L002.lottie.json|cry L002.lottie.json']);
  r('ACT.rxclose()');
  assert.equal(r('RXS.ek'), null);
});
