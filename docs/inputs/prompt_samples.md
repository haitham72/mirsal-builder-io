# generic emojis

Create a clean, high-quality 3D emoji reaction sheet featuring 16 different expressive yellow emoji faces arranged in a perfectly aligned 4×4 grid.

ASPECT RATIO: 16:9 landscape widescreen.

STYLE:

###

Premium glossy 3D emoji illustration, soft rounded shapes, smooth golden-yellow surfaces, subtle realistic shading, expressive dark brown eyebrows, large animated eyes, soft reflections, and gentle ambient shading. All 16 emojis must share the EXACT same visual style, proportions, lighting, material, and size.

GRID LAYOUT:
4 columns × 4 rows, evenly spaced.
All emoji faces must be perfectly circular and consistently sized.
Increase the spacing noticeably between each emoji, with larger horizontal and vertical gaps so every emoji is clearly separated and easy to crop individually later.
Keep generous margins around the full grid.
No overlapping.

BACKGROUND:
Solid pure green chroma key background / green screen background, clean and flat, with no texture, no gradient, no shadow cast onto the background, and no extra elements.

16 UNIQUE REACTIONS:

ROW 1:

1. Happy — wide open-mouth smile.
2. Winking — playful sideways smile.
3. In Love — red heart-shaped eyes.
4. Laughing — eyes closed with blue tears of laughter.

ROW 2: 5. Shocked — wide eyes and open mouth. 6. Pleading — oversized watery eyes and sad expression. 7. Angry — furrowed eyebrows and frowning mouth. 8. Cool — black sunglasses and confident smile.

ROW 3: 9. Blowing a Kiss — one eye closed, puckered lips, floating red heart. 10. Silly — playful expression with tongue sticking out. 11. Thinking — raised eyebrow and hand resting on chin. 12. Sleepy — closed eyes, open mouth, small floating blue ZZZ symbols.

ROW 4: 13. Nervous — anxious wide eyes and clenched teeth. 14. Crying — sad face with two large streams of blue tears. 15. Content — peaceful closed-eye smile with rosy cheeks. 16. Loving — smiling emoji hugging a large red heart.

COMPOSITION:
Professional emoji sheet presentation. Every reaction must be immediately recognizable and visually distinct. Maintain consistent character identity across all 16 variations. Center the complete grid within the 16:9 frame with wide spacing between emojis and balanced outer padding.

No duplicate expressions, no distorted faces, no missing emojis, no extra emojis, no text, no watermark, no border, no dividers.

---

# customized emoji

## teddy bear

You are an expert image-prompt generator for premium 3×3 emoji/sticker packs.

The user will provide a simple request such as:
“yellow teddy bear in Pixar 3D iOS style”

Your job is to transform it into a complete, highly detailed visual prompt while preserving the requested character and visual style.

GLOBAL RULES

1. CHARACTER LOCK
   Create one consistent character design across the entire 3×3 pack.
   Keep identical:

- body proportions
- head shape
- facial structure
- eye design
- colors
- materials
- clothing/accessories unless specifically changed for an action
- rendering style
- lighting
- camera perspective
- overall visual identity

2. STYLE LOCK
   Interpret the user's requested style precisely.
   Translate vague style descriptions into concrete visual properties such as:

- 3D rendering
- materials
- surface finish
- lighting
- shadows
- proportions
- color treatment
- level of realism
- facial expression
- shape language
- polish
- visual softness
- camera treatment

For example, “Pixar 3D iOS style” should become a polished premium 3D animated-film-inspired character combined with modern iOS emoji/sticker aesthetics: rounded forms, expressive face, soft cinematic lighting, clean materials, glossy subtle highlights, appealing proportions, highly polished rendering.

3. 3×3 PACK STRUCTURE
   Generate exactly 9 different concepts arranged conceptually as:

1.1 | 1.2 | 1.3
2.1 | 2.2 | 2.3
3.1 | 3.2 | 3.3

Every cell must depict the SAME character performing a completely different action, emotion, reaction, or situation.

Make the actions highly varied and visually expressive.

Mix:

- comedy
- extreme reactions
- emotions
- physical actions
- celebrations
- failures
- surprises
- cute moments
- dramatic poses
- absurd situations
- social reactions
- useful conversational emotions

Avoid nine variations of the same pose.

4. CREATIVE FREEDOM
   Be imaginative and unexpected.
   Push the concepts beyond basic emotions.
   Use exaggerated cartoon physics, dramatic poses, funny situations, creative props, visual storytelling and expressive body language.

Each concept should be immediately understandable as an emoji/sticker.

5. EMOJI COMPOSITION
   Every individual image must contain:

- one main character
- full body visible
- centered composition
- clear silhouette
- dynamic readable pose
- expressive face
- enough empty space around the character
- flat solid pure chroma-key green background (blue if the character itself contains green); the app removes it later
- no unnecessary environment

Props are allowed when they strengthen the concept.

6. CLEAN OUTPUT
   Do NOT introduce:

- text
- captions
- speech bubbles
- logos
- watermarks
- borders
- frames
- extra characters
- duplicated characters
- unnecessary background scenery
- random decorative particles unless they are clearly useful to the action

7. PRODUCTION QUALITY
   Prompts should describe:

- premium professional rendering
- smooth rounded geometry
- clean silhouette
- polished materials
- believable soft lighting
- no shadow cast onto the background, no floor (shadows on the green key out as dirty smudges)
- high-quality facial expression
- appealing color harmony
- strong readability at small emoji size

8. CONSISTENCY
   Every prompt MUST repeat the important character and style characteristics so the image-generation model does not drift between cells.

9. OUTPUT FORMAT
   Return ONLY this JSON, no explanations. The app assembles it into either one 3×3 sheet prompt or 9 standalone prompts, and adds the background/no-text rules itself.

```json
{
  "extraction": {
    "subject": "...",
    "attributes": [],
    "style_words": "...",
    "occasion": null,
    "tone": "...",
    "constraints": []
  },
  "character_lock": "[every identity detail, repeated verbatim into each cell by the app]",
  "style_lock": "[the requested style translated into concrete visual properties]",
  "cells": [
    {
      "index": 1,
      "name": "[Concept Name]",
      "concept": "[CONCEPT_ID]",
      "emoji": ["[best-matching emoji]"],
      "action": "[the pose, expression, props and situation for this cell]",
      "motion": "[one-sentence looping animation that ends where it starts]",
      "key_color_risk": false,
      "keywords": {
        "en": ["[2-5 search words]"],
        "ar": ["[2-5 Arabic search words]"]
      }
    }
  ],
  "key_color": "green"
}
```

Cells 1–9 map to 1.1 | 1.2 | 1.3 / 2.1 | 2.2 | 2.3 / 3.1 | 3.2 | 3.3.

10. IMPORTANT
    The user's first sentence may be extremely short.
    Infer the missing visual details intelligently.

Example input:
“yellow teddy bear in Pixar 3D iOS style”

Interpret that as:

- Character: cute yellow teddy bear
- Requested visual direction: premium Pixar-inspired 3D animated aesthetic + polished iOS emoji aesthetic
- Produce nine wildly different but stylistically consistent sticker concepts.

Every generated prompt must preserve the same character identity and visual language across all nine images.

## perfect output example for initial tests

### CuteEmoji_element-1.png:

Premium 3D sticker of a cute perfectly round yellow emoji character with the exact same face proportions, smooth polished yellow material, large white eyes with black pupils, simple rounded facial features, and compact expressive silhouette throughout the pack, expressing intense anger and frustration with sharply furrowed eyebrows, narrowed eyes, clenched rectangular teeth, tense cheeks, and a dramatic forward-leaning head pose, with both fists tightly clenched just below the face to reinforce the emotion, subtle tension lines only if needed, square 1:1 composition, character centered and fully visible, generous empty safety margin on every side, nothing touching or crossing the canvas boundary, clean premium sticker outline, soft professional studio lighting, subtle realistic shading, high-detail commercial 3D emoji rendering, minimal uncluttered background.

### CuteEmoji_element-2.png:

Premium 3D sticker of the exact same cute round yellow emoji character, identical facial proportions, smooth yellow material, eye design, and polished 3D construction, expressing nervous worry with raised inner eyebrows, wide slightly upward-looking eyes, a small trembling squiggly mouth, one tiny sweat drop on the temple, tense cheeks, and shoulders subtly raised as if anxiously waiting, square 1:1 composition, centered full character, generous empty margin around the entire character and sweat drop, nothing touching or crossing the canvas edges, clean polished sticker outline, soft professional lighting, subtle depth and shading, high-quality commercial emoji rendering, minimal background.

### CuteEmoji_element-3.png:

Premium 3D sticker of the exact same round yellow emoji character with identical proportions, materials, colors, and facial construction, expressing extreme boredom and unimpressed disbelief with half-lidded eyes, lowered heavy eyelids, slightly raised eyebrows, relaxed cheeks, and a loose open mouth with a bored expression, head tilted slightly backward as though reluctantly listening to something uninteresting, square 1:1 composition, character centered and completely visible with generous empty safety margins, no element touching the edges, clean premium sticker outline, soft studio lighting, subtle realistic shading, polished commercial 3D emoji quality, minimal uncluttered background.

### CuteEmoji_element-4.png:

Premium 3D sticker of the exact same cute round yellow emoji character, identical face geometry, smooth polished yellow material, large expressive eyes, and consistent proportions, expressing an enormous cheerful grin with sparkling happy eyes, lifted cheeks, raised eyebrows, and a broad toothy smile showing clean rounded white teeth, head slightly tilted with an irresistibly playful confident expression, square 1:1 composition, full character centered with generous empty margin on all sides, nothing cropped or touching the canvas boundary, clean high-quality sticker outline, soft professional lighting, subtle depth and shading, premium commercial 3D emoji rendering, simple clean background.

### CuteEmoji_element-5.png:

Premium 3D sticker of the exact same round yellow emoji character with identical proportions and polished material, peacefully sleeping with both eyes gently closed, relaxed eyebrows, softly open rounded mouth, relaxed cheeks, and head slightly tilted downward, with a small pair of floating purple “Z” symbols beside the head to clearly reinforce sleep, keeping the decorative symbols subtle and fully inside the canvas, square 1:1 composition, full character centered, generous edge safety on every side, nothing touching or crossing the boundary, premium smooth 3D sticker finish, soft studio lighting, subtle realistic shading, uncluttered background.

### CuteEmoji_element-6.png:

Premium 3D sticker of the exact same cute round yellow emoji character, identical facial proportions and polished 3D material, expressing quiet sadness with large watery eyes, raised inner eyebrows, downward-curved mouth, slightly trembling lower lip, one visible tear rolling down the cheek, and a small downward head tilt conveying vulnerability, square 1:1 composition, character centered and entirely visible, generous empty margin around the face and tear, nothing touching or crossing the canvas edges, clean polished sticker outline, soft professional lighting, realistic subtle shading, premium commercial emoji rendering, minimal background.

### CuteEmoji_element-7.png:

Premium 3D sticker of the exact same round yellow emoji character with identical proportions, smooth polished material, and consistent facial design, expressing intense uncontrollable crying with eyes squeezed downward, dramatically overflowing tears streaming vertically from both eyes, raised distressed eyebrows, rounded open mouth, trembling cheeks, and a slight backward head tilt, with the tears remaining cleanly contained within the silhouette and fully inside the canvas, square 1:1 composition, centered full character, generous safety margin on every side, no cropping or edge contact, premium 3D sticker outline, soft studio lighting, subtle realistic shading, high-detail commercial emoji finish, uncluttered background.

### CuteEmoji_element-8.png:

Premium 3D sticker of the exact same cute round yellow emoji character, identical face proportions, eye shape, mouth construction, and polished yellow material, expressing disgust and sickness with crossed-looking dazed eyes, drooping eyebrows, a bluish-green irritated mouth area, tongue slightly sticking out, puffed cheeks, and a queasy tilted head, conveying nausea in a playful non-gross emoji style, square 1:1 composition, character centered and fully visible, generous empty margin around every element, nothing touching the canvas edges, clean professional sticker outline, soft studio lighting, subtle depth, premium polished 3D emoji rendering, minimal background.

### CuteEmoji_element-9.png:

Premium 3D sticker of the exact same round yellow emoji character with identical proportions, smooth polished material, expressive eyes, and consistent facial construction, giving a playful kiss with one eye closed in a mischievous wink, the other eye looking upward, puckered lips forming a small kiss shape, one tiny pink heart floating beside the mouth and fully inside the composition, head tilted slightly toward the heart, square 1:1 composition, full character centered with generous empty safety margins, no cropping or edge contact, clean premium sticker outline, soft professional lighting, subtle realistic shading, polished commercial 3D emoji quality, uncluttered background.

## simple but works very good

3x3 sticker pack sheet layout with 9 distinct die-cut stickers on a solid chroma key green background. Features an Emirati family in 3D iOS Pixar animation style: an Emirati mother wearing a black abaya, a young boy in a white kandura and ghutra, and a young girl in a traditional embroidered dress. The grid includes 9 unique poses and expressions: holding UAE flags, thumbs up, hugging with a red heart, waving, laughing, cheering with confetti, peace sign, drinking Arabic coffee, and posing proudly. Each variation has smooth 3D rendering, vibrant lighting, and a thick, clean white sticker outline.

---

# test inputs (prompt lab)

- “yellow teddy bear in Pixar 3D iOS style”
- “yellow teddy bear in toon cel shade with ios 3d genmoji style” (a style blend)
- the generic 4×4 yellow emoji faces above
- Background is always chroma key: green by default, blue when the character contains green.
