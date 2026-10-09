# AddCollection API

Creates an emoji collection with animated media files (e.g. `.webm`) and per-file emoji metadata.

## Endpoint

```
POST /api/v1/Upload/AddCollection
Content-Type: multipart/form-data
Authorization: Basic <base64(username:password)>
```

Base URL: `https://emojicms.devinprocess888.com` (local: `http://localhost:5189`)

> Do not set `Content-Type` manually. `fetch` + `FormData` sets it with the correct multipart boundary.

## Request Model (multipart/form-data)

|Field|Type|Required|Repeatable|Description|
|-|-|-|-|-|
|`CollectionName`|string|Yes|No|Display name of the collection|
|`Description`|string|No\*|No|Description of the collection|
|`Media`|file (binary)|Yes|**Yes**|One part per media file. Same field name repeated for each file|
|`MediaMetadata`|string (JSON)|Yes|No|JSON array of metadata objects, one per `Media` file|

\* Sent in the example; adjust if the server enforces it.

### `MediaMetadata` item

```json
{
  "emoji\_utf": "😀",
  "tags": "grinning\_smile\_happy"
}
```

|Field|Type|Description|
|-|-|-|
|`emoji\_utf`|string|The emoji character (UTF) the media represents|
|`tags`|string|Search tags, underscore-separated in the example|

## Critical Rule: Ordering

`Media\[i]` is paired with `MediaMetadata\[i]` **by index**, not by filename.

```
Media #0  happy.webm  <->  MediaMetadata\[0]  { emoji\_utf: "😀", ... }
Media #1  sad.webm    <->  MediaMetadata\[1]  { emoji\_utf: "😂", ... }
```

Rules:

* `MediaMetadata.length` must equal the number of `Media` parts.
* Append `Media` parts in the same order as the metadata array.
* Mismatched count or order will attach wrong emoji/tags to files (or fail validation).

## Example Request (Node.js)

```js
import fs from "fs";

async function addCollection() {
  const formData = new FormData();

  formData.append("CollectionName", "Test Emoji Collection3");
  formData.append("Description", "Test emoji collection3");

  // Media files - order must match MediaMetadata
  formData.append(
    "Media",
    new Blob(\[fs.readFileSync("./happy.webm")], { type: "video/webm" }),
    "happy.webm"
  );
  formData.append(
    "Media",
    new Blob(\[fs.readFileSync("./sad.webm")], { type: "video/webm" }),
    "sad.webm"
  );

  formData.append(
    "MediaMetadata",
    JSON.stringify(\[
      { emoji\_utf: "😀", tags: "grinning\_smile\_happy" },
      { emoji\_utf: "😂", tags: "laugh\_funny\_joy" }
    ])
  );

  const credentials = process.env.COLLECTION_API_CREDENTIALS; // base64(username:password), never hardcoded

  const baseUrl = "https://emojicms.devinprocess.com";

  const response = await fetch(`${baseUrl}/api/v1/Upload/AddCollection`, {
    method: "POST",
    headers: { Authorization: `Basic ${credentials}` },
    body: formData
  });

  // Read the body once as text, then parse
  const raw = await response.text();
  const result = JSON.parse(raw);

  if (!response.ok) throw new Error(result.message || JSON.stringify(result));

  console.log(result);
}

await addCollection();
```

## Authentication

HTTP Basic: `Authorization: Basic base64("username:password")`.

Load credentials from environment variables or a secret store. Do not hardcode them in source or commit them.

## Responses

|Status|Body|Meaning|
|-|-|-|
|2xx|JSON (created collection)|Collection created|
|non-2xx|JSON, with `message` field if available|Validation / auth / server error|

The client reads the body with `response.text()` and then `JSON.parse`. `JSON.parse` throws if the server returns a non-JSON body (e.g. an HTML error page), so wrap it in `try/catch` if you need the raw text. On failure it reads `result.message` and falls back to the full JSON body. The exact success schema is not defined by the client call. Document it from the server DTO.

## Server-side Model (ASP.NET, inferred from the request)

```csharp
public class AddCollectionRequest
{
    public string CollectionName { get; set; } = default!;
    public string? Description { get; set; }
    public List<IFormFile> Media { get; set; } = new();
    public string MediaMetadata { get; set; } = default!; // JSON string
}

public class MediaMetadataItem
{
    \[JsonPropertyName("emoji\_utf")] public string EmojiUtf { get; set; } = default!;
    \[JsonPropertyName("tags")]      public string Tags { get; set; } = default!;
}
```

Controller binding: `\[FromForm] AddCollectionRequest request`, then deserialize `MediaMetadata` into `List<MediaMetadataItem>` and validate `Media.Count == metadata.Count`.

## Checklist

* \[ ] `Media` repeated once per file
* \[ ] `MediaMetadata` is a JSON **string** (stringified array)
* \[ ] Counts and order match between `Media` and `MediaMetadata`
* \[ ] Correct MIME type per file (`video/webm`)
* \[ ] `Authorization` header present; no manual `Content-Type`

