# Download .zip from the Studio (`flow/batches.export_zip`, 2026-10-05)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

The batch header's **Download .zip** (`GET /api/generations/{id}/export.zip`, native) downloads the batch as it stands, changing nothing:
- every sticker that is READY and not rejected, as its animation when that is ready and not rejected, otherwise as its still, under the engine's file names;
- plus `manifest.json`: the batch, the prompt, and per sticker its `S#`, key, name, emoji, tags, kind and size.

A batch with nothing accepted answers 409. The owner and the batch's own person can download; a stranger's batch is a 404. The pack page's *Download .zip* is unchanged (`Library.export_zip`).
