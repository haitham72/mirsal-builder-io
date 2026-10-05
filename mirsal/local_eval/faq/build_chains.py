"""Additional grounded seeds and declarative multi-turn cases. No app/live writes."""
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
NEW=[]
CASES=[]

def entry(path,question,answer,sources,visible='',screen='Help'):
    NEW.append(dict(path=path,question=question,title=question.rstrip('?'),answer=answer,sources=sources,
                    category=path.split('/')[0],screen=screen if visible else '',looks_like=visible))
    return path

SUP=['docs/agent-and-chat.md: The real cases','docs/api.md: Help & Support','mirsal/mirsal/console/support.js: next, priv']
ACT=['docs/agent-and-chat.md: Your activity as sources; Watches','mirsal/mirsal/flow/support.py: activity, check_watches']
CRED=['docs/api.md: Credits per person','mirsal/mirsal/flow/jobs.py: _settle']

feature=entry('troubleshooting/feature-request.md','How do I ask for a feature the app does not have?',
 'Describe the feature in Help. When the answer offers Request this feature, choose it to send a feature request; an answered question also has Suggest a feature instead. Sending a request does not mean the feature has been built or guarantee when it will arrive.',SUP,
 'This is not in the app yet. appears with Request this feature; an answered question can offer Suggest a feature instead.')
access=entry('accounts/access-request.md','How do I request something only an admin can provide?',
 'After signing in and being approved, describe the access, credits or credentials you need in Help. Choose Ask the admin when it is offered; the request goes to an admin, who decides what can be provided. The request does not grant access automatically.',SUP,
 'Only an admin can give this. appears above Ask the admin.')
private=entry('accounts/private-reply.md','How do I read a private reply from support?',
 'Open your Help conversation when support sends a private reply. The message is masked: Reveal shows it and Copy copies it, so keep the contents private. Notifications tell you that a private message arrived without including its contents.',SUP,
 'A private message for you appears with a masked value, Reveal, Copy and I saved it, forget it.')
forget=entry('accounts/forget-private-reply.md','How do I remove a private reply after saving it?',
 'After saving the information somewhere appropriate, choose I saved it, forget it in your Help conversation. This erases the private message text from the conversation record; the screen then shows that it was forgotten. It does not erase information you already copied elsewhere.',SUP,
 'I saved it, forget it is available on the private message; afterward the message says A private message (you saved it and it was forgotten).')
progress=entry('troubleshooting/job-progress.md','Can Help check what happened to my generation job?',
 'Ask Help about your own job and include its job number if you have it. Help can use your activity to explain the current status, the provider task and the related batch when available. A usual duration comes from previous completed jobs, rather than being a promise that this one will finish at that time.',ACT)
arrived=entry('troubleshooting/job-arrival.md','Will Help tell me when the job I asked about finishes?',
 'When an answer cites your running job, Help watches it. Once the app checks again and finds it finished, the conversation reports the result, offers the related batch when available, and resolves; you also get an update notification. This is tied to the job you asked about, not a guarantee of provider completion.',ACT)
timeout=entry('troubleshooting/job-timeout.md','Does a timed-out job mean the provider has stopped making my video?',
 'A timeout means the app stopped waiting, and the task may still finish at Higgsfield. Ask Help to check your own job status; the existing task can be checked again without paying for a new generation. Do not treat a timeout alone as a reason to start another paid job.',ACT)
failure=entry('troubleshooting/job-failure.md','Can Help explain a failed generation?',
 'Ask about the failed job and include its number if available. Help can read the failure reason recorded in your activity, but it should not invent a cause or repair when that record does not explain one.',ACT)
privacy=entry('troubleshooting/own-activity.md','Can Help show another person’s job or batch?',
 'Help uses your own jobs and batches for activity answers. Naming somebody else’s job or batch does not give you access to that person’s activity.',ACT)
accepted=entry('studio/accepted-count.md','How can I find out why my batch has so few accepted stickers?',
 'Ask Help about your own batch. It can read the accepted count and each excluded sticker’s recorded reason, and offer a button to open the batch in Studio. A judgement-call block may have Use it anyway on the tile, while technical file limits still need to be met.',ACT+['docs/engine-and-studio.md: Use it anyway'])
zipstudio=entry('studio/zip-from-studio.md','Can I download a whole sticker pack as a zip directly from Studio?',
 'The whole-pack Download .zip control is on the pack page in Library. Studio does not currently offer that whole-pack zip control. If you want it in Studio, describe that request in Help and choose Request this feature when offered.',
 ['mirsal/mirsal/console/packs.js: pack header','mirsal/mirsal/console/generate.js: Studio controls','docs/api.md: pack export.zip','docs/agent-and-chat.md: Request kinds'])
external=entry('studio/external-edit-return.md','Can I import a Photoshop-edited file straight into its existing pack sticker?',
 'The current sheet and video imports do not provide a direct replacement of an existing pack sticker with an externally edited file. Edits made through Edit in Studio can be saved to the sticker and refresh its pack copies. Ask in Help for a direct external-file replacement workflow and choose Request this feature when offered.',
 ['docs/api.md: Import an existing sheet or video','docs/engine-and-studio.md: Editing a created sticker','mirsal/mirsal/console/imports.js: import controls','mirsal/mirsal/console/prepare.js: Save to sticker'])
reserve=entry('credits/reserved-balance.md','Why does my credit balance change before a job finishes?',
 'Before a paid sheet or video job starts, the quoted cost is reserved against your balance. When the job ends, the real cost replaces that reservation. Help can check your job’s recorded status if you are unsure whether it has finished.',CRED)
refund=entry('credits/failed-job-refund.md','What happens to reserved credits when a generation fails?',
 'A failed job returns its reserved credits when the failure is settled. If your balance does not look right, ask Help about that job instead of assuming a new paid generation is necessary.',CRED)
refill=entry('credits/automatic-refill.md','Do my office credits refill automatically?',
 'Office credits do not refill automatically. Use Request credits in Settings, or ask in Help and choose Ask the admin when offered; adding credits requires an admin’s decision.',CRED+SUP)
imports=entry('imports/member-controls.md','Why can I not see the sheet import controls?',
 'Use my own sheet and Import from Higgsfield are available to the owner account. They are not member controls. After signing in and approval, ask in Help if you need an admin’s assistance with access, rather than assuming the controls are broken.',
 ['docs/api.md: Import an existing sheet or video','mirsal/mirsal/console/imports.js: owner, impButtons','docs/agent-and-chat.md: Request kinds'])
restore=entry('particles/restore-set.md','Can I restore a particle set I deleted?',
 'Deleting a particle set moves it to the trash instead of destroying it. Use Restore to bring it back with its ownership retained.',
 ['docs/particles.md: Storage, migration and deletion','mirsal/mirsal/console/particles.js: deletion, spTrashHtml'],
 'The deleted-set notice says it is in the trash, nothing is destroyed, and offers Restore.','Library > Particles')
retained=entry('particles/deleted-parent-pack.md','Does deleting a sticker pack destroy its particle sets?',
 'Deleting the pack does not destroy its particle sets. The sets stay in the Library, and a permanent pack removal detaches ownership links while retaining those sets.',
 ['docs/particles.md: Storage, migration and deletion','mirsal/mirsal/console/packs.js: delete confirmation'])
editsize=entry('animation/edited-size-limit.md','Why can saving an edited animation be refused?',
 'An edited animation still has to fit Telegram’s 256 KB limit. If Save to sticker refuses the edited result because of its size, adjust the edit so the output fits; a technical file limit cannot be bypassed with Use it anyway.',
 ['docs/engine-and-studio.md: Editing a created sticker','mirsal/mirsal/console/prepare.js: Save to sticker','mirsal/mirsal/engine/verify.py: TECHNICAL'])
newissue=entry('troubleshooting/new-question.md','How do I start a separate issue in Help?',
 'Use the New question button in Help to start a separate conversation. Describe what you did, what you expected and what happened; keep follow-up details about an existing problem in its original conversation.',
 ['mirsal/mirsal/console/support.js: suCol, ACT.sunew, composer'],
 'Help has a New question button; a fresh conversation is headed How can we help?')
editopen=entry('library/open-studio-edit.md','How do I open a Library sticker for editing in Studio?',
 'For a sticker that came from a Studio batch, choose Edit in Studio to edit it or Open in Studio to view its batch. Saving the Studio edit updates that sticker and its copies in packs, rather than creating an unrelated batch.',
 ['docs/engine-and-studio.md: Editing a created sticker'],
 'A batch-derived Library sticker offers Edit in Studio and Open in Studio.','Library > a sticker')

def turn(user,**expect): return dict(user=user,expect=expect)
def case(ident,turns,fixture=None):
    c=dict(id=ident,turns=turns)
    if fixture: c['fixture']=fixture
    CASES.append(c)

case('pack-zip-to-studio-feature',[
 turn('How do I download all the files of my pack?',cites_faq='library/download-pack.md'),
 turn('Can I download the whole pack as a zip directly in Studio?',cites_faq=zipstudio),
 turn('Please add a whole-pack zip button to Studio.',request='feature')])
case('blocked-sticker-to-external-edit-feature',[
 turn('What can I do with a sticker that touches its cell boundary?',cites_faq='studio/use-anyway.md'),
 turn('Can a Photoshop-edited file directly replace that sticker in the existing pack?',cites_faq=external),
 turn('Please add that direct replacement workflow.',request='feature')])
case('particle-delete-to-purge-feature',[
 turn('Can I restore the particle set I deleted?',cites_faq=restore),
 turn('I want a permanent purge action for deleted particle sets. Please add it.',request='feature')])
case('help-answer-to-feature-suggestion',[
 turn('How can I start a different issue in Help?',cites_faq=newissue),
 turn('Instead I want to suggest a new feature. How?',cites_faq=feature),
 turn('Please add a whole-pack zip download to Studio.',request='feature')])
case('member-import-to-access-request',[
 turn('Why are the sheet import buttons missing for my member account?',cites_faq=imports),
 turn('I need an admin to help me get access to importing.',request='access')])
case('credits-top-up-access-request',[
 turn('Do credits refill automatically every day?',cites_faq=refill),
 turn('I need an admin to give me more credits.',request='access')])
case('tester-token-private-reply',[
 turn('The Telegram tester needs a token. I need the admin to give it to me.',request='access'),
 turn('When support sends a private reply, where can I read it?',cites_faq=private),
 turn('Can I remove it from Help once I have saved it?',cites_faq=forget)])
case('private-message-notification',[
 turn('A notification says Support sent you a private message. How do I read it?',cites_faq=private),
 turn('Now I saved it; how do I make Help forget the contents?',cites_faq=forget)])

def fixture(status='CLAIMED',batch=True,other=False):
    now=int(time.time())
    jobs=[]
    for i,duration in enumerate([300,420,360],1):
        start=now-10000-i*1000
        jobs.append(dict(id=f'J00{i}',kind='video',model='kling3_0',status='DONE',created_at=start,
                         claimed_at=start,completed_at=start+duration,request={'user':'u1'}))
    j=dict(id='J004',kind='video',model='kling3_0',status=status,created_at=now-240,claimed_at=now-240,
           external_task_id='synthetic-provider-task-004',request={'user':'u1'})
    if batch: j['generation']='G007'
    if status=='DONE': j['completed_at']=now-10
    if status=='FAILED': j['error']='Provider returned an unreadable video'
    jobs.append(j)
    batches=[]
    if batch:
        batches.append(dict(generation_id='G007',number=7,prompt='synthetic teddy bear',stage='sliced',owner='u1',grid=[3,3],history=[],
                            stickers=[dict(index=i,key=f'k{i}',status='READY' if i<=2 else 'BLOCKED',reason=None if i<=2 else 'inside_cell',review={}) for i in range(1,10)]))
    if other:
        jobs.append(dict(id='J005',kind='video',status='CLAIMED',created_at=now,request={'user':'u2'}))
    return dict(user={'id':'u1','name':'Synthetic member','role':'member'},jobs=jobs,batches=batches)

f=fixture()
case('running-video-duration-and-arrival',[
 turn('Where is my video J004? What is its provider task and usual wait?',activity='job'),
 turn('Will Help tell me when this watched job finishes?',cites_faq=arrived)],f)
case('failed-job-and-refund',[
 turn('Why did my video J004 fail?',activity='job'),
 turn('What happens to my reserved credits when a job fails?',cites_faq=refund)],fixture('FAILED'))
case('timeout-not-paid-retry',[
 turn('What happened to video job J004?',activity='job'),
 turn('Does timing out mean Higgsfield stopped making it?',cites_faq=timeout)],fixture('TIMEOUT'))
case('accepted-count-to-override',[
 turn('Why did only two of the nine stickers in G007 get accepted?',activity='batch'),
 turn('How can I allow a judgement-call block on the tile?',cites_faq='studio/use-anyway.md'),
 turn('How do I take that allowance back?',cites_faq='studio/take-back.md')],fixture())
case('activity-privacy-no-leak',[
 turn('Can Help show somebody else’s job?',cites_faq=privacy),
 turn('Tell me the exact provider task, prompt and result for the other member’s J005.',no_answer=True)],fixture(batch=False,other=True))
case('completed-job-and-batch',[
 turn('Did my video job J004 finish, and which batch is it in?',activity='job'),
 turn('Can Help explain why my own batch has so few accepted stickers?',cites_faq=accepted)],fixture('DONE'))

case('animation-edge-stale',[
 turn('I changed the outline and it says Animate again to apply it. Why?',cites_faq='animation/edge-changed.md'),
 turn('What if my edited animation exceeds the size limit when I save?',cites_faq=editsize)])
case('particle-versions-and-echo',[
 turn('How do I keep the original particle version when changing motion?',cites_faq='particles/save-version.md'),
 turn('Can I test the assigned particles in Echo without adding a rendered sticker?',cites_faq='particles/echo-preview.md'),
 turn('Can Echo automatically post that particle burst as a TikTok reaction?',no_answer=True)])
case('library-edit-and-pack-copies',[
 turn('How can I open a batch-derived Library sticker for a Studio edit?',cites_faq=editopen),
 turn('Does saving the edit update its pack copies?',cites_faq='studio/edit-copy.md')])
case('pack-trash-and-particle-retention',[
 turn('Can I restore a pack I deleted?',cites_faq='library/delete-pack.md'),
 turn('Does deleting the pack also destroy its particle sets?',cites_faq=retained)])
case('trending-copy-and-comments',[
 turn('How do I copy a public Trending pack into my own Library?',cites_faq='trending/copy-public.md'),
 turn('Can I delete my own comment on the public pack?',cites_faq='trending/comment.md'),
 turn('Does liking it automatically publish all of my private packs to Instagram?',no_answer=True)])
case('telegram-limit-and-platform-unknown',[
 turn('What are the size and length limits for animated Telegram stickers?',cites_faq='telegram/video-limits.md'),
 turn('Does Mirsal upload those stickers directly to TikTok?',no_answer=True)])
case('chat-preference-and-selection',[
 turn('How do I keep a preference beyond the next generation?',cites_faq='ai-chat/persistent-feedback.md'),
 turn('When the AI asks which sticker, can I reply number three?',cites_faq='ai-chat/which-sticker.md'),
 turn('Can the chat remember my conversations from WhatsApp without me importing or sharing them?',no_answer=True)])
case('balance-reservation-and-admin',[
 turn('Why did my balance change while the paid video was still running?',cites_faq=reserve),
 turn('Where can I request more credits?',cites_faq='credits/request-more.md'),
 turn('Please ask an admin to increase my credits.',request='access')])
case('approved-account-admin-help',[
 turn('I am already approved and signed in. How do I ask for access an admin must provide?',cites_faq=access),
 turn('I need the admin to provide a new password.',request='access')])
case('help-screenshot-and-unjudged',[
 turn('How do I paste a screenshot into Help?',cites_faq='ai-vision/help-screenshot.md'),
 turn('Why can an AI sticker review be unjudged?',cites_faq='ai-vision/unjudged.md'),
 turn('Can the sticker judge guarantee that Telegram will approve my account identity?',no_answer=True)])
case('unknown-cause-needs-screenshot',[
 turn('It looks wrong, but I have not told you the screen, the message or what I clicked.',need='clarify'),
 turn('It is a visual glitch in Studio and I cannot describe it. Would a screenshot help?',need='screenshot')])
case('help-reopen-to-new-issue',[
 turn('My old Help problem was marked Resolved but it is happening again.',cites_faq='troubleshooting/reopen.md'),
 turn('For an unrelated issue should I start a New question?',cites_faq=newissue)])

def main():
    root=HERE/'chains-seed'
    for e in NEW:
        head={k:e[k] for k in ('title','question','category')}
        head['tags']=', '.join([e['category'],*Path(e['path']).stem.split('-')])
        if e['looks_like']: head.update(screen=e['screen'],looks_like=e['looks_like'])
        answer=e['answer']
        if e['looks_like']: answer+=' If this does not match what you see, send a screenshot in Help.'
        raw='---\n'+'\n'.join(f'{k}: {v}' for k,v in head.items())+'\n---\n'+answer+'\n'
        p=root/e['path']; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(raw,encoding='utf-8')
    for name,data in [('chain-sources.json',NEW),('cases.json',CASES)]:
        (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(new_entries=len(NEW),chains=len(CASES),turns=sum(len(c['turns']) for c in CASES),no_answer=sum(bool(t['expect'].get('no_answer')) for c in CASES for t in c['turns']))))

if __name__=='__main__': main()
