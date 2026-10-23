# Add Collection API Documentation

## Overview
This API endpoint allows you to upload a new collection with media files and associated metadata.

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
| Price | string | No | Price of the collection |
| Description | string | Yes | Description of the collection |
| ContentType | string | Yes | Type of content (e.g., "emoji_reaction") |
| ContentSubType | string | Yes | Subtype of content (e.g., "json") |
| Media | File | Yes | Media files (can be multiple) |
| MediaMetadata | JSON string | Yes | Metadata for the media files |

### Media Field
- **Type**: File upload
- **Accepts**: JSON files, videos, images (depending on ContentType)
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

  const credentials = 'your-api-key-here';
  const baseUrl = 'http://localhost:5189';

  const response = await fetch(
    `${baseUrl}/api/v1/Upload/AddCollection`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${credentials}`
      },
      body: formData
    }
  );

  const raw = await response.text();
  const result = JSON.parse(raw);

  console.log(result);

  if (!response.ok) {
    throw new Error(result.message || JSON.stringify(result));
  }

  return result;
}

await addCollection();
```

### Python
```python
import requests
import json

def add_collection():
    url = "http://localhost:5189/api/v1/Upload/AddCollection"
    credentials = "your-api-key-here"

    files = [
        ('Media', ('button_reaction.json', open('./button_reaction.json', 'rb'), 'application/json')),
        ('Media', ('emoji_reaction.json', open('./emoji_reaction.json', 'rb'), 'application/json'))
    ]

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

    response = requests.post(url, files=files, data=data, headers=headers)
    result = response.json()

    print(result)

    if response.status_code != 200:
        raise Exception(result.get('message', str(result)))

    return result

add_collection()
```

## Response Format

### Success Response
- **Status Code**: 200 OK
- **Body**: JSON object with collection details

### Error Response
- **Status Code**: 4xx or 5xx
- **Body**: JSON object with error message
```json
{
  "message": "Error description here"
}
```

## Important Notes

1. **File Order**: The order of media files uploaded must match the order of metadata objects in MediaMetadata
2. **File Paths**: Ensure media files exist at the specified paths before making the request
3. **Content Types**: Set appropriate MIME types for media files (e.g., `application/json` for JSON files)
4. **Authentication**: Replace `your-api-key-here` with your actual API credentials
5. **Base URL**: Update the baseUrl to match your API server address

## Common Use Cases

- Uploading emoji reaction collections
- Creating sticker packs
- Uploading animation presets
- Adding media libraries with metadata
