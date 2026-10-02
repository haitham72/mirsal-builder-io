// The markup of the Earlier-batches cards in live.js (the DOM half runs only in a browser). The three statements are read out of the file and run with the few globals
// they use stubbed, so the card is checked for real: the sheet's own grid, the plain title, and the fold that stays inside the card.
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
    HB: { items: [], more: false, total: 0 },
    document: { getElementById: () => null },
  };
  const body = ['const histGrid=', 'const histItem=', 'function drawHist'].map(statement).join('\n');
  const api = new Function(...Object.keys(sandbox), body + '\nreturn {histGrid,histItem,drawHist};')(...Object.values(sandbox));
  return { ...sandbox, ...api, env: sandbox };          // env: the globals the statements closed over (mutate them, not the copy)
}

test('a 3x3 batch is a card of nine cells in three columns, a 2x2 of four in two', () => {
  const hx = load();
  const three = hx.histItem(BATCH([3, 3], [1, 5]));
  assert.match(three, /class=lv-hth style="--c:3"/);
  assert.equal((three.match(/<img /g) || []).length, 9);
  assert.match(three, /title="S1 · animated"/);
  assert.match(three, /title="S5 · animated"/);
  assert.ok(!/title="S2 · animated"/.test(three), 'S2 is not animated');
  const two = hx.histItem(BATCH([2, 2], [4]));
  assert.match(two, /class=lv-hth style="--c:2"/);
  assert.equal((two.match(/<img /g) || []).length, 4);
});

test('the card says which batch it is and a cell with no picture is a cell, not a broken picture', () => {
  const hx = load();
  const html = hx.histItem(BATCH([3, 3], [1, 5, 9], [2]));
  assert.match(html, /A Sad Owl/);
  assert.match(html, /G005 · 9 stickers · 3 animated · edited 2 d ago/);
  assert.equal((html.match(/<img /g) || []).length, 8);
  assert.match(html, /<span class=lv-hnoimg title="S2 · pending">/);
  assert.ok(!/src="[^"]*null/.test(html), 'no src built from a missing png');
});

test('a click expands the card where it stands: the fold is inside it, nothing scrolls away', () => {
  const hx = load();
  const it = BATCH([3, 3]);
  const folded = hx.histItem(it);
  assert.match(folded, /class="lv-hcard"/);
  assert.match(folded, /data-act=hbx data-id=5/);
  assert.ok(!folded.includes('detail of'), 'a card starts folded');
  hx.HX.open.add(5);
  const open = hx.histItem(it);
  assert.match(open, /class="lv-hcard open"/);
  assert.ok(open.includes('detail of G005'), 'the fold lives inside the card');
  assert.ok(open.indexOf('detail of') > open.indexOf('class="lv-hcard'), 'the fold is the card’s own content');
  assert.ok(!open.includes('scrollIntoView'));
  assert.ok(!open.includes('data-act=hopen'), 'no Open in Studio: every click only expands the card in place');
});

test('every card expands on its own and they stack: opening one never closes another', () => {
  const hx = load();
  const cards = [1, 2, 3, 4].map(n => ({ ...BATCH([3, 3]), id: n, generation_id: `G00${n}` }));
  hx.HX.open = new Set([1, 3]);
  const html = cards.map(hx.histItem).join('');
  assert.equal((html.match(/class="lv-hcard open/g) || []).length, 2, 'two cards open at once');
  for (const n of [1, 3]) assert.ok(html.includes(`detail of G00${n}`), `G00${n} shows its own fold`);
  assert.equal((html.match(/detail of/g) || []).length, 2, 'the two that are closed show nothing');
  assert.ok(html.indexOf('detail of G001') < html.indexOf('detail of G003'), 'each fold sits under its own card, in order');
});

test('the batch open in the Studio is marked on its card', () => {
  const hx = load();
  hx.SES.gens = [5];
  assert.match(hx.histItem(BATCH([3, 3])), /class="lv-hcard on"/);
});

test('the title above the cards is plain text and the cards are always there', () => {
  const hx = load();
  const el = { innerHTML: '', className: '' };
  hx.env.document.getElementById = id => (id === 'ghist' ? el : null);
  hx.env.HB.items = [BATCH([3, 3])];
  hx.env.HB.total = 7;
  hx.env.HB.more = true;
  hx.drawHist();
  assert.match(el.innerHTML, /<span class=lv-ht>Earlier batches<\/span>/);
  assert.match(el.innerHTML, /7 in total/);
  assert.equal((el.innerHTML.match(/class="lv-hcard/g) || []).length, 1);
  assert.match(el.innerHTML, /data-act=hmore/, 'Load more when there are more');
  assert.ok(!/<button[^>]*lv-hh/.test(el.innerHTML), 'the title is not a button');
  hx.env.HB.total = 1;
  hx.env.HB.more = false;
  hx.drawHist();
  assert.ok(!el.innerHTML.includes('data-act=hmore'), 'no Load more on the last page');
});
