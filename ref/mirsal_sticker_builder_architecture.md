# Mirsal Sticker Builder — Architecture & Screen Design Specification

## 0. Purpose

Build a native-feeling Sticker Builder inside the existing **Mirsal** messaging application on **mobile and desktop**.

The design should feel like one coherent product, not a separate sticker-maker app.

Reference direction:
- Existing Mirsal mobile + desktop messaging UI.
- Modern WhatsApp-style sticker workflows.
- Premium white/light-gray surfaces.
- Mirsal teal/green accent.
- Rounded controls and cards.
- Transparent checkerboard canvas for sticker editing.
- UAE-oriented sticker examples are allowed, but the editor itself must remain generic.

Primary user journey:

```text
Mirsal Chat
  -> Sticker Picker
  -> Create
  -> Import Media
  -> Auto Cutout
  -> Edit Sticker
  -> Border / Text / Emoji / Drawing
  -> Save to Pack
  -> Send to Chat / Export
```

---

# 1. Product Principles

## 1.1 Integrated experience

The Sticker Builder is a feature of Mirsal. Reuse the Mirsal navigation shell, account identity, theme, spacing, icons, typography and interaction patterns.

## 1.2 Fast path first

The fastest path for a normal photo is:

```text
Create -> Photo -> Auto Cutout -> Optional Border -> Save -> Send
```

Do not force users through unnecessary configuration screens.

## 1.3 Progressive disclosure

Basic controls should be immediately visible. Advanced options should appear only when the relevant tool is selected.

## 1.4 Same editor model on mobile and desktop

Mobile and desktop have different layouts but must operate against the same logical sticker-project model.

```text
Mobile UI
     \
      -> Shared StickerProject State -> Export Pipeline
     /
Desktop UI
```

## 1.5 Visual hierarchy

Primary action = Mirsal green/teal.

Secondary actions = neutral white/light-gray controls.

Danger actions = restrained red only where destructive confirmation is required.

Canvas = visually dominant.

Tool panels = compact and contextual.

---

# 2. Global Design System

## 2.1 Colors

Use a restrained system:

```text
Primary      #10B981 / Mirsal green-teal range
Primary Dark #078A69
Text         #17212B
Muted Text   #64748B
Background   #F7F9FB
Surface      #FFFFFF
Border       #E2E8F0
Canvas       transparency checkerboard
Danger       muted red
Success      primary green
```

Do not flood screens with green. Green is for selected states, primary buttons, toggles and important affordances.

## 2.2 Geometry

Mobile:
- Screen width: 393px target design reference.
- Safe-area aware.
- 16–20px horizontal page margins.
- 12–18px corner radii.
- Bottom sheets with 20–28px top radius.
- Minimum touch target: ~44px.

Desktop:
- Target artboard: 1440 × 900 or 1600 × 1000.
- Existing Mirsal left navigation remains visible.
- Use 12–20px panel radii.
- Desktop editor should have a dense but breathable professional layout.

## 2.3 Typography

Prefer Inter/SF Pro-like system typography.

```text
Display / title: 24–30
Section:          17–20
Body:             14–16
Secondary:        12–13
Button:           14–15 medium/semibold
```

Arabic text must support RTL naturally.

## 2.4 Icons

Use simple outline icons with consistent stroke weight.

Required icon concepts:
- back
- close
- undo
- redo
- search
- create
- camera
- gallery
- video
- file
- text
- emoji
- sticker
- draw
- crop
- rotate
- border
- layers
- play/pause
- export
- send
- delete
- duplicate
- reorder

---

# 3. Application Architecture

## 3.1 Feature structure

```text
features/
  stickers/
    library/
    import/
    cutout/
    editor/
    animation/
    packs/
    export/
    shared/
```

## 3.2 Suggested routes

### Mobile

```text
/stickers
/stickers/create
/stickers/import
/stickers/cutout/:projectId
/stickers/edit/:projectId
/stickers/animate/:projectId
/stickers/pack/:packId
/stickers/export/:projectId
```

### Desktop

```text
/stickers
/stickers/create
/stickers/edit/:projectId
/stickers/animate/:projectId
/stickers/packs/:packId
```

The desktop routes can be rendered inside the Mirsal shell rather than replacing the entire application window.

---

# 4. Shared Domain Model

## 4.1 StickerProject

```ts
interface StickerProject {
  id: string;
  name: string;
  type: 'static' | 'animated';
  source: MediaSource;
  canvas: CanvasConfig;
  layers: StickerLayer[];
  crop?: CropConfig;
  border?: BorderConfig;
  animation?: AnimationConfig;
  packId?: string;
  createdAt: string;
  updatedAt: string;
}
```

## 4.2 MediaSource

```ts
interface MediaSource {
  type: 'image' | 'video' | 'gif' | 'file';
  uri: string;
  width: number;
  height: number;
  duration?: number;
  mimeType: string;
}
```

## 4.3 StickerLayer

```ts
interface StickerLayer {
  id: string;
  type: 'subject' | 'text' | 'emoji' | 'sticker' | 'drawing';
  visible: boolean;
  locked: boolean;
  zIndex: number;
  transform: {
    x: number;
    y: number;
    scale: number;
    rotation: number;
  };
  opacity: number;
  payload: unknown;
}
```

## 4.4 BorderConfig

```ts
interface BorderConfig {
  enabled: boolean;
  width: number;
  color: string;
  shadowEnabled: boolean;
  shadowBlur?: number;
}
```

## 4.5 AnimationConfig

```ts
interface AnimationConfig {
  fps: number;
  durationMs: number;
  startMs: number;
  endMs: number;
  loop: boolean;
  frames?: FrameData[];
}
```

---

# 5. Shared Editor State

```text
EditorState
├── project
├── selectedLayerId
├── activeTool
├── zoom
├── pan
├── history
│   ├── undo[]
│   └── redo[]
├── selection
├── clipboard
├── exportStatus
└── autosaveStatus
```

Every editing operation should be undoable where technically practical.

Examples:

```text
ADD_TEXT
MOVE_LAYER
SCALE_LAYER
ROTATE_LAYER
CROP
REMOVE_BACKGROUND
ERASE_REGION
RESTORE_REGION
SET_BORDER
ADD_EMOJI
ADD_STICKER
DRAW
TRIM_VIDEO
CHANGE_FPS
```

---

# 6. Screen Specifications

# Mobile Screens

---

## MOBILE_01 — Sticker Library

### Purpose

Entry point to the sticker system from a Mirsal conversation.

### Entry

User taps the sticker icon in the chat composer.

### Layout

```text
┌─────────────────────────┐
│ Sticker Library      ×  │
│ Search stickers...      │
│                         │
│ Recent My Stickers Packs │
│                         │
│ RECENT                  │
│ [ ][ ][ ][ ][ ]        │
│                         │
│ MY PACKS                │
│ ┌─────────────────────┐ │
│ │ UAE Moments     >   │ │
│ │ [ ][ ][ ][ ]        │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ Funny Faces      >  │ │
│ │ [ ][ ][ ][ ]        │ │
│ └─────────────────────┘ │
│                         │
│       + Create          │
└─────────────────────────┘
```

### Components

```text
StickerLibraryScreen
├── Header
│   ├── Title
│   └── Close
├── StickerSearch
├── StickerCategoryTabs
├── RecentStickerRow
├── PackList
│   └── StickerPackRow[]
└── CreateStickerButton
```

### Behaviour

- Search filters stickers and packs.
- Tabs switch datasets without leaving the sheet.
- Tapping sticker inserts it into the chat composer/send flow.
- Create opens MOBILE_02.
- Pack opens the pack detail view.

### State

```text
activeTab
searchQuery
recentStickers[]
myPacks[]
publicPacks[]
```

### Coding prompt

> Implement MOBILE_01 as the sticker picker embedded in the existing Mirsal mobile chat UI. Do not create a separate application shell. Reuse the current composer and Mirsal visual language. Build a searchable sticker library with Recent, My Stickers and Public Packs tabs. Render packs as compact horizontal cards with thumbnail previews. Add a prominent green/teal Create button anchored at the bottom. Ensure scrolling does not obscure the primary action. Keep the screen production-oriented, uncluttered and touch friendly.

### Image-generation prompt

```text
Create a high-fidelity Mirsal mobile Sticker Library screen inside a WhatsApp-like chat application. Show a Mirsal conversation partially visible behind the sticker panel. The sticker library has a search field, tabs Recent / My Stickers / Public Packs, recent sticker thumbnails, multiple sticker pack rows and a prominent green-teal + Create button. Use premium white/light-gray UI, subtle shadows, rounded cards, realistic iOS spacing, crisp readable interface, professional production app, no marketing poster composition, 393x852 mobile screen.
```

---

## MOBILE_02 — Media Picker

### Purpose

Give the user a simple choice of source media.

### Presentation

Bottom sheet over dimmed Mirsal chat.

### Options

```text
Take Photo
Photo Library
Video / GIF
Files
Text Sticker
My Projects
```

### Layout

```text
┌─────────────────────────┐
│      Add Media          │
│                         │
│ [Camera] [Gallery]      │
│ Take Photo Photo Library│
│                         │
│ [Video ] [Files]        │
│ Video/GIF Files         │
│                         │
│ [Text ] [Projects]      │
│ Text Sticker My Projects│
│                         │
│ Cancel                  │
└─────────────────────────┘
```

### Behaviour

- Photo -> image import -> MOBILE_03.
- Video/GIF -> animation import -> MOBILE_06.
- Text Sticker -> text-only editor.
- Projects -> resume saved project.

### Coding prompt

> Implement MOBILE_02 as a Mirsal bottom-sheet media picker. Preserve the underlying Mirsal chat context and dim it. Use six large touch-friendly tiles with icons and labels. Camera and gallery should be visually primary. Video/GIF must clearly indicate animation support. Files and Projects are secondary. The sheet should have a strong top title and a simple Cancel action. Avoid dense menus.

### Image-generation prompt

```text
High-fidelity Mirsal mobile Add Media bottom sheet over a softly dimmed Mirsal chat. Six rounded option tiles: Take Photo, Photo Library, Video / GIF, Files, Text Sticker, My Projects. Premium white card, Mirsal green-teal accent, simple outline icons, iOS-quality spacing, soft shadow, polished real application UI, 393x852.
```

---

## MOBILE_03 — Auto Cutout Editor

### Purpose

Automatically remove the photo background and provide manual correction.

### Layout

```text
┌─────────────────────────┐
│ ←   undo redo      Next │
├─────────────────────────┤
│                         │
│      checkerboard       │
│                         │
│       [subject]         │
│                         │
│                         │
├─────────────────────────┤
│ Auto Cutout Erase       │
│ Restore    Crop Rotate  │
└─────────────────────────┘
```

### Core interaction

- Auto cutout runs automatically after image import.
- Show processing state briefly.
- Subject becomes draggable/scalable.
- Erase and Restore use brush controls.
- Crop preserves transparent output.
- Next proceeds to MOBILE_04.

### Coding prompt

> Implement MOBILE_03 as a dedicated background-removal editing screen. The checkerboard canvas is the largest element. On import, automatically execute the background-removal pipeline and create a transparent subject layer. Provide undo/redo at the top and a green Next action. The bottom toolbar has Auto Cutout, Erase, Restore, Crop and Rotate. Selecting Erase or Restore must replace the bottom bar with a contextual brush panel including brush size and Done. Support pinch-to-scale and drag-to-position. The visual result must feel like a professional sticker editor, not an image editor overloaded with controls.

### Image-generation prompt

```text
High-fidelity Mirsal mobile automatic sticker cutout editor. Show a clean human subject isolated from its background and placed on a transparent checkerboard canvas. Top bar: Back, Undo, Redo, Next. Bottom toolbar: Auto Cutout, Erase, Restore, Crop, Rotate. The subject is centred with subtle transform affordances. Premium white interface, Mirsal teal-green accents, realistic iOS application, spacious controls, 393x852.
```

---

## MOBILE_04 — Sticker Editor

### Purpose

Main creative composition screen for static stickers.

### Layers

```text
Subject
Text
Emoji
Sticker
Drawing
```

### Toolbar

```text
Sticker | Text | Emoji | Draw | Border | Adjust
```

### Layout

```text
┌─────────────────────────┐
│ ←       undo redo   Save│
├─────────────────────────┤
│                         │
│      checkerboard       │
│     sticker canvas      │
│                         │
├─────────────────────────┤
│ Sticker Text Emoji      │
│ Draw    Border Adjust   │
└─────────────────────────┘
```

### Coding prompt

> Implement MOBILE_04 as the central static sticker editor. The checkerboard canvas should occupy approximately 60–70% of the screen. The selected object must show transform handles only when actively selected. Bottom tools are Sticker, Text, Emoji, Draw, Border and Adjust. Each tool opens a contextual bottom panel rather than navigating to unrelated screens. Text supports content, font, color, size, alignment, outline and shadow. Existing stickers can be imported as layers. All changes update the shared StickerProject state and participate in undo/redo. Save must autosave and continue to pack management.

### Image-generation prompt

```text
High-fidelity Mirsal mobile Sticker Editor. Transparent checkerboard canvas with a polished cutout character, large playful sticker typography and a small decorative emoji. Top bar with Back, Undo, Redo and Save. Bottom tool bar with Sticker, Text, Emoji, Draw, Border, Adjust. Premium Mirsal white and teal-green UI, rounded controls, realistic iOS application, professional spacing, 393x852.
```

---

## MOBILE_05 — Border Panel

### Purpose

Provide one-tap professional sticker outlining.

### Controls

```text
Border ON/OFF
Thickness
Color presets
Shadow ON/OFF
```

### Behaviour

The canvas preview updates immediately.

### Coding prompt

> Implement MOBILE_05 as a contextual Border tool panel inside the sticker editor. Preserve the canvas above. Use a toggle for enabling the border, a horizontal thickness slider, circular color presets and a shadow toggle. The default border should be clean white with a restrained thickness. Changes must update the selected layer in real time. Keep the UI simple enough to operate with one hand.

### Image-generation prompt

```text
High-fidelity Mirsal mobile sticker border editing panel. Transparent checkerboard canvas with an isolated character surrounded by a smooth white sticker outline. Bottom panel contains Border toggle, Thickness slider, circular border-color presets and Shadow toggle. White UI, Mirsal teal-green controls, polished iOS design, subtle shadows, realistic production application, 393x852.
```

---

## MOBILE_06 — Animated Sticker Editor

### Purpose

Create animated stickers from videos/GIFs.

### Layout

```text
┌─────────────────────────┐
│ ←                    Save│
├─────────────────────────┤
│                         │
│   checkerboard preview  │
│                         │
├─────────────────────────┤
│ 00:00 [====] 00:02      │
│ ◀  ▶  Loop   FPS        │
├─────────────────────────┤
│ Sticker Text Emoji ...  │
└─────────────────────────┘
```

### Coding prompt

> Implement MOBILE_06 for video/GIF stickers. Use a large checkerboard preview and a compact timeline directly underneath it. Timeline must provide trim start/end handles, playback, current time, total duration and loop. Show a small FPS/duration control. Reuse static-editor tools where technically possible. The user should understand immediately that this is an animated sticker. Keep the timeline touch friendly and avoid desktop-style dense editing controls.

### Image-generation prompt

```text
High-fidelity Mirsal mobile animated sticker editor. Transparent checkerboard canvas with a cutout character preview. Beneath the canvas is a clean horizontal video timeline with thumbnail frames, start/end trim handles, play button, loop toggle, FPS and duration. Top bar has Back and Save. Mirsal teal-green accent, premium white interface, polished production app, 393x852.
```

---

## MOBILE_07 — Sticker Pack Manager

### Purpose

Save, organize and export stickers.

### Layout

```text
┌─────────────────────────┐
│ ← My Pack            ⋮  │
│                         │
│ [pack cover]            │
│ UAE Moments             │
│ 24 stickers             │
│                         │
│ [ ][ ][ ][ ]            │
│ [ ][ ][ ][ ]            │
│ [ ][ ][ ][ ]            │
│                         │
│ + Add Sticker   Reorder │
│                         │
│ Save / Export           │
└─────────────────────────┘
```

### Coding prompt

> Implement MOBILE_07 as the sticker-pack management screen. Show pack cover, name, sticker count and a grid of stickers. The user can add stickers, reorder them with drag-and-drop, remove individual stickers and rename the pack. Provide one primary Save action and a secondary Export to WhatsApp action. Make the pack feel like a reusable Mirsal asset collection.

### Image-generation prompt

```text
High-fidelity Mirsal mobile sticker pack manager. Show a sticker pack called UAE Moments, pack cover, sticker count, neat sticker grid, Add Sticker and Reorder actions, and a large Save / Export to WhatsApp action. Premium white interface, Mirsal teal-green accent, rounded sections, polished iOS application, 393x852.
```

---

# Desktop Screens

---

## DESKTOP_01 — Sticker Library

### Purpose

Desktop entry point using the existing Mirsal application shell.

### Layout

```text
┌────┬──────────────┬──────────────────────────────────────────┐
│Nav │ Chat List    │ Sticker Library                        │
│    │              │ Search                                  │
│    │              │ Recent / My Stickers / Public Packs    │
│    │              │                                         │
│    │              │ Pack rows / sticker grid               │
│    │              │                                         │
│    │              │                         + Create        │
└────┴──────────────┴──────────────────────────────────────────┘
```

### Coding prompt

> Implement DESKTOP_01 inside the existing Mirsal desktop shell. Keep the far-left navigation rail and chat list visible. Replace only the main content region with Sticker Library. Include a search bar, category tabs, Recent section, My Packs and Public Packs. Use wider horizontal pack cards and larger sticker previews than mobile. Add Create as the dominant primary action in the main content area. Do not redesign Mirsal's entire desktop application; extend it.

### Image-generation prompt

```text
High-fidelity Mirsal desktop Sticker Library integrated into the existing Mirsal messaging app. Show the Mirsal left navigation rail, chat list column and large main Sticker Library workspace. Include search, Recent, My Stickers, Public Packs, sticker grids and pack rows, plus a green-teal Create Sticker button. Premium white/light-gray UI, subtle shadows, realistic Windows desktop software, 1440x900.
```

---

## DESKTOP_02 — Import Workspace

### Purpose

Desktop media ingestion with drag-and-drop.

### Layout

```text
Main workspace
┌─────────────────────────────────────────────┐
│ Create Sticker                              │
│                                             │
│        Drag & Drop Photo / Video / GIF      │
│                                             │
│ [ Photo ] [ Video/GIF ] [ Files ]          │
│                                             │
│ [ Text Sticker ] [ My Projects ]            │
└─────────────────────────────────────────────┘
```

### Coding prompt

> Implement DESKTOP_02 as an integrated Mirsal sticker import workspace. The central drop zone must accept image, video, GIF and supported file formats. Provide explicit buttons underneath so users do not need drag-and-drop. Recent projects should be accessible without changing context. After import, route image projects to the cutout/editor workflow and videos/GIFs to animation mode.

### Image-generation prompt

```text
High-fidelity Mirsal desktop Create Sticker workspace inside the Mirsal application. Large central drag-and-drop area for Photo, Video, GIF or File. Secondary buttons for Text Sticker and My Projects. Existing Mirsal navigation and chat list remain visible around the workspace. Premium modern desktop UI, teal-green Mirsal accent, clean whitespace, realistic Windows app, 1440x900.
```

---

## DESKTOP_03 — Main Sticker Editor

### Purpose

Full professional creative editor.

### Three-panel layout

```text
┌────────────┬───────────────────────────────┬───────────────┐
│ Tools/Layers│           Canvas              │ Properties    │
│             │                               │               │
│ Sticker     │      checkerboard canvas      │ Transform     │
│ Text        │          [sticker]            │ Crop          │
│ Emoji       │                               │ Text          │
│ Draw        │                               │ Border        │
│ Border      │                               │ Shadow        │
│ Adjust      │                               │               │
├─────────────┴───────────────────────────────┴───────────────┤
│ Layers / timeline / contextual controls                        │
└───────────────────────────────────────────────────────────────┘
```

### Left panel

Tools + layers.

### Centre

Checkerboard canvas.

### Right panel

Properties inspector.

### Top bar

```text
Back | Undo | Redo | Zoom | Preview | Save
```

### Coding prompt

> Implement DESKTOP_03 as the primary Mirsal Sticker Builder desktop editor. Preserve the existing Mirsal application shell while rendering a professional editor in the main workspace. Use a three-zone structure: left tools/layers, centre canvas, right properties inspector. The canvas must support zoom and pan and should remain the visual focus. The left tool stack contains Sticker, Text, Emoji, Draw, Border and Adjust. Layers should display object type, visibility and lock state. The right inspector changes according to selection and must support transform, crop, text styling and border settings. Add Undo/Redo and Save to the top toolbar. Make all editor actions operate on the shared StickerProject state.
```

### Image-generation prompt

```text
High-fidelity Mirsal desktop Sticker Builder editor integrated into Mirsal. Three-panel professional layout: left tools and layers, large central transparent checkerboard canvas with a polished cutout sticker composition, right properties inspector. Top toolbar with Back, Undo, Redo, Zoom, Preview, Save. Bottom contextual layer/timeline area. Mirsal teal-green accents, premium white/light-gray surfaces, rounded panels, realistic Windows production software, 1440x900.
```

---

## DESKTOP_04 — Animated Sticker Editor

### Purpose

Desktop timeline-based animation editing.

### Layout

```text
┌────────────┬───────────────────────────────┬───────────────┐
│ Animation  │       Preview Canvas           │ Properties    │
│ frames     │                               │ FPS           │
│ settings   │        checkerboard           │ duration      │
│            │          sticker              │ loop          │
├─────────────────────────────────────────────────────────────┤
│ Timeline: thumbnails | trim | playhead | add frame | play  │
└─────────────────────────────────────────────────────────────┘
```

### Coding prompt

> Implement DESKTOP_04 as a dedicated animated-sticker editor while retaining the same Mirsal shell and visual system. Use the central canvas for preview, the right inspector for FPS, canvas size, duration, loop and export settings, and a wide bottom timeline for frame/segment manipulation. The user must be able to trim, preview, reorder where applicable, and save the animation project. Timeline interactions should be precise with mouse input and keyboard shortcuts.

### Image-generation prompt

```text
High-fidelity Mirsal desktop Animated Sticker Editor. Existing Mirsal application shell remains visible. Centre contains large transparent checkerboard animation preview. Bottom contains professional timeline with frame thumbnails, playhead, trim handles, playback controls, duration and FPS. Right inspector contains loop, canvas and export settings. Mirsal teal-green accent, premium clean desktop UI, realistic Windows creative software, 1440x900.
```

---

## DESKTOP_05 — Sticker Pack Manager

### Purpose

Manage complete sticker collections from desktop.

### Features

```text
Pack information
Sticker grid
Drag reorder
Add sticker
Delete sticker
Rename pack
Change cover
Preview
Export
```

### Coding prompt

> Implement DESKTOP_05 as a sticker-pack management workspace inside Mirsal. Show pack metadata in a compact top section and a large responsive sticker grid below it. Enable drag-and-drop ordering. Each sticker has hover actions for preview and delete. Include Add Sticker, Rename Pack, Choose Cover, Preview Pack, Save and Export. Preserve Mirsal visual identity and ensure the pack manager can handle dozens of stickers without becoming visually cluttered.

### Image-generation prompt

```text
High-fidelity Mirsal desktop Sticker Pack Manager integrated into Mirsal. Show pack cover, name UAE Moments, sticker count, large responsive sticker grid, drag-and-drop ordering affordances, Add Sticker, Rename, Choose Cover, Preview and Export actions. Existing Mirsal left navigation and chat list remain visible. Premium white/light-gray desktop design, teal-green accent, rounded panels, realistic Windows application, 1440x900.
```

---

## DESKTOP_06 — Final Export / Send

### Purpose

Confirm the completed sticker and select its destination.

### Layout

```text
┌──────────────────────┬─────────────────────────┐
│                      │ Sticker                 │
│   sticker preview    │ Name                    │
│   checkerboard       │ Pack                    │
│                      │ Static / Animated       │
│                      │                         │
│                      │ [Save to Mirsal]        │
│                      │ [Send to Chat]          │
│                      │ [Export to WhatsApp]    │
└──────────────────────┴─────────────────────────┘
```

### Coding prompt

> Implement DESKTOP_06 as the final sticker confirmation and export workspace. Display the finished sticker prominently over transparency. The right panel shows sticker name, pack, type and output status. Primary action is Save to Mirsal. Secondary actions are Send to Chat and Export to WhatsApp. For animated stickers, show duration and format metadata. After saving, provide immediate access to Send to Chat rather than forcing the user back through the library.

### Image-generation prompt

```text
High-fidelity Mirsal desktop final sticker export screen. Large finished sticker preview on transparent checkerboard canvas at left. Right confirmation panel with sticker name, sticker pack, Static or Animated type and three clear actions: Save to Mirsal, Send to Chat, Export to WhatsApp. Existing Mirsal shell visible. Premium white UI, Mirsal teal-green accent, realistic Windows production app, 1440x900.
```

---

# 7. Contextual Tool Architecture

The editor should not create a separate route for every tool.

Use one editor route with contextual panels.

```text
/editor/:projectId

activeTool:
  select
  sticker
  text
  emoji
  draw
  border
  crop
  adjust
  erase
  restore
```

Example:

```text
activeTool = 'border'
```

renders:

```text
Canvas
+
BorderPanel
```

rather than:

```text
BorderScreen
```

This reduces navigation complexity and preserves the mental model of a single editor.

---

# 8. Editing Pipeline

## Static sticker

```text
Input Image
   ↓
Decode
   ↓
Auto Background Removal
   ↓
Segmentation Mask
   ↓
Mask Cleanup
   ↓
Transparent RGBA Subject
   ↓
Editor Composition
   ↓
Border / Shadow
   ↓
Resize / Normalize
   ↓
Sticker Export
   ↓
Pack Storage
   ↓
Mirsal Message Attachment
```

## Animated sticker

```text
Video / GIF
   ↓
Decode
   ↓
Trim
   ↓
Frame Sampling
   ↓
Background Removal
   ↓
Mask Cleanup
   ↓
Per-frame Composition
   ↓
Border / Effects
   ↓
Frame Optimization
   ↓
Animated Sticker Encoding
   ↓
Pack Storage
   ↓
Mirsal Message Attachment
```

---

# 9. Export Layer

Create a dedicated export abstraction so the UI does not know codec details.

```ts
interface StickerExporter {
  exportStatic(project: StickerProject): Promise<ExportResult>;
  exportAnimated(project: StickerProject): Promise<ExportResult>;
}
```

Example:

```text
ExportResult
├── fileUri
├── mimeType
├── width
├── height
├── duration
├── sizeBytes
└── warnings[]
```

Recommended architecture:

```text
Editor
  ↓
Export Service
  ├── Static Encoder
  ├── Animated Encoder
  ├── Optimizer
  └── Validation
```

The exact WhatsApp/Mirsal output limits should be centralized in configuration rather than hard-coded throughout the UI.

---

# 10. Project Persistence

Autosave the editor project.

```text
Create project
    ↓
local/project cache
    ↓
autosave after edits
    ↓
optional cloud sync
```

Project states:

```text
DRAFT
PROCESSING
READY
EXPORTING
EXPORTED
ERROR
```

A failed export must not destroy the editable project.

---

# 11. Undo / Redo Architecture

Use command-style history rather than snapshotting huge media buffers whenever possible.

```ts
interface EditorCommand {
  type: string;
  execute(): void;
  undo(): void;
}
```

Examples:

```text
AddTextCommand
MoveLayerCommand
ResizeLayerCommand
RotateLayerCommand
SetBorderCommand
AddStickerCommand
CropCommand
TrimAnimationCommand
```

Store heavyweight generated masks/media outside the command history and store references to them.

---

# 12. Responsive Desktop Rules

Desktop widths:

```text
< 1200px
  compact inspector

1200–1440px
  standard three-panel editor

> 1440px
  wider canvas + inspector
```

Do not simply stretch the mobile UI onto desktop.

Desktop should reveal more information simultaneously:

```text
Mobile:
  one contextual panel at a time

Desktop:
  tools + canvas + properties + timeline simultaneously
```

---

# 13. Accessibility / UX Requirements

- Every icon button needs an accessible label.
- Do not rely on color alone for selected states.
- Keyboard navigation on desktop.
- Escape closes modal panels.
- Enter activates primary actions where appropriate.
- Undo = Ctrl/Cmd + Z.
- Redo = Ctrl/Cmd + Shift + Z.
- Delete removes selected layer after selection is confirmed.
- Arabic/RTL layouts must mirror directional controls correctly.
- Maintain readable contrast.

---

# 14. Error States

Required:

```text
Unsupported file
Failed background removal
Video too long
Invalid dimensions
Export failed
Storage unavailable
Network unavailable
Pack save failed
```

Error UI should preserve the project and give the user a recovery action.

Example:

```text
We couldn't process this video.
Your project is still saved.

[Try Again]   [Back to Editor]
```

---

# 15. Loading States

Do not show empty screens during AI processing.

Auto-cutout loading:

```text
Preparing your sticker...
Removing background
[progress / subtle animation]
```

Export loading:

```text
Creating sticker...
Optimizing...
Exporting...
```

The original project remains accessible.

---

# 16. AI Extension Layer

The MVP should work without generative AI.

Later AI modules can plug into the same editor:

```text
AI Services
├── Background Removal
├── Image Enhancement
├── Smart Crop
├── AI Sticker Generation
├── Text Styling
└── Animation Assistance
```

Use an interface instead of wiring UI directly to a specific provider:

```ts
interface StickerAIProvider {
  removeBackground(input: MediaSource): Promise<MaskResult>;
  enhanceImage(input: MediaSource): Promise<MediaSource>;
  generateSticker(prompt: string): Promise<MediaSource>;
}
```

This keeps the UI provider-independent.

---

# 17. Recommended MVP Build Order

## Sprint 1

```text
Mirsal integration
Sticker Library
Media Picker
Project state
Basic editor canvas
```

## Sprint 2

```text
Auto Cutout
Move / Scale / Rotate
Crop
Border
Undo / Redo
Save project
```

## Sprint 3

```text
Text
Emoji
Sticker layers
Pack manager
Send to Mirsal chat
```

## Sprint 4

```text
Video/GIF import
Timeline
Trim
Animated export
WhatsApp export
```

## Sprint 5

```text
AI enhancement
AI generation
Advanced effects
Batch operations
```

---

# 18. Master Coding Prompt for the IDE

Use this as the global instruction before implementing individual screens:

```text
You are implementing the Mirsal Sticker Builder as a native feature of an existing Mirsal messaging application.

Do NOT build a separate generic sticker-maker application.
Do NOT redesign the existing Mirsal messaging shell.
Reuse the existing Mirsal navigation, chat list, composer, account identity and overall visual language.

The Sticker Builder must work on mobile and desktop.
Mobile uses a focused, bottom-sheet/contextual-panel workflow.
Desktop uses a persistent multi-panel editor.

Use a shared StickerProject domain model for both platforms.
The project supports:
- image source
- video/GIF source
- transparent cutout
- layers
- text
- emoji
- imported stickers
- drawing
- crop
- transforms
- border
- shadow
- animation
- sticker pack metadata
- export state

Primary mobile flow:
Sticker Library -> Create -> Media Picker -> Auto Cutout -> Sticker Editor -> Border/Tools -> Pack Manager -> Send/Export.

Primary desktop flow:
Sticker Library -> Create Workspace -> Main Editor -> Animated Editor when applicable -> Pack Manager -> Export/Send.

Editor principles:
- checkerboard transparency canvas
- green/teal Mirsal primary actions
- white/light-gray surfaces
- rounded cards and panels
- restrained shadows
- professional messaging-product appearance
- no decorative marketing layouts
- no excessive gradients
- no tiny unreadable labels
- strong touch targets on mobile
- precise mouse/keyboard interaction on desktop

Use one editor route with contextual tools rather than creating a separate route for every editing operation.

All edits must modify the shared project state.
Undo/redo must be available for major editing actions.
Autosave the project without blocking the editor.
Do not destroy the source project when export fails.

For every screen:
1. Match the Mirsal shell.
2. Keep the primary action visually obvious.
3. Use responsive layout rules instead of fixed positioning.
4. Separate UI state from media-processing services.
5. Keep export implementation behind an exporter abstraction.
6. Keep AI functionality behind an AI-provider abstraction.
7. Ensure Arabic/RTL support.
8. Build reusable components instead of duplicated platform-specific logic where practical.

The visual quality target is a polished production application comparable to a modern messaging product, not a prototype dashboard.
```

---

# 19. Screen Naming Convention

Use consistent names in design files and code:

```text
mobile_prompt_01 = MOBILE_01 Sticker Library
mobile_prompt_02 = MOBILE_02 Media Picker
mobile_prompt_03 = MOBILE_03 Auto Cutout Editor
mobile_prompt_04 = MOBILE_04 Sticker Editor
mobile_prompt_05 = MOBILE_05 Border Panel
mobile_prompt_06 = MOBILE_06 Animated Sticker Editor
mobile_prompt_07 = MOBILE_07 Sticker Pack Manager

desktop_prompt_01 = DESKTOP_01 Sticker Library
desktop_prompt_02 = DESKTOP_02 Import Workspace
desktop_prompt_03 = DESKTOP_03 Main Sticker Editor
desktop_prompt_04 = DESKTOP_04 Animated Sticker Editor
desktop_prompt_05 = DESKTOP_05 Sticker Pack Manager
desktop_prompt_06 = DESKTOP_06 Final Export / Send
```

---

# 20. Final Product Structure

```text
MIRSAL
│
├── Chats
│   └── Composer
│       └── Sticker Button
│           └── Sticker Library
│
└── Sticker Builder
    │
    ├── Library
    ├── Create / Import
    ├── Static Editor
    │   ├── Cutout
    │   ├── Crop
    │   ├── Text
    │   ├── Emoji
    │   ├── Stickers
    │   ├── Draw
    │   ├── Border
    │   └── Adjust
    │
    ├── Animated Editor
    │   ├── Timeline
    │   ├── Trim
    │   ├── FPS
    │   ├── Loop
    │   └── Preview
    │
    ├── Pack Manager
    │   ├── Add
    │   ├── Reorder
    │   ├── Remove
    │   ├── Cover
    │   └── Rename
    │
    └── Export
        ├── Save to Mirsal
        ├── Send to Chat
        └── Export to WhatsApp
```

## Definition of Done

A user must be able to open the sticker panel from a Mirsal chat, create a sticker from a photo, automatically remove its background, edit it, add a border, save it into a sticker pack, and send the resulting sticker back into the Mirsal conversation without leaving the Mirsal product experience.

# 21. VERSION 2 — Video / GIF Creation Extension

> This section is an integrated extension of the existing Sticker Builder architecture. It is the source of truth for the new video workflow and supersedes older descriptions where they conflict.

## 21.1 Updated product journey

The Sticker Builder now supports a complete animated-media path in addition to the original photo path.

```text
Mirsal Chat
  -> Sticker Picker
  -> Create
  -> Media Picker
      ├── Photo
      │    -> Auto Cutout
      │    -> Sticker Editor
      │    -> Border / Text / Emoji / Sticker / Draw / Adjust
      │    -> Save to Pack
      │    -> Send / Export
      │
      └── Video / GIF
           -> Video / GIF Prepare
           -> Scrollable video controls
           -> Trim / Preview
           -> GIF conversion option
           -> Optional video background removal
           -> Animated Sticker Editor
           -> Text / Emoji / Sticker / Draw / Border / Adjust
           -> Save to Pack
           -> Send / Export
```

The video workflow must remain inside Mirsal and use the same shared project model as static stickers.

## 21.2 Video / GIF Prepare screen

Introduce a dedicated preparation state before the animated editor. This is not a separate product or disconnected editor; it is a contextual stage of the same StickerProject.

### Mobile

```text
┌─────────────────────────┐
│ ←  Video / GIF      Next│
├─────────────────────────┤
│                         │
│     Video preview       │
│                         │
├─────────────────────────┤
│ Timeline / trim         │
│ 00:00  [======]  00:04  │
│                         │
│ GIF                     │
│ [ Convert to GIF     ON]│
│                         │
│ Background              │
│ [ Remove background   ]  │
│ Optional / AI           │
│                         │
│ Text                    │
│ [ Add text            ]  │
│                         │
│ More editing tools      │
│ Sticker  Emoji  Draw    │
│ Border   Crop   Adjust  │
└─────────────────────────┘
```

The lower controls are vertically scrollable on mobile. The preview and timeline remain prominent while secondary options can scroll beneath them.

### Desktop

```text
┌────────────┬───────────────────────────────┬──────────────────┐
│ Tools      │       Video preview           │ Properties       │
│            │      checkerboard / media     │                  │
│ Trim       │                               │ Format           │
│ GIF        │                               │ Duration         │
│ Background │                               │ FPS              │
│ Text       │                               │ Canvas           │
│ Sticker    │                               │ Background       │
│ Emoji      │                               │ Text             │
│ Draw       │                               │ Border           │
├────────────┴───────────────────────────────┴──────────────────┤
│ Timeline / thumbnails / trim handles / playhead / playback   │
└───────────────────────────────────────────────────────────────┘
```

Desktop should expose the relevant controls simultaneously rather than reproducing the mobile scrolling interaction.

## 21.3 New animated-media capabilities

### A. Video upload

Video is a first-class media source. Import should preserve the original source reference and create an editable animated project.

Required capabilities:

```text
Import video
Preview
Trim
Seek
Play / pause
Frame timeline
Choose output mode
```

### B. GIF conversion

GIF conversion is a processing option within the animated workflow, not a separate application or unrelated screen.

```text
Video
  -> Trim / Prepare
  -> GIF conversion (optional)
  -> Animated composition
  -> Export
```

The same StickerProject must remain editable regardless of whether the source began as a video or GIF.

### C. Potential video background remover

Video background removal must be architected as an optional provider-backed capability because it may require a processing service and may not be available in every build.

```text
Video / GIF
   -> Frame decode
   -> Background-removal provider
   -> Per-frame mask sequence
   -> Mask cleanup / compositing
   -> Transparent animated subject
```

Use a capability flag and provider abstraction. The UI must gracefully hide or disable the feature when unavailable.

Suggested states:

```text
UNAVAILABLE
READY
PROCESSING
READY_WITH_MASK
ERROR
```

A failed background-removal operation must never destroy the original video project.

### D. Text over video

Text is a normal compositing layer and must work over animated media.

Support:

```text
Text content
Font
Size
Color
Alignment
Outline
Shadow
Position
Scale
Rotation
Opacity
Timing / visibility range
```

The timing range allows text to appear for part or all of the animation. The implementation should use the same logical text layer model as static stickers.

## 21.4 Shared domain model extensions

Extend `StickerProject` rather than creating a separate `VideoStickerProject`.

```ts
interface StickerProject {
  id: string;
  name: string;
  type: 'static' | 'animated';
  source: MediaSource;
  canvas: CanvasConfig;
  layers: StickerLayer[];
  crop?: CropConfig;
  border?: BorderConfig;
  animation?: AnimationConfig;
  video?: VideoEditConfig;
  gif?: GifConfig;
  videoBackgroundRemoval?: VideoBackgroundRemovalConfig;
  packId?: string;
  createdAt: string;
  updatedAt: string;
}
```

Add:

```ts
interface VideoEditConfig {
  trimStartMs: number;
  trimEndMs: number;
  currentTimeMs: number;
  fps?: number;
}

interface GifConfig {
  enabled: boolean;
  loop: boolean;
  quality?: number;
}

interface VideoBackgroundRemovalConfig {
  enabled: boolean;
  status: 'UNAVAILABLE' | 'READY' | 'PROCESSING' | 'READY_WITH_MASK' | 'ERROR';
  provider?: string;
  maskReference?: string;
}
```

Do not duplicate text, sticker, emoji, or drawing layer structures for video. They remain `StickerLayer` objects.

## 21.5 StickerLayer timing extension

Animated projects need optional timing metadata on compositing layers.

```ts
interface StickerLayer {
  id: string;
  type: 'subject' | 'text' | 'emoji' | 'sticker' | 'drawing';
  visible: boolean;
  locked: boolean;
  zIndex: number;
  transform: {
    x: number;
    y: number;
    scale: number;
    rotation: number;
  };
  opacity: number;
  timing?: {
    startMs: number;
    endMs: number;
  };
  payload: unknown;
}
```

For static projects, `timing` is omitted.

## 21.6 Shared editor state extensions

Extend the existing `EditorState`:

```text
EditorState
├── project
├── selectedLayerId
├── activeTool
├── mediaMode: 'static' | 'video' | 'gif'
├── zoom
├── pan
├── timeline
│   ├── currentTimeMs
│   ├── trimStartMs
│   └── trimEndMs
├── history
│   ├── undo[]
│   └── redo[]
├── selection
├── clipboard
├── processing
│   ├── backgroundRemoval
│   └── gifConversion
├── capabilities
│   ├── videoBackgroundRemoval
│   └── animatedExport
├── exportStatus
└── autosaveStatus
```

All video operations must participate in the same undo/redo architecture where practical:

```text
TRIM_VIDEO
SET_VIDEO_FPS
CONVERT_TO_GIF
REMOVE_VIDEO_BACKGROUND
ADD_TEXT
MOVE_LAYER
SET_LAYER_TIMING
SET_BORDER
ADD_STICKER
ADD_EMOJI
DRAW
```

## 21.7 Updated feature structure

Extend the existing feature tree:

```text
features/
  stickers/
    library/
    import/
    cutout/
    editor/
    video/
      import/
      prepare/
      timeline/
      gif/
      background-removal/
      composition/
    animation/
    packs/
    export/
    shared/
```

Keep video-specific processing services separate from UI components.

## 21.8 Updated route strategy

Do not create a route for every video tool.

Recommended routes remain:

```text
/stickers
/stickers/create
/stickers/edit/:projectId
/stickers/animate/:projectId
/stickers/packs/:packId
```

For animated projects, `/stickers/edit/:projectId` may enter animated mode, while `/stickers/animate/:projectId` can provide the dedicated timeline-focused experience.

The following must remain contextual tools or panels, not separate routes:

```text
GIF conversion
Video background removal
Text
Emoji
Sticker
Draw
Border
Crop
Adjust
```

## 21.9 Updated contextual tool architecture

The editor now supports:

```text
activeTool:
  select
  sticker
  text
  emoji
  draw
  border
  crop
  adjust
  erase
  restore
  trim
  gif
  videoBackgroundRemoval
```

Example:

```text
activeTool = 'videoBackgroundRemoval'
```

renders:

```text
Canvas / Video Preview
+
BackgroundRemovalPanel
+
Processing State
```

Example:

```text
activeTool = 'text'
mediaMode = 'video'
```

renders:

```text
Animated Canvas
+
TextPanel
+
Layer Timing Controls
```

## 21.10 Updated editing pipeline

### Static sticker

```text
Input Image
   ↓
Decode
   ↓
Auto Background Removal
   ↓
Segmentation Mask
   ↓
Mask Cleanup
   ↓
Transparent RGBA Subject
   ↓
Editor Composition
   ↓
Text / Emoji / Sticker / Draw
   ↓
Border / Shadow
   ↓
Resize / Normalize
   ↓
Static Sticker Export
   ↓
Pack Storage
   ↓
Mirsal Message Attachment
```

### Animated sticker from video

```text
Video
   ↓
Decode
   ↓
Preview
   ↓
Trim
   ↓
Frame Sampling
   ↓
Optional Video Background Removal
   ↓
Mask Cleanup
   ↓
Animated Subject / Original Video
   ↓
Composition Layers
   ├── Text
   ├── Emoji
   ├── Sticker
   ├── Drawing
   └── Border / Shadow
   ↓
Frame Optimization
   ↓
Animated Sticker Encoding
   ↓
Pack Storage
   ↓
Mirsal Message Attachment
```

### Optional video-to-GIF path

```text
Video
   ↓
Decode
   ↓
Trim
   ↓
Frame Sampling
   ↓
GIF Encoding
   ↓
Optional Background Removal
   ↓
Composition
   ↓
Animated Sticker Encoding / GIF Export
```

The exact output limits and encoding constraints remain centralized in configuration.

## 21.11 Processing service abstractions

Add provider-independent services beside the existing exporter and AI abstractions.

```ts
interface VideoProcessor {
  decode(source: MediaSource): Promise<VideoAsset>;
  trim(source: MediaSource, startMs: number, endMs: number): Promise<MediaSource>;
  sampleFrames(source: MediaSource, config: FrameSamplingConfig): Promise<FrameData[]>;
}

interface GifConverter {
  convert(source: MediaSource, config: GifConfig): Promise<MediaSource>;
}

interface VideoBackgroundRemover {
  isAvailable(): Promise<boolean>;
  removeBackground(source: MediaSource): Promise<VideoMaskResult>;
}
```

The UI must communicate with these abstractions rather than a specific provider.

## 21.12 Updated AI extension layer

Extend the existing AI provider abstraction:

```ts
interface StickerAIProvider {
  removeBackground(input: MediaSource): Promise<MaskResult>;
  removeVideoBackground?(input: MediaSource): Promise<VideoMaskResult>;
  enhanceImage(input: MediaSource): Promise<MediaSource>;
  generateSticker(prompt: string): Promise<MediaSource>;
}
```

Video background removal is optional and capability-gated.

The MVP can ship without it while retaining the same UI and project-state contract.

## 21.13 Mobile UX rules for video

The mobile video workflow must use progressive disclosure and vertical scrolling because it has more controls than the static path.

Priority order:

```text
1. Preview
2. Timeline / trim
3. GIF conversion
4. Background removal
5. Text
6. Sticker / Emoji / Draw
7. Border / Adjust
8. Advanced settings
```

The preview should not disappear while the user explores secondary controls. Scrolling should occur in the control area, not through the whole application shell.

Do not put every advanced video setting on screen at once.

## 21.14 Desktop UX rules for video

Desktop should expose the same capabilities simultaneously where space permits:

```text
Left: tools + layers
Centre: animated preview
Right: contextual properties
Bottom: timeline
```

The right inspector should switch between:

```text
Video properties
GIF properties
Background removal status
Text properties
Layer timing
Border properties
Export properties
```

## 21.15 Updated persistence requirements

Autosave must capture video-edit state as well as static state:

```text
source reference
trim range
GIF mode
background-removal state
layer stack
layer timing
canvas settings
border settings
animation settings
pack assignment
```

Heavy video frames, generated masks and intermediate media should live outside command history and be referenced by stable IDs or URIs.

## 21.16 Updated export abstraction

Keep codec and format details behind the exporter:

```ts
interface StickerExporter {
  exportStatic(project: StickerProject): Promise<ExportResult>;
  exportAnimated(project: StickerProject): Promise<ExportResult>;
  exportGif?(project: StickerProject): Promise<ExportResult>;
}
```

The UI should only consume `ExportResult` and validation warnings.

## 21.17 Error and recovery states for video

Add:

```text
Video decode failed
Video unsupported
Trim failed
GIF conversion failed
Video background removal failed
Background removal unavailable
Animated export failed
```

Recovery must preserve the editable project.

Example:

```text
We couldn't remove the video background.
Your original video and edits are still saved.

[Try Again]   [Continue Without Removal]
```

## 21.18 Updated MVP build order

### Sprint 1

```text
Mirsal integration
Sticker Library
Media Picker
Shared project state
Basic static editor
```

### Sprint 2

```text
Auto Cutout
Move / Scale / Rotate
Crop
Border
Undo / Redo
Save project
```

### Sprint 3

```text
Text
Emoji
Sticker layers
Pack manager
Send to Mirsal chat
```

### Sprint 4 — New animated-media foundation

```text
Video import
Video preview
Timeline
Trim
Animated project mode
Text over video
GIF conversion
Animated export
```

### Sprint 5 — Optional video AI

```text
Video background-removal provider
Per-frame masks
Mask cleanup
Processing / retry states
Capability gating
```

### Sprint 6

```text
AI enhancement
AI generation
Advanced effects
Batch operations
```

## 21.19 Updated screen naming

Add:

```text
MOBILE_08 = Video / GIF Prepare & Edit
DESKTOP_07 = Video / GIF Prepare & Edit
```

These are workflow views, not separate applications. The existing Animated Sticker Editor remains the timeline-focused advanced editor.

## 21.20 Updated master coding prompt

```text
You are implementing the Mirsal Sticker Builder as a native feature of an existing Mirsal messaging application.

Keep the existing Mirsal shell, shared StickerProject architecture, contextual editor model, autosave, undo/redo, export abstraction and AI-provider abstraction.

Add a complete animated-media workflow for Video / GIF creation.

Primary animated flow:
Sticker Library -> Create -> Media Picker -> Video / GIF Prepare -> Preview / Trim -> Optional GIF Conversion -> Optional Video Background Removal -> Animated Composition -> Text / Emoji / Sticker / Draw / Border / Adjust -> Timeline -> Save to Pack -> Send / Export.

Video and GIF are first-class media sources but share the same StickerProject model. Do not create a separate VideoStickerProject.

Add video editing state for trim range, current time and FPS. Add GIF conversion state. Add optional video background-removal capability behind a provider abstraction and capability flag. It must support graceful unavailable, processing, success and error states.

Text, emoji, stickers and drawing remain reusable StickerLayer types. Animated layers may have optional start/end timing.

On mobile, the Video / GIF preparation controls are vertically scrollable beneath the preview and timeline. Keep the preview and primary timeline visible and prominent. Use progressive disclosure so secondary controls such as background removal, text and advanced settings do not create a crowded screen.

On desktop, use the existing multi-panel Mirsal editor shell: tools/layers on the left, animated preview in the centre, properties on the right, timeline along the bottom.

Do not create separate routes for GIF conversion, video background removal, text, emoji, border or other individual tools. Implement them as contextual editor tools/panels.

Add provider-independent services for video processing, GIF conversion and optional video background removal. Keep codec and output limits behind the existing exporter abstraction.

All edits must update shared project state and remain autosaveable. Heavy video frames and masks must stay outside command history and be referenced rather than copied into every undo step.

Preserve source media and the editable project when processing or export fails.

The design remains premium, clean and production-oriented with white/light-gray surfaces, dark navy text, blue primary accents, restrained shadows, rounded controls and a transparent checkerboard canvas. Do not redesign the Mirsal messaging shell.
```

## 21.21 Definition of Done — Animated Update

A user must be able to open the sticker panel from a Mirsal chat, choose Video / GIF, import a video, preview and trim it, optionally convert it to GIF, optionally remove the video background when the capability is available, add text and other sticker layers, adjust the animated composition, save it into a sticker pack, and send/export the resulting animated sticker without leaving the Mirsal product experience.
