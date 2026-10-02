// The Prompt tab writes the prompts (2026-10-02): drafts per batch and kind, "with my prompt" only when the text really differs from the template, the buttons' conditions.
// The helpers are read out of generate.js and run with the few globals they use stubbed. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const FILE = path.join(__dirname, '..', '..', 'mirsal', 'console', 'generate.js');
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

function load({ live = true } = {}) {
  const sandbox = {
    esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])),
    liveReadyNow: () => live,
    keptStills: g => g.stickers.filter(t => t.status === 'READY'),
  };
  const body = ['const PD={}', 'const pdKey=', 'const sentVideoPrompt=', 'const pdText=', 'const pdBase=', 'const pdCustom=', 'function pdFoot(g,kind)'].map(statement).join('\n');
  const api = new Function(...Object.keys(sandbox), body + '\nreturn {PD,pdKey,pdText,pdCustom,pdFoot,sentVideoPrompt};')(...Object.values(sandbox));
  return { ...api };
}

const batch = (extra = {}) => ({ number: 5, sheet_prompt: 'SHEET TEMPLATE', video_prompt: 'VIDEO TEMPLATE', video_sheets: [], stickers: [{ status: 'READY' }, { status: 'READY' }], ...extra });

test('without a draft the box shows the template and nothing is custom', () => {
  const h = load();
  const g = batch();
  assert.equal(h.pdText(g, 'sheet'), 'SHEET TEMPLATE');
  assert.equal(h.pdCustom(g, 'sheet'), false);
  assert.match(h.pdFoot(g, 'sheet'), /Generate sheet<span/, 'the label does not say "with my prompt"');
  assert.match(h.pdFoot(g, 'sheet'), /data-act=pgreset[^>]* hidden/, 'nothing to reset');
});

test('a changed text is custom, an identical one or an empty one is not', () => {
  const h = load();
  const g = batch();
  h.PD[h.pdKey(5, 'sheet')] = 'My own wording';
  assert.equal(h.pdCustom(g, 'sheet'), true);
  assert.match(h.pdFoot(g, 'sheet'), /Generate sheet with my prompt/);
  assert.doesNotMatch(h.pdFoot(g, 'sheet'), /data-act=pgreset[^>]* hidden/, 'a draft can be reset');
  h.PD[h.pdKey(5, 'sheet')] = 'SHEET TEMPLATE';
  assert.equal(h.pdCustom(g, 'sheet'), false, 'typing the template back is the template');
  h.PD[h.pdKey(5, 'sheet')] = '   ';
  assert.equal(h.pdCustom(g, 'sheet'), false, 'an empty box is never sent as a prompt');
});

test('drafts are per batch and per kind', () => {
  const h = load();
  h.PD[h.pdKey(5, 'sheet')] = 'mine';
  assert.equal(h.pdText(batch({ number: 6 }), 'sheet'), 'SHEET TEMPLATE');
  assert.equal(h.pdText(batch(), 'video'), 'VIDEO TEMPLATE');
});

test('the video box shows the prompt that was actually sent once there is one', () => {
  const h = load();
  const g = batch({ video_sheets: [{ id: 'A1', status: 'SLICED', video_prompt_sent: 'WHAT WAS SENT' }] });
  assert.equal(h.pdText(g, 'video'), 'WHAT WAS SENT');
  assert.match(h.pdFoot(g, 'video'), /pgvideo[^>]* disabled/, 'a sliced sheet is not animated twice');
});

test('the buttons are off without Higgsfield and the video needs a kept sticker', () => {
  const off = load({ live: false });
  assert.match(off.pdFoot(batch(), 'sheet'), /pgsheet[^>]* disabled/);
  assert.match(off.pdFoot(batch(), 'video'), /pgvideo[^>]* disabled/);
  const on = load();
  assert.doesNotMatch(on.pdFoot(batch(), 'sheet'), /pgsheet[^>]* disabled/);
  assert.doesNotMatch(on.pdFoot(batch(), 'video'), /pgvideo[^>]* disabled/);
  assert.match(on.pdFoot(batch({ stickers: [{ status: 'FAILED' }] }), 'video'), /pgvideo[^>]* disabled/);
});
