// The Studio view that an expanded card in Earlier batches renders: the same counts, the same bar and the same step header as the session, but per batch
// (`gstats` / `barHtml` / `studioFor` are read out of generate.js and run with the few globals they use stubbed). Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const FILE = process.env.MIRSAL_GENERATE_JS || path.join(__dirname, '..', '..', 'mirsal', 'console', 'generate.js');
const src = fs.readFileSync(FILE, 'utf8');

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

/** One batch as the server sends it: `sticker` per sticker, `keep` / `drop` decide what is in the set. */
function batch(number, { keep = 9, dropped = 0, anim = 0, hasVideo = true, stage = 'pack_final' } = {}) {
  const stickers = [];
  for (let i = 1; i <= 9; i++) {
    stickers.push({
      index: i, key: `k${i}`, emoji: '🙂', status: i <= keep + dropped ? 'READY' : 'FAILED',
      review: { still: i <= keep ? 'APPROVED' : i <= keep + dropped ? 'REJECTED' : 'PENDING', anim: 'PENDING' },
      anim_status: i <= anim ? 'READY' : 'NOT_REQUESTED', anim_reason: null,
    });
  }
  return {
    number, generation_id: `G${String(number).padStart(3, '0')}`, stage, prompt: 'a sad owl', outline_px: 12, erode_px: 0,
    grid: [3, 3], template_id: 'sheet_3x3', template_version: 2, plan_source: 'stub', key_colour: 'green',
    error: null, source: { subject: 'sad_owl', subject_id: 1, has_video: hasVideo }, stickers, added: {},
  };
}

function load() {
  const sandbox = {
    esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])),
    ic: () => '•',
    ANIM: new Set(),
    SES: { gens: [], off: [], pack: '' },
    GS: { tab: 'stickers' },
    LIB: { packs: [] },
    making: g => ['requested', 'sheet_picked', 'keyed'].includes(g.stage) && !g.error,
    animPhase: g => g.stickers.some(t => ['READY', 'FAILED'].includes(t.anim_status)),
    processing: g => g.stickers.some(t => t.anim_status === 'PROCESSING'),
    hasVid: g => !!g.source.has_video,
    keptOf: g => g.stickers.filter(t => t.status === 'READY' && t.review.still !== 'REJECTED' && !(g.stickers.some(x => x.anim_status === 'READY') && t.review.anim === 'REJECTED')),
    keptStills: g => g.stickers.filter(t => t.status === 'READY' && t.review.still !== 'REJECTED'),
    nAdded: () => 0,
    packById: () => null,
    stepsHtml: (s, gid, tab) => `<header data-g="${gid}" data-tab="${tab}" data-n="${s.n}"></header>`,
    gbodyHtml: (gs, c, gid, tab) => `<body data-g="${gid}" data-tab="${tab}" data-n="${c.n}">${gs.length} batch</body>`,
  };
  const body = ['function gstats(gs', 'function barHtml(s', 'const CT={}', 'const cardTab=g=>', 'function studioFor(g)']
    .map(statement).join('\n');
  const api = new Function(...Object.keys(sandbox), body + '\nreturn {gstats,barHtml,CT,cardTab,studioFor};')(...Object.values(sandbox));
  return { ...sandbox, ...api, env: sandbox };
}

test('a card counts only its own batch', () => {
  const hx = load();
  const g = batch(5, { keep: 7, dropped: 1, anim: 3 });
  const s = hx.gstats([g]);
  assert.equal(s.n, 7, 'the 7 approved stickers are in the set; the dropped one is not');
  assert.equal(s.ready, true);
  assert.equal(s.gs.length, 1);
  assert.equal(s.inc.length, 1);
  assert.equal(s.done, 3, 'three animations are ready');
  assert.equal(s.tot, 7, 'every kept still can be animated (this batch has a prepared video)');
  assert.equal(s.busyAnim, false);
  assert.equal(s.allAdded, false);
  const two = hx.gstats([batch(5), batch(6)]);
  assert.equal(two.n, 18, 'two batches count together (the session case)');
  assert.equal(two.todoAnim.length, 2);
});

test('the bar of a card names its batch, the bar of the session names none', () => {
  const hx = load();
  const g = batch(5);
  const scoped = hx.barHtml(hx.gstats([g]), 5);
  assert.match(scoped, /data-act=gadd data-g=5/);
  assert.match(scoped, /data-act=ganimate data-g=5/);
  const session = hx.barHtml(hx.gstats([g]));
  assert.ok(!/data-g=/.test(session), 'the session bar keeps acting on every included batch');
  assert.match(session, /Animate/);
});

test('a card renders the Studio view: the header, the body and the bar, all scoped to that batch', () => {
  const hx = load();
  const g = batch(5, { anim: 4 });
  const html = hx.studioFor(g);
  assert.match(html, /<header data-g="5" data-tab="anim"/, 'an animated batch opens on its Animation step');
  assert.match(html, /<body data-g="5" data-tab="anim"/);
  assert.match(html, /data-act=gadd data-g=5/, 'its pack button is its own');
});

test('a batch with no animation opens on its Stickers step', () => {
  const hx = load();
  const html = hx.studioFor(batch(6, { anim: 0 }));
  assert.match(html, /<body data-g="6" data-tab="stickers"/);
});

test('a card counts its batch even when the session has switched that batch off', () => {
  const hx = load();
  hx.env.SES.off = [5];
  assert.equal(hx.gstats([batch(5)]).n, 0, 'the session: switched off means not in the set');
  const html = hx.studioFor(batch(5));
  assert.match(html, /data-n="9"/, 'the card: its own batch is always there, it is not part of the session');
});

test('each card keeps its own step: opening one never changes another', () => {
  const hx = load();
  const a = batch(5, { anim: 4 }), b = batch(6, { anim: 0 });
  assert.equal(hx.cardTab(a), 'anim');
  assert.equal(hx.cardTab(b), 'stickers');
  hx.CT[6] = 'plan';
  assert.equal(hx.cardTab(b), 'plan');
  assert.equal(hx.cardTab(a), 'anim', 'card 5 is untouched');
  assert.match(hx.studioFor(a), /data-tab="anim"/);
  assert.match(hx.studioFor(b), /data-tab="plan"/);
});
