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

test('a scope preselects only its batch or sticker, never another pack', () => {
  assert.deepEqual(run(withPacks("spScopeStickers({generation:'G012'},LIB.packs).map(r=>r.sticker.id)")), ['a1','a2','b1','b2']);
  assert.deepEqual(run(withPacks("spScopeStickers({generation:'G999'},LIB.packs)")), []);
  assert.deepEqual(run(withPacks("spScopeStickers(null,LIB.packs)")), []);
  assert.deepEqual(run(withPacks("spScopeStickers({sticker_id:'a2'},LIB.packs).map(r=>r.sticker.id)")), ['a2']);
});

test('three creation cards (sticker sprites, AI images, Kling) and scoped slices', () => {
  const h=run(withPacks("spSetupHtml(Object.assign(fxNew('sp'),{scope:{generation:'G012'},pack:'p1',kind:'drawn',sel:new Set(['a1','a2']),grid:'2x2'}),LIB.packs,['G012'])"));
  for(const label of ['Sprites from the sticker','AI image sprites','Kling animated · from scratch'])assert.match(h,new RegExp(label));
  assert.equal((h.match(/class="sp-mode/g)||[]).length,3,'three equal choices: the sticker\'s sprites, AI images, Kling from scratch');
  assert.doesNotMatch(h,/data-id=a3/);
  assert.match(h,/data-act=spst data-id=a1/);
  assert.doesNotMatch(h,/Nothing is drawn or spent yet/);
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

test('the batch section is ONE list of versions, each once, with one approval offer and no per-sticker blocks', () => {
 const row=(id,at,o={})=>({id,version:9,label:'AI image sprites',n_sprites:4,saved:true,saved_at:at,shared_with:8,sprites:[],in_pack:[],addable:null,preview:null,credits:2,...o});
 const det=()=>({rows:[row('P002',2),row('P001',1)],drafts:[row('P009',3,{saved:false})]});
 const h=sec({gid:'G107',cells:[1,2,3,4,5,6,7,8,9].map(i=>CELL(i,{link:LINK('s'+i),n:3,det:det()})).concat([CELL(10)])});
 assert.equal((h.match(/data-particle-row=P002/g)||[]).length,1,'one set owned by nine stickers is one row, not nine');
 assert.match(h,/data-particle-row=P001>v1<[\s\S]*data-particle-row=P002>v2<[\s\S]*data-particle-row=P009>Draft</,'oldest first, numbered for the batch; drafts last');
 assert.doesNotMatch(h,/Shared by|Uses the shared|S1 ·|data-act=spmake|<ptbody/,'no per-sticker blocks, no shared label');
 assert.equal((h.match(/Approve as a pack/g)||[]).length,1,'a sticker not in a pack still gets the one approval offer');
 assert.match(sec({gid:'G012',cells:[CELL(1,{link:LINK('a1')})]}),/No particles yet/);
 assert.match(sec({gid:'G012',cells:[]},true),/sp-bh/);
});

test('the section: the data comes from the Studio’s batches, the library and the counts; a dropped sticker is not offered', () => {
  const g = { generation_id: 'G012', stickers: [{ index: 1, key: 'a', png: 'slices/S1.png', status: 'READY', review: {} }, { index: 2, key: 'b', png: 'slices/S2.png', status: 'READY', review: { still: 'REJECTED' } },
    { index: 3, key: 'c', png: null, status: 'FAILED', review: {} }, { index: 4, key: 'd', png: 'slices/S4.png', status: 'READY', review: {} }] };
  const d = run(withPacks(`(GM.set(12,${JSON.stringify(g)}),SES.gens=[12,99],PKPT.c={p1:{a1:{created:2,saved:1}}},PKPT.d={a1:{created:[1]}},spSecData())`));
  assert.equal(d.length, 1, 'a batch that is not loaded yet is skipped');
  assert.deepEqual(d[0].cells.map(c => c.index), [1, 4], 'dropped and blocked stickers are not offered');
  assert.equal(d[0].cells[0].n, 1);
  assert.equal(d[0].cells[0].link.sticker.id, 'a1');
  assert.deepEqual(d[0].cells[0].det, { created: [1] });
  assert.equal(d[0].cells[1].link, null);
  run("(GM.clear(),SES.gens=[],PKPT.c={},PKPT.d={})");
});

test('the section: a heading with the one button that opens the tab, and nothing at all without a batch', () => {
  const h = run("spSecHtml([{gid:'G012',cells:[]}])");
  assert.match(h, /<h2><svg data-i=fx><\/svg> Particles<\/h2>/);
  assert.match(h, /data-act=spopen>.*Create particles/s);
  assert.equal(run("spSecHtml([])"), '');
});

test('the tab replaces the body only while it is current, and a person can leave the flow at any point', () => {
  assert.equal(run("(GS.tab='stickers',gbodyHtml([],{}))"), 'ORIGINAL BODY');
  const h = run(withPacks("(GS.tab='particles',SP.scope={generation:'G012'},SP.eid='',SP.pack='p1',SP.sel=new Set(['a1','a2']),gbodyHtml([{generation_id:'G012'}],{}))"));
  assert.match(h, /^<section class="gplan sp fx" id=sp-root data-fxx=sp>/, 'the root every handler finds its state from');
  assert.match(h, /<h2>Particles<\/h2>/);
  assert.doesNotMatch(h, /Whatever you make is saved under its sticker/);
  assert.match(h, /data-act=spstart/);
  assert.match(run("(SP.eid='E007',SP.rec={id:'E007',pack_name:'Fruits',status:'NEW'},spBody([]))"), /Preparing sprites…/);
  const head = run("spBody([])");
  assert.doesNotMatch(head, /spstart/);
  const ready = run("(SP.rec={id:'E007',pack_name:'Fruits <b>',mode:'sim',status:'READY',grid:[2,2],groups:[],stickers:[],results:[],video:{},history:[]},spBody([]))");
  assert.match(ready, /<a class=link href="#\/effects\/E007"[^>]*>Original run · E007<\/a>/, 'the same effect in the full particle studio');
  assert.match(ready, /data-act=spreset>Back/);
  assert.match(ready, /Fruits &lt;b&gt;/);
  assert.match(run("(SP.rec={id:'E007',status:'ERROR',error:'It <broke>'},spBody([]))"), /It &lt;broke&gt;/);
  run("(GS.tab='stickers',SP.eid='',SP.rec=null)");
});

test('the section is drawn into its container, once, and again when the container is a new one', () => {
  const g = { generation_id: 'G012', stickers: [{ index: 1, key: 'a', png: 'slices/S1.png', status: 'READY', review: {} }] };
  run(withPacks(`(GM.set(12,${JSON.stringify(g)}),SES.gens=[12],PKPT.d={},PKPT.c={},SPS.batches={},DOMSTUB.gpart={writes:0,set innerHTML(v){this.writes++;this.html=v}},0)`));
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1);
  assert.match(run("DOMSTUB.gpart.html"), /No particles yet/);
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1, 'nothing changed: the videos in it are not restarted');
  run("DOMSTUB.gpart={writes:0,set innerHTML(v){this.writes++;this.html=v}}");
  run("spSecDraw()");
  assert.equal(run("DOMSTUB.gpart.writes"), 1, 'the Studio was left and opened again: the new container is filled');
  run("(GM.clear(),SES.gens=[],delete DOMSTUB.gpart)");
});

const SET = (o = {}) => ({ id: 'P001', name: 'Barbie <hearts>', n_cells: 4, n_picked: 3, kind: 'drawn', credits: 2.5,
  packs: ['p1'], owner:[{pack_id:'p1',sticker_id:'a1'}], used_in: [{ id: 'p1', name: 'Fruits <b>' }],
  cells: [{ n: 1, key: 'heart', picked: true, url: '/out/particles/P001/cells/c01.png' }, { n: 2, key: 'flower', picked: true, url: '/out/particles/P001/cells/c02.png' },
    { n: 3, key: 'spark', picked: false, url: '/out/particles/P001/cells/c03.png' }, { n: 4, key: 'dot', picked: true, url: null, missing: true }],
  picked: [1, 2, 4], elements: ['hearts', 'flowers'], motion: { preset: 'burst' }, source: { kind: 'drawn', effect: 'E002', generation: 'G100' }, ...o });

test('a set card: the picked cells as a strip, the name, where it is used, what it cost', () => {
  const h = run(`spSetCard(${JSON.stringify(SET())})`);
  assert.match(h, /data-ps=P001/);
  assert.match(h, /Barbie &lt;hearts&gt;/, 'names are escaped');
  assert.match(h, /P001 · 4 cells · 3 picked · From AI sheet/);
  assert.match(h, /made for 1 sticker/);
  assert.match(h, /about 2\.5 credits spent/);
  assert.equal((h.match(/class=ps-cell/g) || []).length, 3, 'the strip is the picked cells only');
  assert.match(h, /\/out\/particles\/P001\/cells\/c01\.png/);
  for (const a of ['psopen', 'psassign', 'psdup', 'psrename', 'psdel']) assert.match(h, new RegExp(`data-act=${a} data-id=P001`), `${a} is on the card`);
  assert.match(h, /class=ps-hit data-act=psopen/, 'a click on the card itself opens it (Haitham, 2026-10-05)');
  assert.doesNotMatch(h, />Open<\/button>/, 'no Open button');
  const lone = run(`spSetCard(${JSON.stringify(SET({ id: 'P002', name: 'Lone', packs: [], owner: [], used_in: [], credits: 0 }))})`);
  assert.match(lone, /Detached · attach to a sticker/);
  assert.match(lone, /nothing spent yet/);
});

test('the open card: elements, source, motion, every cell with what is kept, and the packs it can leave', () => {
  run("SPL.open='P001'");
  const h = run(`spSetDetail(${JSON.stringify(SET())})`);
  assert.match(h, /hearts/);
  assert.match(h, /from drawn · E002 · G100/);
  assert.match(h, /motion: burst/);
  assert.equal((h.match(/data-act=pspickcell/g) || []).length, 4, 'every cell is ticked, unpicked ones kept');
  assert.match(h, /aria-pressed=true/);
  assert.match(h, /Tick the cells to keep/);
  assert.match(h, /data-act=psunassign data-id=P001 data-s=a1>unlink</, 'unassigning keeps the set: it only leaves the pack');
  run("SPL.open=''");
});

test('the library list: loading, empty, and the sets with a way to make more', () => {
  run("SPL.sets=null");
  assert.match(run("spLibHtml()"), /Reading the particle sets/);
  run("SPL.sets=[]");
  assert.match(run("spLibHtml()"), /No particle sets yet/);
  assert.match(run("spLibHtml()"), /data-act=spopen>.*Make particles/s);
  run(`SPL.sets=[${JSON.stringify(SET())}]`);
  const h = run("spLibHtml()");
  assert.match(h, /data-ps=P001/);
  assert.match(h, /Make particles/);
  run("SPL.sets=null");
});

test('the wizard’s existing-set card lists the sets with what they cost and where they are', () => {
  run("SPL.sets=null");
  assert.match(run("spExistingHtml({pack:'p1',sel:new Set(['a1'])})"), /Reading the particle sets/);
  run("SPL.sets=[]");
  assert.match(run("spExistingHtml({pack:'p1',sel:new Set(['a1'])})"), /No saved particles yet/);
  run(`SPL.sets=[${JSON.stringify(SET())},${JSON.stringify(SET({ id: 'P002', name: 'Bats', owner:[], packs: [], used_in: [], n_picked: 2 }))}]`);
  const h = run("spExistingHtml({pack:'p1',sel:new Set(['a1'])})");
  assert.match(h, /Barbie &lt;hearts&gt;/);
  assert.match(h, /3 picked · used in: Fruits &lt;b&gt;/);
  assert.match(h, /linked to these stickers/);
  assert.match(h, /data-act=pspickset data-id=P002>Use this set</);
  run("SPL.sets=null");
});

test('every new set action has a handler', () => {
  const fx = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', '..', 'mirsal', 'console', 'effects.js'), 'utf8');
  for (const act of ['fxuseset', 'psusesave']) assert.match(fx, new RegExp(`ACT\\.${act}=`), `${act} has a handler`);
});

test('the sets are read once: redrawing the list never refetches', async () => {
  run("SPL.sets=null");
  const before = run("APICALLS");
  await run0("spLibSync()");
  assert.equal(run("APICALLS"), before + 1, 'unknown sets are read');
  run("SPL.sets=[]");
  await run0("spLibSync()");
  await run0("spLibSync()");
  assert.equal(run("APICALLS"), before + 1, 'a known list is never read again without a write (redrawing must not refetch)');
  run("SPL.sets=null");
});

// ---------- the trash: Restore is reachable later, not only on the notice right after a delete ----------
const GONE = (o = {}) => ({ id: 'P007', name: 'Old <bats>', n_cells: 4, n_picked: 3, deleted: true, trashed: true, deleted_at: 1,
  used_in: [{ id: 'p1', name: 'Fruits <b>' }, { id: 'zz', name: 'zz', missing: true }],
  cells: [{ n: 1, picked: true, url: '/out/trash/particles/P007/cells/c01.png' }, { n: 2, picked: false, url: '/out/trash/particles/P007/cells/c02.png' }, { n: 3, picked: true, url: null, missing: true }], ...o });

test('the trash section: nothing when empty, else every deleted set with a Restore button and where it was', () => {
  assert.equal(run("spTrashHtml(null)"), '');
  assert.equal(run("spTrashHtml([])"), '');
  const h = run(`spTrashHtml([${JSON.stringify(GONE())},${JSON.stringify(GONE({ id: 'P008', name: 'Lone', used_in: [] }))}])`);
  assert.match(h, /Deleted \(2\)/);
  assert.match(h, /Old &lt;bats&gt;/, 'names are escaped');
  assert.match(h, /data-act=psrestore data-id=P007>Restore</);
  assert.match(h, /data-act=psrestore data-id=P008>Restore</);
  assert.match(h, /was on Fruits &lt;b&gt;/);
  assert.doesNotMatch(h, /was on Fruits &lt;b&gt;, zz/, 'a pack that no longer exists is not named');
  assert.match(h, /was stand-alone/);
  assert.match(h, /\/out\/trash\/particles\/P007\/cells\/c01\.png/, 'the picture comes from the trash folder');
  assert.equal((h.match(/class=ps-cell/g) || []).length, 4, 'two sets, two picked cells each: the unpicked cell is not in the strip, and a missing file is a blank square, not a broken image');
  assert.equal((h.match(/<img /g) || []).length, 2, 'only the cell with a file has a picture');
});

test('the library shows the trash under the sets, and also when there are no live sets', () => {
  run(`SPL.sets=[${JSON.stringify(SET())}];SPL.trash=[${JSON.stringify(GONE())}]`);
  assert.match(run("spLibHtml()"), /data-ps=P001[\s\S]*Deleted \(1\)[\s\S]*data-act=psrestore data-id=P007/);
  run("SPL.sets=[]");
  assert.match(run("spLibHtml()"), /No particle sets yet[\s\S]*data-act=psrestore data-id=P007/, 'a person who deleted their last set can still get it back');
  run("SPL.trash=null");
  assert.doesNotMatch(run("spLibHtml()"), /Deleted \(/);
  run("SPL.sets=null");
});

test('forgetting the sets forgets the trash too, and a restore re-reads both', () => {
  run(`SPL.sets=[];SPL.trash=[${JSON.stringify(GONE())}];spSetsForget()`);
  assert.equal(run("SPL.trash"), null);
  const src = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', '..', 'mirsal', 'console', 'particles.js'), 'utf8');
  assert.match(src, /api\('\/api\/particles\/deleted'\)/, 'the list is read from the route that serves the trash');
});

// ---------- Generate more ----------
const SHEET = (o = {}) => ({ n: 1, job: 'J043', generation: 'G104', grid: [2, 2], elements: ['hearts'], status: 'DONE', appended: [5, 6, 7, 8], skipped: [], error: null, ...o });
const moreOf = (o = {}) => run(`(delete SPM.P001, spMoreHtml(${JSON.stringify(SET(o))}))`);

test('the open set offers Generate more: the grid, the particles to draw, the price on its own line, a button that says what it does', () => {
  const h = moreOf();
  assert.match(h, /Image sprites/);
  assert.match(h, /Animated sprites · Kling/);
  assert.match(h, /data-act=psmoregrid data-id=P001 data-v=2x2/);
  assert.match(h, /data-act=psmoregrid data-id=P001 data-v=3x3/);
  assert.match(h, /value="hearts, flowers"/, 'the set’s particles seed the prompt');

  assert.match(h, /data-psmoreprompt=P001/);
  assert.match(h, /<div class=fx-price data-psmoreprice[^>]*>[^<]*<\/div>/, 'the price has its own line');
  const btn = h.match(/<button[^>]*data-act=psmoredraw[^>]*>[\s\S]*?<\/button>/)[0];
  assert.match(btn, /Generate image sprites/);
  assert.doesNotMatch(btn, /credit/, 'the price is never inside the button');
  assert.match(btn, /disabled/, 'nothing can be pressed before the price is known');
  assert.doesNotMatch(h, /Nothing is spent until you press the button/);
});

test('once the price is known the button works; a price that is not available is said, never hidden', () => {
  run("SPL.sets=[" + JSON.stringify(SET()) + "]");
  run("SPM.P001={mode:'drawn',prompt:'hearts, flowers',grid:'2x2',chosen:['hearts','flowers'],extra:[],est:{'drawn|2x2|hearts, flowers|hearts|flowers':{credits:2}},busy:0}");
  const h = run(`spMoreHtml(${JSON.stringify(SET())})`);
  assert.match(h, /data-psmoreprice[^>]*>2 credits</);
  assert.doesNotMatch(h.match(/<button[^>]*data-act=psmoredraw[^>]*>/)[0], /disabled/);
  run("SPM.P001.est['drawn|2x2|hearts, flowers|hearts|flowers']={credits:null,error:'The price is not available.'}");
  const bad = run(`spMoreHtml(${JSON.stringify(SET())})`);
  assert.match(bad, /The price is not available/);
  assert.match(bad.match(/<button[^>]*data-act=psmoredraw[^>]*>/)[0], /disabled/);
  run("delete SPM.P001;SPL.sets=null");
});

test('while a sheet is being drawn the set says so and cannot be sent twice', () => {
  const h = moreOf({ drawing: true, sheets: [SHEET({ status: 'REQUESTED', generation: null, appended: [] })] });
  assert.match(h, /Waiting for the sheet \(J043\)/);
  assert.match(h.match(/<button[^>]*data-act=psmoredraw[^>]*>/)[0], /disabled/);
  assert.match(moreOf({ drawing: true, sheets: [SHEET({ status: 'DRAWN', appended: [] })] }), /Cutting the particles \(G104\)/);
});

test('every kind of sheet is told in plain words, newest first, and a dead end always has a next step', () => {
  const h = moreOf({ sheets: [SHEET(), SHEET({ n: 2, status: 'DONE', appended: [9, 10], skipped: [3, 4], generation: 'G105' }),
    SHEET({ n: 3, status: 'FAILED', generation: null, appended: [], error: 'the provider said no' }),
    SHEET({ n: 4, status: 'NO_CELLS', generation: 'G106', appended: [], skipped: [1, 2, 3, 4], error: 'No cell of this sheet came out.' })] });
  assert.match(h, /Sheet 1: 4 particles added/);
  assert.match(h, /Sheet 2: 2 particles added \(2 cells came out empty\)/);
  assert.match(h, /Sheet 3 failed: the provider said no\. Draw it again below/);
  assert.match(h, /Sheet 4 came back with no usable cell/);
  assert.match(h, /data-act=openstudio data-gen=G106 data-i=1[^>]*>Open G106/, 'a sheet with no key screen has one free “Cut it anyway” on its batch: the set links to it');
  assert.ok(h.indexOf('Sheet 4') < h.indexOf('Sheet 1'), 'newest first');
});

test('names the person types are escaped, and the third grid is nine', () => {
  run("SPM.P001={mode:'drawn',prompt:'<img src=x>',grid:'3x3',chosen:[],extra:[],est:{},busy:0}");
  const h = run(`spMoreHtml(${JSON.stringify(SET())})`);
  assert.doesNotMatch(h, /<img src=x>/);
  assert.match(h, /&lt;img src=x&gt;/);
  assert.match(h, /Generate image sprites/);
  assert.match(h, /3 × 3/);
  run("delete SPM.P001");
});

test('Generate more never posts without a known price, and posts the person’s picks with go only on the click', async () => {
  run(`SPL.sets=[${JSON.stringify(SET())}];SPL.detail={};POSTS.length=0;delete SPM.P001`);
  await run0("ACT.psmoredraw({dataset:{id:'P001'},disabled:false})");
  assert.deepEqual(run("POSTS.length"), 0, 'no price, no request');
  run("SPM.P001={mode:'drawn',prompt:'hearts, flowers',grid:'2x2',chosen:['hearts','flowers'],extra:[],est:{'drawn|2x2|hearts, flowers|hearts|flowers':{credits:2}},busy:0}");
  await run0("ACT.psmoredraw({dataset:{id:'P001'},disabled:false})");
  assert.deepEqual(run("POSTS"), [['/api/particles/P001/more', { mode:'drawn', prompt:'hearts, flowers', grid: '2x2', elements: ['hearts', 'flowers'], go: true }]]);
  run("POSTS.length=0;SPM.P001.est={}");
  await run0("spMoreEstimate('P001')");
  assert.deepEqual(run("POSTS"), [['/api/particles/P001/more', { mode:'drawn', prompt:'hearts, flowers', grid: '2x2', elements: ['hearts', 'flowers'], estimate: true }]], 'the quote is a free request, not a go');
  run("delete SPM.P001;SPL.sets=null;POSTS.length=0");
});

test('choosing particles keeps within the sheet and can add the person’s own', () => {
  run(`SPL.sets=[${JSON.stringify(SET({ elements: ['a', 'b', 'c', 'd', 'e'] }))}];delete SPM.P001`);
  assert.deepEqual(run("spMoreState(SPL.sets[0]).chosen"), ['a', 'b', 'c', 'd'], 'a 2x2 sheet starts with the first four');
  run("ACT.psmorechip({dataset:{id:'P001',v:'e'}})");
  assert.deepEqual(run("SPM.P001.chosen"), ['a', 'b', 'c', 'd'], 'a fifth is refused: the sheet holds four');
  run("ACT.psmorechip({dataset:{id:'P001',v:'a'}});ACT.psmorechip({dataset:{id:'P001',v:'e'}})");
  assert.deepEqual(run("SPM.P001.chosen"), ['b', 'c', 'd', 'e']);
  run("ACT.psmoregrid({dataset:{id:'P001',v:'3x3'}})");
  assert.equal(run("SPM.P001.grid"), '3x3');
  run("delete SPM.P001;SPL.sets=null");
});

// ---------- the burst maker: Motion and Finish for a SET, one preview for the whole pack (docs/particles.md section 4) ----------
const BURSTPACKS = "LIB.packs=[{id:'p1',name:'Fruits <b>',stickers:[]},{id:'p2',name:'Princess',stickers:[]}]";
const REND = (o = {}) => ({ id: 'R001', set: 'P001', pack_id: 'p1', preset: 'fountain', status: 'READY', bytes: 120 * 1024, url: '/out/particles/P001/renders/R001.webm', warnings: [], blocks: [], added_to: null, added: [], ...o });
const burst = (o = {}, pre = '') => run(`(()=>{${BURSTPACKS};delete SPB.P001;${pre};return spBurstHtml(${JSON.stringify(SET(o))})})()`);

test('Motion: a preset is lit before anyone picks one: the set\'s own motion, else burst', () => {
  const on = h => [...h.matchAll(/<button class="tab on" data-act=psbpreset data-id=P001 data-n=(\w+)/g)].map(m => m[1]);
  assert.deepEqual(on(burst()), ['burst']);
  assert.deepEqual(on(burst({ motion: { preset: 'vortex' } })), ['vortex']);
  assert.deepEqual(on(burst({ motion: null })), ['burst']);
  assert.deepEqual(on(burst({ motion: { preset: 'vortex' } }, "SPB.P001={pack:'p1',hint:'',preset:'rain',par:{},shown:{},pv:'',pvT:0,busy:0,again:0,size:{px:100,scale:1}}")), ['rain'], 'a pick still wins');
});

test('Motion: ONE preview for the pack, the five presets, Energy / Float / Swirl, count and spin under Advanced', () => {
  const h = burst();
  assert.equal((h.match(/<img id=psbpv-/g) || []).length, 1, 'one preview, not one row per sticker');
  assert.match(h, /id=psbpv-P001/);
  assert.doesNotMatch(h, /fx-sim|data-sid=/, 'no per-sticker row');
  for (const n of ['burst', 'fountain', 'vortex', 'rain', 'confetti']) assert.match(h, new RegExp(`data-act=psbpreset data-id=P001 data-n=${n}`));
  for (const l of ['Energy', 'Float', 'Swirl', 'Size']) assert.match(h, new RegExp(`<span>${l}<\\/span>`));
  assert.doesNotMatch(h, /Explosion|Gravity/);
  assert.match(h, /data-psbp=magnitude data-id=P001/, 'the engine’s keys travel unchanged: only the labels were renamed');
  assert.match(h, /<details class=fx-adv><summary>Advanced: particles, spin<\/summary>/);
  assert.match(h, /data-psbp=count/);
  assert.match(h, /data-psbp=spin/);
  assert.match(h, /data-psbp=particle_size data-id=P001/, 'Size is a main slider: how big the particles look (engine particle_size)');
  assert.match(h, /Advanced: sprite resolution/);
  assert.match(h, /value="100" data-psbpx/, 'sprites are fitted to 100 px by default');
  assert.doesNotMatch(h, /data-act=psbscale|Advanced: particle size/, 'one input-size control, not two that mean the same');
  assert.match(h, /for Fruits &lt;b&gt;/, 'a set in one pack is a burst for that pack');
});

test('Finish: Render says what it does and the checked file is the next thing you see', () => {
  const h = burst();
  assert.match(h, /data-act=psbrender data-id=P001>[^<]*Render</);
  assert.doesNotMatch(h, /the final 512 px sticker, checked/);
  assert.doesNotMatch(h, /<button[^>]*psbrender[^>]*>[^<]*credit/, 'a burst is free: no price anywhere');
});

test('a drawn set with nothing picked has no particles to move, and says how to get some', () => {
  const h = burst({ n_picked: 0, n_cells: 0, cells: [], picked: [] });
  assert.match(h, /Add sprites to preview/);
  assert.match(h, /Add sprites/);
  assert.doesNotMatch(h, /psbrender|psbpreset/, 'no control that cannot work');
  const st = burst({ n_picked: 0, n_cells: 0, cells: [], picked: [], source: { kind: 'stickers' } });
  assert.match(st, /psbrender/, 'a set of the pack’s own stickers bursts them');
  assert.match(st, /the pack’s own stickers fly/);
});

test('which pack: fixed when the set is in one, a choice when it is in several, any pack when it is in none', () => {
  assert.doesNotMatch(burst(), /<select/);
  const two = burst({ packs: ['p1', 'p2'], used_in: [{ id: 'p1', name: 'Fruits <b>' }, { id: 'p2', name: 'Princess' }] });
  assert.match(two, /<select[^>]*data-psbpack=P001/);
  assert.match(two, /<option value="p1" selected>Fruits &lt;b&gt;<\/option><option value="p2">Princess<\/option>/);
  const none = burst({ packs: [], used_in: [] });
  assert.match(none, /<select[^>]*data-psbpack=P001/);
  assert.match(none, /<option value="p1"/);
  assert.match(none, /<option value="p2"/);
  const hint = run(`(()=>{${BURSTPACKS};delete SPB.P001;spBurstState(${JSON.stringify(SET({ packs: ['p1', 'p2'] }))},'p2');return SPB.P001.pack})()`);
  assert.equal(hint, 'p2', 'the pack studio opens the burst for ITS pack');
});

test('the bursts of this pack: a clean one is added with one click, a warning is a sentence and the click is “Add anyway”, a Telegram limit cannot be added', () => {
  const rs = [REND(), REND({ id: 'R002', warnings: ['effect_tail_faded'], checks: [{ id: 'effect_tail_faded', verdict: 'WARN' }] }),
    REND({ id: 'R003', status: 'FAILED', blocks: ['size_budget'], checks: [{ id: 'size_budget', verdict: 'BLOCK' }], url: null }), REND({ id: 'R004', added_to: 'p1', added: [{ sticker: 'x', pack: 'p1' }] }),
    REND({ id: 'R005', pack_id: 'p2' })];
  const h = burst({ renders: rs });
  assert.match(h, /data-act=psbadd data-id=P001 data-r=R001 data-p=p1>Add to pack</);
  assert.match(h, /data-act=psbadd data-id=P001 data-r=R002 data-p=p1>Use it anyway · Add</);
  assert.match(h, /last frames were faded out/, 'the warning is in words');
  assert.doesNotMatch(h, /Warnings are only warnings: you decide/);
  assert.doesNotMatch(h, /data-r=R003/, 'a file Telegram would reject cannot be added');
  assert.match(h, /Over Telegram’s size limit\./);
  assert.match(h, /In pack ✓/, 'an added burst says where it is');
  assert.doesNotMatch(h, /data-r=R004/);
  assert.doesNotMatch(h, /R005/, 'a burst made for another pack is listed under that pack');
  assert.equal((h.match(/<video /g) || []).length, 3, 'a looping thumbnail for each burst that has a file');
});

test('the preview is asked of the set, with the pack, the preset, the person’s sliders and the size; the sliders then show what the server used', async () => {
  run(`${BURSTPACKS};SPL.sets=[${JSON.stringify(SET())}];SPL.detail={};delete SPB.P001;delete SPBS.P001;POSTS.length=0`);
  run("spBurstState(SPL.sets[0],'').preset='vortex';SPB.P001.par={gravity:.4,touched:1};SPB.P001.size={px:150,scale:2}");
  await run0("spBurstPreview('P001')");
  assert.deepEqual(run("POSTS"), [['/api/particles/P001/preview', { pack_id: 'p1', preset: 'vortex', params: { gravity: 0.4, sprite_px: 150, scale: 2 }, size: 256 }]]);
  run("POSTS.length=0;SPL.sets=null;delete SPB.P001");
});

test('Render posts the pack, preset and sliders to the set; Add posts the burst and the pack; neither runs without a pack', async () => {
  run(`${BURSTPACKS};SPL.sets=[${JSON.stringify(SET())}];SPL.detail={};delete SPB.P001;delete SPBS.P001;POSTS.length=0`);
  run("spBurstState(SPL.sets[0],'').preset='rain'");
  await run0("ACT.psbrender({dataset:{id:'P001'},disabled:false})");
  assert.deepEqual(run("POSTS"), [['/api/particles/P001/render', { pack_id: 'p1', preset: 'rain', params: { sprite_px: 100, scale: 1 } }]]);
  run("POSTS.length=0");
  await run0("ACT.psbadd({dataset:{id:'P001',r:'R001',p:'p1'},disabled:false})");
  assert.deepEqual(run("POSTS"), [['/api/particles/P001/add', { renders: ['R001'], pack_id: 'p1' }]]);
  run("POSTS.length=0;SPL.sets=[" + JSON.stringify(SET({ packs: [], used_in: [] })) + "];delete SPB.P001;delete SPBS.P001;spBurstState(SPL.sets[0],'')");
  await run0("ACT.psbrender({dataset:{id:'P001'},disabled:false})");
  assert.deepEqual(run("POSTS"), [], 'with no pack chosen nothing is sent');
  run("SPL.sets=null;delete SPB.P001");
});

test('the set card opens with Generate more AND the burst maker', () => {
  run(`${BURSTPACKS};SPL.open='P001';delete SPB.P001;delete SPM.P001`);
  const h = run(`spSetDetail(${JSON.stringify(SET())})`);
  assert.match(h, /data-psgen=P001/);
  assert.match(h, /data-psb=P001/);
  run("SPL.open=''");
});

test('every new burst action has a handler, and the burst listeners are the file’s own', () => {
  const src = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', '..', 'mirsal', 'console', 'particles.js'), 'utf8');
  for (const a of ['psbpreset', 'psbshuffle', 'psbrender', 'psbadd']) assert.match(src, new RegExp(`ACT\\.${a}=`), `${a} has a handler`);
  assert.match(src, /addEventListener\('input'/);
  assert.match(src, /addEventListener\('change'/);
});
