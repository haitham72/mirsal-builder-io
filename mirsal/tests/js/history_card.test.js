// The markup of the Earlier-batches column and of an open batch's card in live.js (the DOM half runs only in a browser). The statements are read out of the file and run with the few
// globals they use stubbed, so the markup is checked for real: the sheet's own grid, the plain title, one row per batch, and the card that only an opened batch gets.
// Run: node --test tests/js     (MIRSAL_LIVE_JS points the test at another copy of live.js)
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const FILE = process.env.MIRSAL_LIVE_JS || path.join(__dirname, '..', '..', 'mirsal', 'console', 'live.js');
const src = fs.readFileSync(FILE, 'utf8');

/** One whole top-level statement of live.js: from `marker` to the next line that starts in column 0. */
function statement(marker) {
  const i = src.indexOf(marker);
  assert.notEqual(i, -1, `${marker} is not in live.js`);
  const lines = src.slice(i).split('\n');
  const out = [lines[0]];
  for (const ln of lines.slice(1)) {
    if (ln && !/^\s/.test(ln)) break;
    out.push(ln);
  }
  return out.join('\n');
}

const BATCH = (grid, animated = [], noPng = []) => ({
  id: 5, generation_id: 'G005', prompt: 'a sad_owl', stage: 'sliced', ready: grid[0] * grid[1], animated: animated.length,
  edited: 0, created: 0, outline_px: 2, grid,
  cells: Array.from({ length: grid[0] * grid[1] }, (_, n) => ({
    index: n + 1, row: Math.floor(n / grid[1]), col: n % grid[1],
    png: noPng.includes(n + 1) ? null : `slices/S${n + 1}.png?e=7`,
    status: noPng.includes(n + 1) ? 'PENDING' : 'READY', animated: animated.includes(n + 1),
  })),
});

function load() {
  const sandbox = {
    esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])),
    titleCase: s => s.replace(/(^|\s)([a-z])/g, (_, a, b) => a + b.toUpperCase()),
    ago: () => '2 d ago',
    SES: { gens: [] },
    HX: { open: new Set(), det: {} },
    hxBatch: it => `<div class=lv-hdet>detail of ${it.generation_id}</div>`,
    HB: { items: [], more: false, total: 0, loaded: true },
    route_: 'library',
    histCol: () => {},
    document: { getElementById: () => null },
  };
  const body = ['const histTitle=', 'const histInfo=', 'const histGrid=', 'const histRow=', 'const histItem=', 'function histColHTML', 'function drawHist'].map(statement).join('\n');
  const api = new Function(...Object.keys(sandbox), body + '\nreturn {histGrid,histRow,histItem,histColHTML,drawHist};')(...Object.values(sandbox));
  return { ...sandbox, ...api, env: sandbox };          // env: the globals the statements closed over (mutate them, not the copy)
}

test('a 3x3 batch is nine cells in three columns, a 2x2 four in two', () => {
  const hx = load();
  const three = hx.histRow(BATCH([3, 3], [1, 5]));
  assert.match(three, /class=lv-hth style="--c:3"/);
  assert.equal((three.match(/<img /g) || []).length, 9);
  assert.match(three, /title="S1 · animated"/);
  assert.match(three, /title="S5 · animated"/);
  assert.ok(!/title="S2 · animated"/.test(three), 'S2 is not animated');
  const two = hx.histRow(BATCH([2, 2], [4]));
  assert.match(two, /class=lv-hth style="--c:2"/);
  assert.equal((two.match(/<img /g) || []).length, 4);
});

test('the row says which batch it is and a cell with no picture is a cell, not a broken picture', () => {
  const hx = load();
  const html = hx.histRow(BATCH([3, 3], [1, 5, 9], [2]));
  assert.match(html, /A Sad Owl/);
  assert.match(html, /G005 · 9 stickers · 3 animated · edited 2 d ago/);
  assert.equal((html.match(/<img /g) || []).length, 8);
  assert.match(html, /<span class=lv-hnoimg title="S2 · pending">/);
  assert.ok(!/src="[^"]*null/.test(html), 'no src built from a missing png');
});

test('a row is one button that opens the batch; an open batch and the batch the Studio works on are marked', () => {
  const hx = load();
  const it = BATCH([3, 3]);
  const closed = hx.histRow(it);
  assert.match(closed, /^<button class="lv-hrow" data-act=hbx data-id=5 aria-pressed=false/);
  assert.ok(!closed.includes('detail of'), 'a row never carries the batch itself');
  hx.HX.open.add(5);
  assert.match(hx.histRow(it), /class="lv-hrow on"[^>]*aria-pressed=true/);
  hx.SES.gens = [5];
  assert.match(hx.histRow(it), /class="lv-hrow on cur"/);
  assert.ok(!hx.histRow(it).includes('data-act=hopen'), 'only the credits pill opens a batch as the Studio session');
});

test('an open card is that batch: its header closes it and its own detail sits under it', () => {
  const hx = load();
  const open = hx.histItem(BATCH([3, 3]));
  assert.match(open, /^<div class="lv-hcard open" data-id=5>/);
  assert.match(open, /data-act=hbx data-id=5 aria-expanded=true/);
  assert.ok(open.includes('detail of G005'), 'the per-sticker history and captions stay in the card');
  assert.ok(open.includes('Reading the batch…'), 'until the batch is read the card says so');
  assert.ok(open.indexOf('detail of') > open.indexOf('Reading the batch'), 'the detail is below the Studio view');
});

test('the column title is plain text, every batch is a row and nothing says Load more', () => {
  const hx = load();
  hx.env.HB.items = Array.from({ length: 120 }, (_, n) => ({ ...BATCH([3, 3]), id: n + 1, generation_id: `G${n + 1}` }));
  hx.env.HB.total = 120;
  const html = hx.histColHTML();
  assert.match(html, /<h1>Earlier batches<\/h1>/);
  assert.match(html, /120 in total/);
  assert.equal((html.match(/class="lv-hrow/g) || []).length, 120, 'the whole list is rendered, not one page');
  assert.ok(!/hmore|Load more/.test(html), 'no pagination button');
  assert.ok(!/<button[^>]*lv-hh/.test(html), 'the title is not a button');
  hx.env.HB.items = [];
  hx.env.HB.total = 0;
  assert.match(hx.histColHTML(), /No batches yet/);
});

test('the Studio shows only the batches that are open, each as a card, in the main area', () => {
  const hx = load();
  const el = { innerHTML: '' };
  hx.env.document.getElementById = id => (id === 'ghist' ? el : null);
  hx.env.HB.items = [1, 2, 3, 4].map(n => ({ ...BATCH([3, 3]), id: n, generation_id: `G00${n}` }));
  hx.drawHist();
  assert.equal(el.innerHTML, '', 'nothing open: nothing in the main area');
  hx.env.HX.open = new Set([1, 3]);
  hx.drawHist();
  assert.match(el.innerHTML, /<span class=lv-ht>Open batches<\/span>/);
  assert.equal((el.innerHTML.match(/class="lv-hcard open/g) || []).length, 2, 'two cards open at once');
  assert.ok(el.innerHTML.indexOf('detail of G001') < el.innerHTML.indexOf('detail of G003'), 'each detail sits under its own card, in order');
  assert.ok(!el.innerHTML.includes('detail of G002'), 'a closed batch shows nothing');
});
