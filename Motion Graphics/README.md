# Motion Graphics: the Mirsal Creator film

This folder is a motion-as-code kit. Every frame of the film is a deterministic function of time, written in TypeScript and rendered by three.js. The browser preview and the exported MP4 are the same pixels. This guide turns the kit into **the launch film for the Mirsal Creator**, the sticker engine this repo builds for the Mirsal app.

**Where it stands (2026-10-04).** Two films share the kit, switched by `FILM` in `app/src/timeline.ts`:
- **`reel` (the current one):** the 48 s fast-cut ad, `app/src/scenes/reel.ts`, cut to the Suno track `audio/suno-48.mp3` (129.75 BPM, first beat 0.22 s, measured): the chat box, the green sheet keyed and cut, checks, stickers alive, particle bursts, one-click export to Mirsal going live, three packs at once, "Use it anyway", taste, team, Trending, the logo. Liam explains it in nine lines (`audio/reel48-vo/`); `analysis/reel_mix.py` places them, 277 effect cues and the music. Output `out/mirsal-reel-48s_sound.mp4`. Real pictures from the library, copied into `app/public/` and not committed. Render with `--url` on a port of its own: another project's dev server may hold 5173.
- **`voiced`:** the 87 s cut with Liam's voiceover (aligned; analysis in `data/voiced/audio.json`), its hook a real scene (`scenes/hook.ts`), the rest still rough-cut cards.

Companion file: [`mirsal-ai-redesign-prompt.md`](mirsal-ai-redesign-prompt.md) holds the prompt for the new look of Mirsal AI, a full redesign of the original Mirsal chat. Plate 7 of the film shows that new look, so both pieces should agree.

---

## 1. The film at a glance

| | |
|---|---|
| Length | about 90 s (the voiceover sets the length; the timeline follows it) |
| Format | 1920×1080 at 60 fps, H.264. `--scale 2` gives 4K. The engine is fixed at 16:9 (`W`, `H` in `app/src/engine/gl.ts`); a 9:16 cut for phones is separate work (§10) |
| Story | one sentence becomes a moving sticker pack → **one click** → **it learns you** → **batching** → **no dead ends** → **the whole team** → **inside the Mirsal app** → logo, loop |
| Look | **the Mirsal app's clean iOS look** (Haitham, 2026-10-04: "clean iOS, based on the app design"; not the plotter-on-graph-paper style and not the busy concept board): a light `#F7F8FA` stage, white cards with soft shadows and continuous corners, Inter, slate text, Mirsal blue `#3B82F6` for every action and the spoken word, the glossy blue orb as the guide, AI cyan `#22D3EE` only while the AI works |
| Sound | a new ElevenLabs voiceover. The kit's 28 effects are reused, and about 8 new Mirsal sounds are added (§7) |

---

## 2. How the kit works (read once)

```
audio/voiceover.mp3 ──► analysis/align_vo.py ──► data/lyrics.json     (every word's start and end)
                    └─► analysis/audio_vo.py ──► data/audio.json      (loudness envelopes, word onsets)
                                                     │
app/src/timeline.ts  (when each plate plays, cut in the pause before a line)
app/src/scenes/*.ts  (one plate each: a Scene class, render(f) draws frame t)
app/src/engine/      (the pdoom-video engine: GL, post, type, lyrics, audio, stroke fonts)
                                                     │
bunx vite ─► live preview          bun scripts/render.ts video ─► headless Chrome ─► raw frames ─► ffmpeg ─► out/*.mp4
analysis/sfx_mix.py (cue sheet from the same word times) ─► out/mix.wav ─► ffmpeg mux ─► final film
```

**Main rule: plates find their words by content, never by seconds.** A plate asks `lineOf(lyrics, 'press one button')` and `wordOf(line, 'button')`, then keys its animation to `word.start` and `word.end`. After a new read of the same script, every animation re-times itself. Do not write a literal time like `t = 14.2` in a plate.

**The scene contract** (`app/src/engine/scene.ts`): a plate is `export default class X extends Scene`. It builds everything in `init()` and draws everything in `render(f, out)`, as a function of `f.t` (song time), `f.lt` and `f.p` (its own local time and progress) and `f.a` (the voice loudness at t). `render` returns post overrides: `bloom`, `zoom` punch-ins, `shake`, `flash`, `paper` (light plate), `fade`. A plate that keeps state sets `stateful = true`. Most plates should stay stateless.

**The shared toolkit** (`app/src/scenes/_vo.ts`, `_motifs.ts`):

| tool | what it gives a plate |
|---|---|
| `Cam2D` | a keyframed 2D camera: `.key(t, cx, cy, zoom, roll, ease)`. The ease shapes the move that arrives at that key |
| `placeRow` + `drawKaraoke` | words laid out in world space. An unsaid word is a hairline outline; the word being said wipes in the **signal** colour; a said word cools to bone (or ink on a paper plate) |
| `Plot` | the plotter: strokes laid down by the pen on a timetable, plus construction lines, dimensions and mono notes |
| `drawOrb` (`scenes/card.ts`) | the Mirsal orb, drawn like the logo, as the guide that moves under the spoken word. The first film's additive `drawPen` / `sparkHead` glow does not show on a light stage |
| `gridPass` + `setGrid` | the graph-paper sheet of the first film. Not used in the Mirsal look; plates clear to the light stage (`clearRT(renderer, out, LIN.bone)`) |
| `label`, `arrowHead`, `triangle`, `returnArrow` | the mono UI voice and drawn arrows that match the hairlines |
| `Layer2D` | a Canvas2D layer uploaded as a texture: `U.clear()`, draw, then `comp.draw(renderer, U.upload(), out)` |
| `ease`, `prog`, `pulse`, `keys`, `noise1`, `hash` (`engine/util.ts`) | easing; 0..1 progress between two times; a decaying hit; piecewise keys; deterministic noise |

---

## 3. The script

This is the voiceover. One entry per display line. It goes into `SCRIPT` in `analysis/align_vo.py`, replacing the old one. Write numbers as words ("three", "nine") so the aligner has letters to match. `SPOKEN` handles the rest.

```python
SCRIPT = [
    # hook
    "What if one sentence could become a whole sticker pack… already moving, already in your chat?",
    "No designer. No editing app. Just Mirsal.",
    # creator: one click
    "Meet the Mirsal Creator.",
    "You say what you want, you see the price, and you press one button.",
    "Turn on “approve for me”, and that one click runs the whole path: sheet, cut, check, approve, animate, pack — and send.",
    # persona: it learns you
    "And it gets to know you.",
    "Tell it your name, where you live, what you love — and it remembers.",
    "Ask for cartoonish twice, and next time it offers it. It never decides for you.",
    # batch
    "Need more than one? Ask for three packs of fruit.",
    "It picks the subjects, plans each one, shows one price, and runs them all at once.",
    "Nine stickers a sheet, every frame checked.",
    # override: no dead ends
    "And a rejection is never a dead end.",
    "Every blocked sticker says why, in plain words, and a judgement call gets “Use it anyway” right on the picture.",
    # users
    "It’s made for the whole team.",
    "Everyone signs in, gets approved, and has their own credits and their own work.",
    "The best packs go to Trending — to like, to comment on, to make your own.",
    # app: the Mirsal app
    "This is the piece Mirsal has been waiting for.",
    "The Creator is an engine with an API, built to live right inside the Mirsal app, next to your chats.",
    # outro
    "Your words. Your taste. Your stickers.",
    "Mirsal Creator — one click.",
]
SPOKEN = {
    "—": [],                      # the dash is a pause between two words
    "API,": ["AY", "PEE", "EYE"],
}
```

About 230 words. **The words "one click" occur twice** (P2 and the outro): a plate must query a longer phrase (`lineOf(ly, 'that one click runs')`) or pass `nth`, or it animates on the wrong line. At a launch pace of 155 to 165 words per minute, that is 85 to 92 s.

### Every claim is true today

The film may only say what the code does. If a line changes, check it against this table first.

| line | where it is true |
|---|---|
| approve-for-me on, one click runs the whole path | the agentic creator, `agent/creator.py`; bypass is **off by default** (`DEFAULTS`, line 29), and only with it on does the standing approval cover G2, G4 and G5 (`docs/agent-and-chat.md`). P2 must show the switch being turned on |
| you see the price | one plan card with the price of the whole run; nothing is spent before the click (rule 13) |
| it remembers name, place, likes | the per-user profile, `agent/profile.py` (`out/profile/<user>.json`) |
| cartoonish twice → offers it, never decides | taste memory: offered after two consistent signals, never applied unasked (Haitham, 2026-10-04) |
| three packs of fruit, one price, all at once | `NEW_MULTI`, `subjects.pick`, `jobs.paid_parallel()` (default 3 in flight) |
| every frame checked | `engine/verify.py`, and the boundary check on every frame of the animation (G4) |
| a judgement call gets "Use it anyway" on the picture | rule 10, `docs/design.md` §9; a block where Telegram itself would refuse the file has no override, so the line says "a judgement call" |
| sign in, approved, own credits and work | office LAN accounts, Users > People, credits per person (`docs/api.md`) |
| Trending: like, comment, make your own | `flow/trending.py`, "Use in my workflow" |
| an engine with an API, built to live inside the Mirsal app | rule 11, `README.md` "Delivery" |

**Do not claim** that it is already live inside the Mirsal app, public sign-up, Google sign-in (both paused), or a live end-to-end run on real Higgsfield (W6 is still open). "Built to live inside" is the honest wording, so keep it.

---

## 4. The look: the Mirsal app, clean iOS

The film looks like the app it sells, at its best: what a person would see on an iPhone or a Mac, animated. Not a mood board, not a dark tech film, not graph paper. **Rule of thumb: if a frame would not pass as a screenshot of a beautifully designed iOS app, it is wrong.**

### 4.1 Palette (`app/src/engine/palette.ts`, built)

```ts
ink: '#1E293B',      // text on the light stage (Slate 800)
ink2: '#FFFFFF',     // surface: cards, sheets, the window
graphite: '#64748B', // secondary text (Slate 500)
ash: '#CBD5E1',      // hairlines, separators (Slate 300)
bone: '#F7F8FA',     // the stage: the app's background
signal: '#3B82F6',   // Mirsal blue: the spoken word, every button, every "go"
ember: '#22D3EE',    // AI cyan: only while the AI works (the rolling highlight)
blood: '#2563EB',    // Primary Dark: pressed states, gradients
acid: '#F59E0B',     // gold, at most once per plate: the falcon, the price, the heart
```

Plus, inside UI mockups, the app's own semantic colours: Success `#10B981`, Danger `#EF4444`, and the locked issue colours of `docs/design.md` §2 on a blocked sticker.

### 4.2 Post-processing (`app/src/engine/post.ts`, built)

`DEFAULT_POST` is now the clean look: bloom 0.06 (threshold 1.4, so it barely acts), **no** halation, **no** chromatic aberration, **no** vignette, grain 0.006 (only against banding in gradients), `paper: 1`. The tone shoulder starts at 0.92, so the light stage stays white and does not go grey. A plate may punch in with `zoom` or a soft white `flash`; it never adds film grit.

### 4.3 The visual language

| element | how |
|---|---|
| stage | `#F7F8FA`, with at most a faint blue radial wash from one corner (10% alpha) |
| cards | white, radius 20 to 28 (continuous-corner feel), shadow `rgba(15,23,42,0.08)` blur 16 to 40, offset y 4 to 12. No borders, or a 1 px `#E2E8F0` hairline |
| type | **Inter** (`F.inter(weight)`, static TTFs in `app/public/fonts/inter/`): display 64 to 96 at weight 700 with tracking −0.02; UI 15 to 17 at 500/600; numbers and prices in Inter too (no mono) |
| the orb | `drawOrb` (`scenes/card.ts`): the logo, a blue sphere with a lighter inner sphere and a small white highlight, a soft blue shadow. It guides the eye; it replaces the spark |
| UI | real iOS patterns: pill buttons (Mirsal blue, white text 600), segmented controls, bottom sheets with a grabber, chat bubbles (blue outgoing, white incoming), switches, list rows with chevrons, SF-style outline icons at 2 px |
| motion | iOS motion: springs (`ease.outBack` at small overshoot), 250 to 450 ms moves, sheets that slide up, cards that scale from 0.96 to 1 as they appear, gentle parallax. No shake, no glitch, no flash cuts |
| the AI | the only "magic": the cyan highlight rolling around the composer while the AI works, and stickers coming alive |

### 4.4 Real Mirsal pictures

Code draws everything except the stickers. Use real ones:

1. Copy 9 to 18 finished stickers (512 px PNG/WEBP, transparent) from `mirsal/out/library/files/<G…>/` into `app/public/stickers/`, and the falcon slides `mirsal/mirsal/console/assets/welcome/s1.webp…s4.webp` into `app/public/brand/`. Do not commit stickers from personal packs.
2. Load them in a plate's `init()` (`const img = new Image(); img.src = 'stickers/s1.webp'; await img.decode();`), then draw with `ctx.drawImage`. Loading belongs in `init()` only, never in `render()`.
3. Choose stickers by their names and the verifier's status, not by opening files (rule 9). Haitham chooses the final set by eye in the preview.

## 5. The plates

Estimated times assume a read of about 160 wpm. The real times come from the alignment. Each plate lists its **anchor words** (the words that trigger beats), what happens on screen, the old plate to copy from as a starting point, and its sound.

### P1 `hook`: 0 to ~9.5 s. "What if one sentence…" / "No designer… Just Mirsal."
- The light stage. A Mirsal composer bar ("Type a message", with the paperclip, lightning, emoji and mic icons) slides up like an iOS keyboard accessory. The sentence types into it as it is said: the karaoke words sit **inside** the bar.
- **"whole sticker pack"**: the send button fires and the orb flies out. Behind it, a 3×3 sheet unfolds tile by tile, one tile per syllable.
- **"already moving"**: every tile starts a small loop (bob, wave, squash), drawn from the real stickers. **"already in your chat"**: the sheet folds down into a chat bubble.
- **"No designer. No editing app."**: two app icons (a design tool, an editor) slide away and fade (`snip`). **"Just Mirsal."**: the orb springs to the centre and the wordmark appears beside it in Inter 800.
- From: `hook.ts` (typing plus the pen reveal). Sound: `typewriter`/`key_click` on the typed words, `enter_key` on send, `whoosh_fast` on the unfold, a new `sticker_pop` per tile, `snip` ×2, `impact_slam` on "Mirsal".

### P2 `creator`: ~9.5 to ~23 s. "Meet the Mirsal Creator." / "…press one button." / "…the whole path…"
- **"Meet the Mirsal Creator"**: the title in Inter 800, the word "Creator" in Mirsal blue, rising in with a spring.
- **"Turn on approve for me"**: a small switch on the card's footer flips on, in Mirsal blue.
- **"you see the price"**: a plan card slides up as an iOS bottom sheet: subject, style, a 3×3 grid icon, and the price ticking up to its value (`acid`). **"press one button"**: one big Mirsal-blue button, "Create and send", and a cursor. The click is a `zoom` punch, `flash 0.3`, `impact_slam`.
- **"sheet, cut, check, approve, animate, pack — and send"**: the card becomes a run card with seven steps in a row, each turning from grey to a blue check, one per said word, the orb travelling along them: sheet → cut → check → approve → animate → pack → send. Each node shows its real artifact (the sheet, nine cut cells, a green tick from the verifier, the G2 approval stamp, a moving cell, a pack tray, a paper plane). The human gates G1 to G5 sit under their nodes as small mono labels.
- From: `prompt.ts` for the card and `pipeline.ts` for the chain. Sound: `ui_blip` per node, `stamp` on "approve", `whoosh_soft` on "send", new `coin_tick` under the price, new `orb_whoosh` along the trail.

### P3 `persona`: ~23 to ~36 s. "And it gets to know you." / "…it remembers." / "…It never decides for you."
- An iOS bottom sheet, "What Mirsal knows about you": the rows **"name"**, **"where you live"** and **"what you love"** each fill in as they are said, like a form being typed. The values are generic examples ("Sara", "Dubai", "falcons, coffee"); never use a real person's details.
- **"remembers"**: the card folds into the orb, which pulses once.
- **"Ask for cartoonish twice"**: two chat bubbles, "make it more cartoonish" ×2, and a counter in mono, `cartoonish ×1 → ×2`. **"next time it offers it"**: a new plan card shows a soft chip: *you asked for cartoonish 2 times: say "cartoonish" to use it here*. **"It never decides for you"**: a cursor hovers and does **not** click, and the chip stays a choice. That is the point of the beat.
- From: `model.ts` (a card that writes itself) and `edits.ts` (the chat commands). Sound: `pen_line` while writing, `ui_tick` on the counter, `confirm_chime` on the offer, and silence on the non-click.

### P4 `batch`: ~36 to ~49 s. "…three packs of fruit." / "…runs them all at once." / "Nine stickers a sheet, every frame checked."
- **"three packs of fruit"**: one chat bubble splits into three lanes: cherry, banana, mango. Each is drawn as a fruit icon in hairlines.
- **"picks the subjects, plans each one"**: each lane gets its own small plan card. **"shows one price"**: the three prices sum into one total (`acid`). **"runs them all at once"**: three progress bars fill in parallel, with a mono readout `3 in flight · J058 J059 J060`. The ids are real-shaped job tickets.
- **"Nine stickers a sheet"**: the three sheets land. **"every frame checked"**: a scan line sweeps each animation's frames (the film strip from `frames.ts`) and leaves a tick per frame. Cells pass the boundary check (`inside_slot`, `loop_seam`) as small green marks.
- From: `frames.ts` (the strip and scan) and `pipeline.ts`. Sound: a new `sheet_slice` per sheet, `scan_sweep`, `projector_run` as a bed under the parallel bars, `ui_blip` triplets.

### P5 `override`: ~49 to ~58 s. "And a rejection is never a dead end." / "Every blocked sticker says why… “Use it anyway”…"
- A 3×3 sheet. One cell is blocked: hatched, with its issue colour (orange = out of bounds, from the locked palette in `docs/design.md` §2, kept here on purpose). **"dead end"**: a wall starts to draw, then is erased by the pen (`reverse_suck`).
- **"says why, in plain words"**: one sentence types under the tile: *"The wing crosses the edge of its square."* **"Use it anyway"**: the button draws on **the picture itself**. It is clicked, the hatch dissolves, and a small "allowed by you" warning stays. A ghost "Take it back" appears beside it, so the click is visibly reversible.
- From: `edits.ts`. Sound: `marker_strike` for the hatch, `typewriter` for the reason, `mouse_click` and `confirm_chime` on the allow.

### P6 `users`: ~58 to ~71 s. "It's made for the whole team." / "…approved… own credits and their own work." / "…Trending…"
- **"the whole team"**: a row of five avatars draws in (initials only, generic). **"signs in"** shows an email field with `@nadi.ae`. **"gets approved"** shows an Approve button pressed in Users > People, with a matching Telegram bot button flashing at the side. **"their own credits"**: a credits bar under each avatar. **"their own work"**: each avatar pulls its own stack of batches.
- **"Trending"**: the stacks fan out into a gallery of packs. **"to like"**: a heart pops (`acid`). **"to comment on"**: a speech mark. **"to make your own"**: "Use in my workflow", and a pack flies into a new batch.
- From: `pipeline.ts` (rows) and `verdict.ts` (the grid). Sound: `ui_blip` per avatar, `stamp` on approve, new `heart_pop`, `paper_slide` for the fan-out.

### P7 `app`: ~71 to ~82 s. "This is the piece Mirsal has been waiting for." / "…an engine with an API, built to live right inside the Mirsal app…"
- **"waiting for"**: a hard cut. The **new Mirsal AI desktop window** (the look from `mirsal-ai-redesign-prompt.md`) draws itself: a left rail, the chat list with "Mirsal AI" pinned at the top with its orb, a conversation over the doodle wallpaper, and the composer with the orb's cyan rolling highlight running around its border.
- **"an engine with an API"**: the window turns briefly transparent like an X-ray, showing the stack beneath it in mono: `engine → JSON API → Mirsal app`. A route label like `POST /api/chat/sessions` scrolls past.
- **"right inside the Mirsal app, next to your chats"**: the X-ray closes. In the composer, the orb button opens the sticker panel ("Create with AI"), and the pack from P1 drops into the conversation as a real sent sticker with a timestamp and ticks.
- From: `crazy.ts` (the reveal) plus a new window drawer in Canvas2D (Inter allowed here, §4.4). Sound: `impact_slam` on the cut, `scan_sweep` for the X-ray, new `message_pop` on the sent sticker.

### P8 `outro`: ~82 s to end. "Your words. Your taste. Your stickers." / "Mirsal Creator — one click."
- Three big words, one per phrase, each with a different sticker behind it. **"Mirsal Creator"** shows the wordmark and the orb. **"one click"** is the single button from P2 again: pressed, a white flash, and the frame returns to P1's empty composer. **The last frame equals frame 0**, so the film loops.
- From: `verdict.ts` (it already loops to frame 0). Sound: `riser` into "one click", `impact_slam`, then `reverse_suck` ending on frame 0.

### `app/src/timeline.ts`

```ts
const b = {
  creator:  cut('Meet the Mirsal Creator'),
  persona:  cut('And it gets to know you'),
  batch:    cut('Need more than one'),
  override: cut('a rejection is never'),
  users:    cut('made for the whole team'),
  app:      cut('Mirsal has been waiting'),
  outro:    cut('Your words'),
  end: au.duration,
};
return [
  E('hook', 'hook', 0, b.creator),
  E('creator', 'creator', b.creator, b.persona),
  E('persona', 'persona', b.persona, b.batch),
  E('batch', 'batch', b.batch, b.override),
  E('override', 'override', b.override, b.users),
  E('users', 'users', b.users, b.app),
  E('app', 'app', b.app, b.outro),
  E('outro', 'outro', b.outro, b.end),
];
```

Move the nine old plates to `app/src/scenes/_old/` before starting. The timeline's `import.meta.glob('./scenes/*.ts')` does not look into sub-folders, so the old plates stop loading. They stay readable as references, and the `lineOf` calls they make on the old script can no longer throw.

### A new plate, minimal skeleton

```ts
// CREATOR — "Meet the Mirsal Creator." / "…press one button." / "…the whole path…"
import type * as THREE from 'three';
import { Scene, type Frame, type PostOverrides } from '../engine/scene';
import { Layer2D, clearRT } from '../engine/gl';
import { LIN, rgba } from '../engine/palette';
import { F } from '../engine/type';
import { type Word } from '../engine/lyrics';
import { ease, prog, pulse } from '../engine/util';
import { Cam2D, drawKaraoke, placeRow, setWorld, lineOf, wordOf, type KWord } from './_vo';

export default class Creator extends Scene {
  cam = new Cam2D();
  ui = new Layer2D();
  kw: KWord[] = [];
  button!: Word;

  override init() {
    const ly = this.ctx.lyrics;
    const L = lineOf(ly, 'press one button');
    this.button = wordOf(L, 'button');
    this.kw.push(...placeRow(L.words, -760, -320, 58, F.inter(700), 'r1', { ant: 0.08, tracking: -0.02 }).words);
    this.cam.key(this.ctx.start, 0, 0, 1.2).key(this.button.start, 0, 40, 1.6, 0, ease.outExpo).key(this.ctx.end, 0, 40, 1.5);
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t, c = this.cam.at(t);
    clearRT(renderer, out, LIN.bone);           // the light stage first: it overwrites `out`
    const U = this.ui; U.clear(); const ctx = U.ctx;
    // the one button: grows in before the word, pressed on it
    const k = ease.outBack(prog(t, this.button.start - 0.5, this.button.start));
    setWorld(ctx, c, 0, 120, k);
    ctx.fillStyle = rgba('signal', 1);
    ctx.beginPath(); ctx.roundRect(-220, -48, 440, 96, 48); ctx.fill();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    drawKaraoke(ctx, c, t, this.kw, { paper: true, outline: false });
    comp.draw(renderer, U.upload(), out);
    return { zoom: 1 + 0.03 * pulse(t, this.button.start, 0.1), flash: 0.3 * pulse(t, this.button.start, 0.08) };
  }
}
```

Check which names `ease` offers in `engine/util.ts` before using one. `outExpo`, `inOutCubic` and `linear` are used throughout the plates.

---

## 6. The voiceover (ElevenLabs)

**Spending: this is a paid call.** Show the character count and price, and wait for Haitham's go before generating (rule 13; it is a voiceover, but the rule is the same). One take of about 1,400 characters costs very little on any plan, but the go-ahead still comes first.

**Through the ElevenLabs MCP** (`claude mcp add elevenlabs -s user -e ELEVENLABS_API_KEY=… -- uvx elevenlabs-mcp`; the key stays in the user config, never in the repo), `text_to_speech` with:
- **Text**: the `SCRIPT` lines above, one paragraph per plate, with a line break between plates. That gives the natural 0.3 to 0.6 s pause that `cut()` lands in.
- **Voice**: **Liam – Energetic, Social Media Creator** (`TX3LPaxmHKxFdv7VOQHJ`, an ElevenLabs premade voice; Haitham, 2026-10-04: "any available male voice"). The take is `audio/takes/liam-take1.mp3`, `eleven_multilingual_v2`, stability 0.45, similarity 0.8, style 0.3, `mp3_44100_128` (the free plan refuses 192 kbps, and refuses shared library voices through the API, which ruled out the first pick, Haytham – Dramatic and Narrative).
- **Model**: the newest multilingual model offered (an Arabic read comes later, §10). **Stability** 0.45, **similarity** 0.8, **style** 0.3, speaker boost on, speed 1.0 to 1.05.
- **Output**: MP3 44.1 kHz, 192 kbps or better. Save it as `audio/voiceover.mp3`, replacing the old one. Keep the old one in git history only.

**Without the MCP**, do the same in the ElevenLabs web app and download the MP3 to the same path. A shared library voice works there on the free plan; through the API it needs a paid plan.

Read-through check before aligning: the read must say every word of `SCRIPT` exactly. An ad-lib breaks the alignment. If the voice says "A-P-I" as "appy", regenerate that line or add the spoken form to `SPOKEN`.

---

## 7. Sound

### 7.1 Reuse (already in `audio/sfx/`)

`whoosh_fast`, `whoosh_soft`, `impact_slam`, `impact_small`, `key_click`, `typewriter`, `enter_key`, `mouse_click`, `ui_blip`, `ui_tick`, `confirm_chime`, `stamp`, `snip`, `scan_sweep`, `projector_run`, `paper_slide`, `pen_line`, `riser`, `reverse_suck`, `marker_strike`. Retire `spark_sizzle`, `spark_ignite` and `zap_slash`: they are the orange spark's voice, not the orb's.

### 7.2 New (ElevenLabs Sound Effects, 2 takes each, saved as `name_1.mp3`, `name_2.mp3`)

| name | prompt | placement mode |
|---|---|---|
| `orb_whoosh` | "soft glassy whoosh with a gentle airy shimmer, short, clean, modern UI" | peak |
| `sticker_pop` | "tiny satisfying vinyl sticker pop, crisp, playful, very short" | onset |
| `sticker_peel` | "quick sticker peeling off a sheet, light and crisp" | onset |
| `sheet_slice` | "fast paper cutter slicing a grid, three quick clean cuts" | onset |
| `coin_tick` | "small soft digital counter ticks rising, warm, subtle" | raw |
| `heart_pop` | "cute bubbly pop with a light sparkle, social like button" | onset |
| `message_pop` | "modern chat message sent sound, soft whoosh into a light pop" | onset |
| `orb_hum` | "low warm glassy hum with slow shimmer, ambient bed, seamless loop" | raw (a bed under P7) |

Add each new name to `MODE` in `analysis/sfx_mix.py` when its mode is not `onset`.

### 7.3 The cue sheet

`analysis/sfx_mix.py` keeps its helpers (`line`, `W`, `parts`, `cut`, `cue`, `bed`, `typing`, `type_words`, `jitter`). Replace everything below `# ---- cues` with Mirsal cues written the same way: every cue gets a time **from a word**, never a number. Examples:

```python
L = line("press one button"); b = W("press one button", "button")
cue(b["start"] - 0.005, "impact_slam", -14, length=0.5, fade=0.2)   # the one click
cue(b["start"], "mouse_click", -12)
type_words("key_click", line("What if one sentence")["words"], -24, pan=-0.1)   # P1 typing
bed("projector_run", W("runs them all", "runs")["start"], W("Nine stickers", "checked")["end"], -30)
cue(cut("Your words"), "reverse_suck", -17)
```

Also set `DUR` to the new duration (it is the old 92.64 hard-coded; read it from `data/audio.json` `duration`), and rename the outputs from `motion-as-code` to `mirsal-creator`. Keep the mix rules: effects ducked up to 7 dB under the voice, the master at −14 LUFS. A film this dense needs fewer cues than the old one. Aim for 150 to 250 cues, not 500: a click per UI action, a whoosh per camera move, and silence where the beat is a choice (P3's non-click).

---

## 8. Step by step

All commands run from `Motion Graphics/`. Needed tools: bun, Google Chrome, ffmpeg with libx264, and Python with uv (`uv` on the PATH; `python -m uv` fails on this Mac).

1. **Script**: paste `SCRIPT` and `SPOKEN` (§3) into `analysis/align_vo.py`.
2. **Voiceover**: §6, after the go-ahead. Result: `audio/voiceover.mp3`.
3. **Align and analyse** (before the read exists, `uv run --no-project python analysis/approx_vo.py` writes provisional timings from the same `SCRIPT`, so plates can be built first):
   ```sh
   uv run --no-project --with onnxruntime --with numpy python analysis/align_vo.py
   uv run --no-project --with numpy python analysis/audio_vo.py
   ```
   Check `data/lyrics.json`: every line is present and no word has `end - start < 0.04`.
4. **The look** (§4): built; new plates follow §4.3.
5. **Retire the old plates**: move them to `app/src/scenes/_old/`. Write `timeline.ts` (§5).
6. **Plates, one at a time**, in film order. Preview each and lock it before starting the next:
   ```sh
   cd app && bunx vite              # http://localhost:5173 , ?t=23 starts at 23 s
   ```
   | key | action |
   |---|---|
   | space | play / pause |
   | ← / → | seek ±1 s (±5 s with shift) |
   | `,` / `.` | one frame back / forward |
   | `[` / `]` | previous / next plate |
   | `l` | loop the current plate |
   | `h` | hide the UI |

   Stills and contact sheets while editing:
   ```sh
   bun scripts/render.ts stills --t 12.5,17.0 --only creator --out ../out/wip
   bun scripts/render.ts sheet --from 9 --to 23 --n 12 --cols 4 --only creator --out ../out/wip/creator.png
   ```
   Errors show in red in the preview. A wrong `lineOf` query throws at load and names the missing line.
7. **Sound**: generate the new effects (§7.2, after the go-ahead), write the cue sheet, and build the mix:
   ```sh
   uv run --no-project --with numpy python analysis/sfx_mix.py
   ```
8. **Render and mux**:
   ```sh
   cd app
   bun scripts/render.ts video --samples auto --min-samples 4 --max-samples 12 --shutter 0.5 --crf 17 --out ../out/mirsal-creator.mp4
   cd ../out
   ffmpeg -i mirsal-creator.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest mirsal-creator_sfx.mp4
   ffmpeg -i mirsal-creator_sfx.mp4 -c:v libx264 -crf 24 -preset slow -c:a aac -b:a 192k -movflags +faststart mirsal-creator_web.mp4
   ```
   `--samples auto` adds motion blur only where motion is fast. Use `--samples 4` for a quick draft and `--scale 2` for 4K. A sound change never needs a re-render: rebuild the mix and re-mux.
9. **Review** (Haitham, by eye and ear): the stickers chosen, the voice, any misspelled word on screen, and whether P3's "never decides" reads clearly. Measurable things are checked with numbers: duration, that frame 0 equals the last frame (loop), the loudness at −14 LUFS (`ffmpeg -af ebur128`).

### Done means

- [ ] Every line of the script is on screen when it is said, and every claim is in the table in §3
- [ ] Every frame passes as a well-designed iOS screen (§4); no grit, glow or old spark sounds
- [ ] Real Mirsal stickers and the falcon, with no personal or real-person data
- [ ] The P7 window matches `mirsal-ai-redesign-prompt.md`
- [ ] The film loops (last frame = frame 0) and plays from `mirsal-creator_web.mp4` in a browser
- [ ] Shipped files: the web MP4 and a poster JPG. If it replaces the welcome film (`docs/onboarding.md`), that doc changes in the same step

---

## 9. Layout of this folder

| path | what |
|---|---|
| `audio/voiceover.mp3` | the voiceover the whole film is timed to (Liam, ElevenLabs) |
| `audio/takes/` | every ElevenLabs take (ignored; the old film's read is `takes/old/`) |
| `audio/sfx/` | the effect library, `name_N.mp3` = take N |
| `data/lyrics.json` | word timings made by the aligner, read by the plates and the cue sheet (never edit by hand) |
| `data/audio.json` | loudness envelopes, word onsets, a nominal 120 BPM grid that only feeds generic helpers |
| `analysis/align_vo.py` | CTC forced alignment with wav2vec2-base-960h (quantized ONNX, `analysis/models/`), then word edges refined against the silences |
| `analysis/audio_vo.py` | the audio analysis |
| `analysis/sfx_mix.py` | the cue sheet and the mixer |
| `app/src/engine/` | the engine (do not fork it per plate; change it once, for all plates) |
| `app/src/scenes/` | the plates, plus `_vo.ts` and `_motifs.ts` (the shared toolkit) |
| `app/src/timeline.ts` | the edit |
| `app/scripts/render.ts` | the offline renderer: `stills`, `sheet`, `plates`, `perf`, `video` |
| `out/` | renders (not committed) |

`app/node_modules/` is ignored: install it with `cd app && bun install` on each machine (a copy made on Windows lacks the macOS build of Vite's bundler and Vite will not start). `out/` and the alignment model are ignored too. The model is `onnx/model_quantized.onnx` of [Xenova/wav2vec2-base-960h](https://huggingface.co/Xenova/wav2vec2-base-960h) (95,286,046 bytes, SHA-256 `cd5040c1…b4d760a3`); fetch it once:

```sh
curl -L -o analysis/models/w2v2_base_960h_q.onnx https://huggingface.co/Xenova/wav2vec2-base-960h/resolve/main/onnx/model_quantized.onnx
```

Never commit personal stickers into `app/public/stickers/`.

## 10. Later

- **9:16 for phones and stories**: parameterise `W`/`H` in `engine/gl.ts` and give each plate a portrait camera. Most plates are centred, so it is camera work, not a redraw.
- **Arabic read**: the aligner's model is English-only (wav2vec2-base-960h). An Arabic voiceover needs an Arabic CTC model or word times from ElevenLabs, plus right-to-left karaoke (`placeRow` lays words out left to right).
- **15 s cut-down**: P1, P2's click, P7's sent sticker and the outro. The same plates on a shorter script.

## Credits

The engine and the plotter/spark visual language come from **[pdoom-video](https://github.com/mexicat/pdoom-video)** by mexicat (Giacomo Magnanini), under the MIT licence; see `LICENSE.pdoom-engine`, which must ship with any copy of the engine. The fonts are under the SIL OFL (`app/public/fonts/src/OFL.txt`). The Mirsal plates, script and sound design are this project's own.
