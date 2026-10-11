const {readConsoleFile,statement:consoleStatement}=require('./console_source');
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = readConsoleFile(path.join(__dirname, '../../mirsal/console/theme.js'), 'utf8');

function boot(value, blocked = false) {
  let theme;
  const listeners = {}, buttons = ['dark', 'light'].map(v => ({
    dataset: {v}, classList: {toggle(k, on) {this[k] = on;}},
    setAttribute(k, val) {this[k] = val;},
  }));
  const storage = {value, getItem() {if (blocked) throw Error('blocked'); return this.value;},
    setItem(k, v) {if (blocked) throw Error('blocked'); this.value = v;}};
  const ctx = vm.createContext({localStorage: storage,
    window: {addEventListener(k, f) {listeners[k] = f;}},
    document: {documentElement: {setAttribute(k, v) {theme = v;}, getAttribute() {return theme;}},
      querySelectorAll() {return buttons;}},
  });
  vm.runInContext(source, ctx);
  return {run: code => vm.runInContext(code, ctx), theme: () => theme, storage, listeners, buttons};
}

test('dark is the startup default, while an explicit light preference is applied before paint', () => {
  for (const value of [null, '', 'invalid', 'dark']) assert.equal(boot(value).theme(), 'dark');
  assert.equal(boot('light').theme(), 'light');
  const html = readConsoleFile(path.join(__dirname, '../../mirsal/console/index.html'), 'utf8');
  assert.ok(html.indexOf('/ui/theme.js') < html.indexOf('/ui/studio.css'));
  assert.ok(html.indexOf('/ui/theme.css') > html.indexOf('/ui/agent.css'));
});

test('switching persists without a page redraw, and updates accessible button state across tabs', () => {
  const b = boot(null);
  b.run("thmSet('light')");
  assert.equal(b.theme(), 'light');
  assert.equal(b.storage.value, 'light');
  assert.equal(b.buttons[1]['aria-pressed'], 'true');
  assert.equal(boot(b.storage.value).theme(), 'light');
  b.storage.value = 'dark';
  b.listeners.storage({key: 'mirsal.ui.theme'});
  assert.equal(b.theme(), 'dark');
  assert.equal(b.buttons[0]['aria-pressed'], 'true');
  b.storage.value = null;
  b.listeners.storage({key: null});
  assert.equal(b.theme(), 'dark');
});

test('blocked storage still allows theme switching for the current page', () => {
  const b = boot(null, true);
  assert.equal(b.theme(), 'dark');
  b.run("thmSet('light')");
  assert.equal(b.theme(), 'light');
});
