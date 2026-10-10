# The welcome modal (onboarding), 2026-10-03

What a person sees when the app is first opened in a browser session (on the LAN only once they are signed in and approved: `auth.js` calls `wlAuto()`, so the film and its sound never play behind the sign-in or waiting card, and showing a card closes it), and whenever Home's "Watch the film" is pressed (the Mirsal logo opens Home, `console/home.js`): a fast-cut 14-second ad film and four sliding feature images (stickers from one idea, stickers that move, emoji particle bursts, the AI chat). The modal is `console/welcome.js` (+ `studio.css` `.wl-*`, `docs/design.md` §9); the media are real files in `console/assets/welcome/`, served by `GET /assets/welcome/<name>` (Range, so a browser can seek and loop). A missing file leaves the soft gradient; the modal still works. Tests: `tests/test_welcome.py`, `tests/js/welcome.test.js`.

## How the media were made (two approved runs, Haitham, 2026-10-03: about 188 + 105 credits)

| asset | model and parameters | credits | file |
|---|---|---|---|
| slide 1, the mascot and a 3x3 sheet | `nano_banana_flash`, 16:9, 2k, no reference | 2.0 | `s1.webp` |
| slides 2, 3, 4 | `nano_banana_flash`, 16:9, 2k, `--image-references` = slide 1 (same mascot) | 2.0 each | `s2.webp`, `s3.webp`, `s4.webp` |
| film, take 1 (**not shipped**) | `seedance_2_5`, `omni_reference` (slide 1), 15 s, 1080p, `VIDEO` prompt below | 180.0 | rejected by Haitham: "extremely slow and tedious" (a cinematic reel; per-second frame difference 1 to 15, 4 hard cuts) |
| film, take 2 (**shipped**) | `seedance_2_5`, `omni_reference` (slide 1), 15 s, **720p**, 16:9, audio on, `VIDEO2` prompt below | 105.0 | `welcome.mp4` and `welcome-poster.jpg` |

Haitham's brief for take 2: an extremely fast ad in the Gemini-launch style: a chat box, the camera zooms in and whips right, many icons arrive extremely fast, and big words zoom in and out in fast cuts every 0.2 to 0.6 seconds. The prompt is a timed shot list of about 40 cuts with the words spelled out; every word is in quotes so the model writes it exactly. One attempt each, no retries. The tickets were written before waiting; every call is a line in `out/model_calls.jsonl` (labels `welcome <name>`). Sources (2752 x 1536 PNG, the provider's clips) stay outside the repo; shipped files are re-encoded (slides: WebP at 1920 px; film: H.264 `-crf 24 -movflags +faststart`, because HEVC does not play in every browser). The film's first 2.6 seconds (the chat bar typing) came out slow, so they are played at 2x (`welcome.mp4` is 13.8 s), picture and sound.

## Checked with numbers, not eyes (rule 9)

Images: size 2752 x 1536, mean colour about (205, 230, 233), the left 40% of every image is nearly flat (luma std 2.8 to 5.6, so the text sits on calm gradient), the right part carries the subject (std 22 to 42), edges bright (about 230). Film take 2 (provider clip, before the 2x of its start): 15.07 s, 1280 x 720, AAC audio; 25 to 27 hard cuts in 15 s (average 0.56 s, about 0.35 s after the first 2.9 s; the first 2.5 s were calm, hence the 2x), mean frame difference per second 2.4 / 1.4 / 5.6 / 13.5 / 9.9 / 15.8 / 20.5 / 28 / 8 / 7 / 5.7 / 18.9 / 7 / 14.7 / 10.3 (take 1: 1 to 15). In Chrome the film plays, ends, and the modal moves to slide 1. **What numbers cannot say:** whether the words on screen are spelled right and read well (video models garble letters); Haitham has seen take 1 only. The modal puts nothing over the film (it carries its own words); under 760 px the title and text sit under it.

## The prompts

```python
"""The prompts of the welcome modal (images + the 15 s video). Kept in the repo as docs/onboarding.md once the run is done."""

MASCOT = ("a cute glossy 3D cartoon falcon mascot: round chunky proportions, warm caramel-brown feathers with a cream chest and soft darker wing tips, large expressive dark eyes with "
          "bright white highlights, a small golden-yellow beak, tiny rounded talons, soft clay-and-glossy-plastic material with gentle subsurface glow")

LOOK = ("Premium modern 3D product illustration, high-key bright clean studio lighting, soft diffused shadows, pastel aqua to sky-blue gradient background "
        "(#E8F9FD to #CFEFFB) with a faint glass-morphism glow, warm coral and golden-yellow accents, shallow depth of field, smooth gradients, crisp edges, "
        "ultra clean and uncluttered, generous empty space on the left 40% of the frame (a calm smooth gradient where text can sit), main subject on the right 60%. "
        "No text, no letters, no numbers, no logos, no watermark, no UI screenshots, no human faces, no brand marks.")

IMAGES = {
    "s1": ("Slide one, 'from one idea to a whole pack'. " + LOOK + " Subject: " + MASCOT + ", shown large and smiling in front, in a white die-cut sticker outline, "
           "and behind and around it a floating, softly tilted 3 by 3 grid of nine glass-edged sticker tiles, each tile showing the SAME falcon mascot with a different expression "
           "(laughing, heart eyes, surprised, sleepy, cool with sunglasses, winking, crying with joy, cute angry, thumbs-up with a wing), tiles with subtle depth and soft reflections, "
           "one tile glowing slightly brighter. The mood is delightful, fresh, effortless."),
    "s2": ("Slide two, 'stickers that move'. " + LOOK + " Subject: the same falcon mascot from the reference image in a dynamic motion-sequence composition: five ghosted, "
           "progressively fading copies of the mascot in successive poses (wing wave, bounce, spin, laugh, landing) arranged along a smooth curved arc like a multi-exposure animation strip, "
           "the sharpest and most solid copy in the front, soft glossy motion trails and tiny sparkle dots following the arc, a thin elegant timeline bar of five small dots floating beneath "
           "it (no numbers). Energetic but clean, smooth and modern."),
    "s3": ("Slide three, 'emoji that burst'. " + LOOK + " Subject: a large glossy red 3D heart emoji in the centre-right, caught at the instant it pops, exploding outward into a ring "
           "of dozens of tiny glossy hearts, golden stars, white sparkles and little confetti shards flying radially in every direction with soft motion blur, some of them tumbling and "
           "beginning to fall, depth of field making far pieces soft; a few pieces of the burst are tiny falcon feathers in warm caramel brown. Celebratory, crisp, high energy, "
           "very clean background, pieces never touch the frame edge."),
    "s4": ("Slide four, 'just tell the AI chat'. " + LOOK + " Subject: a floating stack of three frosted-glass chat bubbles with soft rounded corners (the top one shows only a few "
           "abstract typing dots, no readable text), and the same falcon mascot from the reference image peeking cheerfully over the top bubble holding a tiny glowing wand-like pen, "
           "a small glossy sticker sheet and a sparkle bursting out of the lowest bubble, tiny floating emoji-like glossy shapes (heart, star, thumbs up) orbiting. Friendly, helpful, "
           "intelligent and calm."),
}

VIDEO = """A premium, modern, highly engaging 15-second product reel, 16:9, smooth 30 fps feel, no cuts that break continuity, one continuous elegant camera journey. The hero is the glossy 3D cartoon falcon mascot shown in the reference image: keep its design, colours, proportions and material identical in every shot. Visual language: high-key bright clean studio, an endless pale aqua-white infinity cove with soft volumetric light, pastel aqua and sky-blue gradients, warm coral and golden-yellow accents, glossy clay-and-plastic 3D materials, glass-morphism tiles, soft diffused shadows, shallow depth of field with creamy bokeh, subtle bloom, ultra clean and uncluttered. No text, no subtitles, no letters, no numbers, no logos, no watermarks, no real brand marks, no human faces.

[0.0-2.0s] A single tiny point of light pulses in the centre of the empty bright space. It pops open and the falcon mascot stamps into existence with a satisfying squash-and-stretch bounce, a crisp white die-cut sticker outline drawing itself around its silhouette in one smooth stroke and snapping tight. Slow gentle camera push-in, the mascot smiling and blinking once. A soft glassy 'pop' sound.

[2.0-5.0s] The camera glides back and slightly up. The mascot multiplies: a 3 by 3 grid of frosted glass sticker tiles unfurls outward from the centre in a smooth ripple, each tile flipping over with a tiny pop to reveal the same falcon with a different expression: laughing, heart eyes, surprised, sleepy, cool with sunglasses, winking, crying with joy, cute angry, thumbs-up. Tiles settle with delicate overshoot and soft reflections, an ascending light chime scale plays with each flip.

[5.0-8.0s] The heart-eyes tile lifts out of the grid and glides toward the camera until the mascot fills the frame. It comes alive with polished character animation: a happy bounce, a quick wing wave, a blink, a tiny squash on landing, feathers settling, smooth natural motion blur. The other tiles blur softly into the background and drift. The mood is warm, playful, effortless.

[8.0-11.0s] A glossy red 3D heart emoji floats up beside the mascot, hovers, and bursts: it explodes into dozens of tiny glossy hearts, golden stars, white sparkles and small confetti shards radiating outward in a perfect expanding ring like the burst effect that plays in a messaging app when you press an emoji, brief slow motion at the peak, then gravity gently takes every piece, tumbling and spinning as it falls, the pieces thinning out until the screen is clean and empty again. A bright sparkle whoosh on the burst, a soft sparkling fade on the fall.

[11.0-13.5s] A minimal frosted-glass smartphone with no brand marks glides in from the right, its screen showing a clean chat with soft rounded bubbles made only of abstract dots, no readable text. The falcon sticker leaps from the left, arcs through the air with a joyful spin, and lands inside a chat bubble with a bouncy settle, releasing a small ring of sparkles. A gentle 'send' swoosh and a soft pop.

[13.5-15.0s] The camera pulls back to a wide, balanced hero composition: the falcon mascot waves cheerfully in the centre, a few glossy confetti shapes and sparkles drifting slowly in the light, a gentle bloom washing the frame toward a calm, bright, clean aqua-white finish; the last second is calm and nearly still so it loops gracefully.

Audio: modern, upbeat, minimal electronic pop at about 110 bpm, warm soft bass and light plucky melodic hooks building across the reel, crisp glassy sound design for pops, whooshes, sparkles and chimes in sync with the visuals, a clean resolving final chord. No vocals, no speech, no spoken words."""


VIDEO2 = """An EXTREMELY FAST, high-energy, modern product ad, 16:9, 15 seconds, in the style of a viral AI-app launch spot (think a Gemini or ChatGPT feature ad): relentless fast cuts, camera punch-ins, whip-pans, flash frames, kinetic typography. This is NOT slow, NOT cinematic, NOT calm: no slow motion, no lingering, no quiet moments, no gentle camera moves. Every shot lasts only 0.2 to 0.6 seconds, about 40 cuts in total, each cut landing exactly on a beat. Visual language: bright high-key world of electric blue, aqua, white and hot coral and sunny yellow, glossy 3D icons and emoji, frosted-glass UI, heavy bold extra-black sans-serif letters (giant, centred, perfectly legible, spelled EXACTLY as written in quotes, nothing else written anywhere), strong motion blur on the whip-pans, tiny screen shakes and white flash frames between beats. The glossy 3D cartoon falcon mascot from the reference image appears only in quick flashes (keep its design identical). No logos, no brand marks, no real app interfaces, no human faces.

The big words always enter the same way: they slam in from huge (about 300% scale) down to full size with a punchy zoom-out, or punch in from small to huge with a zoom-in, fully legible for the cut, then the next cut hits immediately.

TIMELINE (seconds):
[0.00-0.30] White flash. A giant frosted-glass chat input bar slams into the centre of the screen, blinking cursor.
[0.30-0.80] The camera punches in at lightning speed toward the bar; the text "a happy falcon" types itself in a blur, the round send-arrow button glows.
[0.80-1.10] The send arrow is hit; the camera whip-pans hard to the RIGHT with heavy motion blur.
[1.10-1.50] Electric-blue screen, the word "STICKERS" slams in, zoom out from huge.
[1.50-1.80] A dense swarm of about 25 glossy emoji icons (laughing face, heart eyes, fire, red heart, star, thumbs up, rocket, crown, sparkles) streaks across the screen from left to right in motion-blur trails.
[1.80-2.10] Hot-coral screen, the word "ANIMATED" punches in, zoom in.
[2.10-2.40] A 3 by 3 grid of nine glossy falcon stickers pops onto the screen, each tile flashing.
[2.40-2.70] Tight punch-in on one tile, the falcon winks, white flash.
[2.70-3.10] Yellow screen, the words "9 AT ONCE" zoom out.
[3.10-3.40] Whip-pan right through a burst of hearts and stars.
[3.40-3.70] The falcon does a fast flip with speed lines.
[3.70-4.10] Aqua screen, the words "3 SECONDS" zoom in.
[4.10-4.40] A film strip of the falcon in five poses whips across the screen to the right.
[4.40-4.70] Blue screen, the word "MOVES" zoom out.
[4.70-5.00] Hard cut: a giant glossy red heart emoji fills the screen.
[5.00-5.40] The heart bursts into hundreds of tiny hearts and stars flying outward fast, then falling.
[5.40-5.80] Coral screen, the word "BURST" punches in huge, zoom in.
[5.80-6.10] Hundreds of tiny pieces rain down fast over the word.
[6.10-6.50] White screen, the word "EMOJI" zoom out.
[6.50-6.80] Whip-pan right through a flying swarm of emoji icons.
[6.80-7.10] Blue screen, the word "PARTICLES" zoom in.
[7.10-7.40] A burst of gold coins, gold bars and diamonds explodes outward.
[7.40-7.70] A burst of black bat silhouettes explodes outward on a yellow glow.
[7.70-8.00] A burst of paw prints and cat ears explodes outward.
[8.00-8.40] Coral screen, the words "ANY EMOJI" zoom out.
[8.40-8.70] A glass chat window appears, message bubbles stack up at high speed.
[8.70-9.10] Aqua screen, the words "ASK THE AI" punch in, zoom in.
[9.10-9.40] Camera punches in on the input bar, "3 packs of fruits" types itself in a blur.
[9.40-9.70] Three sticker sheets (strawberry, cherries, banana) slam in side by side.
[9.70-10.00] Whip-pan right through a swarm of fruit icons.
[10.00-10.40] Yellow screen, the words "ONE PRICE" zoom out.
[10.40-10.70] Blue screen, the words "ALL AT ONCE" zoom in.
[10.70-11.00] A fast swarm of sparkles and stars crosses the screen.
[11.00-11.40] White screen, the words "IT REMEMBERS" zoom out.
[11.40-11.70] Heart, star and check icons flash rapidly one after another.
[11.70-12.10] Coral screen, the words "YOU APPROVE" punch in, zoom in.
[12.10-12.40] Big green check marks flash across the screen.
[12.40-12.70] Stickers whoosh into glossy chat bubbles on a frosted-glass phone with no brand marks.
[12.70-13.20] Aqua screen, the words "SEND IT" zoom out.
[13.20-13.60] Confetti, icons and stickers explode across the whole frame.
[13.60-14.00] The falcon mascot slams in big and smiling with a squash-and-stretch pop.
[14.00-14.60] Blue screen, the word "MIRSAL" slams in giant, zoom out, settles for the last half second.
[14.60-15.00] White flash and out.

Audio: a tight, punchy, fast electronic beat at about 150 bpm, a hard hit, whoosh or pop on every single cut, typing clicks, sparkle risers, bass hits on the big words, a final hit on the last word. No vocals, no speech, no spoken words."""
```
