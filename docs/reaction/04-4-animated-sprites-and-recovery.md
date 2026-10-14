# 4. Animated sprites and recovery

<sub>Part of [reaction.md](../reaction.md).</sub>

The full animated path is **prompt → text-only Kling 2×2/3×3 animated sheet → key and slice → animated sprites in the simulator → render → add to the same pack**. The existing nothing-to-nothing pipeline and technical checks remain. Each flying particle plays its own sprite's frames while simulator movement, spin, scale and fade are applied. Image sprites are single-frame inputs. Selected video tiles loop; job/credit details remain accessible. Directly adding a cut clip remains a secondary legacy action.

Recovery for artwork accidentally saved as a sticker pack is **Use as particle pack → This sticker / All N stickers → Parent pack and target stickers → Use selected · free**. Source artwork is copied without deleting originals. The selected parent stickers own the set; supplying artwork does not make source stickers owners.
