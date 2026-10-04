// The pack's particle studio and the sticker's one line (2026-10-03, docs/particles_plan.md section 5): one set belongs to the pack, so the pack page carries the
// particle studio (its sets as shared cards, its bursts with Add, Make particles for this pack / Use an existing set) and a sticker shows one line
// linking to it. The statements are read out of packs.js and run with the few globals they use stubbed. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const DIR = path.join(__dirname, '..', '..', 'mirsal', 'console');
const src = fs.readFileSync(path.join(DIR, 'packs.js'), 'utf8');
const app = fs.readFileSync(path.join(DIR, 'app.js'), 'utf8');

/** One whole top-level statement of packs.js: from `marker` to the next line that starts in column 0. */
function statement(marker) {
  const i = src.indexOf(marker);
  assert.notEqual(i, -1, `${marker} is not in packs.js`);
  const lines = src.slice(i).split('\n');
  const out = [lines[0]];
  for (const ln of lines.slice(1)) {
    if (ln && !/^\s/.test(ln)) break;
    out.push(ln);
  }
  return out.join('\n');
}

function load(pkpt) {
  const counts = [];
  const sandbox = {
    esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])),
    ic: n => `<svg data-i=${n}></svg>`,
    PKPT: pkpt,
    ptBody: (j,s) => '<owner-gallery>'+(j.rows||[]).map(x=>x.id).join(',')+'</owner-gallery>',
    ptCount: j => (j.rows||[]).length + (j.drafts||[]).length,
    ptCounts: pid => { counts.push(pid); },
    spSetCard: s => `<setcard data-for=${s.id}>`,
  };
  const body = ['const ptWhy=', 'const ptPackName=', 'function pkPsHtml(', 'function pkBurst(', 'function pkStickerLine('].map(statement).join('\n');
  const f = new Function(...Object.keys(sandbox), body + '\nreturn {pkPsHtml,pkBurst,pkStickerLine};')(...Object.values(sandbox));
  return { ...f, counts };
}

const SETS = [{ id: 'P001', name: 'Barbie <hearts>',owner:[{sticker_id:'a1'}] }, { id: 'P002', name: 'Bats',owner:[{sticker_id:'a2'}] }];
const BURSTS = [{ set: 'P001', id: 'R001', set_name: 'Barbie hearts', preset: 'burst', status: 'READY', url: '/out/particles/P001/renders/R001.webm', warnings: ['effect_tail_faded'], blocks: [], added_to: null }];

test('while the pack’s sets are not read yet the studio says so and asks for nothing', () => {
  const h = load({ sets: {}, bursts: {} });
  const s = h.pkPsHtml({ id: 'p1', name: 'Barbie' });
  assert.match(s, /Particle studio/);
  assert.match(s, /Reading the pack's particle sets/);
  assert.doesNotMatch(s, /data-act=/);
});

test('the studio shows the pack’s sets as shared cards and both ways to get one', () => {
  const h = load({ sets: { p1: SETS }, bursts: {} });
  const s = h.pkPsHtml({ id: 'p1', name: 'Barbie' });
  assert.match(s, /particles made for the stickers in this pack/);
  assert.match(s, /data-act=psmakepack data-p=p1>Make particles for this pack</);
  assert.match(s, /data-act=pspickpack data-p=p1>Use particles of another sticker</);
  assert.match(s, /<setcard data-for=P001>/);
  assert.match(s, /<setcard data-for=P002>/);
  const empty = load({ sets: { p1: [] }, bursts: {} }).pkPsHtml({ id: 'p1', name: 'Barbie' });
  assert.match(empty, /No particles made for these stickers yet/);
  assert.match(empty, /data-act=psmakepack/);
});

test('bursts are wired to the set’s routes: a ready one is added with a click, an added one says so, a failed one says why and cannot be added', () => {
  const ok = { ...BURSTS[0], id: 'R002', warnings: [] };
  const done = { ...BURSTS[0], id: 'R003', warnings: [], added_to: 'p1' };
  const bad = { ...BURSTS[0], id: 'R004', status: 'FAILED', blocks: ['size_budget'], warnings: [], url: null };
  const h = load({ sets: { p1: [] }, bursts: { p1: [BURSTS[0], ok, done, bad] } });
  const s = h.pkPsHtml({ id: 'p1', name: 'Barbie' });
  assert.match(s, /Bursts rendered for this pack/);
  assert.match(s, /<video src="\/out\/particles\/P001\/renders\/R001\.webm" autoplay loop muted/);
  assert.match(s, /Barbie hearts/);
  assert.match(s, /burst · ready/);
  assert.match(s, /data-act=psbadd data-id=P001 data-r=R002 data-p=p1>Add to this pack</, 'the same handler as the set card’s burst maker');
  assert.match(s, /data-act=psbadd data-id=P001 data-r=R001 data-p=p1>Add anyway</, 'a warning is a warning: the person decides');
  assert.doesNotMatch(s, /data-r=R003/, 'already in the pack: no second Add');
  assert.doesNotMatch(s, /data-r=R004/, 'a file Telegram would reject cannot be added');
  assert.match(s, /size_budget|size budget/, 'and it says why');
  assert.doesNotMatch(s, /data-act=ptadd|data-act=psdel/, 'no per-sticker Add and no delete of a burst');
});

test('a burst’s warnings are sentences, a missing file says so', () => {
  const h = load({ sets: {}, bursts: {} });
  assert.match(h.pkBurst(BURSTS[0]), /effect tail faded/, 'FXWHY lives in effects.js: here the id stays readable');
  assert.match(h.pkBurst({ ...BURSTS[0], url: null, missing: true }), /file missing/);
});

test('a sticker shows only its own particles and scoped creation',()=>{
 const h=load({sets:{},bursts:{}});assert.match(h.pkStickerLine({id:'a1',pack_id:'p1'}),/Reading the sticker/);
 const none=load({sets:{p1:[]},bursts:{}});assert.match(none.pkStickerLine({id:'a1',pack_id:'p1'}),/data-act=ptmake data-p=p1 data-s=a1>Create particles/);
 const reading=load({sets:{p1:SETS},bursts:{}}).pkStickerLine({id:'a1',pack_id:'p1'});
 assert.match(reading,/Reading the sticker/);assert.match(reading,/>New version</);
 const some=load({sets:{p1:SETS},bursts:{},d:{a1:{rows:[{id:'P001',version:1}],drafts:[]}}}),line=some.pkStickerLine({id:'a1',pack_id:'p1'});
 assert.match(line,/1 saved version/);assert.doesNotMatch(line,/Bats|P002|No particles yet/);assert.match(line,/New version/);assert.match(line,/<owner-gallery>P001/);
});

test('the Library has a Particles tab on the shared switch, and every new action has a handler', () => {  assert.match(app, /data-act=libtab data-t=particles>Particles</, 'the third Library tab');
  const all = src + fs.readFileSync(path.join(DIR, 'particles.js'), 'utf8') + fs.readFileSync(path.join(DIR, 'effects.js'), 'utf8');
  for (const act of ['psopen', 'psassign', 'psassignsave', 'psunassign', 'psdup', 'psrename', 'psdel', 'psrestore', 'pspickcell', 'pspickcancel', 'pspicksave', 'pspickset', 'psmakepack', 'pspickpack', 'fxuseset']) {
    assert.match(all, new RegExp(`ACT\\.${act}=`), `${act} has a handler`);
    assert.match(all, new RegExp(`data-act=${act}\\b`), `${act} is used`);
  }
});

test('the chrome says particles, not pieces, on every screen', () => {
  const bad = [];
  for (const f of fs.readdirSync(DIR).filter(x => x.endsWith('.js'))) {
    let code = fs.readFileSync(path.join(DIR, f), 'utf8');
    code = code.replace(/\/\*.*?\*\//gs, '');
    code = code.replace(/fx-pieces|\w*[Pp]iece\w*/g, '');
    const m = code.match(/\bpieces?\b/i);
    if (m) bad.push(`${f}: ${m[0]}`);
  }
  assert.deepEqual(bad, [], 'a person reads particles everywhere (identifiers like fxPieces are not chrome)');
});
