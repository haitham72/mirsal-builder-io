# Mirsal Sticker Upload — Backend Team Deliverable

## Your required filename fields

Use only the **first four fields**:

```text
{pack_id}-{pack_slug}-{action}-{emoji}
```

| Field | Use in receiving app |
|---|---|
| `pack_id` | Persistent internal PostgreSQL pack lookup; same ID for the whole pack. |
| `pack_slug` | Resolve the pack/category for the **Assign to emoji** flow (e.g. `falcon`). |
| `action` | Set **Title** (e.g. `laugh`). |
| `emoji` | Set the actual **Assign to emoji** value (e.g. 🤣) and index for interactions/search. |

**Tags:** include action, relevant aliases and actual emoji, separated with `_`, e.g. `laugh_happy_joy_🤣` or `love_heart_😍`. Search should support both text and the actual Unicode emoji. `pack_slug` is the category identifier; `emoji` is the emoji glyph.

## Filename examples

```text
AH43-falcon-laugh-🤣-s04-static-g01-20261008.png
AH43-falcon-laugh-🤣-s04-video-g01-20261008.webm
AH43-falcon-love-😍-s05-static-g01-20261008.png
AH43-falcon-approve-👌-s06-video-g02-20261008.webm
```

The remaining suffix is **for Mirsal API/database use only**:

```text
-s{sticker_number}-{media}-g{group}-{date}.{ext}
```

Do not ask upload operators to fill these fields, rename them or derive identifiers from them. Retain the full filename when saving the asset. The same `pack_id` appears on many files; it **does not** uniquely identify a sticker or file.

## Deliverable / acceptance checklist

- Read or receive `pack_id`, `pack_slug`, `action`, `emoji` as distinct metadata values; prefer the accompanying export manifest/API metadata over fragile filename splitting.
- Map `pack_slug` to pack/category; `action` to Title; `emoji` to Assign to emoji.
- Populate searchable tags with action aliases **and literal Unicode emoji**; preserve full emoji sequences, not aliases like `:laugh:`.
- Accept both `.png`/`.webp` static assets and `.webm` videos; keep the complete filename, including the API suffix.
- Permit many files with the same pack ID and multiple actions/emojis; do not deduplicate by `pack_id` alone.
- Preserve Mirsal-supplied group, sticker, and asset metadata without changing it. Support lookup/search by action and emoji.

**Boundary:** Pack code creation, source `S#`, `gNN`, media type, export date, versioning, and Postgres asset traceability are Mirsal Builder responsibilities—not manual upload-team fields.
