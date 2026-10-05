# Prompt: write the Mirsal help FAQ (paste into a model that can read this repository)

You are writing the first help FAQ for **Mirsal**, an app that makes animated Telegram stickers. You can read this whole repository. Your output becomes the knowledge base that an in-app support agent answers from, so accuracy matters more than volume.

## What to read first
1. `README.md` (the index), `run.md`, `CLAUDE.md` (rules), then every file in `docs/` except `docs/inputs/`.
2. Read the code under `mirsal/mirsal/` only to confirm what a screen or button really does. Never describe code to the user.
3. Read `mirsal/local_eval/README.md`, `results.md` and `summary.json`: a measured run of the AI vision pre-review (the local Qwen 3.5 9B model) on 30 real stickers. They are the facts for the `ai-vision/` entries: what the pre-review does, that it never approves for you, how long it takes (about 10 seconds a sticker there), and why a sticker can be left "unjudged" (5 of 30 answers there used a reason the app does not accept). Give these numbers as what one test measured, not as a promise. Do not copy sticker ids, file paths or the endpoint.

## What to write
Write **50 to 100 entries**, one question per file, as Markdown files under a top-level `faq/` folder, nested by category:

```
faq/
  getting-started/      signing in, the screens, the first batch
  studio/               making a batch, the sheet, approving and rejecting, "Use it anyway", regenerating one sticker
  animation/            animated stickers, loops, why an animation was blocked
  particles/            particle sets, bursts, the Echo chat, saving versions
  library/              packs, My Stickers, moving and deleting, the trash
  trending/             public packs, likes, comments, "Use in my workflow"
  telegram/             sending a pack, the size and format limits, why Telegram refuses a file
  ai-chat/              talking to the AI, what it remembers, plan cards and prices
  credits/              what costs credits, asking before spending, asking for more
  accounts/             office accounts, approval, roles, forgotten password
  imports/              using your own sheet, importing from Higgsfield
  ai-vision/            the AI pre-review of stickers, "unjudged", allowing AI vision once, captions, sending a screenshot to Help
  troubleshooting/      slow pages, stuck jobs, missing files, errors
```

Each file looks exactly like this (file name: a short slug, e.g. `faq/telegram/pack-refused.md`):

```markdown
---
title: Telegram refuses my pack
question: Why does Telegram refuse my sticker pack?
category: telegram
tags: telegram, size, webm
screen: Library > a pack > Send to Telegram
looks_like: a red notice under the Send to Telegram button saying the file is too large, next to the sticker that failed
---
One to three short paragraphs in plain words, with numbered steps when the person has to do something.
Name screens and buttons exactly as the app shows them (for example: Library > a pack > Send to Telegram).
```

## Screenshots: write what the problem LOOKS like
When a person sends a screenshot, the support agent shows it to a local vision model (Qwen 3.5 9B). The model describes what it sees, and that description is searched against these entries. So give every entry where a person **sees** the problem two more header lines:
- `screen:` where it happens, as a path of the app's own names (`Studio > a batch > Animation tab`, `Library > My Stickers`, `Chat`, `Settings`).
- `looks_like:` one or two sentences describing the screen as a camera would see it: the labels, badges, colours, button names and exact message text the docs or the code show for this case (for example "a sticker tile with a grey Blocked label and the reason under it, and a Use it anyway button"). Use the words the app prints, so the vision model's description matches them. No interpretation, no cause: only what is visible.
- Leave both out for a question with nothing to see (for example "What does a batch cost?").
- In the answer, when a screenshot would help, end with: "If this does not match what you see, send a screenshot in Help."

Also write a few `ai-vision/` entries about Help itself: that a person can send a screenshot, that the local model reads it (nothing leaves the office machine), and what makes a useful screenshot (the whole window, the message visible).

Aim for at least half the entries to have `looks_like`: troubleshooting, blocked and rejected stickers, animation, particles, Telegram, imports and errors especially.

## Rules (follow every one)
- **Only facts the repository states.** Every claim must come from `docs/`, the README or the code. If you are not sure, leave that entry out. A wrong answer is worse than a missing one.
- **Write for the person using the app, not for a developer.** No code, no file paths, no function names, no API routes, no environment variables. Telegram limits (256 KB, 512×512, 3 s, 30 FPS) are fine because users meet them.
- **Nothing only staff may know.** Leave out admin procedures, server setup, the database, tokens, the Telegram bot's setup, deployment, tests, and anything described as owner-only or admin-only, except what a member sees (for example "your account waits for approval").
- **No personal or secret data:** no names of people, e-mail addresses, record ids (G104, T012, ...), tokens, keys, passwords or machine paths.
- **One question per file**, asked the way a user would ask it ("Why is my animation grey at the end?", not "Loop closing algorithm"). Do not write two entries for the same question.
- **Current behaviour only.** Skip anything the docs call planned, paused, parked, a proposal or not built (for example public deployment, Google sign-in, burst creation).
- Answers: 2 to 8 sentences, plus steps where useful. Plain English, no marketing.
- Use these exact header keys: `title`, `question`, `category` (the folder name), `tags` (comma separated), and when there is something to see, `screen` and `looks_like`. Each header value goes on one line. Begin the file with the `---` line, and put nothing before it.

## When you finish
List the files you wrote, grouped by category, and add a short list of questions you skipped because the repository was unclear. Do not edit any other file.

---
*After the files exist, Haitham runs `python -m mirsal support import-faq --repo ../faq` from `mirsal/`. Every entry becomes a **draft** to review in Help > FAQ review. Run it again after editing a file: unchanged files are skipped, and an edited published entry becomes a proposed revision.*
