# A1 — documentation review

2026-10-14; docs-only on ui/ux-review. Reviewed README, CLAUDE, rules, architecture, six split-area indexes, all design sections, redesign, dark-mode, onboarding, reaction files 12–14, backlog, waiting-for-haitham and relevant inventory rows. No code changes/tests. Sizes below measured from disk; behavior remains for browser/code verification.

## Contradictions (both sides)

| ID | Evidence | Consequence |
|---|---|---|
| D-01 | docs/design/04-4-the-shell-rules-that-hold-on-every-screen.md:18 says two clipped rows, :22 **Your reactions**. docs/reaction/14-13-reaction-effects-one-emoji-flying-as-itself-t.md:33 says scrolling wall, All/Done/Not done, **Animation presets**, replacing that list; the reaction file's :5 also retains old flow. | Latest dated paragraph wins; do not redesign toward stale two-row prose. |
| D-02 | docs/redesign_plan.md:32 puts Particle effects (#/effects) in + New; design shell file :14 puts Reaction effects (#/reactions) there and scopes effects to Studio. | Preserve both routes; current shell owns navigation. |
| D-03 | docs/design/09-9-every-rejected-picture-carries-its-own-overrid.md:8/:14 say other sheet-cell clicks open details; docs/design/11-ui-ux-pass-of-2026-10-03-what-a-click-means.md:34 says cells never open a tile. | Verify behavior; preserve override semantics. |
| D-04 | docs/architecture.md:76 says three separate batch views await consolidation; docs/redesign_plan.md:175/:178 say map built; design interaction file :11 describes it. | Architecture current-state paragraph stale. |
| D-05 | redesign :35 says Studio journey still to build; :175/:177 say built. Design interaction :10 documents seven-stop track instead of the older five-stop proposal. | Replace completed proposal with current contract. |
| D-06 | redesign :164 names Stickers/Particles/History pack tabs; design interaction :15 names two tabs Stickers/Reactions. | Migration map is not current spec. |
| D-07 | docs/backlog.md:112 and docs/waiting-for-haitham.md:78 call History retired; design shell :9 exposes Watch folders in owner avatar; docs/ui_inventory.md:23/:223 contain screen/five actions. | Revalidate retirement; do not silently remove it or revive held W34. |
| D-08 | CLAUDE.md:5 requires lean task-specific startup; docs/rules.md:9 requires dev notes/trackers upfront. | Current CLAUDE wins; synchronize full text. |
| D-09 | CLAUDE.md:46 limits final blocks to Telegram/no cut picture; docs/rules.md:68 explains overrides but ends “its BLOCK verdicts are final”; docs/agent-and-chat.md:5 says Python blocks final. | Clarify technical-final/judgment-overridable; engine owns decision. |
| D-10 | architecture :65 says Plan spends nothing; waiting tracker :49 tracks unpriced cloud expander/intent calls and unresolved enhancer budget. | Merge “free” visibility issue with W18; API before spending UI. |

Abbreviated “design shell” and “design interaction” rows refer to the full paths named in D-01/D-03; redesign/architecture/tracker abbreviations refer to docs/*.md named above.

## Stale statements

- Inventory :3 still narrates two rows/created cards. Current :5 totals **481 actions, 482 definitions, 35 scripts, 17 screens, 171 named routes**; redesign :60 lists historical 429/16/155. Label snapshots; preserve baseline.
- docs/design/06-6-earlier-batches-the-redesign-built-2026-10-02.md:13/:19/:25 mix grid thumbnails/Load more/unpaged target; :11 says paged under the hood without button; design interaction :35 says one sticker picture. Explicit old-plan precedence at section 6 :15 helps but costs reading.
- Design interaction :12 moves Download/Report/Remove to ⋯; :29–:30 still places them beside Add to group/Create more.
- docs/particles.md:3 and docs/reaction.md:3 promise reaction labels. Old prescriptions retain “Particles switch” in design section 6 :5, “Particles section” in section 10 :6, “With particles” in section 5 :9, Particle effects in redesign :32. Internal IDs may remain particles.
- docs/engine-and-studio.md:26 and docs/agent-and-chat.md:29 call AI landing screen; Home is current in docs/design/05-5-per-screen.md:7 and architecture :97.
- Stages: redesign :35 says five; architecture :239 says four; design interaction :7 says six including Auto.
- backlog :147 says only main/edit-design, whereas CLAUDE.md:27 includes reactions. Design index :3/architecture :4 advertise 2026-10-11 despite later content.
- README.md:126 and docs/design/14-llm-selector-catalog.md:5 name GPT-5.6 Luna; rules :71/CLAUDE :49 use gpt-6-luna. A2 should verify catalog alias before declaring UI wrong.
- Waiting :3 says live IDs 1–39 yet has 49/50; **49 duplicated** at :28 FAQ acceptance and :85 CMS/Telegram. Rules :26 stops W48; backlog :38 has ambiguous W49. Assign unique stable IDs.
- README.md:126 old agent-and-chat.md#models-servicesllmpy anchor no longer names a heading: Models is index link at docs/agent-and-chat.md:30. Audit split-doc deep links.

## Structure, size, ownership and ≤8 KB reading path

Measured bytes: CLAUDE **7,954**; README 21,503; rules 21,963; architecture **28,356**; redesign 19,330; onboarding 16,467; backlog 24,314; waiting 21,019. Index sizes: engine/Studio 10,869; agent/chat 7,608; API 6,579; generation 5,917; reaction 4,524; design 4,225. Design interaction section 17,445; per-screen section 9,543.

- Split architecture summary/wiring (docs/architecture.md:87) from every Python module (:136); UI tasks need §6.
- Recut design: reaction contract embedded in shell at :16 belongs to reaction §13; interaction file :5–:38 mixes chat, Studio, packs and old placement. Split by stable screen contract, not implementation date.
- One owner: shell/rail → design §1/§4; theme → dark-mode; override visuals → design §9 (rules invariant, engine API); reaction UI → reaction §13; Home → design §5; media provenance → onboarding; project map → Studio design. D-01–D-09 show duplicated explanations.
- Onboarding :3 is runtime contract; :6 provenance/costs, :21 historical prompts. Separate linked appendix; UI task need not read two video prompts.
- Index summaries duplicate sections despite “read only needed section” (docs/design.md:13). Use compact responsibility/link rows. Reaction index :17–:19 numbers §8 twice and places §8 before §7.
- Additional measured oversized docs (only headings/size inspected): export architecture **176,287 B** (generated bank :126–before :2068), HTTP inventory **90,292** (schema appendix :430), review prompt **56,657** (old report :3, instructions :394), UI inventory **46,474**, deployment **32,985**, review **30,988**. Extract appendices or search rows; keep paused deployment/audit baseline out of UI startup.
- **Existing core path = 7,134 B:** design shared shell (907) → non-negotiables (1,388) → foundations (1,838) → rejected-picture contract (3,001). Search index for task-specific link then bounded paragraph. This fits **after inherited session rules**. Full CLAUDE alone is 7,954 B; full CLAUDE plus index cannot satisfy a literal ≤8 KB cold start. Proposed compact ≤1 KB UI gateway should link contracts and distinguish inherited rules from task-reading budget. No gateway created here.

## UX promises checklist for browser phase

1. Shared 96px rail, 392px list/300 at ≤1180, drawer <900, bottom rail <760; consistent geometry. docs/design/01-1-shared-shell.md:5; shell :27–:29.
2. Four Home/Create/Library/Help items; avatar roles; rail Create opens last tab fresh empty, tabs preserve work. Shell :7–:15.
3. Global/Appearance theme controls, next-theme accessible name, pre-paint dark default, persistence/cross-tab/blocked-storage/focus retention; media unchanged. docs/dark-mode.md:3–:7/:24.
4. AI visual reference and shared feedback states. docs/design/05-5-per-screen.md:15–:18/:26–:28; interaction :17 newer flat restyle.
5. Picture/plain reason/on-picture reversible override on still/animation/sheet/chat; honest bulk count, technical limit explained, vision does not hide pictures. Design §9 :7–:15; CLAUDE :46.
6. Animation useful before clips: video sheet, priced model controls, editable prompt/motion chips; style tiles collapse. docs/design/07-7-what-done-means-for-this-work.md:8–:9.
7. Project/Batch/Sheet/Video tree/breadcrumb/branching/selected node; one floating main action; docked panel arrows/Escape. Interaction :11–:14.
8. Planner feedback/disable/scroll, unknown price Retry; immediate override queue feedback/cancel; no polling entrances; Queue reserves space. Interaction :23/:26; design browser-look :11/:16; foundations :15.
9. Pack header Studio/Download/owner Send/⋯, batch groups/actions, two tabs, cross-group selection; bursts excluded from stickers/counts/Home and never reaction sources. Interaction :15; docs/reaction/12-11-added-bursts-are-reactions-not-stickers-2026.md:5.
10. Current Reaction effects wall/search/Done; newest saved version/start look; sliders/Reset; motion presets; Select/Shift/select-all; batch progress/Cancel/newest-Lottie zip; shared fit pack hover. Reaction file 14 :25/:33.
11. Library reactions finished/unclaimed bank, ≤9 select, free preview/Approve-collapse; scoped Studio; priced Generate more in card. docs/reaction/13-12-library-create-flow-2026-10-13.md:5.
12. Home distinct bands/full-row films/preserved nodes/empty states; welcome keyboard/Skip/opt-out/reduced motion/after LAN approval. Design per-screen :7–:13; welcome section :5; docs/onboarding.md:3.
13. Packs scroll/newest order/search reset, per-person Library and owner-only send/import. Per-screen :22; personal-packs section :5–:7.
14. Settings Appearance first/sticky sections; Help issues/notifications/source chips/current action/staff queue/FAQ. Per-screen :47/:50–:60.

Design abbreviated sections map directly to docs/design.md links; the long paths above identify shell/interaction; other section filenames have matching heading names.

## Already tracked UI work (merge; not new proposals)

| Existing item | Source / treatment |
|---|---|
| Type scale/style art/visual acceptance | backlog :11–:13; W1 waiting :9. Owner art input remains. |
| Spending settings API first | backlog :151; redesign :189. |
| Selected-batch Animate/Add, authorized gbdrop retirement | redesign :186–:188/D3-D4 :195–:197; inventory :524–:525 still gbdrop/ginc. |
| Video-sheet override preview, old-sheet restoration, reaction trash purge | backlog :21–:24; W4 waiting :14. |
| Enter/price, enhancer budget, non-live create, composer ambiguity | W16/18/19/20 waiting :47–:53; backlog :83. |
| Settings create empty chat; wrong animated editor; redo; ambiguous last-one | W22/23 waiting :57–:59; backlog :35. |
| Lost input/settings race/Thinking lock/deleted-batch polling/large session polling | backlog :33; link shared polling proposals to existing behavior debt. |
| Export bank picker, older clip viewer/version naming | backlog :63–:65/:111; picker endpoint needed. |
| Studio browser smoke, DEAD queue rows | backlog :69/:107. |
| Mobile editor/parked React/History | backlog :110–:112; held W33/34 waiting :76–:78; do not revive held removals. |
| Help/FAQ acceptance, pending access, Report reply visibility | First W49 waiting :28–:33; backlog :135–:136. |
| Group suggestions/confirmation/request trace | backlog :90–:91. |

Paid W2/5/6/7, sprite W21, burst W27 and deployment stay in current scopes (backlog :18–:22/:85; waiting :11–:20/:55/:63/:94). Provider-off review supplies evidence, not paid experiments or real answer-quality validation.

## Final inventory reconciliation

The initial inventory prose is a snapshot, not current measured truth. The final code_reader.md scan records 481 unique ACT names and 483 assignments: intentional ggo plus unintended gkeepsize overwrite. The generated heading counts need correction, as F-21 records. Final current-contract decisions and task scope are in ../uiux_plan.md; this reader report preserves the original evidence.
