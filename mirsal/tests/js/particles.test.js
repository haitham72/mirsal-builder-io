// particles.js: the Studio's Particles tab (setup, the tab's step in the header) and the Particles section under the batch. The file runs in a vm after effects.js with the Studio's few globals stubbed,
// so what is checked is the real markup and the real linking of a batch's cells to the library's stickers. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const { loadConsole } = require('./console_vm');

const run0 = loadConsole(['effects.js', 'particles.js'], { studio: true });
const J = v => (v === undefined ? v : JSON.parse(JSON.stringify(v)));
const run = code => J(run0(code));
const st = (id, over = {}) => ({ id, name: 'Sticker <' + id + '>', emoji: '🍓', type: 'static', source: {}, ...over });
const PACKS = [
  { id: 'p1', name: 'Fruits <b>', stickers: [st('a1', { source: { generation: 'G012', index: 1 } }), st('a2', { source: { generation: 'G012', index: 2 } }), st('a3', { source: { generation: 'G013', index: 1 } })] },
  { id: 'p2', name: 'Animated', stickers: [st('b1', { type: 'animated', source: { generation: 'G012', index: 1 } }), st('b2', { type: 'animated', source: { generation: 'G012', index: 3 } })] },
  { id: 'p3', name: 'Empty', stickers: [] },
];
const withPacks = code => `(()=>{LIB.packs=${JSON.stringify(PACKS)};return ${code}})()`;

test('every name of the file starts with sp, and the effects state of the tab is its own', () => {
  assert.equal(run("SP.who"), 'sp');
  assert.equal(run("FXS.sp===SP"), true);
  assert.equal(run("SP===FX"), false);
  assert.deepEqual(run("[SP.kind,SP.mode,SP.src]"), ['pack', 'sim', 'own']);
  assert.deepEqual(run("(spKind('drawn'),[SP.kind,SP.mode,SP.src])"), ['drawn', 'sim', 'drawn']);
  assert.deepEqual(run("(spKind('video'),[SP.kind,SP.mode,SP.src])"), ['video', 'video', 'video']);
  run("spKind('pack')");
});

test('batch ids are read as G### whatever way the library stored them', () => {
  assert.equal(run("spGid('G012')"), 'G012');
  assert.equal(run("spGid(12)"), 'G012');
  assert.equal(run("spGid('g7')"), 'G007');
  assert.equal(run("spGid('')"), '');
  assert.equal(run("spGid('hello')"), '');
  assert.equal(run("spGid(null)"), '');
});

test('the library sticker of a batch cell: the one that came from it, a still preferred to an animated one', () => {
  const ix = run(withPacks("spLinkIndex(LIB.packs,'G012')"));
  assert.deepEqual(Object.keys(ix).sort(), ['1', '2', '3']);
  assert.equal(ix[1].sticker.id, 'a1', 'the still wins over the animated one of the same cell');
  assert.equal(ix[1].pack_id, 'p1');
  assert.equal(ix[3].sticker.id, 'b2', 'an animated sticker is used when it is the only one');
  assert.equal(ix[3].pack, 'Animated');
  assert.deepEqual(Object.keys(run(withPacks("spLinkIndex(LIB.packs,'G013')"))), ['1']);
  assert.deepEqual(run(withPacks("spLinkIndex(LIB.packs,'G999')")), {});
  assert.deepEqual(run("spLinkIndex(null,'G012')"), {});
  assert.deepEqual(run(withPacks("spLinkIndex(LIB.packs,'')")), {});
});

test('a run starts with the batch’s stickers of the pack, else the pack’s first ones, at most 24', () => {
  assert.deepEqual(run(withPacks("[...spPickSel(LIB.packs[0],['G012'])]")), ['a1', 'a2']);
  assert.deepEqual(run(withPacks("[...spPickSel(LIB.packs[0],['G999'])]")), ['a1', 'a2', 'a3']);
  assert.equal(run("spPickSel({stickers:Array.from({length:40},(_,i)=>({id:'s'+i,source:{}}))},[]).size"), 24);
});

test('the pack a run starts with: the one holding the most of this batch, then the session’s, then the first with stickers', () => {
  assert.equal(run(withPacks("spDefaultPack(LIB.packs,['G012'],'')")), 'p1');
  assert.equal(run(withPacks("spDefaultPack(LIB.packs,['G012','G013'],'')")), 'p1');
  assert.equal(run(withPacks("spDefaultPack(LIB.packs,['G999'],'p2')")), 'p2');
  assert.equal(run(withPacks("spDefaultPack(LIB.packs,['G999'],'zzz')")), 'p1');
  assert.equal(run("spDefaultPack([{id:'x',stickers:[]}],[],'')"), '');
});

test('setup: the pack, three plain choices, the stickers; nothing starts without a click', () => {
  const S = (o = {}) => `Object.assign(fxNew('sp'),{kind:'pack',pack:'p1',sel:new Set(['a1','a2']),grid:'2x2'},${JSON.stringify(o)},{sel:new Set(${JSON.stringify(o.sel || ['a1', 'a2'])})})`;
  const html = (o, gids = ['G012']) => run(withPacks(`spSetupHtml(${S(o)},LIB.packs.filter(p=>p.stickers.length),${JSON.stringify(gids)})`));
  const h = html();
  assert.match(h, /Choose the pack/);
  assert.match(h, /data-act=sppack data-id=p1/);
  assert.match(h, /Fruits &lt;b&gt;/, 'pack names are escaped');
  assert.doesNotMatch(h, /Empty/, 'a pack with no stickers is not offered');
  assert.match(h, /3 stickers · 2 from this batch/);
  for (const l of ['Pack stickers', 'Drawn particles', 'Video particles']) assert.match(h, new RegExp(`<b>${l}</b>`));
  assert.match(h, /<em>Free<\/em>/);
  assert.equal((h.match(/<em>Costs credits<\/em>/g) || []).length, 2);
  assert.match(h, /class="sp-mode on" data-act=spkind data-v=pack aria-pressed=true/);
  assert.match(h, /The price is on the button before anything is spent/);
  assert.match(h, /Which stickers fly out \(they are the particles and they burst\)/);
  assert.match(h, /class="fx-st on" data-act=spst data-id=a1/);
  assert.match(h, /class="fx-st" data-act=spst data-id=a3/);
  assert.match(h, /data-act=spstart >.*Continue with 2 stickers<\/button>/s);
  assert.match(h, /Nothing is drawn or spent yet/);
  assert.doesNotMatch(h, /spgrid/, 'the grid is asked for video only');
  const drawn = html({ kind: 'drawn' });
  assert.match(drawn, /class="sp-mode on" data-act=spkind data-v=drawn/);
  assert.match(drawn, /Which stickers get particles/);
  const video = html({ kind: 'video', grid: '3x3' });
  assert.match(video, /data-act=spgrid data-v=2x2/);
  assert.match(video, /class="tab on" data-act=spgrid data-v=3x3/);
  assert.match(video, /3 x 3 was measured poor/, 'the measured warning, as a warning');
  assert.doesNotMatch(html({ kind: 'video' }), /measured poor/);
  const none = html({ sel: [] });
  assert.match(none, /data-act=spstart disabled>.*Continue with 0 stickers/s);
  const many = html({ sel: Array.from({ length: 25 }, (_, i) => 's' + i) });
  assert.match(many, /data-act=spstart disabled>/);
  assert.match(many, /at most 24 stickers/);
  assert.match(run("spSetupHtml(Object.assign(fxNew('sp'),{pack:'',kind:'pack'}),[],[])"), /Make a pack first/);
});

test('the Studio’s header gets a Particles step after Animation, and the steps after it are numbered again', () => {
  const done = t => `<button class="gst done " data-act=gtab data-t=${t}><span class=gsm><svg></svg></span><span class=gsl><b>${t}</b></span></button>`;
  const steps = '<div class=gsteps>' + done('request') + done('plan') + done('stickers')
    + '<button class="gst todo " data-act=gtab data-t=anim><span class=gsm>4</span><span class=gsl><b>Animation</b></span></button>'
    + '<button class="gst todo " data-act=gadd ><span class=gsm>5</span><span class=gsl><b>Pack</b></span></button></div>';
  const h = run(withPacks(`spSteps(${JSON.stringify(steps)},[])`));
  assert.ok(h.indexOf('data-t=particles') > h.indexOf('data-t=anim') && h.indexOf('data-t=particles') < h.indexOf('data-act=gadd'), 'between Animation and Pack');
  assert.match(h, /<button class="gst todo " data-act=gtab data-t=particles><span class=gsm>5<\/span><span class=gsl><b>Particles<\/b><small>None yet<\/small>/);
  assert.match(h, /data-act=gadd ><span class=gsm>6<\/span>/, 'Pack is the sixth step now');
  assert.match(h, /data-t=anim><span class=gsm>4<\/span>/, 'what is before it is untouched');
  assert.equal(run("spSteps('no steps at all',[])"), 'no steps at all');
  const cur = run(withPacks(`(GS.tab='particles',spSteps(${JSON.stringify(steps)},[]))`));
  assert.match(cur, /class="gst todo cur" data-act=gtab data-t=particles/);
  run("GS.tab='stickers'");
});

test('the step counts what was made for the batch’s stickers', () => {
  const made = run(withPacks("(PKPT.c={p1:{a1:{created:2,saved:1},a3:{created:9,saved:9}}},spMade([{generation_id:'G012'}]))"));
  assert.equal(made, 3, 'only the stickers that came from this batch count');
  const h = run(withPacks("(PKPT.c={p1:{a1:{created:2,saved:1}}},spSteps('<button class=\"gst todo \" data-act=gadd ><span class=gsm>5</span></button>',[{generation_id:'G012'}]))"));
  assert.match(h, /data-t=particles><span class=gsm><svg data-i=check><\/svg><\/span><span class=gsl><b>Particles<\/b><small>3 made<\/small>/);
  assert.match(h, /class="gst done "/);
  run("PKPT.c={}");
});

const CELL = (i, o = {}) => ({ index: i, key: 'cape_piece', png: `slices/S${i}.png`, link: null, n: 0, det: null, ...o });
const LINK = (id, pid = 'p1', pack = 'Fruits <b>') => ({ pack_id: pid, pack, sticker: { id } });
const sec = (b, many = false) => run(`spSecBatchHtml(${JSON.stringify(b)},${many})`);

test('the section: a sticker with particles shows its gallery, one without is a chip, one outside a pack is ONE line', () => {
  const h = sec({ gid: 'G012', cells: [CELL(1, { link: LINK('a1'), n: 2, det: { created: [] } }), CELL(2, { link: LINK('a2') }), CELL(3, { link: LINK('a3') }), CELL(4), CELL(5)] });
  assert.match(h, /<b>S1 · cape piece<\/b>/);
  assert.match(h, /in <button class=link data-act=ptsaved data-id=p1>Fruits &lt;b&gt;<\/button>/, 'the pack is a link, escaped');
  assert.match(h, /<ptbody data-for=a1>data<\/ptbody>/, 'the gallery of the library’s sticker view is reused');
  assert.match(h, /data-act=spmake data-p=p1 data-s=a1>.*Make more/s);
  assert.match(h, /No particles yet, click one to make some:/);
  assert.match(h, /class=sp-chip data-act=spmake data-p=p1 data-s=a2 title="Make particles for S2 \(in Fruits &lt;b&gt;\)"/);
  assert.match(h, /data-s=a3/);
  assert.equal((h.match(/Add to a pack to give them particles/g) || []).length, 1, 'one line for all the stickers that are not in a pack');
  assert.equal((h.match(/class=sp-th title="S[45]"/g) || []).length, 2);
  assert.doesNotMatch(h, /<ptbody data-for=a2/, 'a sticker with no particles has no gallery');
  assert.doesNotMatch(h, /sp-bh/, 'a single batch has no heading of its own');
  assert.match(sec({ gid: 'G012', cells: [CELL(4)] }), /Add to a pack to give it particles/, 'one sticker: "it"');
  assert.match(sec({ gid: 'G012', cells: [CELL(1, { link: LINK('a1'), n: 1 })] }, true), /<div class=sp-bh><b>G012<\/b>/, 'several batches: each has its name');
  assert.equal(sec({ gid: 'G012', cells: [] }).replace(/\s+/g, ''), '<divclass=sp-bt></div>');
});

test('the section: the data comes from the Studio’s batches, the library and the counts; a dropped sticker is not offered', () => {
  const g = { generation_id: 'G012', stickers: [{ index: 1, key: 'a', png: 'slices/S1.png', status: 'READY', review: {} }, { index: 2, key: 'b', png: 'slices/S2.png', status: 'READY', review: { still: 'REJECTED' } },
    { index: 3, key: 'c', png: null, status: 'FAILED', review: {} }, { index: 4, key: 'd', png: 'slices/S4.png', status: 'READY', review: {} }] };
  const d = run(withPacks(`(GM.set(12,${JSON.stringify(g)}),SES.gens=[12,99],PKPT.c={p1:{a1:{created:2,saved:1}}},PKPT.d={a1:{created:[1]}},spSecData())`));
  assert.equal(d.length, 1, 'a batch that is not loaded yet is skipped');
  assert.deepEqual(d[0].cells.map(c => c.index), [1, 4], 'dropped and blocked stickers are not offered');
  assert.equal(d[0].cells[0].n, 3);
  assert.equal(d[0].cells[0].link.sticker.id, 'a1');
  assert.deepEqual(d[0].cells[0].det, { created: [1] });
  assert.equal(d[0].cells[1].link, null);
  run("(GM.clear(),SES.gens=[],PKPT.c={},PKPT.d={})");
});

test('the section: a heading with the one button that opens the tab, and nothing at all without a batch', () => {
  const h = run("spSecHtml([{gid:'G012',cells:[]}])");
  assert.match(h, /<h2><svg data-i=fx><\/svg> Particles<\/h2>/);
  assert.match(h, /data-act=spopen>.*Create particles for pack/s);
  assert.equal(run("spSecHtml([])"), '');
});

test('the tab replaces the body only while it is current, and a person can leave the flow at any point', () => {
  assert.equal(run("(GS.tab='stickers',gbodyHtml([],{}))"), 'ORIGINAL BODY');
  const h = run(withPacks("(GS.tab='particles',SP.eid='',SP.pack='',gbodyHtml([{generation_id:'G012'}],{}))"));
  assert.match(h, /^<section class="gplan sp fx" id=sp-root data-fxx=sp>/, 'the root every handler finds its state from');
  assert.match(h, /Give the stickers of a pack a burst of particles/);
  assert.match(h, /Whatever you make is saved under its sticker/);
  assert.match(h, /data-act=spstart/);
  assert.match(run("(SP.eid='E007',SP.rec={id:'E007',pack_name:'Fruits',status:'NEW'},spBody([]))"), /Looking at your stickers…/);
  const head = run("spBody([])");
  assert.doesNotMatch(head, /spstart/);
  const ready = run("(SP.rec={id:'E007',pack_name:'Fruits <b>',mode:'sim',status:'READY',grid:[2,2],groups:[],stickers:[],results:[],video:{},history:[]},spBody([]))");
  assert.match(ready, /<a class=link href="#\/effects\/E007"[^>]*>Open in the particle studio<\/a>/, 'the same effect in the full particle studio');
  assert.match(ready, /data-act=spreset>Start over/);
  assert.match(ready, /Fruits &lt;b&gt;/);
  assert.match(run("(SP.rec={id:'E007',status:'ERROR',error:'It <broke>'},spBody([]))"), /It &lt;broke&gt;/);
  run("(GS.tab='stickers',SP.eid='',SP.rec=null)");
});

test('the section is drawn into its container, once, and again when the container is a new one', () => {
  const g = { generation_id: 'G012', stickers: [{ index: 1, key: 'a', png: 'slices/S1.png', status: 'READY', review: {} }] };
  run(withPacks(`(GM.set(12,${JSON.stringify(g)}),SES.gens=[12],DOMSTUB.gpart={writes:0,set innerHTML(v){this.writes++;this.html=v}},0)`));
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1);
  assert.match(run("DOMSTUB.gpart.html"), /No particles yet, click one to make some/);
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1, 'nothing changed: the videos in it are not restarted');
  run("DOMSTUB.gpart={writes:0,set innerHTML(v){this.writes++;this.html=v}}");
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1, 'the Studio was left and opened again: the new container is filled');
  run("(GM.clear(),SES.gens=[],delete DOMSTUB.gpart)");
});
