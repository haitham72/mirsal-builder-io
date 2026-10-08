"""The canonical action bank for export tags (`docs/export to team/mirsal-export-architecture.md` §6): 36 tokens, each with a
primary emoji and aliases. `canonical_for` maps a sticker's key/tags onto one token (+ its aliases) for the filename's
`multi_action_tag`; unknown words stay unresolved (`None`: the exporter picks from the bank, nothing is guessed).
`fallback_tag` builds a deterministic search-friendly token from free text when nothing maps.

Pure: stdlib only (the engine never imports this; rule 3)."""
from __future__ import annotations

import re

# token -> {"emoji": primary glyph, "aliases": [single-token spellings]}
ACTION_BANK: dict[str, dict] = {
    "happy": {"emoji": "😀", "aliases": ["smile", "joy"]},
    "laugh": {"emoji": "🤣", "aliases": ["laughing", "lol", "rofl", "lmao", "lmfao"]},
    "cry": {"emoji": "😭", "aliases": ["crying", "sobbing", "tears"]},
    "sad": {"emoji": "😔", "aliases": ["unhappy", "disappointed"]},
    "love": {"emoji": "😍", "aliases": ["heart", "loving"]},
    "angry": {"emoji": "😠", "aliases": ["mad", "furious", "rage"]},
    "wink": {"emoji": "😉", "aliases": ["winking"]},
    "kiss": {"emoji": "😘", "aliases": ["kissing"]},
    "surprised": {"emoji": "😮", "aliases": ["shocked", "wow"]},
    "scared": {"emoji": "😱", "aliases": ["frightened", "fear"]},
    "confused": {"emoji": "😕", "aliases": ["puzzled"]},
    "think": {"emoji": "🤔", "aliases": ["thinking"]},
    "eye-roll": {"emoji": "🙄", "aliases": ["eyeroll"]},
    "sleep": {"emoji": "😴", "aliases": ["sleepy"]},
    "cool": {"emoji": "😎", "aliases": ["sunglasses"]},
    "shy": {"emoji": "😊", "aliases": ["bashful", "blushing"]},
    "sick": {"emoji": "🤒", "aliases": ["ill"]},
    "sneeze": {"emoji": "🤧", "aliases": ["sneezing"]},
    "celebrate": {"emoji": "🥳", "aliases": ["party"]},
    "clap": {"emoji": "👏", "aliases": ["applause"]},
    "approve": {"emoji": "👍", "aliases": ["okay", "yes", "thumbsup"]},
    "disapprove": {"emoji": "👎", "aliases": ["reject", "no"]},
    "thanks": {"emoji": "🙏", "aliases": ["thankyou"]},
    "hello": {"emoji": "👋", "aliases": ["wave", "hi"]},
    "hug": {"emoji": "🤗", "aliases": ["openarms"]},
    "flex": {"emoji": "💪", "aliases": ["flexing"]},
    "scheme": {"emoji": "😏", "aliases": ["scheming"]},
    "facepalm": {"emoji": "🤦", "aliases": ["facepalm"]},
    "shrug": {"emoji": "🤷", "aliases": ["dunno"]},
    "bored": {"emoji": "😑", "aliases": ["unimpressed"]},
    "dance": {"emoji": "🕺", "aliases": ["dancing"]},
    "plead": {"emoji": "🥺", "aliases": ["begging", "please"]},
    "salute": {"emoji": "🫡", "aliases": ["saluting", "respect"]},
    "cheers": {"emoji": "🍻", "aliases": ["toast"]},
    "gift": {"emoji": "🎁", "aliases": ["present", "surprise"]},
    "star-struck": {"emoji": "🤩", "aliases": ["starstruck", "amazed"]},
}


def _flat(word: str) -> str:
    """One lookup spelling: lowercase alphanumerics only (`thank_you`, `thank-you`, `thank you` -> `thankyou`)."""
    return re.sub(r"[^a-z0-9]+", "", str(word or "").lower())


_ALIAS_TO_TOKEN = {"facepalm": "facepalm"}
for _tok, _row in ACTION_BANK.items():
    _ALIAS_TO_TOKEN.setdefault(_flat(_tok), _tok)
    for _al in _row["aliases"]:
        _ALIAS_TO_TOKEN.setdefault(_flat(_al), _tok)


def _candidates(key: str | None, tags: list | tuple | None) -> list[str]:
    """Lookup spellings in a fixed order: the whole key, each tag whole, then every word of both."""
    words: list[str] = []
    for blob in [key, *list(tags or [])]:
        flat = _flat(blob)
        if flat:
            words.append(flat)
        words.extend(_flat(w) for w in re.split(r"[^a-z0-9]+", str(blob or "").lower()) if _flat(w))
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def canonical_for(key: str | None, tags: list | tuple | None = None) -> tuple[str, list[str]] | None:
    """`(token, aliases)` for the first bank hit, or `None` when nothing maps (unresolved: a human picks)."""
    for w in _candidates(key, tags):
        tok = _ALIAS_TO_TOKEN.get(w)
        if tok:
            return tok, list(ACTION_BANK[tok]["aliases"])
    return None


def fallback_tag(key: str | None = None, tags: list | tuple | None = None, exclude: list | tuple | None = None) -> str:
    """A deterministic tag segment when nothing maps: the tags joined (they are the curated search words),
    else the key's words, else `sticker`. Subject/pack words (`exclude`) are stripped and repeats collapsed, so
    `generic_emojis_grumpy` + `[grumpy, arms, crossed]` becomes `grumpy_arms_crossed`, never
    `generic_emojis_grumpy_grumpy_arms_crossed`. Each word is lowercase alphanumerics, joined with `_`."""
    words = []
    for t in (list(tags) if tags else [key]):
        words.extend(w for w in re.split(r"[^a-z0-9]+", str(t or "").lower()) if w)
    banned: set[str] = set()
    for t in (list(exclude) if exclude else []):
        banned.update(w for w in re.split(r"[^a-z0-9]+", str(t or "").lower()) if w)
    seen, out, plain, pseen = set(), [], [], set()
    for w in words:
        if w not in pseen:
            pseen.add(w)
            plain.append(w)
        if w not in banned and w not in seen:
            seen.add(w)
            out.append(w)
    return "_".join(out or plain) or "sticker"
