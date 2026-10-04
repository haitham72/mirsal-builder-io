# Motion Graphics: the Mirsal Creator film

This folder is a motion-as-code kit. Every frame of the film is a deterministic function of time, written in TypeScript and rendered by three.js. The browser preview and the exported MP4 are the same pixels. This guide turns the kit into **the launch film for the Mirsal Creator**, the sticker engine this repo builds for the Mirsal app.

**Where it stands (2026-10-04).** The kit still holds its first film: a 92.6 s explainer called "Motion as Code", with its own voiceover, nine plates and about 500 sound cues. Everything in it works and renders. Nothing Mirsal-specific has been made yet. The steps below replace the voiceover, the script, the palette, the plates and the sound. The engine stays.

Companion file: [`mirsal-ai-redesign-prompt.md`](mirsal-ai-redesign-prompt.md) holds the prompt for the new look of Mirsal AI, a full redesign of the original Mirsal chat. Plate 7 of the film shows that new look, so both pieces should agree.

---

## 1. The film at a glance

| | |
|---|---|
| Length | about 90 s (the voiceover sets the length; the timeline follows it) |
| Format | 1920×1080 at 60 fps, H.264. `--scale 2` gives 4K. The engine is fixed at 16:9 (`W`, `H` in `app/src/engine/gl.ts`); a 9:16 cut for phones is separate work (§10) |
| Story | one sentence becomes a moving sticker pack → **one click** → **it learns you** → **batching** → **no dead ends** → **the whole team** → **inside the Mirsal app** → logo, loop |
| Look | the kit's plotter-and-spark language, retuned to Mirsal: deep navy stage, Mirsal blue `#3B82F6` as the signal colour, AI cyan `#22D3EE` as the hot core, the glossy blue orb as the pen head |
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
| `drawPen`, `sparkHead`, `sparkParticles` | the spark that draws. For Mirsal it becomes the orb (§4) |
| `gridPass` + `setGrid` | the graph-paper sheet behind a plate (reveal, fade, ink, paper) |
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

## 4. Re-skin: from P(doom) orange to Mirsal blue

### 4.1 Palette (`app/src/engine/palette.ts`)

Keep the key names, because every plate and the karaoke read them. Change only the values:

```ts
export const HEX = {
  ink: '#070B16',      // stage: deep night navy (the film is dark; the app is light, so keep the two apart)
  ink2: '#111A2E',     // raised navy: cards, panels, the chat window frame
  graphite: '#475569', // dim lines, secondary text (Slate 600)
  ash: '#94A3B8',      // mid grey, unsaid karaoke outlines (Slate 400)
  bone: '#F7F8FA',     // paper white: primary text and light plates (the app's background)
  signal: '#3B82F6',   // Mirsal blue: the said word, the pen, the one button, every "go"
  ember: '#22D3EE',    // AI cyan: the hot core of the orb and the rolling highlight
  blood: '#2563EB',    // Primary Dark: the shadow side of signal
  acid: '#F59E0B',     // one rare accent: the falcon's gold, the price, the Trending heart
} as const;
```

These come from the builder board (`ref/Mirsal-Builder-upscaled.jpg`) and `docs/design.md` §3. Use `acid` at most once per plate. It is the falcon's beak, not a second brand colour.

### 4.2 Glow and halation

**Blue does not bloom like orange.** Mirsal blue `#3B82F6` has a much lower luminance than the old orange, so at the default `bloomThreshold` 0.85 it barely glows. In additive passes (the pen, the orb, the button) scale `LIN.signal` and `LIN.ember` by 2 to 3, or return a `bloomThreshold` of about 0.6 from the plate.

**Halation** (`app/src/engine/post.ts`, line 141)

The film glow around highlights is hard-coded as red-orange: `vec3(1.0, 0.18, 0.04)`. Retune it to a cold blue, `vec3(0.18, 0.55, 1.0)`. Without this change every highlight bleeds orange and the blue reads muddy. In `DEFAULT_POST`, start with `halation: 0.3` and `bloom: 0.6` for a glossy, product-launch feel.

### 4.3 Motifs

| kit motif | Mirsal version |
|---|---|
| the spark (`sparkHead`, the pen of `drawPen`) | **the Mirsal orb**: a blue disc with a lighter inner sphere and one small white highlight (`ref/mirsal logo.jpeg`), with a cyan `ember` core and the existing particles for the trail. Change `sparkHead` / `sparkHead2D` in `_motifs.ts` once, and every plate inherits the change |
| graph-paper construction sheet | keep it for the "how it works" plates (creator, batch). It is the engine's blueprint |
| bone-paper forms (`paper: 1`) | the Mirsal app itself: light `#F7F8FA` cards, 16 px radius, the chat wallpaper's faint doodles. Use it for the persona, users and app plates |
| the P(doom) readout (`hud.ts`) | leave it off (`pdoom: 0` is already the default). The crop-mark frame is optional for the bookends |
| the mask motif (`MASK`, `drawMask2D`) | do not use. The Mirsal character is the falcon (`console/assets/welcome/s1.webp`) |

### 4.4 Type

Keep **Archivo** for display and kinetic type. Its width axis (620 to 1250) drives the word stretches, and opentype.js needs TTF outlines. Keep **IBM Plex Mono** for labels, prices, ids (`G111`, `S4`) and timecodes. The Mirsal app's own face is Inter (`ref/InterVariable.woff2`). It may appear only inside UI mockups drawn with Canvas2D. To add it, copy the file to `app/public/fonts/`, then register a `FontFace` for it alone. Do not add it to `DEFS`: opentype.js cannot parse WOFF2, so `layout()` and `ot()` would fail on it. Drop Cormorant. A serif has no place in this brand.

### 4.5 Real Mirsal pictures

Code draws everything except the stickers. Use real ones:

1. Copy 9 to 18 finished stickers (512 px PNG/WEBP, transparent) from `mirsal/out/library/files/<G…>/` into `app/public/stickers/`. Copy the falcon slides `mirsal/mirsal/console/assets/welcome/s1.webp…s4.webp` into `app/public/brand/`. Do not commit stickers from personal packs.
2. In a plate's `init()`, load them with `await img.decode()` (`const img = new Image(); img.src = 'stickers/s1.webp'; await img.decode();`). Then draw with `ctx.drawImage` inside `setWorld(...)`. Loading belongs in `init()` only, never in `render()`.
3. Choose stickers by their names and the verifier's status, not by opening files (rule 9). Haitham chooses the final set by eye in the preview.

---

## 5. The plates

Estimated times assume a read of about 160 wpm. The real times come from the alignment. Each plate lists its **anchor words** (the words that trigger beats), what happens on screen, the old plate to copy from as a starting point, and its sound.

### P1 `hook`: 0 to ~9.5 s. "What if one sentence…" / "No designer… Just Mirsal."
- A dark stage. A Mirsal composer bar ("Type a message", with the paperclip, lightning, emoji and mic icons) draws itself in hairlines. The sentence types into it as it is said: the karaoke words sit **inside** the bar.
- **"whole sticker pack"**: the send button fires and the orb flies out. Behind it, a 3×3 sheet unfolds tile by tile, one tile per syllable.
- **"already moving"**: every tile starts a small loop (bob, wave, squash), drawn from the real stickers. **"already in your chat"**: the sheet folds down into a chat bubble.
- **"No designer. No editing app."**: two struck-out mono labels (`snip`). **"Just Mirsal."**: a hard cut to the orb. It swells, `flash 0.4`, and the wordmark writes on in Archivo 125/900.
- From: `hook.ts` (typing plus the pen reveal). Sound: `typewriter`/`key_click` on the typed words, `enter_key` on send, `whoosh_fast` on the unfold, a new `sticker_pop` per tile, `snip` ×2, `impact_slam` on "Mirsal".

### P2 `creator`: ~9.5 to ~23 s. "Meet the Mirsal Creator." / "…press one button." / "…the whole path…"
- **"Meet the Mirsal Creator"**: the title in kinetic Archivo. The width stretches from 620 to 1250 across the word "Creator".
- **"Turn on approve for me"**: a small switch on the card's footer flips on, in Mirsal blue.
- **"you see the price"**: a plan card slides up (bone paper): subject, style, a 3×3 grid icon, and the price in Plex Mono ticking up to its value (`acid`). **"press one button"**: one big Mirsal-blue button, "Create and send", and a cursor. The click is a `zoom` punch, `flash 0.3`, `impact_slam`.
- **"sheet, cut, check, approve, animate, pack — and send"**: the camera pulls back onto the graph paper. Seven nodes light up in sequence, one per said word, joined by the orb's trail: sheet → cut → check → approve → animate → pack → send. Each node shows its real artifact (the sheet, nine cut cells, a green tick from the verifier, the G2 approval stamp, a moving cell, a pack tray, a paper plane). The human gates G1 to G5 sit under their nodes as small mono labels.
- From: `prompt.ts` for the card and `pipeline.ts` for the chain. Sound: `ui_blip` per node, `stamp` on "approve", `whoosh_soft` on "send", new `coin_tick` under the price, new `orb_whoosh` along the trail.

### P3 `persona`: ~23 to ~36 s. "And it gets to know you." / "…it remembers." / "…It never decides for you."
- A light plate (`paper: 1`). A profile card on bone paper: **"name"**, **"where you live"** and **"what you love"** each fill in with the plotter's stroke font (`strokeText`, `writtenLength`). The values are generic examples ("Sara", "Dubai", "falcons, coffee"); never use a real person's details.
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
import { Layer2D } from '../engine/gl';
import { rgba } from '../engine/palette';
import { F } from '../engine/type';
import { type Word } from '../engine/lyrics';
import { ease, prog, pulse } from '../engine/util';
import { Cam2D, gridPass, setGrid, drawKaraoke, placeRow, setWorld, lineOf, wordOf, type KWord } from './_vo';

export default class Creator extends Scene {
  cam = new Cam2D();
  grid = gridPass(24, 96);
  ui = new Layer2D();
  kw: KWord[] = [];
  button!: Word;

  override init() {
    const ly = this.ctx.lyrics;
    const L = lineOf(ly, 'press one button');
    this.button = wordOf(L, 'button');
    this.kw.push(...placeRow(L.words, -760, -320, 58, F.archivo(100, 700), 'r1', { ant: 0.2 }).words);
    this.cam.key(this.ctx.start, 0, 0, 1.2).key(this.button.start, 0, 40, 1.6, 0, ease.outExpo).key(this.ctx.end, 0, 40, 1.5);
  }

  override render(f: Frame, out: THREE.WebGLRenderTarget): PostOverrides {
    const { renderer, comp } = this.ctx;
    const t = f.t, c = this.cam.at(t);
    setGrid(this.grid, c, { reveal: [0, 0, 1e5], ink: 0.6 });
    this.grid.render(renderer, out);            // background first: it overwrites `out`
    const U = this.ui; U.clear(); const ctx = U.ctx;
    // the one button: grows in before the word, pressed on it
    const k = ease.outBack(prog(t, this.button.start - 0.5, this.button.start));
    setWorld(ctx, c, 0, 120, k);
    ctx.fillStyle = rgba('signal', 1);
    ctx.beginPath(); ctx.roundRect(-220, -48, 440, 96, 48); ctx.fill();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    drawKaraoke(ctx, c, t, this.kw);
    comp.draw(renderer, U.upload(), out);
    return { bloom: 0.65, zoom: 1 + 0.03 * pulse(t, this.button.start, 0.1), flash: 0.3 * pulse(t, this.button.start, 0.08) };
  }
}
```

Check which names `ease` offers in `engine/util.ts` before using one. `outExpo`, `inOutCubic` and `linear` are used throughout the plates.

---

## 6. The voiceover (ElevenLabs)

**Spending: this is a paid call.** Show the character count and price, and wait for Haitham's go before generating (rule 13; it is a voiceover, but the rule is the same). One take of about 1,400 characters costs very little on any plan, but the go-ahead still comes first.

**With the ElevenLabs MCP connected** (it is not connected in this session yet; add it in claude.ai connector settings or with `claude mcp add`, then ask Claude to "voice the Mirsal Creator script"), the request is:
- **Text**: the `SCRIPT` lines above, one paragraph per plate, with a line break between plates. That gives the natural 0.3 to 0.6 s pause that `cut()` lands in.
- **Voice**: **Haytham – Dramatic and Narrative**, id `wxweiHvoC2r2jFM7mS8b` (Haitham's pick, 2026-10-04), a shared ElevenLabs library voice: a warm middle-aged Egyptian storyteller reading the English script. For an Arabic version later the same voice fits natively (§10).
- **Model**: the newest multilingual model offered (an Arabic read comes later, §10). **Stability** 0.45, **similarity** 0.8, **style** 0.3, speaker boost on, speed 1.0 to 1.05.
- **Output**: MP3 44.1 kHz, 192 kbps or better. Save it as `audio/voiceover.mp3`, replacing the old one. Keep the old one in git history only.

**Without the MCP**, do the same in the ElevenLabs web app and download the MP3 to the same path.

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
3. **Align and analyse**:
   ```sh
   uv run --no-project --with onnxruntime --with numpy python analysis/align_vo.py
   uv run --no-project --with numpy python analysis/audio_vo.py
   ```
   Check `data/lyrics.json`: every line is present and no word has `end - start < 0.04`.
4. **Re-skin**: palette (§4.1), halation (§4.2), the orb in `_motifs.ts` (§4.3).
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
- [ ] No orange left anywhere: palette, halation and the old spark sounds
- [ ] Real Mirsal stickers and the falcon, with no personal or real-person data
- [ ] The P7 window matches `mirsal-ai-redesign-prompt.md`
- [ ] The film loops (last frame = frame 0) and plays from `mirsal-creator_web.mp4` in a browser
- [ ] Shipped files: the web MP4 and a poster JPG. If it replaces the welcome film (`docs/onboarding.md`), that doc changes in the same step

---

## 9. Layout of this folder

| path | what |
|---|---|
| `audio/voiceover.mp3` | the voiceover the whole film is timed to |
| `audio/sfx/` | the effect library, `name_N.mp3` = take N |
| `data/lyrics.json` | word timings made by the aligner, read by the plates and the cue sheet (never edit by hand) |
| `data/voiceover.words.json` | the old read's raw word times; nothing reads it, so delete it with the old voiceover |
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
