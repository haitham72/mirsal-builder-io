# Mirsal AI: the new look (redesign prompt)

A complete redesign of the original **Mirsal chat**, the messaging app this repo was built to serve. In the redesign, the Creator is part of the chat itself, not a separate tool. This file has three prompts:

- **A** is the full design brief, for a design LLM or a designer.
- **B** is a one-shot image prompt for a presentation board, in the format of `ref/Mirsal-Builder-upscaled.jpg`.
- **C** is the short spec that plate P7 of the Creator film draws in code (`README.md` §5).

Sources: the current app as it is today (`ref/ref-only.jpg`, right half: rail, chat list, a conversation over a doodle wallpaper, the composer with paperclip, lightning, emoji and mic); the logo (`ref/mirsal logo.jpeg`, a glossy blue orb); the builder's design system (`ref/Mirsal-Builder-upscaled.jpg`); the rolling cyan highlight (`ref/chat with cyan rolling highlight.jpg`, a cyan light along the edge of a panel); and `docs/design.md` (tokens, locked issue colours, rule 10).

Generating an image from prompt B is a paid call: show the price and wait for a go-ahead (rule 13).

---

## A. The design brief

> **Role.** You are a senior product designer redesigning **Mirsal**, a messaging app used in the UAE (Arabic and English, desktop and mobile). Redesign the whole chat experience around **Mirsal AI**, an assistant that lives inside the chat and creates **animated sticker packs** from one sentence. The result must feel like **one calm, premium messenger**, with no separate tool bolted onto it. Deliver desktop (1440×900) and mobile (390×844) screens, in light and dark mode, with LTR English and RTL Arabic variants of the key screens.
>
> **Keep (the identity people know).**
> - The **glossy blue orb** logo, the left **rail** (desktop) / bottom tab bar (mobile), the **chat list → conversation** layout, the soft **doodle wallpaper** behind messages, a pill-shaped **composer** at the bottom.
> - Colour: Primary Blue `#3B82F6` (every action: buttons, selection, focus), Primary Dark `#2563EB`, Slate text `#1E293B`, Soft gray `#64748B`, Background `#F7F8FA`, Surface `#FFFFFF`, Border `#E2E8F0`, Success `#10B981`, Warning `#F59E0B`, Danger `#EF4444`. **AI cyan `#22D3EE`** is used *only* for AI presence: the orb's glow, the rolling highlight and "thinking" states. It never colours a button.
> - Type: **Inter** (display 24 to 30, section 17 to 20, body 14 to 16, small 12 to 13, buttons 14 to 15). Arabic: a Naskh/Kufi sans that pairs with Inter (for example IBM Plex Sans Arabic). Icons: 2 px outline on a 24 px grid. Radius 16 px for cards, full pill for the composer and chips.
>
> **What changes.**
> 1. **Mirsal AI is a contact, pinned first.** It sits at the top of the chat list with the orb as its avatar and a verified tick. Its chat is the home of creation. It is the same conversation UI people already know, not a dashboard.
> 2. **The composer becomes the creation surface.** Next to emoji and mic sits an **orb button**. In any chat, pressing it opens the sticker panel with a **"Create with AI"** tab. Typing into Mirsal AI's chat works the same way. While the AI works, a **cyan highlight rolls around the composer's border** (a thin light travelling along the pill's edge). It is the only motion that means "AI is busy".
> 3. **One click, with the price first.** A request answers with **one plan card**: subject, style, a 3×3 or 2×2 grid chip, "Images" or "Full video", the **price of the whole run**, and **one primary button: "Create and send"** plus a quiet "Not yet". Nothing is spent before that click. A toggle "Approve everything for me" sits in the card's footer, off by default.
> 4. **Progress lives in the conversation.** After the click, the card becomes a **run card** with seven steps in a row: sheet, cut, check, approve, animate, pack, send. Each step shows a check, a spinner or a stop. The 3×3 sheet appears inside the card as it is cut, and the stickers come alive one by one when animated.
> 5. **No dead ends (hard rule).** A sticker the checks blocked is still **visible**. It is hatched, with an issue colour (orange: out of bounds; purple: bad green screen; yellow: bad loop; pink: look or motion; blue: a file or Telegram limit; red: dropped). Under it is **one plain sentence** saying why ("The wing crosses the edge of its square."), and **on the picture itself** a button **"Use it anyway"**, which becomes **"Take it back"** after the click. Each batch has one bulk control, "Use all anyway (N)". A bare word "Rejected" without a picture and a button is not allowed anywhere. These issue colours carry meaning: do not restyle them.
> 6. **It knows you, and it shows what it knows.** A **"What Mirsal knows about you"** sheet (from the AI contact's profile) lists name, place, likes and dislikes, each editable and deletable. Taste appears as an **offer, never a decision**: a soft chip on the plan card says *"You asked for cartoonish 2 times. Use it here?"*. A style the person types always wins.
> 7. **Batching.** "Three packs of fruit" answers with one **multi card**: three subject rows, each with its own small preview and plan, one **total** price and one button. Running batches show as a slim **tray above the composer** (`3 in flight`), each with a progress ring, and each opens its own card.
> 8. **The sticker panel, redesigned.** Tabs: **Recent · My packs · Trending · Create with AI**. Trending is a gallery of packs shared by the team, with like, comment and **"Use in my workflow"**. Packs show their stickers moving (animated thumbnails, reduced motion respected).
> 9. **People and credits.** Settings gains **Team**: who is approved, who is waiting (with Approve / Decline), each person's **credits** as a bar, and their usage. For a member, Settings shows their own credits only.
> 10. **Sending.** A finished pack sends as a real sticker message in any chat, with the animated sticker at 512 px, a timestamp and read ticks. Long-press (mobile) or right-click (desktop) offers "Make more like this", which opens the Creator with the sticker as reference.
>
> **Mood.** A bright, airy, premium messenger: calm white and blue surfaces, generous space, soft shadows, and glass only on the AI layers (the plan, run and multi cards get a faint frosted panel with a 1 px cyan inner edge). Motion is quick and purposeful: 150 to 250 ms eases, with springs only for stickers. The falcon mascot (glossy 3D, caramel feathers, gold beak) may appear in empty states and onboarding only, never in the chrome.
>
> **Avoid.** A second accent colour on buttons. Dark navy panels inside the light app. A dashboard look. Hiding the reason for a rejection behind a tooltip. Fake user data that looks like real people (use generic names and initials). Logos of other messengers.
>
> **Deliver.** (1) Desktop: the chat list with Mirsal AI pinned, plus Mirsal AI's conversation with a plan card. (2) Desktop: a run card mid-way, including one blocked sticker with "Use it anyway". (3) Desktop: the sticker panel open on Trending, inside a normal chat. (4) Mobile: the composer with the rolling highlight and the orb button. (5) Mobile: the "What Mirsal knows about you" sheet. (6) Mobile, RTL Arabic: a conversation with a sent animated sticker. (7) Dark mode for (1). (8) A design-system strip: colours, type, icons, the composer states (idle, typing, AI busy) and the card family (plan, run, multi, blocked sticker).

---

## B. Image prompt (concept board, 16:9, 4K)

For a model that writes text well, such as Nano Banana 2. Keep every visible word in quotes so the model spells it exactly. Expect to fix small garbled letters afterwards; text in a generated board is never exact.

```
A premium product design presentation board, 16:9, ultra clean white background with soft light-gray section cards, in the style of a Dribbble/Behance case-study board. Top-left header: a glossy blue orb logo and the words "Mirsal AI" in bold Inter, then a thin divider and "The new chat". Top-right small caps: "Create • Learn • Batch • Share".

Left section, "1  Mirsal AI on desktop": a large light-mode desktop messenger window. Left: a narrow icon rail with outline icons. Next: a chat list titled "Chats" with a search pill; the first row is pinned, a glowing blue orb avatar named "Mirsal AI" with a blue verified tick and the preview "Your pack is ready". Right: the open conversation over a very faint blue doodle wallpaper. A user bubble says "make me a falcon pack, cartoonish". Below it, a frosted-glass AI card with a thin cyan inner edge titled "Falcon pack · 3×3 · Full video", a small 3×3 preview grid of cute glossy 3D falcon stickers, the price "≈ 12 credits" in a monospace font, and one bright blue pill button "Create and send" plus a quiet text link "Not yet". At the bottom, a white pill composer "Type a message" with a paperclip, a blue orb button, an emoji face and a mic; a thin cyan light travels along the composer's edge.

Middle section, "2  One click, every step": a run card with seven small steps in a row, "sheet", "cut", "check", "approve", "animate", "pack", "send", the first five with blue checks, the sixth spinning. Inside, a 3×3 sheet of falcon stickers; one tile is hatched with an orange outline, the sentence "The wing crosses the edge of its square." under it, and a small blue button "Use it anyway" on the picture.

Right section, "3  Mobile": three phone mockups. Phone one: the composer with the orb button and the cyan rolling highlight, a tray above it reading "3 in flight" with three progress rings (cherry, banana, mango). Phone two: a bottom sheet "What Mirsal knows about you" with rows "Name", "City", "Likes" and an edit pencil on each, and a soft chip "You asked for cartoonish 2 times. Use it here?". Phone three: an Arabic right-to-left chat with a large animated falcon sticker sent as a message, with timestamp and blue read ticks.

Bottom strip, "4  Design system": colour swatches labelled "Primary Blue #3B82F6", "Primary Dark #2563EB", "AI Cyan #22D3EE", "Slate #1E293B", "Background #F7F8FA", "Success #10B981", "Warning #F59E0B", "Danger #EF4444"; a type ramp in Inter; a row of 2px outline icons; the composer in three states labelled "Idle", "Typing", "AI busy".

Bright high-key lighting, crisp vector UI, soft shadows, generous whitespace, pixel-perfect alignment, no real people's faces, no other brands' logos, no watermark.
```

Suggested run: 16:9, 4K (or 2K first to check the layout), one take. If the board comes out right, upscale and store it as `ref/Mirsal-AI-redesign.jpg` next to the builder board.

---

## C. What plate P7 draws in code

The film draws this with Canvas2D, Inter allowed (`README.md` §4.4), on a light plate (`paper: 1`), at about 1400×860 world px, centred:

1. **Window**: white, 16 px radius, a soft shadow, three window dots replaced by the orb and "Mirsal" at top-left.
2. **Rail**: 72 px, five outline icons (chats active in blue, contacts, stickers, star, settings).
3. **Chat list**: 360 px. The first row is "Mirsal AI" with the orb avatar and a blue tick. Four generic rows follow (initial avatars, grey previews).
4. **Conversation**: the faint doodle wallpaper (a few hairline icons at 6% alpha, tiled), one user bubble, then the plan card from P2 shrunk into place.
5. **Composer**: a pill, "Type a message", the paperclip, **the orb button**, emoji and mic. A cyan dash (`ember`, about 12% of the perimeter) travels around the pill's border once per 1.6 s while the AI works. Draw it as a polyline of the rounded-rect perimeter, sampled with `lengths` / `at` from `_vo.ts`.
6. **The payoff**: the sticker panel slides up from the orb button with the tabs "Recent · My packs · Trending · Create with AI". The P1 pack then drops into the conversation as a sent sticker: 512 px, a timestamp and two blue ticks, with `message_pop`.

Keep it legible at 1080p: nothing smaller than 14 world px at the plate's resting zoom.
