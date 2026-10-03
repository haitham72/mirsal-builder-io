// The left sheet is clickable per slice (2026-10-03): every cell of the still sheet and of the video sheet is a full-cell hit area. A blocked cell that
// the server says may be allowed carries the allow click (gsallow for a still, gallow for an animation); any other cell opens the tile. The hover and the
// label say the reason in plain words, never a raw check id. The statements are read out of generate.js and run with the few globals they use stubbed.
// Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const src = fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'generate.js'), 'utf8');

/** One whole top-level statement of generate.js: from `marker` to the next line that starts in column 0. */
function statement(marker) {
  const i = src.indexOf(marker);
  assert.notEqual(i, -1, `${marker} is not in generate.js`);
  const lines = src.slice(i).split('\n');
  const out = [lines[0]];
  for (const ln of lines.slice(1)) {
    if (ln && !/^\s/.test(ln)) break;
    out.push(ln);
  }
  return out.join('\n');
}

function load() {
  const sandbox = { esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])) };
  const body = ['const CAT=', 'const CATORDER=', 'const CATOF=', 'const WARNWHY=', 'const plainWarn=', 'const ANIMWHY=', 'const ALW=', 'const whyOf=',
    'const canAllow=', 'const hasAllowed=', 'const clickAllow=', 'const isOob=', 'const oobNote=', 'const cellState=', 'const CELLTXT=',
    'function issuesOf(', 'function mark(', 'function chip(', 'const sheetOf=', 'const LAY=', 'const layoutOfCell=', 'function issueSvg(', 'function allowAllRow('].map(statement).join('\n');
  return new Function(...Object.keys(sandbox), body + '\nreturn {issueSvg,allowAllRow,chip,ALW,LAY};')(...Object.values(sandbox));
}

const CELL = [0, 0, 100, 100];
const ALLOW = {
  still: { can: [1], allowed: [3], undo: [3], why: { 1: 'the character touches the edge of its cell', 2: 'almost nothing was found in this cell' }, final: { 2: 'Nothing was cut from this cell, so there is no picture to use.' } },
  animation: { can: [4], allowed: [], undo: [], why: { 4: 'the loop does not close' }, final: {} },
};
const T = (i, o = {}) => ({ index: i, status: 'READY', reason: 'inside_cell', metrics: { cell: CELL }, review: { still: 'APPROVED' }, ...o });
const G = (stickers, allow = ALLOW) => ({ number: 7, source: { sheet_size: [900, 900] }, video_sheets: [], allow, stickers });

test('a blocked still that may be allowed is a full-cell allow button with the reason in plain words', () => {
  const h = load();
  const svg = h.issueSvg(G([T(1, { status: 'FAILED' })]), 'still');
  assert.match(svg, /data-act=gsallow data-g=7 data-i=1/);
  assert.match(svg, /role="button"/);
  assert.match(svg, /the character touches the edge of its cell/);
  assert.match(svg, /click to use it anyway/);
  assert.doesNotMatch(svg, /inside_cell/, 'never a raw check id on hover');
});

test('a still that cannot be allowed opens the tile and says why, with no allow click', () => {
  const h = load();
  const svg = h.issueSvg(G([T(2, { status: 'FAILED', reason: 'empty_subject' })]), 'still');
  assert.match(svg, /data-act=gopen data-g=7 data-i=2/);
  assert.match(svg, /almost nothing was found/);
  assert.match(svg, /no picture to use/);
  assert.doesNotMatch(svg, /gsallow|gallow/);
});

test('an allowed still offers taking the permission back from the sheet', () => {
  const h = load();
  const svg = h.issueSvg(G([T(3, { status: 'FAILED' })]), 'still');
  assert.match(svg, /data-act=gsallow data-g=7 data-i=3/);
  assert.match(svg, /click to take the permission back/);
});

test('a cell with no mark is an invisible hit area that opens the tile', () => {
  const h = load();
  const svg = h.issueSvg(G([T(1)], {}), 'still');
  assert.match(svg, /class=sh-hit data-act=gopen data-g=7 data-i=1/);
  assert.match(svg, /aria-label="S1: accepted · click to open"/);
});

test('an animation that may be allowed carries the animation click; the kind never leaks across stages', () => {
  const h = load();
  h.LAY.set('70', { slots: [{ slot: 4, rect: [0, 0, 50, 50] }] });
  const g = G([T(4, { anim_status: 'FAILED', anim_reason: 'loop_seam' })]);
  g.video_sheets = [{ id: 0, status: 'READY' }];
  const svg = h.issueSvg(g, 'anim');
  assert.match(svg, /data-act=gallow data-g=7 data-i=4/);
  assert.match(svg, /the loop does not close/);
  assert.doesNotMatch(svg, /gsallow/, 'a still click never appears on the video sheet');
  const still = h.issueSvg(G([T(1, { status: 'FAILED' })]), 'still');
  assert.doesNotMatch(still, /gallow/, 'an animation click never appears on the still sheet');
});

test('the bulk control counts per kind what is allow-able now', () => {
  const h = load();
  const g = G([T(1)]);
  const still = h.allowAllRow(g, 'still');
  assert.match(still, /data-act=gallowall data-g=7 data-kind=still data-allow=1/);
  assert.match(still, /Use all anyway \(1\)/);
  assert.match(still, /data-kind=still data-allow=0/);
  assert.match(still, /Take all back \(1\)/);
  assert.match(still, /or click a cell on the sheet/);
  const anim = h.allowAllRow(g, 'animation');
  assert.match(anim, /data-kind=animation/);
  assert.match(anim, /Use all anyway \(1\)/);
  assert.doesNotMatch(anim, /Take all back/);
  assert.equal(h.allowAllRow(G([], { still: { can: [], allowed: [], undo: [], why: {}, final: {} }, animation: { can: [], allowed: [], undo: [], why: {}, final: {} } }), 'still'), '');
});

test('a still chip allows on click exactly when the tile does', () => {
  const h = load();
  const g = G([T(1, { status: 'FAILED' })]);
  assert.match(h.chip(g, g.stickers[0], 'still'), /data-act=gsallow/);
  assert.match(h.chip(g, g.stickers[0], 'still'), /click to use it anyway/);
  const plain = h.chip(G([T(9)], {}), T(9), 'still');
  assert.match(plain, /data-act=gopen/);
  assert.doesNotMatch(plain, /gsallow/);
});
