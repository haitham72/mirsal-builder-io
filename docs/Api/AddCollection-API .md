# Mirsal Creator API: Submit a Pack for Approval

The external emoji CMS that **Export to collection** sends packs to. This page is the CMS's own reference (developer keys, the endpoint, its answers) followed by how Mirsal calls it (`mirsal/mirsal/services/collection.py`; routes in [../api.md](../api.md) "Export to the AddCollection API").

## Developer keys

Developer keys let an integration call the Mirsal Creator API on your behalf, with the same permissions as your account.

1. On the CMS, open the **Developer Keys** page and click **Generate New Key**.
2. Give the key a label you will recognise, and choose how long it stays valid: a number of days, months or years, or **No expiration**.
3. Copy the key immediately. It is shown only once and cannot be retrieved again; if you lose it, delete it and generate a new one.
4. Store it somewhere safe: anyone who has it can act on your account through the API. For Mirsal that place is `mirsal/.env` only (`MIRSAL_COLLECTION_API_CREDENTIALS`), never a file in the repo.

## Authentication

Every request carries the key in the `Authorization` header with the Bearer scheme:

```
Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

A request with no key, or with an expired, deleted or unknown key, gets **401 Unauthorized**.

## Submit a Pack for Approval

Creates a new collection from uploaded emoji media and submits it into the approval workflow, the same as publishing through the website.

```
POST /api/v1/Upload/AddCollection
Authorization: Bearer <your-developer-key>
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|---|---|---|---|
| `CollectionName` | string | yes | Name of the new collection, **at most 40 characters**. |
| `Description` | string | yes | Short description of the pack, **at most 160 characters**. |
| `ContentSubType` | string | yes | Media sub-type, for example `webm`. |
| `Media` | file[] | yes | One or more emoji media files; the same field name repeated once per file. |
| `MediaThumbnails` | file[] | yes | One PNG thumbnail per file in `Media`, **in the same order**; the same field name repeated once per file. |
| `MediaMetadata` | string (JSON) | yes | A JSON array with one entry per file in `Media`, **in the same order**. Each entry needs `emoji_utf` and `tags`. |

`Media[i]` is paired with `MediaThumbnails[i]` and `MediaMetadata[i]` **by index**, never by file name: both must have as many entries as there are `Media` parts.

```bash
curl -X POST "https://emojicms.devinprocess.com/api/v1/Upload/AddCollection" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxx" \
  -F "CollectionName=My Pack" \
  -F "Description=A short description" \
  -F "ContentSubType=webm" \
  -F 'MediaMetadata=[{"emoji_utf":"😀","tags":"smile,happy"}]' \
  -F "Media=@smile.webm" \n  -F "MediaThumbnails=@smile.png;type=image/png"
```

| Status | Meaning |
|---|---|
| 200 OK | `Success: true` and the created pack's details in `Result`. |
| 400 Bad Request | Validation failed; `ErrorMessages` explains why. |
| 401 Unauthorized | The developer key is missing, invalid or expired. |
| 500 Internal Server Error | Something went wrong while processing the upload. |

More endpoints will be added to the CMS's reference as they become available.

## How Mirsal calls it

- **What is sent** is exactly what the pack's (or batch's) Download .zip holds, in its order: `Media` once per asset (`.webm` animated, `.png` / `.webp` static), `MediaThumbnails` once per asset in the same order (a PNG named `{stem}.png`: a `.png` sticker as it is, a `.webp` converted, a `.webm`'s first frame with its alpha, which is the approved still the animation starts from), `MediaMetadata` one JSON string `[{emoji_utf, tags}]` of the same length (`emoji_utf` the asset's first grapheme cluster, `tags` its action tokens joined by `_`, never empty), `ContentSubType` `webm` for animated packs (and a mix), else the stills' own type.
- **Limits are checked before anything is uploaded**: a name over 40 or a description over 160 characters is a 400 with a sentence; the dialog caps both fields, offers a longer pack name cut at a word for you to edit, and asks for the description. An API caller who sends no description gets the collection's name as the description.
- **Answers**: a 2xx counts as accepted unless its JSON says `Success: false`; the refusal's words come from `ErrorMessages` (a list is joined with `; `), else an older `message` / validation answer, else the status. A 401 says the developer key was not accepted and how to replace it. The created pack's `Result` is returned as `result`.
- **Configuration** (`mirsal/.env`): `MIRSAL_COLLECTION_API_CREDENTIALS` = the `sk-...` developer key (sent as Bearer; a legacy `user:password` or its base64 still sends HTTP Basic), `MIRSAL_COLLECTION_API_URL` = the CMS (the code's default is `https://emojicms.ehub.ae`; the example above uses `https://emojicms.devinprocess.com`). Every export, ok or not, is a line in `out/collection_exports.jsonl`, never the key.
- **Losing or leaking a key**: delete it on the Developer Keys page, generate a new one, put it in `.env`, restart the server.
