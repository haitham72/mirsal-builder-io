"""The models a user can pick, and the selections each one offers. Pure data + validation: the UI draws it, the fulfiller (jobs.fulfil) calls
`resolve` to turn a selection into the Higgsfield CLI's job_type and --params. Anything not listed here cannot be requested.
Haitham's standing rules live here: images default to Nano Banana 2 at 2k; animation is always 1080 or more (Kling pro, Grok 1080p), and Kling never offers `4k`."""
from __future__ import annotations

DEFAULT_IMAGE = "nano_banana_flash"
DEFAULT_VIDEO = "kling3_0"


def _opt(name, label, choices, default, hint=""):
    return {"name": name, "label": label, "choices": [str(c) for c in choices], "default": str(default), "hint": hint}


IMAGE = [
    {"id": "nano_banana_flash", "label": "Nano Banana 2", "logo": "google", "default": True,
     "note": "Fast and sharp; Mirsal's default for sheets.",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("resolution", "Resolution", ["1k", "2k", "4k"], "2k")]},
    {"id": "nano_banana_pro", "label": "Nano Banana Pro", "logo": "google",
     "note": "Slower, steadier backgrounds.",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("resolution", "Resolution", ["1k", "2k", "4k"], "2k")]},
    {"id": "nano_banana_2_lite", "label": "Nano Banana 2 Lite", "logo": "google",
     "note": "Cheapest Nano Banana; 1k only.",
     "fixed": {"aspect_ratio": "1:1", "resolution": "1k"}, "options": [_opt("thinking", "Thinking", ["MINIMAL", "HIGH"], "HIGH")]},
    {"id": "gpt_image_2", "label": "GPT Image 2", "logo": "openai",
     "note": "",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("quality", "Quality", ["low", "medium", "high"], "high"),
                                                   _opt("resolution", "Resolution", ["1k", "2k", "4k"], "2k")]},
    {"id": "gpt_image_2_5", "label": "GPT Image 2.5", "logo": "openai",
     "note": "Two variants: flare and sunburst.",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("variant", "Variant", ["flare", "sunburst"], "flare"),
                                                   _opt("quality", "Quality", ["low", "medium", "high", "xhigh", "max"], "medium"),
                                                   _opt("resolution", "Resolution", ["1k", "2k", "4k"], "2k")]},
    {"id": "seedream_v5_pro", "label": "Seedream 5.0 Pro", "logo": "bytedance",
     "note": "",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("resolution", "Resolution", ["1k", "1.5k", "2k"], "2k")]},
    {"id": "seedream_5_0_flash", "label": "Seedream 5.0 Flash", "logo": "bytedance",
     "note": "",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("resolution", "Resolution", ["1k", "1.5k", "2k"], "2k")]},
    {"id": "seedream_v5_lite", "label": "Seedream 5.0 Lite", "logo": "bytedance",
     "note": "",
     "fixed": {"aspect_ratio": "1:1"}, "options": [_opt("quality", "Quality", ["basic", "high"], "high")]},
]

VIDEO = [
    {"id": "kling3_0", "label": "Kling v3.0", "logo": "kuaishou", "default": True, "end_image": True,
     "note": "With Loop on, the start image is also the end image. Always pro: 1440 px for a square sheet (std is 960 px and looks pixelated); the 4k mode is never offered.",
     "fixed": {"aspect_ratio": "1:1", "sound": "off"},
     "options": [_opt("mode", "Quality", ["pro"], "pro", "pro: 1440 px"),
                 _opt("duration", "Seconds", [3, 5], 3)]},
    {"id": "grok_video_v15", "label": "Grok Video 1.5", "logo": "xai", "end_image": False,
     "note": "Starts from the sheet; no end image, so the loop is not guaranteed. Costs several times more than Kling.",
     "fixed": {},
     "options": [_opt("resolution", "Resolution", ["1080p"], "1080p"),
                 _opt("duration", "Seconds", [3, 5], 3)]},
    {"id": "grok_video_v15_lite", "label": "Grok Imagine 1.5 Lite", "logo": "xai", "end_image": False,
     "note": "Haitham's pick (2026-10-08). Starts from the sheet; no end image, so the loop is not guaranteed. Half the price of Grok Video 1.5 (12 credits for 3 s at 1080p), still more than Kling.",
     "fixed": {"aspect_ratio": "1:1"},
     "options": [_opt("resolution", "Resolution", ["1080p"], "1080p"),
                 _opt("duration", "Seconds", [3, 5], 3)]},
]

for _m in IMAGE:
    _m.setdefault("refs", True)        # all eight accept image_references (checked against `model get`, 2026-10-01)
for _m in VIDEO:
    _m.setdefault("refs", False)
KINDS = {"image": IMAGE, "video": VIDEO}


class CatalogError(ValueError):
    pass


_DUMP: dict | None = None          # the full Higgsfield list (higgsfield.load_models), set by the server; None = curated models only
SKIP_PARAMS = {"prompt", "image_references", "video_references", "audio_references", "start_image", "end_image", "mask", "is_inpaint",
               "width", "height", "input_image", "input_images", "medias", "reference_elements", "batch_size", "application", "surface"}


def set_dump(d: dict | None) -> None:
    global _DUMP
    _DUMP = d


def generic(kind: str, d: dict) -> dict:
    """A catalog entry built from a model's own parameter list: every enum parameter becomes a drop-down; the aspect ratio is 1:1 when allowed."""
    fixed, options = {}, []
    names = {p["name"] for p in d.get("params", [])}
    for p in d.get("params", []):
        n, enum = p["name"], p.get("enum")
        if n in SKIP_PARAMS or p.get("type") not in ("string", "integer", "boolean", "string|null"):
            continue
        if n == "aspect_ratio":
            if enum and "1:1" in enum:
                fixed[n] = "1:1"
            continue
        if enum:
            default = p.get("default")
            options.append(_opt(n, n.replace("_", " ").capitalize(), enum, default if default is not None and str(default) in map(str, enum) else enum[0]))
    return {"id": d["job_type"], "label": d.get("display_name") or d["job_type"], "logo": None, "generic": True,
            "end_image": "end_image" in names, "refs": "image_references" in names and kind == "image", "note": "", "fixed": fixed, "options": options}


def more(kind: str) -> list[dict]:
    """Every dumped model of this kind that is not in the curated list."""
    if not _DUMP:
        return []
    have = {m["id"] for m in KINDS[kind]}
    seen, out = set(), []
    for d in _DUMP.get(kind, []):
        if d["job_type"] in have or d["job_type"] in seen or d.get("error"):
            continue
        seen.add(d["job_type"])
        out.append(generic(kind, d))
    return sorted(out, key=lambda m: m["label"].lower())


def catalog() -> dict:
    return {"image": IMAGE, "video": VIDEO, "more": {"image": more("image"), "video": more("video")},
            "defaults": {"image": DEFAULT_IMAGE, "video": DEFAULT_VIDEO}, "full_list": bool(_DUMP),
            "counts": (_DUMP or {}).get("counts", {})}


def find(kind: str, model_id: str | None) -> dict:
    items = KINDS.get(kind)
    if items is None:
        raise CatalogError(f"kind must be image or video, not '{kind}'")
    mid = model_id or (DEFAULT_IMAGE if kind == "image" else DEFAULT_VIDEO)
    m = next((x for x in items if x["id"] == mid), None) or next((x for x in more(kind) if x["id"] == mid), None)
    if not m:
        raise CatalogError(f"'{mid}' is not an available {kind} model")
    return m


def resolve(kind: str, model_id: str | None, options: dict | None = None) -> tuple[str, dict]:
    """(job_type, params) for a selection. Unknown options and values outside the model's choices are refused."""
    m = find(kind, model_id)
    options = dict(options or {})
    params = dict(m["fixed"])
    for o in m["options"]:
        v = str(options.pop(o["name"], o["default"]))
        if v not in o["choices"]:
            raise CatalogError(f"{m['label']}: {o['label'].lower()} '{v}' is not available (choose {', '.join(o['choices'])})")
        params[o["name"]] = v
    if options:
        raise CatalogError(f"{m['label']} has no option '{', '.join(sorted(options))}'")
    return m["id"], params
