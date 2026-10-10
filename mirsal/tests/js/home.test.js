// Home (console/home.js): the filters, the hero's pick, and the page drawn from the caller's real library; the logo opens Home. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { loadConsole } = require('./console_vm');

const st = (id, type = 'still', o = {}) => ({ id, name: 'Cat ' + id, emoji: '😺', type, file: id + (type === 'animated' ? '.webm' : '.png'), ...o });
const packs = [
  { id: 'p1', name: 'Cats', created: 1, cover: 'a', stickers: [st('a', 'animated'), st('b')] },
  { id: 'p2', name: 'Falcon', created: 3, stickers: [st('c', 'animated', { particles: ['P001'] })], telegram: { sets: [{ link: 'https://t.me/addstickers/falcon_by_bot' }] } },
  { id: 'p3', name: 'Dogs', created: 2, stickers: [st('d', 'still', { emoji: '🐶' })] },
];
const STUB = `document.querySelectorAll=()=>[];const location={hash:''};const matchMedia=()=>({matches:false});
const box=()=>({innerHTML:'',hidden:false,value:'',oninput:null,scrollIntoView(){},scrollTo(){}});['s-home','hm-q','hm-gal','hm-empty','hm-disc'].forEach(k=>DOMSTUB[k]=box());`;
const load = () => loadConsole(['home.js'], { extra: STUB });

test('a pack is animated, static, with particles, or several of them; the Telegram link is its first set', () => {
  const run = load();
  run(`LIB={packs:${JSON.stringify(packs)}}`);
  assert.deepEqual(JSON.parse(run(`JSON.stringify(LIB.packs.map(p=>hmPackInfo(p).tags))`)), [['animated', 'static'], ['animated', 'particles'], ['static']]);
  assert.equal(run(`hmPackInfo(LIB.packs[0]).label`), 'Mixed pack');
  assert.equal(run(`hmPackInfo(LIB.packs[1]).telegram`), 'https://t.me/addstickers/falcon_by_bot');
});

test('the filters and the search pick the packs; the search reads sticker names and emoji too', () => {
  const run = load();
  run(`LIB={packs:${JSON.stringify(packs)}}`);
  const ids = (q, f) => JSON.parse(run(`JSON.stringify(LIB.packs.filter(p=>hmShown(p,${JSON.stringify(q)},${JSON.stringify(f)})).map(p=>p.id))`));
  assert.deepEqual(ids('', 'all'), ['p1', 'p2', 'p3']);
  assert.deepEqual(ids('', 'animated'), ['p1', 'p2']);
  assert.deepEqual(ids('', 'static'), ['p1', 'p3']);
  assert.deepEqual(ids('', 'particles'), ['p2']);
  assert.deepEqual(ids('🐶', 'all'), ['p3']);
  assert.deepEqual(ids('falcon', 'static'), []);
});

test('the hero shows up to three stickers, newest pack first, its cover when it has one', () => {
  const run = load();
  assert.deepEqual(JSON.parse(run(`JSON.stringify(hmHero(${JSON.stringify(packs)}).map(s=>s.id))`)), ['c', 'd', 'a']);
  assert.equal(run(`hmHero([]).length`), 0);
});

test('Home draws the real packs: every card opens its pack, every shortcut a real screen; an empty library asks for a first pack', async () => {
  const run = load();
  run(`LIB={packs:${JSON.stringify(packs)}}`);
  await run(`RENDER.home()`);
  const page = run(`$('s-home').innerHTML`), gal = run(`$('hm-gal').innerHTML`);
  assert.match(page, /3 packs/);
  assert.match(page, /4 stickers/);
  for (const id of ['p1', 'p2', 'p3']) assert.match(gal, new RegExp(`data-act=openpack data-id=${id}`));
  assert.match(gal, /href="https:\/\/t.me\/addstickers\/falcon_by_bot"/);
  for (const to of ['effects', 'generate', 'library']) assert.match(page, new RegExp(`data-act=nav data-to=${to}`));
  assert.match(page, /data-act=hmai/);
  assert.match(page, /data-act=hmfilm/);
  assert.doesNotMatch(page, /preview/i, 'nothing on Home is a preview');
  run(`LIB={packs:[]}`);
  await run(`RENDER.home()`);
  assert.match(run(`$('s-home').innerHTML`), /Make your first pack/);
});

test('a filter redraws the gallery; the logo opens Home', async () => {
  const run = load();
  run(`LIB={packs:${JSON.stringify(packs)}}`);
  await run(`RENDER.home()`);
  run(`ACT.hmfilter({dataset:{f:'particles'}})`);
  const gal = run(`$('hm-gal').innerHTML`);
  assert.match(gal, /data-id=p2/);
  assert.doesNotMatch(gal, /data-id=p1/);
  run(`route_='agent';ACT.home()`);
  assert.equal(run(`location.hash`), '#/home');
  const app = fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'app.js'), 'utf8');
  assert.match(app, /\|\|'home'/, 'an empty hash opens Home');
});

test('the first start of a session opens Home from any screen, once; a link to one thing keeps it', () => {
  const run = load();
  const first = h => run(`(()=>{const m={};const s={getItem:k=>m[k]||null,setItem:(k,v)=>{m[k]=v}};return [hmFirstStart(s,${JSON.stringify(h)}),hmFirstStart(s,${JSON.stringify(h)})].join()})()`);
  assert.equal(first('#/agent'), 'true,false', 'the old first screen goes to Home, and only on the first start');
  assert.equal(first(''), 'true,false');
  assert.equal(first('#/pack/20b742ee'), 'false,false', 'a deep link is kept');
  assert.equal(run(`hmFirstStart({getItem(){throw 0}},'')`), false, 'no storage: the hash decides, as before');
});
