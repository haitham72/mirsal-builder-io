# Reaction tabs on redesign-ui-ux

Reconciled from main (380384a3 / dc8c0c6b). The current contract and implementation
are maintained in [reaction section 18](reaction/18-18-reaction-tabs-emoji-lottie-packs-2026-10-15.md).
Both Create and Library use one Emoji Style / Lottie Style / Packs tab state.

Emoji Style is the emoji-free preset library, with Motion/Size/Advanced editing
and external emoji slots in exports. Lottie Style embeds its sources in a
self-contained export. Packs shows the server sets list on both surfaces.
See [preset section 14](reaction/15-14-the-animation-preset-library.md) and
[Lottie section 17](reaction/17-17-lottie-style-reactions.md).

This branch preserves duplicate-choice import routing and grid-mismatch consent.
Technical browser acceptance is recorded in docs/uiux_review; owner visual and
wording verdicts remain in waiting-for-haitham.md.
