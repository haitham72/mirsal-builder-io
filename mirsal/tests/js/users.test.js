// The Users screen's pure builders (users.js UV): the roster and its filters, the hand-drawn bars, a person's page for staff and for "My usage". Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ctx = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'users.js'), 'utf8'), ctx);
const U = ctx.UV;

const users = [
  { id: 'U001', name: 'Amira', role: 'member', status: 'active', spent: 2, batches: 1 },
  { id: 'U002', name: 'Bilal', role: 'admin', status: 'pending', spent: 0, batches: 0 }];

test('the roster lists people with role, status and spend, and the filters narrow it', () => {
  const all = U.roster(users, {}, 'U001');
  assert.match(all, /class="us-row on" data-act=usopen data-id="U001"[\s\S]*Amira[\s\S]*member · Active · 2 cr spent · 1 batches/);
  assert.match(all, /Bilal[\s\S]*admin · Waiting/);
  assert.doesNotMatch(U.roster(users, { status: 'pending' }), /Amira/);
  assert.doesNotMatch(U.roster(users, { role: 'member' }), /Bilal/);
  assert.match(U.roster(users, { role: 'owner' }), /Nobody matches/);
  assert.match(U.filters({ status: 'pending' }), /class="chip2 on" data-act=usfilter data-k=status data-v="pending"/);
});

test('bars are one SVG rect per day, scaled to the tallest, with the day in the title', () => {
  const h = U.bars([0, 2, 4], ['2026-10-02', '2026-10-03', '2026-10-04'], 'Credits spent');
  assert.equal((h.match(/<rect /g) || []).length, 3);
  assert.match(h, /height="60\.00"[\s\S]*<title>2026-10-04: 4<\/title>/, 'the tallest fills the height (64 - 4)');
  assert.match(h, /height="1\.00"/, 'an empty day is a hairline');
  assert.match(h, /<span>10-02<\/span><span>10-04<\/span>/);
  assert.match(U.split(3, 1), /width:75%[\s\S]*width:25%[\s\S]*3 worked[\s\S]*1 failed/);
});

test('a person page: staff see the name and the management card, a member sees "My usage"; text is escaped', () => {
  const d = { user: { id: 'U001', name: 'Amira <b>', email: 'a@nadi.ae', role: 'member', credits_left: 8 }, summary: { spent: 2, batches: 1, stickers: 1, animated: 0, bytes: 2048, jobs_ok: 1, jobs_failed: 0 },
    series: { days: ['2026-10-04'], spend: [2], batches: [1] },
    jobs: [{ id: 'J001', kind: 'sheet', status: 'DONE', cost: 3, estimate: 2, label: 'falcon', created: 1791100000 }],
    ledger: [{ ts: 1791100000, kind: 'IMAGE_SHEET', model: 'nano', job: 'J001', status: 'OK', cost: 3 }],
    families: [{ root: 'G001', batches: [{ id: 'G001', prompt: 'falcon <script>', sheet_prompt: 'sheet', stickers: [{ index: 1, png: '/out/G001/slices/a.png', webm: '/out/G001/slices/a.webm' }] }] }] };
  const staff = U.page(d, true, '<div class=mgmt></div>');
  assert.match(staff, /<h1>Amira &lt;b&gt;<\/h1>/);
  assert.match(staff, /<div class=mgmt><\/div>/);
  assert.match(staff, /class="num over">3</, 'a cost above its estimate is marked');
  assert.match(staff, /2 KB/);
  assert.match(staff, /falcon &lt;script&gt;/);
  assert.match(staff, /href="\/out\/G001\/slices\/a\.webm"[\s\S]*<img src="\/out\/G001\/slices\/a\.png"[\s\S]*▶/);
  assert.match(staff, /1 paid call/);
  const mine = U.page(d, false);
  assert.match(mine, /<h1>My usage<\/h1>/);
  assert.doesNotMatch(mine, /mgmt/);
});

test('bytes read like a person would say them', () => {
  assert.equal(U.bytes(0), '0 B');
  assert.equal(U.bytes(1536), '1.5 KB');
  assert.equal(U.bytes(420488515), '401 MB');
});
