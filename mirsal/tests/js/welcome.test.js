// The welcome modal's markup (welcome.js): slides are data, markup is built by pure functions. The functions are read out of the file and run with esc / ic stubbed.
// Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const src = fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'welcome.js'), 'utf8');
function statement(marker) {
  const i = src.indexOf(marker);
  assert.notEqual(i, -1, `${marker} is not in welcome.js`);
  const lines = src.slice(i).split('\n');
  const out = [lines[0]];
  for (const ln of lines.slice(1)) { if (ln && !/^\s/.test(ln) && !ln.startsWith('}')) break; out.push(ln); if (ln.startsWith('}')) break; }
  return out.join('\n');
}
const slidesSrc = src.slice(src.indexOf('const WL_SLIDES='), src.indexOf('const WL={'));
const code = [slidesSrc, 'const WL={i:0};', 'const wlGet=(s,k)=>null;const WL_OFF="off";', statement('function wlSlideHTML('), statement('function wlHTML(')].join('\n');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const m = new Function('esc', 'ic', 'localStorage', `${code}\nreturn {WL_SLIDES, wlHTML, wlSlideHTML};`)(esc, n => `<svg data-i=${n}></svg>`, {});

test('five pages: the film, then the four features', () => {
  assert.equal(m.WL_SLIDES.length, 5);
  assert.deepEqual(m.WL_SLIDES.map(s => s.kind), ['video', 'image', 'image', 'image', 'image']);
  assert.deepEqual(m.WL_SLIDES.map(s => s.id), ['film', 'ideas', 'motion', 'burst', 'chat']);
});
test('every file the slides name is under /assets/welcome/ and exists on disk', () => {
  const dir = path.join(__dirname, '..', '..', 'mirsal', 'console', 'assets', 'welcome');
  for (const s of m.WL_SLIDES) for (const f of [s.src, s.poster].filter(Boolean)) {
    assert.match(f, /^\/assets\/welcome\/[a-z0-9_-]+\.(mp4|webp|jpg)$/);
    assert.ok(fs.existsSync(path.join(dir, path.basename(f))), `${f} is missing from console/assets/welcome/`);
  }
});
test('every call to action goes to a real screen', () => {
  const screens = ['agent', 'effects', 'studio', 'library', 'create', 'history'];
  for (const s of m.WL_SLIDES.filter(s => s.cta)) assert.ok(screens.includes(s.cta[1]), s.cta[1]);
});
test('the markup has the dialog, the dots, the video controls, and escapes text', () => {
  const html = m.wlHTML(m.WL_SLIDES);
  assert.match(html, /role=dialog aria-modal=true/);
  assert.equal((html.match(/data-act=wlgoto/g) || []).length, 5);
  assert.match(html, /<video class=wl-v id=wl-v muted playsinline/);
  assert.match(html, /data-act=wlsound/);
  const evil = m.wlSlideHTML({ kind: 'image', src: '/assets/welcome/s1.webp', kicker: '<b>k</b>', title: '"t"', body: '<script>x</script>', cta: ['Go', 'agent'] }, 3);
  assert.ok(!evil.includes('<script>') && !evil.includes('<b>k</b>'));
});
