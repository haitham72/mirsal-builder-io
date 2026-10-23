# Add Collection API Documentation

**Last synchronized: 2026-10-23.** This receiving-CMS reference combines the supplied request contract with observed smoke results. Mirsal's own queued export endpoints and pricing rules are in [api-integration.md](../api-integration.md); acceptance evidence is in [DELIVERY_CHECKLIST.md](../../DELIVERY_CHECKLIST.md).

## Overview

This API endpoint allows you to upload a new collection with media files and associated metadata.

The live CMS accepted the existing animated pack named `test` with four inserted assets. Direct simulator/Lottie JSON uploads returned HTTP 200 and `Success: true` with **zero inserted and zero updated assets**, including attempts with paired thumbnails. JSON delivery is therefore unconfirmed. `ContentType: super_like` returned 400; the receiver reported only `emoji` and `emoji_reaction` as allowed values. No collection ID or stored-price/name readback was returned.

## Endpoint

- **URL**: `/api/v1/Upload/AddCollection`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

## Authentication

- **Type**: Bearer Token
- **Header**: `Authorization: Bearer <token>`

## Request Parameters

### Form Data Fields

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| CollectionName | string | Yes | Name of the collection |
| Price | string | No | Optional decimal string; Mirsal sends `"0"` for free and omits the field when unset. Currency, monetary precision/range and stored-price behavior still need CMS confirmation. |
| Description | string | Yes | Description of the collection |
| ContentType | string | Yes in supplied contract | `emoji` or `emoji_reaction`; `super_like` is rejected. See the implementation difference below. |
| ContentSubType | string | Yes | Media subtype; Mirsal exports `webm`, `png` or `webp`. The supplied `json` example has not produced inserted assets. |
| Media | File | Yes | Media files (can be multiple) |
| MediaThumbnails | PNG files | Sent by Mirsal | One PNG per media file, paired by index. PNG as-is, WebP converted, WEBM grey silhouette. JSON thumbnail requirements remain unresolved. |
| MediaMetadata | JSON string | Yes | Metadata for the media files |

**Implementation difference:** Mirsal's current multipart builder sends `ContentSubType` and omits `ContentType`; the animated `test` upload was accepted in that form. Direct JSON probes explicitly supplied `ContentType`. The supplied required-field declaration and this observed behavior need reconciliation with the receiver before extending reaction delivery.

**Saved and per-export pricing in Mirsal:** pack metadata stores `price` as a decimal string or null. Omitted pack updates retain it; null clears it. A pack export inherits the saved price when omitted, a string overrides it for that export, and explicit null omits multipart `Price`. Batch exports can supply a price directly. The resolved value is frozen before queueing, persisted in outcome/log records and inherited by chat exports. Exact normalization turns `"0002.5000"` into `"2.5"`; negative, malformed and non-string values fail before sending. Generation credits are separate. This behavior has local fake-receiver and browser evidence; live stored-price verification remains open.

### Media Field

- **Type**: File upload
- **Supplied contract**: JSON files, videos, images (depending on ContentType). Observed JSON uploads made no inserts; do not treat the declaration as successful delivery evidence.
- **Current Mirsal pack exporter**: WEBM/PNG/WebP only; JSON export is rejected with 409. Supporting saved simulator/Lottie/super-like JSON remains open work.
- **Multiple files**: Supported - upload all media files in order matching MediaMetadata
- **File naming**: Must include file extension (e.g., "button_reaction.json")

### MediaMetadata Field

A JSON stringified array of objects containing metadata for each media file.

**Structure**:
```json
[
  {
    "emoji_utf": "😀",
    "tags": "grinning_smile_happy"
  },
  {
    "emoji_utf": "😢",
    "tags": "sad_crying"
  }
]
```

**Note**: The order of metadata objects must match the order of media files uploaded.

## Example Implementation

These are **direct-CMS request templates for the supplied JSON contract**, not a verified reaction-delivery path. Both examples require a positive asset-count result matching the submitted files; the observed zero-count JSON response will fail that check. The application's current queue worker checks HTTP status and the success flag only; adding count validation there remains open. Do not automatically repeat a zero-count or ambiguous upload.

### JavaScript/Node.js

```javascript
import fs from "fs";

async function addCollection() {
  const formData = new FormData();

  // Collection details
  formData.append("CollectionName", "Emoji Reaction latest Collection1");
  formData.append("Price", "2");
  formData.append("Description", "Emoji reaction latest collection1");
  formData.append("ContentType", "emoji_reaction");
  formData.append("ContentSubType", "json");

  // Media files - order must match MediaMetadata
  formData.append(
    "Media",
    new Blob([fs.readFileSync("./button_reaction.json")], {
      type: "application/json"
    }),
    "button_reaction.json"
  );
  formData.append(
    "Media",
    new Blob([fs.readFileSync("./emoji_reaction.json")], {
      type: "application/json"
    }),
    "emoji_reaction.json"
  );

  // Metadata
  formData.append(
    "MediaMetadata",
    JSON.stringify([
      {
        emoji_utf: "😀",
        tags: "grinning_smile_happy"
      },
      {
        emoji_utf: "😢",
        tags: "sad_crying"
      }
    ])
  );

  const credentials = process.env.MIRSAL_COLLECTION_API_CREDENTIALS;
  const baseUrl = process.env.MIRSAL_COLLECTION_API_URL || 'http://localhost:5189';
  if (!credentials) throw new Error('Set MIRSAL_COLLECTION_API_CREDENTIALS');

  const response = await fetch(
    `${baseUrl}/api/v1/Upload/AddCollection`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${credentials}`
      },
      body: formData,
      signal: AbortSignal.timeout(60000)
    }
  );

  const raw = await response.text();
  const result = JSON.parse(raw);

  if (!response.ok || result.Success !== true) {
    throw new Error(`CMS refused upload (${response.status}): ${JSON.stringify(result)}`);
  }

  const { insertedCount, updatedCount } = result.Result || {};
  const expected = 2;
  if (!Number.isInteger(insertedCount) || insertedCount < 0 ||
      !Number.isInteger(updatedCount) || updatedCount < 0 ||
      insertedCount + updatedCount !== expected) {
    throw new Error(`CMS did not confirm ${expected} assets; inspect receipt/readback before retrying`);
  }

  console.log(result);

  return result;
}

await addCollection();
```

### Python

```python
import requests
import json
import os
from contextlib import ExitStack

def add_collection():
    base_url = os.environ.get('MIRSAL_COLLECTION_API_URL', 'http://localhost:5189')
    url = base_url.rstrip('/') + '/api/v1/Upload/AddCollection'
    credentials = os.environ['MIRSAL_COLLECTION_API_CREDENTIALS']

    data = {
        'CollectionName': 'Emoji Reaction latest Collection1',
        'Price': '2',
        'Description': 'Emoji reaction latest collection1',
        'ContentType': 'emoji_reaction',
        'ContentSubType': 'json',
        'MediaMetadata': json.dumps([
            {
                'emoji_utf': '😀',
                'tags': 'grinning_smile_happy'
            },
            {
                'emoji_utf': '😢',
                'tags': 'sad_crying'
            }
        ])
    }

    headers = {
        'Authorization': f'Bearer {credentials}'
    }

    with ExitStack() as stack:
        files = [
            ('Media', (name, stack.enter_context(open(name, 'rb')), 'application/json'))
            for name in ('button_reaction.json', 'emoji_reaction.json')
        ]
        response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
    result = response.json()

    if not response.ok or result.get('Success') is not True:
        raise RuntimeError(f'CMS refused upload ({response.status_code}): {result}')

    counts = result.get('Result') or {}
    inserted, updated = counts.get('insertedCount'), counts.get('updatedCount')
    expected = len(files)
    if (type(inserted) is not int or inserted < 0 or
            type(updated) is not int or updated < 0 or inserted + updated != expected):
        raise RuntimeError(f'CMS did not confirm {expected} assets; inspect receipt/readback before retrying')

    print(result)

    return result

add_collection()
```

## Response Format

### Success Response

- **Status Code**: 200 OK
- **Body observed**: `{Success, Message, TotalCount, Result, ErrorMessages}`, with `Result: {insertedCount, updatedCount, existingList}`. Example from the four-asset animated upload:

```json
{
  "Success": true,
  "Message": null,
  "TotalCount": 0,
  "Result": {"insertedCount": 4, "updatedCount": 0, "existingList": []},
  "ErrorMessages": []
}
```

Use the per-result counts to assess asset acceptance. `TotalCount: 0` was also returned for the successful four-insert upload. A success flag alone is insufficient: JSON probes returned the same envelope with both result counts zero. Existing/duplicate handling requires explicit receipt/readback review; these responses do not confirm stored naming, price/currency, app availability or final approval.

### Error Response

- **Status Code**: 4xx or 5xx
- **Body**: JSON object with error message
```json
{
  "message": "Error description here"
}
```

- **400**: observed for `ContentType: super_like`, message `ContentType must be emoji or emoji_reaction.`
- **429**: observed on back-to-back collection uploads with `retryAfterSeconds: 57`. Respect the receiver's cooldown and inspect the prior receipt before a deliberate retry. Mirsal's current worker fails the export rather than scheduling a retry; automatic cooldown recovery remains open.
- A 2xx response with `Success: false` is an application-level refusal.

## Important Notes

1. **File Order**: The order of media files uploaded must match the order of metadata objects in MediaMetadata
2. **File Paths**: Ensure media files exist at the specified paths before making the request
3. **Content Types**: Set appropriate MIME types for media files (e.g., `application/json` for JSON files)
4. **Authentication**: Keep credentials in environment settings, never source or committed receipts. The examples use the Bearer developer key.
5. **Base URL**: The examples default to a local receiver. The app's configured default is `https://emojicms.ehub.ae`; use an explicit environment override for any deliberate live submission.
6. **Verification**: Compare inserted/updated counts with the intended files, then verify the receiving collection when readback is available. Do not turn HTTP 200 into an unconditional delivery-success message.

## Common Use Cases

- Verified live: an animated sticker collection (`test`, four inserted assets).
- Declared but unresolved: JSON emoji reactions, animation presets and super-like representation within the accepted content types.
- Locally verified: saved/override/free/unset collection pricing, exact validation and immutable queued `Price`; live persistence and currency remain unverified.
