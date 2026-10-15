# 6. JSON contract and compatibility

<sub>Part of [reaction.md](../reaction.md).</sub>

The authoritative shapes and errors are in [api.md](../api.md) and the OpenAPI document. Functions live in `flow/particle_sets.py`, using the pure simulator in `engine/particles.py` and shared video verification in `engine/effect_video.py`.

| Route | Purpose |
| --- | --- |
| `GET /api/particles`, `GET /api/particles/{id}` | Sets with owners, derived packs, source metadata, cells, renders and affirmation |
| `GET /api/particles/deleted` | Trash listing with Restore |
| `GET /api/generations/{id}/particles` | Per-cell owners, sets, approval offer and legacy results |
| `GET /api/packs/{id}/particles` | Sticker-set union, bursts and summed per-sticker counts |
| `GET /api/packs/{id}/stickers/{sid}/particles` | That sticker's sets and legacy gallery |
| `GET /api/packs/{id}/stickers/{sid}/particle-preview` | Free current-owned-set preview with saved motion for Echo |
| `POST /api/particles` | Create/import via owners and `from_effect`, `from_generation`, `from_slices` or `from_video`; free `from_stickers` recovery with a selected parent is being tested; imports can target an existing set |
| `POST /api/particles/{id}` | Rename, pick cells and save motion |
| `POST /api/particles/{id}/link`, `/unlink` | Free edits to sticker links |
| `POST /api/particles/{id}/more` | Quote first, confirmed AI generation, append to the same set |
| `POST /api/particles/{id}/preview`, `/render` | Same deterministic simulator; render verifies Telegram limits |
| `POST /api/particles/{id}/add` | Add render to destination pack and record affirmation |
| `POST /api/particles/{id}/duplicate`, `/delete`, `/restore` | Independent copy; soft delete; restoration |

Legacy `/api/effects/*`, `packs` input and `/assign`/`unassign` remain for one release. Pack input maps to its library stickers. It does not restore pack ownership. Member reads preserve their authorization boundaries; writes remain owner-only.

### Sprite erosion and independent editing (2026-10-15)

ParticleParams accepts erosion_px (integer0–6, default0); strict numeric validation/clamping stays in the engine. The saved-set Advanced slider sends it through existing motion params. Raster preview/render and sprite Lottie export apply the same existing elliptical alpha morphology to keyed static/animated RGBA before sprite preparation; cached art retains its earlier despill and is never re-keyed. Zero bypasses processing and RNG draws, preserving default frames/Lottie bytes. Open and save uses the existing save-as-new endpoint on explicit Save; the source row is unchanged.
