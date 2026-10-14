# Particle sets in the chat (2026-10-04)

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`resolver.particles_intent` selects make, more, link/assign, render/add, delete or restore. The node is `Agent.n_particles`; tools call `flow/particle_sets.py`, the same functions as Studio. Durable sets belong to library stickers. A pack request resolves its selected stickers; a batch outside the library gets an Approve-as-a-pack card that continues to the scoped editor.

Set choice is centralized in `_focus_set`: **an explicit set name overrides; otherwise the focused sticker's newest owned set comes first, then the focused set, then the only suitable set, then chips**. A session's unrelated old set must not replace the chosen sticker's own particles. `particles_start` reuses the newest common owned set unless New set/fresh is explicit. Linking adds sticker ownership without copying sprite files or spending.

| Request | Behavior |
| --- | --- |
| "make particles for my Barbie pack" | Resolve its stickers, reuse their common current set or create one; quote an AI sheet before confirmation |
| "create particles for lipsticks and ribbons" | No pack named, none in focus: "For which pack, or on their own?" with the recent packs, The last pack, On their own; "... on their own" quotes a stand-alone set and `particles_alone` starts it after the go-ahead (docs/particles.md section 8) |
| "more particles for sticker 3" | Choose S3's newest owned set; append without overwriting |
| A request naming another set | Use the explicitly named set |
| "use them for the next sticker" | Free link edit, preserving the set |
| "render a burst for sticker 3" / "add it to the pack" | Same set selection order; render/add to the destination and affirm |
| "delete the bat particles" / "restore the bat particles" | Soft delete with confirmation when in use; restore the same ID and ownership |

The legacy effects intent links into the scoped editor, preserving the animated choice. Both Image sprites and Animated sprites · Kling must be available during Add more; source-kind-locked cards are being replaced in the compact-flow pass. Priced chat cards retain pending plans on a refused start. No chat/browser provider job starts without the shown quote and permitted confirmation.

### Mirsal Echo: testing assigned particle settings

The local **Chat → Mirsal Echo** contact tests saved particle settings independently of Render/Add. Save particles stores the current motion in its set; Save as new branches settings, and assigning that branch to another sticker lets the person test its reaction there. Assignment controls which settings Echo plays; it is a free sticker link edit.

Send a library sticker from the tray, its carousel, or the simulator's Test in chat action. The browser preserves its library `id` and `pack_id`. Echo replies to it and likes the outgoing sticker. At that moment `chat.js` requests `GET /api/packs/{pack}/stickers/{sid}/particle-preview`: the engine resolves that sticker's newest assigned set and saved motion and returns `{set, motion, params, url}`. The overlay is anchored to the outgoing sticker that received the reply. Clicking its reaction re-fetches and replays, so subsequent assignment/settings changes apply to existing messages.

The message does not cache a set choice. There is no unrelated focused/session-set fallback; unassigned stickers return `{set:null,url:null}` and retain their ordinary heart reaction. Old local messages missing library IDs omit particle playback. Per-message request tokens and a chat-clear epoch reject late previews and pending Echo replies after clear. No preview response repaints a different screen. This path spends nothing and does not add a rendered sticker to a pack.

Node regressions in `tests/js/chat_particles.test.js` cover identity preservation, current-assignment lookup, outgoing-sticker overlay, replay after changed assignment, clear/late-response handling and old-message compatibility. Endpoint and scratch-browser validation belong to the integration acceptance gate.
