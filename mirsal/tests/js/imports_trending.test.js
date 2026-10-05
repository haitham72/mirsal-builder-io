const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ctx=vm.createContext({});
for(const name of ['imports','trending'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../../mirsal/console',name+'.js'),'utf8'),ctx);
test('history distinguishes existing results from completed and pending imports, and escapes names',()=>{
 const h=ctx.IMPV.rows([{id:'a',kind:'image',prompt:'<script>',status:'completed'},{id:'b',kind:'video',status:'running'},{id:'c',known:{job:'J1'}}]);
 assert.match(h,/&lt;script&gt;/);assert.match(h,/data-id="a" >Import/);assert.match(h,/data-id="b" disabled/);assert.match(h,/Open existing/);
});
test('public cards show maker and views; only staff can delete another persons comment',()=>{
 assert.match(ctx.TRV.card({pack_id:'a',name:'Cat',by:'Mona',views:9,stickers:1,likes:0,comments:0}),/Mona · 9 views/);
 const d={pack_id:'a',name:'Cat',by:'Mona',views:9,uses:2,likes:0,stickers:[],comments:[{id:'c',user:'U2',name:'Rana',text:'nice'}]};
 const mine=ctx.TRV.detail(d,{id:'U1',role:'member'},true);
 assert.match(mine,/Stop sharing/);assert.doesNotMatch(mine,/data-act=truncomment/);assert.match(mine,/9 views · 2 uses/);
 assert.match(ctx.TRV.detail(d,{id:'local',role:'owner'},true),/data-act=truncomment/);
});

test('owner upload keeps destination options, navigates to its batch, and members have no import controls',async()=>{
 const fields={'imp-file':{files:[{name:'own sheet.png'}]},'imp-prompt':{value:'Cats'},'imp-generation':{value:'G104'},'imp-sheet':{value:'A2'}};
 const sent=[];
 const browser=vm.createContext({document:{},ACT:{},ME:{role:'owner'},SES:{gens:[104]},GS:{},location:{},route_:'generate',glast:'',
  $:id=>fields[id],esc:s=>s,dlg:()=>{},closeDlg:()=>{},toast:()=>{},saveSes:()=>{},tick:async()=>{},
  api:async(url,opts)=>{sent.push({url,opts});return {ok:true,j:{id:111,kind:'sheet'}}},URLSearchParams});
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../../mirsal/console/imports.js'),'utf8'),browser);
 assert.match(browser.impButtons(),/Use my own sheet/);
 browser.ACT.impopen();browser.ACT.impupload();
 await new Promise(resolve=>setImmediate(resolve));
 assert.match(sent[0].url,/name=own\+sheet.png/);assert.match(sent[0].url,/generation=G104/);assert.match(sent[0].url,/sheet=A2/);
 assert.equal(sent[0].opts.method,'POST');assert.equal(sent[0].opts.body,fields['imp-file'].files[0]);
 assert.equal(browser.SES.gens[0],111);assert.equal(browser.location.hash,'#/studio');
 browser.ME={role:'member'};assert.equal(browser.impButtons(),'');
});
