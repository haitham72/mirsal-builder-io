// P3 of the UI/UX spec: the pack screen offers Delete as a labelled button, and its confirmation says exactly what leaves and what stays (nothing is destroyed silently): the stickers
// that came from a batch stay in their batch and can be added again, the ones that exist only in this pack (editor renders, bursts) go with it, the particle sets stay in the Library.
// The statements are read out of packs.js. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const src = fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'packs.js'), 'utf8');
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
const sandbox = { esc: s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])) };
const { pkDelText } = new Function(...Object.keys(sandbox), statement('function pkDelText(') + '\nreturn {pkDelText};')(...Object.values(sandbox));

const st = (id, src = {}) => ({ id, name: id, source: src });

test('the confirmation counts what stays in its batch and what exists only here', () => {
  const t = pkDelText({ name: 'Barbie', stickers: [st('a', { generation: 'G012', index: 1 }), st('b', { generation: 'G012', index: 2 }), st('c', { generation: 'G013', index: 4 }), st('d'), st('e', { effect: 'E001' })] });
  assert.match(t, /Delete the pack “Barbie”\?/);
  assert.match(t, /3 of its 5 stickers came from batches \(G012, G013\) and stay there: you can add them to a pack again/);
  assert.match(t, /2 exist only in this pack/);
  assert.match(t, /particle sets stay in the Library/);
});

test('a pack of batch stickers only says nothing is lost; an empty pack is short', () => {
  const t = pkDelText({ name: 'Cats', stickers: [st('a', { generation: 'G001', index: 1 })] });
  assert.match(t, /1 of its 1 stickers came from batches/);
  assert.doesNotMatch(t, /exist only in this pack/);
  assert.match(pkDelText({ name: 'Empty', stickers: [] }), /has no stickers/);
});

test('the text is plain (confirmDlg escapes it once) and the pack screen shows a labelled Delete button', () => {
  assert.match(pkDelText({ name: '<b>x</b>', stickers: [] }), /“<b>x<\/b>”/, 'not escaped here: the dialog does it, and double escaping would show &lt;');
  assert.match(src, /data-act=pkdel[^>]*>\$\{ic\('trash'\)\} Delete pack</, 'a label, not only an icon');
  assert.match(src, /ACT\.pkdel=.*pkDelText\(/, 'the confirmation is the one that counts');
});
