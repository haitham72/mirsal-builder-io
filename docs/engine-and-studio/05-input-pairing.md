# Input pairing

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

A subject's variants are its `img-NNN-<subject>` folders in number order (`img-001..004-teddy_bear` = variants 1-4). The image in `img-NNN` is paired with `vid-NNN` **by the same folder number** (`pairing: folder`); several takes inside one folder pair by the same `(K)` number, and only as a last resort by position (`pairing: order`, flagged by `doctor`). **Names in the watch folders are final: nothing renames them.** The prompt is matched to a subject by whole words of the folder name (`teddy_bear` <- "teddy yellow bear for school"). In Phase 2 the API ticket replaces filename matching.

**Copied clip sets are ignored.** If a variant's pre-sliced clips have the same per-cell file sizes as an earlier variant's (a stat call; media is never read), they are copies. They would animate the wrong stickers, so they are dropped: `clips_dup_of: "001"` is recorded on the pick and in `result.json`, `doctor` warns, and that variant uses its own 3x3 mp4. Found on the real inputs: vid-002/003/004's clips were byte copies of vid-001's.

**Pre-sliced clips.** When `vid-NNN/slices/` holds clips whose name ends in `(n)` (n = grid cell 1-9, any prefix, `.mov` and/or `.webm`), the app uses them instead of slicing the 3x3 MP4. `mov` (ProRes 4444) is preferred (`clip_prefer`); see "Clip formats".
