const {readConsoleFile, statement} = require('./console_source');
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const vm = require('node:vm');
const source = readConsoleFile(path.join(__dirname, '../../mirsal/console/app.js'));

test('redrawing the clicked avatar keeps its menu open until a genuine outside click', () => {
  const rail = {}, listeners = {};
  let redraws = 0, focused = 0;
  const ctx = vm.createContext({
    ACT: {}, RME: false, location: {hash: '#/settings'},
    $: () => rail,
    drawRail: () => redraws++,
    document: {
      querySelector: selector => selector.startsWith('#rmenu') ? {focus() {focused++;}} : null,
      addEventListener: (name, fn) => {listeners[name] = fn;},
    },
  });
  vm.runInContext([
    statement(source, 'ACT.rme ='),
    statement(source, 'ACT.nav ='),
    statement(source, 'const rmeClose ='),
    statement(source, "document.addEventListener('click', (e) => { if (RME"),
  ].join('\n'), ctx);
  const avatarClick = {target: {closest: () => null}, composedPath: () => [rail]};
  vm.runInContext('ACT.rme()', ctx);
  listeners.click(avatarClick);
  assert.equal(ctx.RME, true);
  assert.equal(redraws, 1);
  assert.equal(focused, 1);
  vm.runInContext('ACT.rme()', ctx);
  listeners.click(avatarClick);
  assert.equal(ctx.RME, false);
  vm.runInContext('ACT.rme()', ctx);
  listeners.click({target: {closest: () => null}, composedPath: () => []});
  assert.equal(ctx.RME, false);
  vm.runInContext('ACT.rme(); ACT.nav({closest: () => true, dataset: {to: "settings"}})', ctx);
  assert.equal(ctx.RME, false, 'selecting the current route also closes the menu');
  assert.equal(ctx.location.hash, '#/settings');
});
