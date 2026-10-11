const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function boot(){
 const ctx=vm.createContext({console,setTimeout:()=>0,clearTimeout(){},Date,JSON,Math,Promise,
  document:{addEventListener(){},getElementById:()=>null,querySelector:()=>null},
  localStorage:{getItem:()=>null,setItem(){}},history:{replaceState(){}},location:{hash:''},matchMedia:()=>({matches:false}),
  ACT:{},ICONS:{},RENDER:{},ic:()=>'', $:()=>null,route_:'generate',toast(){},
  api:async()=>({ok:false,j:{}}),POSTS:[],post:async(u,b)=>{ctx.POSTS.push([u,b]);return {ok:false,j:{}}}});
 ctx.window=ctx;
 const src=fs.readFileSync(path.join(__dirname,'../../mirsal/console/agent.js'),'utf8');
 // Expose closure state only in the test's copy; execute the complete script.
 vm.runInContext(src.replace(/\}\)\(\)\}\s*$/, 'globalThis.TEST_API={A,selectorDetails,saveSet};})()}'),ctx);
 vm.runInContext('const {A,selectorDetails,saveSet}=TEST_API;',ctx);
 return code=>vm.runInContext(code,ctx);
}

const report = {
  preference: 'cloud', default: 'openai:gpt-5.6-luna', current: 'qwen', selected: null,
  aliases: {'gpt-5.6-luna':'openai:gpt-5.6-luna','nararouter:gpt-5.6-luna':'openai:gpt-5.6-luna'},
  local: [{ id: 'local:qwen', model: 'qwen', label: 'qwen' }],
  nararouter: ['mimo-v2.6-flash-free', 'agnes-3-flash'].map(model => ({ id: `nararouter:${model}`, model, label: model })),
  openai: [{ id: 'openai:gpt-5.6-luna', model: 'gpt-5.6-luna', label: 'gpt-5.6-luna' }], models: [],
};

test('the shared selector groups all providers and preserves a saved model on reopen', () => {
  const run = boot();
  run(`A.llm=${JSON.stringify(report)}; A.sess={settings:{models:{ai:'nararouter:agnes-3-flash'}}};`);
  const draw = () => run(`AIU.modelSel('ai','Chat',selectorDetails().models.ai)`);
  const html = draw();
  for (const group of ['Local', 'Nararouter', 'OpenAI']) assert.match(html, new RegExp(`optgroup label="${group}"`));
  assert.match(html, /nararouter:agnes-3-flash" selected/);
  assert.match(html, /mimo-v2.6-flash-free/);
  assert.match(html, /Default · openai:gpt-5.6-luna/);
  assert.equal(draw(), html);
  run(`A.sess.settings.models.ai='';`);
  assert.match(draw(), /option value="" selected/);
  run(`A.sess.settings.models.ai='nararouter:removed-model';`);
  assert.match(draw(), /removed-model" selected disabled/);
  run(`A.sess.settings.models.ai='nararouter:gpt-5.6-luna';`);
  assert.match(draw(), /openai:gpt-5.6-luna" selected/);
  assert.doesNotMatch(draw(), /value="nararouter:gpt-5.6-luna"/);
});

test('session choices save the qualified id and the stage/composer contain no AI selector', async () => {
  const run = boot();
  run(`A.llm=${JSON.stringify(report)}; A.sid='S001'; A.sess={id:'S001',settings:{models:{}}};`);
  await run(`saveSet({models:{ai:'openai:gpt-5.6-luna'}})`);
  const posts = JSON.parse(run('JSON.stringify(POSTS)'));
  assert.deepEqual(posts[0], ['/api/chat/sessions/S001/settings', { models: { ai: 'openai:gpt-5.6-luna' } }]);
  assert.doesNotMatch(run(`AIU.stageHTML('emojis',true)`), /data-agm|optgroup|model/);
  const source = fs.readFileSync(path.join(__dirname, '../../mirsal/console/agent.js'), 'utf8');
  const composerPanel = source.slice(source.indexOf('function setSet()'), source.indexOf("document.addEventListener('click'", source.indexOf('function setSet()')));
  assert.doesNotMatch(composerPanel, /modelSel\('ai'/);
});

test('Settings and the enhancer share the grouped global selector', () => {
  const run = boot();
  run(`A.llm=${JSON.stringify({ ...report, selected: 'nararouter:agnes-3-flash' })};`);
  const source = { preference: 'cloud', agent: { provider: 'openai', model: 'nararouter:agnes-3-flash' }, availability: {} };
  const html = run(`AIENG.rows(${JSON.stringify(source)})`);
  assert.match(html, /data-agmodel/);
  assert.doesNotMatch(html, /data-agm=ai/);
  assert.match(html, /nararouter:agnes-3-flash" selected/);
  const settings = fs.readFileSync(path.join(__dirname, '../../mirsal/console/app.js'), 'utf8');
  assert.match(settings, /id=set-ai-engine/);
  assert.match(settings, /AIENG.settings\(/);
});
