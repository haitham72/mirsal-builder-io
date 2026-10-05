const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ctx=vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../../mirsal/console/support.js'),'utf8'),ctx);
const S=ctx.SUV;

test('an answer from the help asks whether it solved it; with nothing documented it offers support',()=>{
 const grounded={id:'C001',title:'Telegram',status:'answered',messages:[{role:'user',text:'it fails'},{role:'agent',text:'Re-export it.',grounded:true,cites:[{kind:'faq',id:'F001',title:'Telegram refuses a pack'}]}]};
 const h=S.conv(grounded,false,false,null);
 assert.match(h,/Did this solve it\?/);assert.match(h,/data-act=susolved/);assert.match(h,/data-act=suunsolved/);
 assert.match(h,/data-act=sucite data-id="F001">Telegram refuses a pack/,'the FAQ entry it read is one click away');
 const none={...grounded,messages:[{role:'user',text:'x'},{role:'agent',text:'I could not find this',grounded:false}]};
 assert.match(S.conv(none,false,false,null),/data-act=suesc/);assert.doesNotMatch(S.conv(none,false,false,null),/Did this solve it/);
 const shot={...grounded,messages:[{role:'agent',text:'Can you show me?',need:'screenshot'}]};
 assert.match(S.conv(shot,false,false,null),/Attach a screenshot/);
});

test('every state says where the issue is, and searching shows a spinner instead of the buttons',()=>{
 const base={id:'C002',title:'t',messages:[{role:'agent',text:'a',grounded:true}]};
 assert.match(S.conv({...base,status:'awaiting_admin',ticket:'T001'},false,false,null),/Waiting for support/);
 assert.match(S.conv({...base,status:'admin_replied',ticket:'T001'},false,false,null),/Support replied/);
 assert.match(S.conv({...base,status:'resolved',ticket:'T001'},false,false,null),/data-act=sureopen/);
 const busy=S.conv({...base,status:'answered'},false,true,null);
 assert.match(busy,/Looking for an answer/);assert.doesNotMatch(busy,/data-act=susolved/);
});

test('what the vision model saw and the search details are for staff only, and everything is escaped',()=>{
 const m={role:'user',text:'<b>help</b>',seen:'The Library screen with an error',image:'/api/support/conversations/C1/images/img-1.png',mode:'lexical'};
 const member=S.msg(m,false),staff=S.msg(m,true);
 assert.doesNotMatch(member,/Vision model saw/);assert.match(staff,/Vision model saw:<\/b> The Library screen/);
 assert.match(member,/&lt;b&gt;help&lt;\/b&gt;/);assert.match(member,/img-1\.png/);
 assert.match(S.msg({role:'agent',text:'x',cites:[{kind:'code',id:'code:a#1',title:'a.py',path:'a.py'}]},true),/code: a\.py/);
});

test('the staff views: a ticket offers reply and resolve, an FAQ proposal shows what is published now',()=>{
 const t=S.ticket({ticket:{id:'T004',status:'open',summary:'uploads fail',proposed_fix:'raise the limit',faq:'F002'},conversation:{messages:[{role:'user',text:'it fails'}]}});
 assert.match(t,/data-act=sureply data-id="T004"/);assert.match(t,/data-act=suresolve/);assert.match(t,/Reply keeps the issue open/);assert.match(t,/FAQ proposal F002/);
 const f=S.faqEdit({id:'F001',status:'published',revision:2,question:'Old q',answer:'Old a',pending:{title:'N',question:'New q',answer:'New a'},provenance:[{ticket:'T004'}]});
 assert.match(f,/Published now \(revision 2\)/);assert.match(f,/value="New q"/);assert.match(f,/data-act=sufpub/);assert.match(f,/From T004/);
 assert.doesNotMatch(S.faqEdit({id:'F003',status:'archived',question:'q',answer:'a'}),/data-act=sufpub/,'an archived entry cannot be published');
});

test('a private message is masked until revealed, and an action opens the batch it cited',()=>{
 const m={id:'m4',role:'admin',private:true,text:'123:SECRET'};
 const hidden=S.msg(m,false,false),shown=S.msg(m,false,true);
 assert.doesNotMatch(hidden,/SECRET/);assert.match(hidden,/data-act=supriv/);assert.match(hidden,/I saved it, forget it/);
 assert.match(shown,/123:SECRET/);
 assert.match(S.msg({...m,text:'[a private message]'},true,false),/A private message for the person/,'staff see that it was sent');
 assert.match(S.msg({role:'agent',text:'x',actions:[{kind:'open_batch',id:'G007',label:'Open G007 in the Studio'}]},false),/data-act=sugo data-g="G007">Open G007 in the Studio/);
 const feat={id:'C9',title:'t',status:'answered',messages:[{role:'agent',text:'not yet',request:'feature'}]};
 assert.match(S.conv(feat,false,false,null),/data-act=sureq data-k=feature/);
 assert.match(S.conv({...feat,messages:[{role:'agent',text:'ask',request:'access'}]},false,false,null),/Ask the admin/);
});
