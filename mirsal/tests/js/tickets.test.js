// Settings > Tickets and the Report dialog (tickets.js, docs/tickets_plan.md): the pure builders in TKV, run in a vm. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ctx = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'tickets.js'), 'utf8'), ctx);
const T = ctx.TKV;
const ROW = { id: 'T001', source: 'job', status: 'open', issue: 'stuck_job', summary: 'The Kling job failed <after> paying', count: 3, at: 1, last_at: 2, open_questions: 2 };
const FULL = { ...ROW, intent: 'it never finished', what_happened: 'video job failed: timeout', proposed_fix: 'resume the same provider job',
  questions: [{ text: 'What did you see?', choices: ['the spinner never ended', 'it said failed'], allow_other: true }], answers: [{ question: 0, choice: 'it said failed' }], drafted_by: 'qwen3.5-4b' };

test('a ticket row says what, how often and how many questions wait, escaped', () => {
  const h = T.row(ROW, false);
  assert.match(h, /data-act=tkopen data-id=T001 aria-expanded=false/);
  assert.match(h, /Stuck or failed job/);
  assert.match(h, /The Kling job failed &lt;after&gt; paying/);
  assert.match(h, /failed job · 3 times/);
  assert.match(h, /2 questions/);
});

test('an open ticket shows the person\'s words, what happened, the fix, and its questions as one-click choices; the owner gets the status buttons', () => {
  const h = T.detail(FULL, true);
  assert.match(h, /<b>You said<\/b><div>it never finished<\/div>/);
  assert.match(h, /resume the same provider job/);
  assert.match(h, /data-act=tkans data-id=T001 data-q=0 data-qt="What did you see\?" data-c="the spinner never ended" aria-pressed=false/);
  assert.match(h, /class="ganew-chip on" data-act=tkans data-id=T001 data-q=0 data-qt="What did you see\?" data-c="it said failed" aria-pressed=true/, 'the chosen answer is lit');
  assert.match(h, /data-act=tkother data-id=T001 data-q=0 data-qt="What did you see\?">something else…/);
  assert.match(h, /data-act=tkstatus data-id=T001 data-s=fixed>Fixed/);
  assert.doesNotMatch(T.detail(FULL, false), /data-act=tkstatus/, 'a member answers but does not close tickets');
});

test('the list has the Open / All filter and a sentence when empty; the Report dialog carries its target', () => {
  assert.match(T.list([], null, null, true, 'open'), /No tickets\./);
  assert.match(T.list([ROW], 'T001', FULL, true, 'open'), /class="tab on" data-act=tkfilter data-v="open">Open/);
  const d = T.reportDlg('particle_set', 'P005');
  assert.match(d, /What went wrong with P005\?/);
  assert.match(d, /data-act=tksend data-k="particle_set" data-id="P005">Send/);
});
