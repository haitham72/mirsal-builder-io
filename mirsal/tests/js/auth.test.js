// The sign-in card, Waiting for approval, and Settings > People (auth.js, docs/office_lan_plan.md): the pure builders in AUV, run in a vm. Run: node --test tests/js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ctx = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', '..', 'mirsal', 'console', 'auth.js'), 'utf8'), ctx);
const A = ctx.AUV;

test('the sign-in card has the three ways in, and each form only the fields it needs', () => {
  const s = A.gate('signin');
  assert.match(s, /Sign in to Mirsal/);
  assert.match(s, /id=au-email type=email autocomplete=username/);
  assert.match(s, /id=au-pw type=password autocomplete=current-password/);
  assert.match(s, /data-act=ausignin>Sign in</);
  assert.match(s, /data-act=aumode data-v=signup>Create account/);
  assert.match(s, /data-act=aumode data-v=forgot>Forgot password/);
  assert.doesNotMatch(s, /au-name/);
  assert.match(A.gate('signup'), /id=au-name[\s\S]*autocomplete=new-password/);
  assert.doesNotMatch(A.gate('forgot'), /au-pw/, 'forgot needs the email only');
  assert.match(A.gate('signin', 'If this email <b>'), /If this email &lt;b&gt;/, 'a message is text, escaped');
});

test('a pending account waits; a given password is changed first', () => {
  assert.match(A.waiting({ name: 'Amira', email: 'a@nadi.ae' }), /Waiting for approval[\s\S]*Thanks, Amira[\s\S]*data-act=aulogout/);
  assert.match(A.change({ email: 'a@nadi.ae' }), /au-old[\s\S]*au-new[\s\S]*data-act=auchange/);
});

test('People: a waiting sign-up has Approve and Reject; an active member has roles, password, credits, disable; the owner row has no buttons', () => {
  const h = A.people([
    { id: 'U001', name: 'Amira', email: 'a@nadi.ae', role: 'member', status: 'pending', credits_left: 0 },
    { id: 'U002', name: 'Bilal', email: 'b@nadi.ae', role: 'member', status: 'active', credits_left: 7, credits_spent: 3 },
    { id: 'local', name: 'local', role: 'owner' }],
    [{ id: 'R002', kind: 'credits', user: 'U002', name: 'Bilal', reason: 'a client' }]);
  assert.match(h, /data-act=aupeople data-id=U001 data-a=approve>Approve/);
  assert.match(h, /data-act=aupeople data-id=U001 data-a=reject>Reject/);
  assert.match(h, /7 credits left, 3 spent/);
  assert.match(h, /data-act=aupeople data-id=U002 data-a=admin>Make admin/);
  assert.match(h, /data-act=aupeople data-id=U002 data-a=disable>Disable/);
  assert.match(h, /Bilal asks for more credits: “a client”[\s\S]*data-a=credits data-n=10>Give 10/);
  assert.doesNotMatch(h.split('data-uid=local')[1], /data-act=aupeople/, 'the owner cannot be changed from here');
});
