# Export to AddCollection API — Implementation Guide

**Purpose:** Add a new export button in the Studio/Library that sends a pack's stickers to the external AddCollection API (`POST /api/v1/Upload/AddCollection` at `emojicms.devinprocess888.com`).

**Status:** Guide prepared 2026-10-09. Not yet implemented. Requires Haitham's go before starting.

## Context

The external API (`docs/Api/AddCollection-API .md`) expects:
- `CollectionName` (string): pack title
- `Description` (string, optional): pack description
- `Media` (repeated file parts): one per sticker file (`.webm` for animated, `.png`/`.webp` for static)
- `MediaMetadata` (JSON string): array of `{emoji_utf, tags}` per media file, paired by index

**Critical constraint:** `Media[i]` pairs with `MediaMetadata[i]` by order, not filename. The metadata array length must equal the number of media parts.

## Where it fits

This is a **new export surface** alongside the existing:
- Studio "Download .zip" button (`GET /api/generations/{id}/export.zip`)
- Library pack export (`GET /api/packs/{id}/export.zip`)

The new button appears on:
- **Library pack page** (besides "Download .zip" and "Send to Telegram")
- **Studio batch view** (besides "Download .zip")

It sends the same sticker set (accepted, ready stickers, animated where available) but in the AddCollection multipart format instead of a ZIP.

## Data mapping

### Pack → Collection

| AddCollection field | Mirsal source | Notes |
|---|---|---|
| `CollectionName` | Pack `title` or `slug` | Pack name from `library.json` |
| `Description` | Pack metadata (optional) | Could be empty or auto-generated from tags |
| `Media` | Sticker files (`.webm`/`.png`/`.webp`) | Read from `out/library/files/<G###>/` or pack's sticker copies |
| `MediaMetadata` | Per-sticker emoji + tags | See below |

### Sticker → MediaMetadata item

| AddCollection field | Mirsal source | Transformation |
|---|---|---|
| `emoji_utf` | Sticker `emoji` | First grapheme cluster (use `media/export_names.py:first_emoji`) |
| `tags` | Sticker `tags` + `key` | Underscore-separated, normalized (lowercase, no special chars) |

**Tags building:**
1. Start with sticker's `tags` array (if exists)
2. Add sticker's `key` (canonical action) if not already present
3. Normalize: lowercase, replace spaces/hyphens with underscores, collapse repeats
4. Result: `"laugh_laughing_lol_rofl_lmao"` format

**Example:**
```json
{
  "emoji_utf": "🤣",
  "tags": "laugh_laughing_lol_rofl_lmao"
}
```

## Implementation plan

### Phase 1 — Backend route

**File:** `mirsal/mirsal/console/app.py` (native FastAPI)

**New route:** `POST /api/packs/{id}/export-collection`

**Logic:**
1. Load pack from `out/library/library.json` by id
2. Verify ownership (caller must own the pack)
3. Iterate pack's stickers:
   - Filter: only `READY` and not rejected
   - Prefer animated (`.webm`) if ready and not rejected
   - Fall back to static (`.png`/`.webp`)
   - Skip if no file exists
4. Build `MediaMetadata` array in the same order as files
5. Construct `FormData` with:
   - `CollectionName` = pack title
   - `Description` = empty or auto-generated
   - Repeated `Media` file parts (same order as metadata)
   - `MediaMetadata` = JSON string of the array
6. POST to external API:
   - Base URL: `https://emojicms.devinprocess888.com` (configurable via env var `MIRSAL_COLLECTION_API_URL`)
   - Endpoint: `/api/v1/Upload/AddCollection`
   - Auth: Basic header from env var `MIRSAL_COLLECTION_API_CREDENTIALS` (base64 `username:password`)
7. Parse response:
   - 2xx: return `{ok: true, response: <server-response>}`
   - non-2xx: return `{ok: false, error: <message from server or HTTP status>}`
8. Return to caller

**Environment variables:**
```bash
MIRSAL_COLLECTION_API_URL=https://emojicms.devinprocess888.com
MIRSAL_COLLECTION_API_CREDENTIALS=<base64(username:password)>
```

**Error handling:**
- Pack not found: 404
- Permission denied: 403
- External API timeout: 504 (with details)
- External API error: propagate error message
- Missing credentials: 500 (server misconfiguration)

**Dependencies:**
- `httpx` (async HTTP client, already in use)
- No new package dependencies

### Phase 2 — Studio/Library UI buttons

**File:** `mirsal/mirsal/console/pack.js` (Library pack page)

**New button:** "Export to Collection API" (besides existing export buttons)

**Click handler:**
1. Call `POST /api/packs/{id}/export-collection`
2. Show loading state on button
3. On success: show toast/confirmation with response summary
4. On error: show error message inline or in toast

**File:** `mirsal/mirsal/console/studio.js` (Studio batch view)

**New button:** "Export to Collection API" (besides "Download .zip")

**Click handler:** Same as Library

**Styling:** Reuse existing `.btn` classes, no new CSS needed.

### Phase 3 — Tests

**File:** `mirsal/tests/test_live.py` (add a new test class)

**Test coverage:**
1. Mock external API (using `httpx.AsyncMockTransport` or similar)
2. Test successful export with a fake pack
3. Test error responses (404, 403, 500 from external API)
4. Test ordering constraint (media count = metadata count)
5. Test emoji normalization (first grapheme cluster)
6. Test tag normalization (underscores, lowercase)

**File:** `mirsal/tests/js/pack.test.js` (add button click test)

**Test coverage:**
1. Button exists on pack page
2. Button calls the correct API route
3. Loading state appears
4. Success/error handling

### Phase 4 — Documentation

**Update `docs/api.md`:**
- Add route entry under "Library, packs, Telegram, projects, search, health"
- Document request/response schema
- Note environment variables

**Update `docs/backlog.md`:**
- Mark this as "open" before implementation
- Delete entry after completion

**Update `README.md`:**
- Add a note about the new export surface (if visible to users)

## Open questions (for Haitham)

1. **Credential storage:** Should credentials be in `.env` only, or also in the runtime settings UI?
2. **Description field:** Should it be empty, auto-generated from pack tags, or a manual field in the UI?
3. **Batch export:** Should Studio batches also export directly, or only Library packs?
4. **Error visibility:** How much detail from the external API should be shown to the user?
5. **Rate limiting:** Should we add per-user rate limiting for this endpoint?

## Dependencies on existing work

None. This is standalone and does not block or depend on:
- Pack resolver (plan Phase 2)
- Short codes (plan Phase 3)
- Bank picker UI (plan Phase 4)
- In-batch versions (plan Phase 5)

It can be built in parallel or after those phases.

## Verification checklist

Before marking this complete:
- [ ] Backend route implemented and tested
- [ ] UI buttons added on both Library and Studio
- [ ] Environment variables documented
- [ ] API documentation updated
- [ ] All tests pass (fast tier: `mirsal test fast`)
- [ ] One browser look at the button flow
- [ ] Credentials never committed (check `.gitignore`)
- [ ] Error handling tested with real external API (or faithful mock)
