"""Grounded FAQ seed builder. Writes only beneath local_eval/faq; no app calls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ENTRIES = []

def group(category, source, screen, rows):
    for slug, question, answer, visible in rows:
        ENTRIES.append(dict(path=f'{category}/{slug}.md', title=question.rstrip('?'), question=question,
                            category=category, tags=', '.join([category, *slug.split('-')]),
                            answer=answer, screen=screen if visible else '', looks_like=visible, sources=source))

group('getting-started', ['README.md: Overview and Console', 'docs/onboarding.md: The welcome modal'], 'Studio', [
 ('stickers-not-emoji', 'Does Mirsal make stickers or custom emoji?', 'Mirsal makes Telegram stickers, including animated stickers. The emoji attached to a sticker is its tag, not a custom emoji output.', ''),
 ('welcome-again', 'How can I watch the welcome introduction again?', 'Press the Mirsal logo to open the welcome introduction again. It also opens automatically once per browser session after sign-in and approval.', 'The Mirsal logo opens the welcome introduction.'),
 ('two-ways', 'Should I use the AI chat or Studio?', 'Use the AI chat to describe what you want in everyday words and refine it in conversation. Use Studio when you want explicit controls for the prompt and sticker settings.', ''),
 ('batch-and-sheet', 'What is the difference between a batch and a sheet?', 'A batch is one generation of stickers. Its sheet contains the individual pictures arranged in cells; each sticker keeps its original cell number through review and animation.', ''),
])
group('accounts', ['docs/api.md: Office accounts on the LAN', 'mirsal/mirsal/console/auth.js: gate, waiting, change, me'], 'Sign in', [
 ('create-account', 'How do I create an office account?', 'Choose Create account on the sign-in screen and enter your name, an email from an allowed office domain, and a password. A new account waits for approval before the app opens.', 'Sign in to Mirsal has Create account and Forgot password links.'),
 ('waiting-approval', 'Why does my account say Waiting for approval?', 'Your account has not been approved yet. Keep the waiting page open; it opens the app by itself after approval.', 'Waiting for approval appears with a Sign out button.'),
 ('forgot-password', 'How do I reset a forgotten password?', 'Choose Forgot password, enter your account email, and press Ask for a new password. This requests a new password from support staff; it is not an automatic email reset.', 'Forgot password has an Ask for a new password button.'),
 ('choose-password', 'Why am I asked to choose my own password?', 'Your account was given a starting password. Enter a new password of at least eight characters and press Save; Keep the given password for now postpones the change until a later sign-in.', 'Choose your own password shows Your new password (8 characters or more), Save and Keep the given password for now.'),
 ('sign-out', 'Where can I sign out?', 'Open Settings and find Signed in as. Press Sign out to leave the account.', 'Signed in as appears beside Sign out and Request credits.'),
])
group('studio', ['docs/engine-and-studio.md: The golden path; Use it anyway; Editing a created sticker', 'mirsal/mirsal/console/generate.js: cellVerb, tileHtml, grmText', 'mirsal/mirsal/console/live.js: remHtml'], 'Studio', [
 ('drop-sticker', 'Does dropping a sticker delete it?', 'Dropping a sticker excludes it from the set without deleting its picture. Use Bring back to include it again when the sticker is eligible.', 'A sticker tile says Dropped and offers Bring back.'),
 ('use-anyway', 'What does Use it anyway do on a blocked sticker?', 'Use it anyway lets you allow a judgement-call block, such as the picture touching its cell boundary. The warning remains as allowed by you, and you can undo that choice with Take it back.', 'A blocked sticker shows its picture, a reason and Use it anyway.'),
 ('take-back', 'How do I undo allowing a blocked sticker?', 'Press Take it back on the sticker you allowed. This reverses the override, so the original judgement-call block applies again.', 'The sticker says allowed by you beside Take it back.'),
 ('bulk-allow', 'Can I allow several judgement-call blocks together?', 'Use all anyway applies to the currently allow-able stickers in that batch. Its number counts eligible overrides, and Take all back reverses those allowances.', 'Use all anyway has a count next to the button; Take all back is the reverse control.'),
 ('hard-limit', 'Why can I not override a file or Telegram limit?', 'A judgement-call warning can be allowed, but a file that Telegram would reject still has to meet its technical limits. An empty cell with no picture also cannot become a usable sticker through an override.', 'The check category says File or Telegram limit.'),
 ('remove-batch', 'Will removing a batch remove stickers already in my packs?', 'Remove batch moves the batch to the trash, where it can be restored. Stickers already added to a pack stay in their packs.', 'Remove batch is available, and Removed batches appears under Earlier batches.'),
 ('restore-batch', 'How do I restore a removed batch?', 'Open Removed batches under Earlier batches and press Restore beside the batch. Restore brings it back; the Remove button in that list is a permanent-removal action.', 'Removed batches lists Restore and Remove beside each batch.'),
 ('edit-copy', 'Will editing a Studio sticker update its pack copy?', 'An edit saved to a sticker from a Studio batch refreshes the copies of that sticker in its packs. Its name, emoji and order stay the same.', ''),
 ('fixed-sheet', 'What is the Fixed sheet view?', 'Fixed shows the batch sheet with edited cells replaced by their current pictures. The original layout and cell numbers are preserved.', 'The sheet panel has a Fixed view with edited cell numbers.'),
])
group('animation', ['docs/engine-and-studio.md: Animation; Edge; The golden path', 'mirsal/mirsal/console/generate.js: ANIMWHY, tileHtml, gate counts'], 'Studio > Animation', [
 ('not-animated', 'Why does a sticker say Not animated yet?', 'The still picture is ready but does not have an animation yet. Animation needs the prepared video, and the Animation stage reports when no video is prepared.', 'A sticker tile says Not animated yet; the Animation stage can say No video prepared.'),
 ('outside-slot', 'Why is an animation out of bounds?', 'The character leaves its own slot or reaches into a neighbouring slot on the animation sheet. It is off by default, but a judgement-call boundary warning can be allowed with the visible override.', 'Animation shows out of bounds (off), and the tile can offer Include anyway.'),
 ('bad-loop', 'Why does an animation show Bad loop?', 'The end of the animation does not join cleanly to its beginning. Loop quality is a judgement call that can be allowed where the tile offers Use it anyway.', 'The problem category says Bad loop and the reason says the loop does not close.'),
 ('edge-changed', 'Why must I animate again after changing the edge?', 'Changing the outline or rim trim makes animations created with the previous edge stale. Animate again to apply the new edge to those animations.', 'The tile says edge changed: Animate again to apply it.'),
 ('frame-checks', 'What does the app check while animating?', 'It checks each animation frame by frame, including file size, the loop and whether the character stays within its cell. Finished animations appear as they become ready.', ''),
])
group('particles', ['docs/particles.md: Ownership; One scoped editor; Animated sprites and recovery; Galleries and chat'], 'Library > Particles', [
 ('sprites-burst', 'What is the difference between sprites and a burst?', 'Sprites are the individual still or animated pieces of artwork. A burst is the composition made from selected sprites and their motion settings.', ''),
 ('free-source', 'Can I make particles without spending credits?', 'Choose Sprites from the sticker and select existing artwork. Use selected · free reuses those sprites without a paid generation.', 'The source card says Sprites from the sticker and Use selected · free.'),
 ('paid-sources', 'Which particle sources use credits?', 'AI image sprites and Kling animated · from scratch create new artwork using credits. Check the quoted price before choosing Generate.', 'The source choices include AI image sprites and Kling animated · from scratch.'),
 ('save-version', 'How do I save a new particle version?', 'Save turns a draft into the next saved version. When editing a saved row, Save replaces that row, while Save as new preserves the old row and creates a new one with the changed settings.', 'A saved particle version offers Save and Save as new.'),
 ('open-version', 'Why does entering Particles start a new version?', 'Entering Particles starts a new draft rather than reopening an old saved set automatically. To edit a particular saved version, press Open on that version row.', 'Saved version rows have Open buttons and version numbers.'),
 ('add-more', 'Does Add more replace my existing particle sprites?', 'Add more appends sprites to the set you have open. Existing sprites are preserved, and a set can contain both image and video sources.', 'The open particle set offers Add more.'),
 ('size-sharpness', 'How do I make the particles look larger?', 'Change Size to alter how large the particles appear. Sprite resolution changes sharpness rather than their apparent size.', 'The simulator controls include Energy, Float, Swirl and Size.'),
 ('put-in-pack', 'How do I add a particle burst to a pack?', 'Render the burst, then use Add to pack on its row. In pack ✓ indicates that the burst has been added as an animated pack sticker.', 'The row offers Add to pack or shows In pack ✓.'),
 ('echo-preview', 'Can I test particles in chat without rendering a pack sticker?', 'Use Assign to stickers followed by Test in chat. Echo plays the assigned set using its saved settings, without requiring a rendered pack sticker.', 'The particle controls include Assign to stickers and Test in chat.'),
 ('standalone', 'Can a particle set exist without a parent sticker?', 'Yes, a stand-alone particle set is usable without a sticker owner. You can preview it, render it, download it or make a pack from it.', ''),
])
group('library', ['mirsal/mirsal/console/app.js: libBody, libByPackHtml', 'mirsal/mirsal/console/packs.js: pack header, delete confirmation, carousel', 'mirsal/mirsal/console/trash.js: Trash panel'], 'Library', [
 ('empty-library', 'Why does my Library say Nothing here yet?', 'Your Library has no packs or stickers to show yet. Use Open Studio to make a pack, or Create from photo to create a sticker from a photo.', 'Nothing here yet appears with Open Studio and Create from photo.'),
 ('my-stickers', 'Where can I see all my stickers grouped by pack?', 'Open Library and choose My Stickers. It groups the stickers under their pack names, with Open pack beside each group.', 'My Stickers shows pack headings and Open pack buttons.'),
 ('search-library', 'What does the Library search match?', 'The Library filter matches sticker names, emoji and pack names. A filter with no matching results can leave the Recent section showing No matches.', 'Recent can show No matches when the filter has no results.'),
 ('bulk-select', 'How can I select multiple Library stickers?', 'Tick the square selection markers or drag a box over the stickers. Shift adds to the selection and Ctrl un-selects, so you can delete selected stickers together.', 'My Stickers says Tick the square, or drag a box over the stickers (Shift adds, Ctrl un-selects).'),
 ('delete-pack', 'Can I restore a deleted pack?', 'Delete pack moves it to the trash with its sticker files intact. Use Settings > Trash to restore it or explicitly delete it for good; copies that came from batches stay in those batches.', 'The pack has Delete pack; Settings has Trash and Restore.'),
 ('download-pack', 'Can I download all sticker files in a pack together?', 'Open the pack in Library and press Download .zip. The download contains its animated and static sticker files together.', 'The pack header offers Download .zip.'),
])
group('trending', ['mirsal/mirsal/console/trending.js: list, detail, ORDERS', 'docs/api.md: Trending'], 'Library > Trending', [
 ('copy-public', 'How do I use a public pack in my own work?', 'Open the public pack in Trending and press Use in my workflow. This makes a copy in your own Library rather than editing the original public pack.', 'A public pack has Use in my workflow.'),
 ('no-public', 'Why does Trending say Nothing public yet?', 'Trending shows packs that have been made public. If none are available, it shows Nothing public yet rather than your private Library packs.', 'Trending says Nothing public yet. Make a pack public from its page.'),
 ('sort-public', 'How can I change the ordering of public packs?', 'Use the Trending, New and Most liked tabs in Library > Trending. Each tab selects a different ordering of the public packs.', 'The public-pack list has Trending, New and Most liked tabs.'),
 ('comment', 'How do I comment on a public pack?', 'Open the public pack, write in Say something about this pack, and press Comment. You can delete your own comment using its delete control.', 'The public pack has Say something about this pack and a Comment button.'),
])
group('telegram', ['docs/engine-and-studio.md: Telegram limits', 'mirsal/mirsal/engine/config.py: EngineConfig', 'mirsal/mirsal/engine/verify.py: no_audio', 'mirsal/mirsal/console/packs.js: owner send control, sticker details'], '', [
 ('video-limits', 'What limits apply to an animated Telegram sticker?', 'Animated stickers use transparent WEBM video and must fit within 256 KB. Mirsal targets 512 by 512 pixels, at most three seconds and 30 frames per second, with no audio.', ''),
 ('static-limits', 'What limits apply to a static Telegram sticker?', 'Static stickers use PNG or WEBP with transparency and must fit within 512 KB. Mirsal makes the final sticker on a 512 by 512 pixel canvas.', ''),
 ('emoji-tag', 'Why does every sticker need an emoji tag?', 'Telegram requires at least one emoji tag per sticker. Open Sticker details to edit its Emoji tag; the tag does not turn the sticker into a custom emoji.', ''),
 ('member-send', 'Why can I not see Send to Telegram in my pack?', 'Sending a pack to Telegram is available to the owner account. Members can still work with their packs and use Download .zip to download the sticker files.', ''),
])
group('ai-chat', ['docs/agent-and-chat.md: Spending; Memory; Questions and their answers', 'mirsal/mirsal/console/agent.js: settings popover'], '', [
 ('remember-subject', 'What does the AI chat remember about my stickers?', 'Within a conversation, the chat keeps each subject and its generations, together with what you liked or disliked. This context helps it interpret follow-up requests about the same subject.', ''),
 ('persistent-feedback', 'How can I make a preference apply beyond the next generation?', 'Ordinary feedback shapes the next generation. State a lasting preference explicitly, such as saying that you never want dark outlines, to make it persistent.', ''),
 ('which-sticker', 'How do I answer when the AI asks which sticker I mean?', 'Reply with the sticker number, an ordinal such as number three, or select the sticker and say this one. The chat uses that answer to continue the request it just asked about.', ''),
 ('not-yet', 'How do I postpone a proposed generation?', 'Choose Not yet on the plan card instead of accepting it. With Ask before spending enabled, the plan shows the price and waits for your go-ahead.', ''),
])
group('credits', ['docs/agent-and-chat.md: Spending', 'mirsal/mirsal/console/agent.js: Ask before spending', 'mirsal/mirsal/console/auth.js: me'], 'Settings', [
 ('spend-confirmation', 'Will the AI start spending without asking me?', 'With Ask before spending enabled, a plan shows the price and waits for confirmation. Turning it off lets the chat start generation immediately, so keep it on if you want to approve each spend.', 'The AI settings have Ask before spending and Show the price and wait for your go-ahead.'),
 ('request-more', 'How can I ask for more credits?', 'Open Settings and press Request credits beside Signed in as. This sends a request rather than immediately adding credits to your balance.', 'Signed in as shows credits left and Request credits.'),
])
group('ai-vision', ['docs/agent-and-chat.md: The vision judge; Consent; Per-frame captions; Support', 'mirsal/local_eval/results.md', 'mirsal/mirsal/console/support.js: screenshot composer'], 'Help', [
 ('review-not-approval', 'Does the AI pre-review approve stickers for me?', 'No, the vision model only pre-reviews the pictures. Human review still decides whether to approve or reject them.', ''),
 ('unjudged', 'Why can the AI leave a sticker unjudged?', 'A model answer that cannot be accepted leaves the sticker unjudged rather than pretending the review succeeded. In one local test, five of thirty answers used unsupported reasons; that is one measurement, not a guarantee about future reviews.', ''),
 ('review-time', 'How long does the local AI pre-review take?', 'One test of thirty stickers measured about ten seconds per sticker with the local model. Actual time depends on the model and workload, so that measurement is not a promised wait time.', ''),
 ('consent', 'Why does the app ask me to allow AI vision?', 'The app asks for permission before sending generated pictures to a vision model. Allow AI vision permits the requested look; Not now declines it, and the chat also has an AI vision switch.', ''),
 ('captions', 'What are AI captions for my stickers?', 'AI captions describe what each ready sticker shows, including visible text. They do not change your approval or rejection decisions, and stored captions are reused until the picture changes.', ''),
 ('help-screenshot', 'How can I send a screenshot to Help?', 'Open Help, describe the problem and use Attach a screenshot, or paste an image with Ctrl+V. The local vision model reads the support screenshot on the office machine; that support reading does not send it to a cloud model.', 'Help has Attach a screenshot and Paste a screenshot with Ctrl+V; the local AI reads it.'),
 ('useful-screenshot', 'What should I include in a useful support screenshot?', 'Capture the app window with the relevant screen, controls and error message visible. Add what you did, what you expected and what happened so Help has both the picture and your explanation.', ''),
])
group('troubleshooting', ['mirsal/mirsal/console/support.js: next, fresh, noteRow, suOpen, suFile', 'docs/api.md: Help & Support'], 'Help', [
 ('no-answer', 'What do I do when Help has no answer?', 'Press Send to support when Help says it has no answer. This raises the issue for a person, and their reply appears in the conversation with a notification.', 'Nothing in the help answers this yet. appears beside Send to support.'),
 ('answer-wrong', 'What if the Help answer did not solve my issue?', 'Press No, send to support beneath Did this solve it? to escalate the issue. If the answer did work, choose Yes, solved instead.', 'Did this solve it? has Yes, solved and No, send to support.'),
 ('waiting-support', 'What does Waiting for support mean?', 'Your question has been sent to a person for a reply. You can add details in the same conversation, and a notification arrives when support answers.', 'Waiting for support appears with A person will answer here; you get a notification.'),
 ('notification', 'Where do I find a reply from support?', 'Open Help and look under Notifications for Support answered or Resolved. Selecting a notification opens the related conversation and marks its notifications read.', 'Notifications lists Support answered or Resolved.'),
 ('reopen', 'How do I reopen a support issue marked Resolved?', 'Open the resolved conversation and press Reopen under Not fixed after all? Continue in that conversation so your previous explanation remains available.', 'Resolved appears with Not fixed after all? and Reopen.'),
 ('screenshot-large', 'Why does Help reject my screenshot as too large?', 'The message A screenshot must be under 8 MB means the attachment exceeds the size limit. Use a smaller screenshot and attach it again.', 'Help shows A screenshot must be under 8 MB.'),
])

def main():
    dest = HERE / 'seed'
    for e in ENTRIES:
        if e['path']=='credits/spend-confirmation.md': e['screen']='AI > settings'
        head = {k:e[k] for k in ('title','question','category','tags')}
        if e['looks_like']:
            head.update(screen=e['screen'], looks_like=e['looks_like'])
        # YAML-safe single-line values, also accepted by the simple importer.
        lines = ['---', *[f'{k}: '+ "'"+v.replace("'", "''")+"'" for k,v in head.items()], '---', e['answer']]
        if e['looks_like']:
            lines[-1] += ' If this does not match what you see, send a screenshot in Help.'
        p=dest/e['path']; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'sources.json').write_text(json.dumps(ENTRIES,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Inventory all documentation, preserving hashes and headings for the audit.
    inventory=[]
    for p in [REPO/'README.md',REPO/'run.md',REPO/'CLAUDE.md',*sorted((REPO/'docs').rglob('*'))]:
        if not p.is_file() or 'inputs' in p.relative_to(REPO).parts: continue
        raw=p.read_bytes()
        inventory.append(dict(path=p.relative_to(REPO).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),
                              headings=[s for s in raw.decode('utf-8','replace').splitlines() if s.startswith('#')][:100]))
    (HERE/'source-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(entries=len(ENTRIES),visual=sum(bool(e['looks_like']) for e in ENTRIES),categories=len(set(e['category'] for e in ENTRIES)))))

if __name__=='__main__': main()
