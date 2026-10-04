// The Studio's AI enhancer shows the AI screen's own engine control (2026-10-03, Haitham: "the AI enhancer should show model selection same like AI"). ONE implementation (agent.js: beRow / modelRow,
// exposed to the Studio as AIENG), two screens; the chip is enabled whenever a model can answer (LM Studio alone is enough) and its tooltip says what is missing otherwise.
// agent.js runs in a vm with the few globals it uses stubbed; composer.js is read as text and its statements run on their own. Nothing touches a DOM, a server or a provider. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const dir = path.join(__dirname, '..', '..', 'mirsal', 'console');
const read = f => fs.readFileSync(path.join(dir, f), 'utf8');
const agentSrc = read('agent.js'), composer = read('composer.js'), gen = read('generate.js'), html = read('index.html'), css = read('studio.css');

const AV_LOCAL = { local: { ok: true, model: 'qwen3.5-4b', why: null }, cloud: { ok: false, model: 'gpt-4o-mini', why: 'no OPENAI_API_KEY in mirsal/.env' } };
const AV_CLOUD = { local: { ok: false, model: 'qwen3.5-4b', why: 'LM Studio is not answering at http://localhost:1234/v1: start it and load qwen3.5-4b' }, cloud: { ok: true, model: 'gpt-4o-mini', why: null } };
const AV_NONE = { local: AV_CLOUD.local, cloud: AV_LOCAL.cloud };
const MODELS = { ok: true, current: 'qwen3.5-4b', why: null, models: [{ id: 'qwen3.5-4b', loaded: true }, { id: 'qwen3.5-9b', loaded: false }] };

// ---- agent.js, whole, in a vm: the page's two settings (the AI screen's gear panel and the Studio's AI enhancer) call the same functions
function boot({ models = MODELS, post = async () => ({ ok: true, j: {} }) } = {}) {
  const log = { posts: [], toasts: [], draws: 0, refreshes: 0, listeners: {} };
  const ctx = vm.createContext({
    console, setTimeout, clearTimeout, Date, JSON, Math, Promise,
    document: { addEventListener: (t, f) => { (log.listeners[t] = log.listeners[t] || []).push(f); }, getElementById: () => null, querySelector: () => null },
    localStorage: { getItem: () => null, setItem() {} }, history: { replaceState() {} }, location: { hash: '' }, matchMedia: () => ({ matches: false }),
    ACT: {}, ICONS: {}, ic: n => `<svg data-i=${n}></svg>`, $: () => null, route_: 'generate', RENDER: {},
    toast: (m, bad) => log.toasts.push([m, !!bad]), confirmDlg() {},
    api: async url => url === '/api/llm/models' ? { ok: true, j: models } : { ok: true, j: { agent: { provider: 'local', model: 'qwen3.5-4b' }, availability: AV_LOCAL, preference: 'auto' } },
    post: async (u, b) => { log.posts.push([u, b]); return post(u, b); },
    cpDrawEngine() { log.draws++; }, aiRefresh: async () => { log.refreshes++; },
  });
  ctx.window = ctx;
  vm.runInContext(agentSrc, ctx, { filename: 'agent.js' });
  return { ctx, log, ACT: ctx.ACT, AIENG: ctx.globalThis ? ctx.AIENG : ctx.AIENG };
}
const SRC = (pref, av, provider = 'local', model = 'qwen3.5-4b') => ({ agent: { provider, model }, agent_status: {}, availability: av, preference: pref, noModel: 'no model, the built-in prompt is used' });
const J = x => JSON.parse(JSON.stringify(x));       // objects made inside the vm are not reference-equal to the test's own
const flush = () => new Promise(r => setImmediate(r));

test('the Studio gets the AI screen\'s control through AIENG: Auto / Local / Cloud on the shared action, one line saying which model answers', async () => {
  const b = boot();
  assert.equal(typeof b.ctx.AIENG.rows, 'function');
  b.ctx.AIENG.ensure();
  await flush();
  const rows = b.ctx.AIENG.rows(SRC('auto', AV_LOCAL));
  for (const v of ['auto', 'local', 'cloud']) assert.match(rows, new RegExp(`data-act=agbe data-v=${v}`), `${v} uses the AI screen's handler`);
  assert.match(rows, /<small>now: local · qwen3\.5-4b<\/small>/, 'the engine line says which model answers');
  assert.match(rows, /data-v=auto class="on"/);
  assert.match(rows, /data-v=cloud class=" is-off"[^>]*title="no OPENAI_API_KEY in mirsal\/\.env"/, 'a backend that cannot answer is dimmed and says why');
  assert.match(rows, /<select class=ag-sel data-agmodel aria-label="Local model">/);
  assert.match(rows, /<option value="qwen3\.5-4b" selected>qwen3\.5-4b · loaded<\/option><option value="qwen3\.5-9b">qwen3\.5-9b<\/option>/);
  assert.match(rows, /<small class="" title="">now: qwen3\.5-4b<\/small>/);
});

test('with no model reachable the line says so in the enhancer\'s words, not "rules only", and a model that cannot answer says why', async () => {
  const b = boot({ models: { ok: false, current: 'qwen3.5-4b', why: 'LM Studio is running but the model could not answer: No models loaded. Load qwen3.5-4b in LM Studio (or turn on Just-in-Time loading)', models: [{ id: 'qwen3.5-4b', loaded: false }] } });
  b.ctx.AIENG.ensure();
  await flush();
  const rows = b.ctx.AIENG.rows(SRC('auto', AV_NONE, 'none', ''));
  assert.match(rows, /now: no model, the built-in prompt is used/);
  assert.doesNotMatch(rows, /rules only/);
  assert.match(rows, /<small class="ai-err"[^>]*>Local model not loaded: Load qwen3\.5-4b in LM Studio/);
  const pinned = b.ctx.AIENG.rows(SRC('cloud', AV_NONE, 'none', ''));
  assert.match(pinned, /<span class=ai-err>no OPENAI_API_KEY in mirsal\/\.env<\/span>/, 'a chosen engine that is down says why next to the line');
});

test('the AI screen keeps drawing the same rows from its own state (no second copy): the gear panel calls beRow()', () => {
  assert.match(agentSrc, /\$\{beRow\(\)\}/);
  assert.equal((agentSrc.match(/function beRow\(/g) || []).length, 1);
  assert.equal((agentSrc.match(/function modelRow\(/g) || []).length, 1);
  assert.doesNotMatch(composer + gen, /data-agmodel|ACT\.agbe\s*=|\/api\/ai\/backend|\/api\/llm\/models/, 'the Studio has no handler, no endpoint call and no drop-down of its own');
  assert.match(composer, /AIENG\.rows\(cpEngSrc\(\)\)/);
});

test('an engine pick from the Studio posts the choice, re-reads the Studio\'s facts and redraws both screens', async () => {
  const b = boot();
  await b.ACT.agbe({ dataset: { v: 'local' } });
  assert.deepEqual(J(b.log.posts[0]), ['/api/ai/backend', { backend: 'local' }]);
  assert.equal(b.log.refreshes, 1, 'GET /api/ai is read again (GAI)');
  assert.ok(b.log.draws >= 1, 'the Studio\'s control is redrawn');
});

test('a model pick posts {model} to the same endpoint, shows "Switching" while it loads, then re-reads and redraws', async () => {
  const b = boot();
  const seen = [];
  b.ctx.cpDrawEngine = () => { b.log.draws++; seen.push(b.ctx.AIENG.rows(SRC('local', AV_LOCAL))); };
  const [h] = b.log.listeners.change;
  await h({ target: { dataset: { agmodel: '' }, value: 'qwen3.5-9b' } });
  assert.deepEqual(J(b.log.posts[0]), ['/api/ai/backend', { model: 'qwen3.5-9b' }]);
  assert.match(seen[0], /Switching the local model/);
  assert.doesNotMatch(seen.at(-1), /Switching the local model/);
  assert.equal(b.log.refreshes, 1);
});

test('a refused pick (a member may read but not pick) shows the server\'s sentence and changes nothing', async () => {
  const b = boot({ post: async () => ({ ok: false, j: { error: 'Only the owner can do this.' } }) });
  await b.ACT.agbe({ dataset: { v: 'cloud' } });
  assert.deepEqual(J(b.log.toasts.at(-1)), ['Only the owner can do this.', true]);
  assert.equal(b.log.refreshes, 0);
  const [h] = b.log.listeners.change;
  await h({ target: { dataset: { agmodel: '' }, value: 'qwen3.5-9b' } });
  assert.deepEqual(J(b.log.toasts.at(-1)), ['Only the owner can do this.', true]);
});

// ---- composer.js: the chip and the control's visibility
function statement(src, marker) {
  const i = src.indexOf(marker);
  assert.notEqual(i, -1, `${marker} is not in the file`);
  const lines = src.slice(i).split('\n');
  const out = [lines[0]];
  for (const ln of lines.slice(1)) { if (ln && !/^\s/.test(ln)) break; out.push(ln); }
  return out.join('\n');
}
function chip({ ai = false, gai }) {
  const log = { engine: [], loads: 0, ensures: 0 };
  const el = { hidden: true, innerHTML: '', _h: undefined };
  const sb = {
    CP: { ai, refs: [] }, GAI: gai, gstore() {}, esc: s => String(s).replace(/"/g, '&quot;'), $: id => id === 'cpeng' ? el : null, aiRefresh: async () => gai, cpDrawBar() {},
    gdEngineName: () => gai && gai.provider && gai.provider !== 'none' ? `${gai.provider === 'openai' ? 'cloud' : 'local'} · ${gai.model}` : '',
    AIENG: { rows: src => { log.engine.push(src); return '<ROWS>'; }, ensure: () => { log.ensures++; }, load: () => { log.loads++; } },
  };
  const body = [statement(composer, 'const aiOn='), statement(composer, 'function aiWhy('), statement(composer, 'function aiChipTitle('), statement(composer, 'const cpEngSrc='), statement(composer, 'function cpDrawEngine('), statement(composer, 'ACT.cpai=')].join('\n');
  const f = new Function(...Object.keys(sb), 'const ACT={};\n' + body + '\nreturn {aiOn,aiWhy,aiChipTitle,cpDrawEngine,cpEngSrc,ACT};')(...Object.values(sb));
  return Object.assign(f, { el, log, sb });
}
const G = (o) => Object.assign({ configured: true, provider: 'local', model: 'qwen3.5-4b', preference: 'auto', availability: AV_LOCAL }, o);

test('LM Studio alone enables the chip: GAI.configured is true on the local model without an OpenAI key, and the tooltip says what the engine costs', () => {
  const c = chip({ ai: true, gai: G() });
  assert.equal(c.aiOn(), true);
  const t = c.aiChipTitle();
  assert.match(t, /local · qwen3\.5-4b/);
  assert.match(t, /Local: free\./);
  assert.doesNotMatch(t, /OPENAI_API_KEY/, 'no key is asked for when a model can answer');
  const cloud = chip({ ai: true, gai: G({ provider: 'openai', model: 'gpt-4o-mini', availability: AV_CLOUD }) });
  assert.match(cloud.aiChipTitle(), /Cloud: one small OpenAI call\./);
  assert.match(composer, /\$\{GAI&&GAI\.configured\?'':'disabled'\} title="\$\{esc\(aiChipTitle\(\)\)\}"/, 'the chip is disabled exactly when nothing can answer');
});

test('the chip is off, and says which of the two is missing, only when neither engine can answer', () => {
  const none = chip({ gai: G({ configured: false, provider: 'none', model: null, availability: AV_NONE }) });
  assert.equal(none.aiOn(), false);
  assert.match(none.aiChipTitle(), /No AI model is reachable: start LM Studio \(free\) or add OPENAI_API_KEY to mirsal\/\.env\./);
  const cloudOnly = chip({ gai: G({ configured: false, provider: 'none', preference: 'cloud', availability: AV_LOCAL }) });
  assert.match(cloudOnly.aiChipTitle(), /Cloud is chosen and no OPENAI_API_KEY in mirsal\/\.env\. Add it, or pick Auto or Local below\./);
  const localOnly = chip({ gai: G({ configured: false, provider: 'none', preference: 'local', availability: AV_CLOUD }) });
  assert.match(localOnly.aiChipTitle(), /Local is chosen and it is not available \(LM Studio is not answering/);
});

test('the engine control shows while the enhancer is On, and while it cannot run (so an engine that can is one click away); it is hidden otherwise', () => {
  const on = chip({ ai: true, gai: G() });
  on.cpDrawEngine();
  assert.equal(on.el.hidden, false);
  assert.match(on.el.innerHTML, /<ROWS>/);
  assert.match(on.el.innerHTML, /Local: free\. Cloud: one small OpenAI call\./, 'the honest cost note');
  assert.equal(on.log.ensures, 1, 'the model list is read');
  assert.deepEqual({ ...on.log.engine[0], agent: undefined }, { agent: undefined, agent_status: {}, availability: AV_LOCAL, preference: 'auto', noModel: 'no model, the built-in prompt is used' });
  assert.deepEqual(on.log.engine[0].agent, { provider: 'local', model: 'qwen3.5-4b' }, 'the Studio\'s source is GET /api/ai, shaped like GET /api/chat/agent');
  const off = chip({ ai: false, gai: G() });
  off.cpDrawEngine();
  assert.equal(off.el.hidden, true);
  assert.equal(off.el.innerHTML, '');
  const stuck = chip({ ai: false, gai: G({ configured: false, provider: 'none', availability: AV_NONE }) });
  stuck.cpDrawEngine();
  assert.equal(stuck.el.hidden, false, 'nothing can answer: the control is the way out');
});

test('a redraw with nothing changed leaves the drop-down alone (an open <select> would close)', () => {
  const c = chip({ ai: true, gai: G() });
  c.cpDrawEngine();
  const first = c.el.innerHTML;
  let writes = 0;
  Object.defineProperty(c.el, 'innerHTML', { get: () => first, set: () => { writes++; } });
  c.cpDrawEngine();
  assert.equal(writes, 0);
});

test('On, Off, On again: the engine and model choice come back (the panel stayed empty after an Off)', () => {
  const c = chip({ ai: true, gai: G() });
  c.cpDrawEngine();
  assert.match(c.el.innerHTML, /<ROWS>/);
  c.sb.CP.ai = false; c.cpDrawEngine();
  assert.equal((c.el.hidden, c.el.innerHTML), '');
  c.sb.CP.ai = true; c.cpDrawEngine();
  assert.equal(c.el.hidden, false);
  assert.match(c.el.innerHTML, /<ROWS>/, 'drawn again, not skipped as unchanged');
  assert.doesNotMatch(c.el.innerHTML, /cp-engnote/, 'compact: the cost note is the tooltip, not a third row');
});

test('turning the enhancer On reads the models and the engine again', async () => {
  const c = chip({ ai: false, gai: G() });
  c.ACT.cpai();
  assert.equal(c.sb.CP.ai, true);
  assert.equal(c.log.loads, 1);
});

test('wiring: the control has a mount in the composer, agent.js is loaded and its styles are scoped', () => {
  assert.match(composer, /<div class=cp-engwrap id=cpeng hidden><\/div>/);
  assert.match(html, /\/ui\/composer\.js[\s\S]*\/ui\/agent\.js/);
  assert.match(css, /\.ai-set\.cp-eng\{position:static/);
  assert.match(agentSrc, /globalThis\.AIENG=\{rows:/);
});
