# Chat interaction proposal

Requested by Haitham, 2026-10-11. This is a proposal for conversational behaviour; it does not authorize additional implementation. Playback speed is outside the requested scope. Current behaviour is documented in [agent-and-chat.md](agent-and-chat.md).

The chat should answer three separate questions before acting: **what does the person want, which existing objects do they mean, and how much should change?** A confident answer to one does not settle the others. Recognizing “make happier” does not identify its target; recognizing S4 does not make an unknown change understandable.

## Keep distinct conversational state

| State | Purpose |
|---|---|
| Active project and batch | The default home for numbers and “this batch”. Keep stable across descriptions. |
| Explicit UI selection | The stickers the person deliberately selected for an action. |
| Last discussed sticker or group | The referent for “he”, “it”, “those two”; separate from a whole carousel being visible. |
| Last displayed collection | Resolve “show the rest”, search-result follow-ups and “all of these”. |
| Pending clarification | Original request, understood clauses, unresolved field and candidate targets. |
| Pending generation plan | Exact proposed change, scope, price and version awaiting authorization. |
| Running work | Job and generation ids, approved scope and current status. |
| Person's stage and vision permission | Stage controls how far creation goes; consent controls whether pictures may reach vision. Neither changes what “show” means. |

Showing all nine stickers should expand the visible collection without making a later “make him happier” automatically mean all nine. A full carousel is a presentation, not an edit selection. When selection and conversational focus disagree, use the request's wording to distinguish them; ask when that distinction changes the outcome.

## Conditional decisions

| Condition and example | Response or action |
|---|---|
| Existing batch, display request: “show all of them” | Show the entire referenced batch immediately, including after a one-sticker description. No generation plan or creation price. |
| Display request, no identifiable collection | Ask which batch or collection. Do not invent a new subject. |
| Numbered description: “what is the second sticker doing?” | Show S2 immediately. With vision allowed, inspect S2's still and stream what is visibly happening. Keep the batch and S2 as conversational context. |
| Follow-up after that description: “what is he doing?” | Resolve to S2 and answer the question. If the user repeats it, add visible detail or acknowledge uncertainty; avoid repeating the label. |
| Same context, “what about the fourth?” | Keep the description intent, switch to S4 of the same batch. If the preceding topic was replacement or approval, inherit that topic only when its consequences are clear. |
| “What is he doing in the animation?” | Use animation evidence if supported. Otherwise explain the limitation and offer the still description. Never infer actual motion from a still or name. |
| Clear local edit: “make 3 laugh” | Plan a change to S3; preserve the other cells and the character's unrelated features. Show scope and price before creating. |
| Clear subject replacement: “replace 2 with a cat” | Replace S2's character; preserve its requested action and the other stickers. The replacement subject is not evidence for choosing the source sticker. |
| Attribute replacement: “replace his red hat with a blue cap” | Change the hat on the resolved character; preserve the character. Do not treat “blue cap” as the new subject of the entire sticker. |
| Ambiguous replacement: “replace 2 with 4” | Ask whether to copy S4 into S2 or swap the two. These are different operations and should not become a new paid sheet by default. |
| Clear replacement, missing source: “replace it with a cat” | Use one clear discussed/selected sticker; if none or several fit, ask which one. |
| Explicit batch scope: “make all of them happier” | Plan the change for the entire referenced batch. Do not reuse the last one-sticker subset. |
| Ambiguous edit scope: “make him happier” with several candidates | Ask which character or whether the whole batch should change. A pronoun alone does not authorize a batch-wide change. |
| Reference transfer: “make 5 like 2” | Distinguish the target S5 from the reference S2. Ask which aspect to borrow when the request does not say style, pose, expression or character. |
| Mixed understood and unknown clauses | Briefly acknowledge the understood part and ask what the unknown phrase means. Hold the request together; do not silently perform half of it. |
| Several clear changes with clear targets | Represent each operation separately, show each affected sticker, then give one combined plan and total. Ask only about conflicting operations. |
| Clear new subject: “make a cat pack” | Create a new plan according to the person's stage. Existing batch context should not turn every new subject into an edit. |
| Feedback only: “this looks wrong” | Identify the referred sticker, then ask what should improve or offer a grounded diagnosis. Do not invent an approved replacement. |
| “show them” while creation is running | Show ready results and state what is still being made. Do not start duplicate work. |
| Target missing, deleted or out of range: “describe 12” in a nine-sticker batch | State the actual count/status and offer existing choices. Do not fall back to a different sticker. |
| Permission undecided or declined | Keep display available. Ask for vision permission only when inspection needs it; respect a refusal and distinguish stored metadata from an inspected answer. |
| Vision fails after selection | Keep the selected card visible and explain that inspection failed. Offer retry of inspection, never generation as an implicit recovery. |

## The user's stage slider

Treat the slider as an explicit preference about creation depth. First resolve intent, targets and scope; then apply the stage to work that would create or deliver results. Display, description, feedback and clarification retain their own meaning at every slider position.

The existing six stops mean:

| Slider | Ordinary new creation request |
|---|---|
| Auto | Infer the endpoint from the request; an ordinary sticker request ends at Stickers. Infer from clear intent, never randomly. |
| Prompt | Prepare the plan and prompt; start generation only after an explicit Generate action. |
| Stickers | Create the still stickers and stop for review. |
| Animation | Create stickers and animation, stopping at the configured review gates. |
| Telegram | Continue through the pack and Telegram delivery. |
| Export | Continue through Telegram and the configured collection API export, subject to access and setup. |

The preference is one per person, shared by their chats and Studio. A new chat reads that preference; Auto is the initial default when none was saved. An individual request also needs its own effective endpoint, distinct from the saved preference and from a running job's approved endpoint.

| Condition | Proposed decision |
|---|---|
| Animation selected; “show all” or “what is 4 doing?” | Display or describe existing stickers. Do not create animation merely because the slider is at Animation. |
| Auto selected; “make a cat pack” | Plan creation to Stickers. “Make cats and animate them” instead resolves to Animation. |
| Fixed endpoint; ordinary new creation without another endpoint named | Plan to the selected endpoint and show its complete price. Review gates and spending permission remain separate controls. |
| Stickers selected; “animate 4” | Resolve S4 first, then explain that animation exceeds the selected stop. Offer a clearly labelled stage change and continuation; do not start or silently change the preference. |
| Animation selected; “just the stickers” | Explain the conflict and offer the requested earlier stop. An explicit “only” must survive planning and confirmation. |
| Prompt selected; “replace 2 with a cat” | Prepare a replacement plan for S2 without generating it. The source batch and unrelated stickers remain intact. |
| Animation selected; “replace 2 with a cat” | Resolve replacement scope first, then plan the still and downstream animation for the affected result only. Do not regenerate the other eight or reuse an animation of the old character. |
| Earlier slider stop selected while later results already exist | Continue to display existing results. Explain that the preference applies to future work; do not delete results or undo completed stages. |
| Slider moved with no request or pending plan | Save the preference and update its label. Start no work; create no empty chat. |
| Slider moved while a plan awaits confirmation | Preserve the requested content and targets, revise the endpoint and price, and invalidate the old confirmation. Show the revised plan before execution. Moving the slider alone is not approval. |
| Slider moved during approved running work | Keep the running job's approved scope. Apply the preference to future plans; cancellation or extending the current job needs a separate explicit action. |
| Required still or animation already exists | Reuse valid work and price only the remaining necessary work. A stage choice alone does not request fresh generation. |

Apply these checks to every generation path: new packs, replacements, slice edits, whole-sheet edits, regeneration and additional batches. Changing character or pose invalidates that result's downstream animation; free editor changes may also require revalidation before an existing animation can be reused. Separate a free edit, a new still and a new animation in the proposed cost and outcome.

Current code already supports saved person preferences, stage conflicts for new requests and explicit animation/Telegram actions, and the repaired popup. The existing slice/whole-sheet regeneration edit paths do not uniformly apply stage planning. Uniform edit handling, pending-plan revision on slider changes and request-specific endpoints are proposed here, not reported as completed fixes.

## Resolve targets before changing anything

Prefer an explicit batch/sticker id, then a sticker number or ordinal in the active batch. “Change 4” should not edit a stale selected S2. Selection is useful for “this selected one”; recent discussion is useful for “he”. A unique semantic source such as “the proud one” can resolve a target, but two plausible matches need a short choice.

Parse source, replacement and reference roles separately. In “replace the proud one with a cat”, “proud” identifies the source and “cat” describes the result. In “use 2's pose for 5”, S2 supplies a pose and S5 changes. Numbers naming a grid, quantity or price must stay outside target resolution. Cross-batch references need their own batch identity; “previous” should mean the conversational predecessor rather than the highest generation id.

Use the same stable S numbers that appear on the stickers. Explicit exclusions such as “all except 3” must survive every later step. Before offering a plan, check that its actual target set exactly matches the interpreted scope.

## Clarification should continue the original request

Ask for the smallest missing piece. For “make 3 laugh and [unknown phrase]”, an appropriate response is “I understand making sticker 3 laugh. What do you mean by ‘[unknown phrase]’?” Asking the user to repeat the entire request loses useful information.

Persist a clarification as structured state. If the user answers “add a blue hat”, combine it with the held instruction, revalidate all clauses and present the complete change. If they answer “just the laughing part”, deliberately remove the unclear clause. If they give an unrelated new request, abandon the clarification explicitly and route the new request. A response consisting of “4” should fill a requested sticker field; it should not become a new subject or a confirmation of spending.

Missing-target clarification, missing-change clarification and vision consent are different states. A single generic `pending` object is liable to overwrite a generation plan when the user merely asks about its pictures. Preserve the plan across informational detours and use separate state for permission and clarification.

## Plans and confirmations

Tie confirmation to the exact displayed plan version. “Yes, but make it blue” revises the plan and needs the updated scope/price shown; it is not permission to run the old plan. An unqualified “yes” after a clarification or permission question answers that question first. When the last question has multiple meanings, use labelled actions rather than guessing.

Viewing and describing existing work should leave a pending generation plan available. Cancellation of that plan should not imply cancellation of an already running job. If the user changes direction during running work, show what already started and plan the new request separately. When a newer message changes context during an older streamed description, keep the older answer attached to its original sticker and avoid resetting the newer conversational focus.

For undo, name the actual last reversible change and restore its prior version. If the action cannot be reversed, explain the concrete result before proposing another action. Do not turn “undo” into another generation.

## Model interpretation and deterministic validation

Let the model propose an intent, operations, source targets, replacement/reference roles, scope, understood clauses and unresolved fields. Preserve the user's exact unknown phrase. Prefer field-specific uncertainty to one overall confidence score: intent can be clear while scope is unresolved.

Code should validate existence, access, supported operations, scope and reference roles. A model's interpretation cannot approve spending or turn an unsupported operation into a tool call. If interpretation is unavailable, use narrow known rules and ask for unclear changes. Avoid a long vocabulary blacklist: unknown instructions are an uncertainty problem, not a list of forbidden words.

## Suggested order and acceptance checks

First stabilize the frequent loop: show → describe → follow up → select → edit/replace → apply stage → review price → confirm. Apply stage planning uniformly to creation and regeneration edits. Next preserve pending clarification and plans across conversational detours, including slider changes. Then address reference transfer, compound edits and interruptions during running work. No dedicated playback-speed feature is proposed.

This change already addresses the reported carousel routing, numbered still descriptions with streaming, stage popup, several source-replacement cases and clarification before unclear generation edits. The remaining rules above are proposed behaviour, particularly independent pending states, attribute replacements, multi-operation plans and plan versions; their presence here is not an implementation claim.

Test the decision table with fakes and assert outcomes, not just intent labels: exact target ids, number of displayed stickers, images actually sent to vision, card-before-text ordering, whether pending work survived, and zero generation calls for display/clarification. The supplied S2 → “he” → S4 → “all” sequence is the core regression. Run display and description cases at all six slider positions, assert no generation for Prompt-stage edits, and check the endpoint/price of Animation-stage replacements. Add pending-plan slider changes, stale selection, two semantic matches, unknown second clause, clarification reply, permission detour, “yes but…”, out-of-range target and running-job cases before expanding the routing.
