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


# Saved nine-slot preset grids (row-major token order). A preset pack claims them in order: the first request takes
# the first unclaimed grid, `generate more` the next (`docs/export to team/mirsal-export-architecture.md` §10).
PRESETS = {
    "core-v1": ["happy", "laugh", "love", "cry", "sad", "angry", "surprised", "scared", "thanks"],
    "social-v1": ["hello", "hug", "kiss", "wink", "shy", "celebrate", "clap", "approve", "disapprove"],
    "reactions-v1": ["think", "confused", "eye-roll", "facepalm", "shrug", "bored", "cool", "flex", "scheme"],
    "daily-v1": ["sleep", "sick", "sneeze", "dance", "plead", "salute", "cheers", "gift", "star-struck"],
}

# Face-only image/video sentences per bank token (emoji-style packs draw faces, never bodies). Same keys and emoji
# as ACTION_BANK; every sentence stays clear of `emotions.LIMB_WORDS`.
FACE_SENTENCES = {
    "happy": ("pure happiness with a bright beaming smile and joyful eyes", "beams brightly, eyes shine with joy, happy sway"),
    "laugh": ("laughing so hard tears of joy fly out, mouth wide open, eyes squeezed shut", "the face shakes with laughter, tears fly, the mouth opens wide"),
    "cry": ("bawling with big streaming tears and a trembling lip", "tears stream in two arcs, the lip quivers, the face crumples"),
    "sad": ("sad and drooping face with a single tear", "sighs, a tear slides down, the face droops lower"),
    "love": ("lovestruck with sparkling eyes, blushing cheeks and a dreamy smile", "eyes sparkle, cheeks flush deeper, dreamy sway"),
    "angry": ("furious and steaming with a deep scowl and flared nostrils", "steam puffs from the head, the face shakes with rage, the scowl deepens"),
    "wink": ("playful wink with one eye closed and a cheeky grin", "winks, the grin tilts, the cheek lifts"),
    "kiss": ("blowing a kiss with a wink, a small heart floating free", "lips purse, a wink, the heart pulses"),
    "surprised": ("surprised with wide round eyes and a small o-shaped mouth", "eyes widen, the mouth forms a small o, quick gasp"),
    "scared": ("terrified and trembling with wide darting eyes", "shivers fast, eyes dart, the face pales"),
    "confused": ("confused with a tilted head, crooked brow and sideways glance", "the head tilts, one brow lifts, eyes glance aside"),
    "think": ("thinking hard, eyes glancing up and to the side, one eyebrow raised", "eyes glance up, the brow furrows then lifts, a slow nod"),
    "eye-roll": ("rolling eyes with a bored deadpan face", "eyes circle slowly, head tilts back with a sigh"),
    "sleep": ("fast asleep with a drool bubble, snoring softly", "eyes stay shut, the bubble inflates and shrinks, gentle drift"),
    "cool": ("wearing sunglasses, smirking, ultra cool", "slow confident head nod, the sunglasses glint"),
    "shy": ("shy with a bashful smile and downcast glancing eyes", "smiles bashfully, eyes glance down and away"),
    "sick": ("sickly with a greenish tint, droopy eyes and a weak frown", "the face pales greenish, eyes droop, weak shiver"),
    "sneeze": ("mid-sneeze with squeezed eyes and a drippy nose", "the face scrunches, bursts into the sneeze, sniffles"),
    "celebrate": ("celebrating with sparkling joyful eyes and a huge party grin", "eyes sparkle, the grin stretches wide, joyful tremble"),
    "clap": ("cheering with a huge congratulatory grin and sparkling eyes", "grins widely, nods along, joyful sway"),
    "approve": ("confident wink with a proud grin", "winks twice, the grin widens, proud nod"),
    "disapprove": ("stern disapproval with a tight frown and narrowed eyes", "frowns firmly, eyes narrow, slow disapproving shake of the head"),
    "thanks": ("grateful smile with eyes closed in thanks and glowing cheeks", "the head bows gently, the smile widens, warm glow"),
    "hello": ("friendly hello with a warm open smile and bright welcoming eyes", "smiles warmly, eyes light up, cheerful tilt"),
    "hug": ("warm loving smile with happy squinted eyes and glowing cheeks", "the face glows, happy squint, gentle tilt side to side"),
    "flex": ("proud smug grin with a confident raised brow", "the smug grin spreads, the brow lifts, confident nod"),
    "scheme": ("scheming grin with wiggling eyebrows", "eyebrows wiggle, the grin widens, sneaky giggle"),
    "facepalm": ("disbelief with squeezed-shut eyes and a deep sigh", "eyes squeeze shut, the head shakes slowly, deep sigh"),
    "shrug": ("clueless sideways glance with a crooked half-smile", "glances side to side, the half-smile tilts, head tilts"),
    "bored": ("bored with half-lowered eyelids and a flat unimpressed mouth", "eyelids droop, the mouth stays flat, slow exhale"),
    "dance": ("pure joy, eyes closed, huge blissful smile, jiggling cheeks", "the face bobs to a beat, cheeks jiggle, blissful sway"),
    "plead": ("huge shiny puppy eyes with a trembling lip, begging please", "eyes shimmer and widen, the lip trembles, hopeful tilt"),
    "salute": ("respectful attention with a chin-up nod and focused eyes", "the chin lifts, eyes lock forward, firm respectful nod"),
    "cheers": ("cheerful toast with a clinking grin and merry crinkled eyes", "grins broadly, eyes crinkle merrily, joyful nod"),
    "gift": ("delighted with wide sparkling eyes and a joyful gasp", "eyes widen and sparkle, happy gasp"),
    "star-struck": ("star-struck with huge starry eyes and an awestruck open smile", "eyes turn starry, the mouth opens in awe"),
}


# Whole-character image/video sentences per bank token, for subjects that are not faces ("teddy bear for school"): "Next batch" takes the next nine
# tokens a session has not used yet, in bank order (`next_tokens`). Same keys and emoji as ACTION_BANK.
BODY_SENTENCES = {
    "happy": ("beaming with happiness, bouncing on the spot with a huge smile", "bounces happily, the smile widens, a little hop"),
    "laugh": ("laughing so hard tears of joy fly out, holding the belly", "doubles over laughing, shoulders shake, wipes a tear"),
    "cry": ("bawling with big streaming tears, rubbing the eyes", "tears stream in two arcs, the body shakes with sobs"),
    "sad": ("sad and slumped, head hanging low, a single tear", "sighs, the shoulders drop, a tear slides down"),
    "love": ("hugging a big red heart, eyes sparkling, blushing", "squeezes the heart, it pulses, sways side to side"),
    "angry": ("furious and stomping, steam puffing from the head, fists clenched", "stomps twice, steam puffs, the scowl deepens"),
    "wink": ("winking playfully with a finger-gun and a cheeky grin", "winks, the finger-gun pops, the grin tilts"),
    "kiss": ("blowing a kiss from the hand, a small heart floating away", "kisses the hand, the heart floats off, a wink"),
    "surprised": ("jumping back in surprise, wide eyes and an open mouth", "jolts back, eyes widen, a quick gasp"),
    "scared": ("terrified and trembling, hiding behind the hands", "shivers fast, peeks between the fingers"),
    "confused": ("confused, scratching the head with a tilted look", "scratches the head, tilts, a question mark pops"),
    "think": ("thinking hard, chin on the hand, eyes glancing up", "taps the chin, eyes glance up, a slow nod"),
    "eye-roll": ("rolling the eyes with crossed arms, unimpressed", "eyes circle, the head tilts back with a sigh"),
    "sleep": ("fast asleep curled up with a drool bubble", "breathes slowly, the bubble inflates and shrinks"),
    "cool": ("wearing sunglasses, leaning back with crossed arms, ultra cool", "slow confident nod, the sunglasses glint"),
    "shy": ("shy, twisting a foot, hands behind the back, blushing", "sways bashfully, glances down, the cheeks flush"),
    "sick": ("sick under a blanket with a thermometer in the mouth", "shivers, the thermometer wobbles, a weak cough"),
    "sneeze": ("mid-sneeze holding a tissue, eyes squeezed shut", "winds up, bursts into the sneeze, sniffles"),
    "celebrate": ("celebrating with a party hat and a popping party popper", "the popper bursts, confetti flies, jumps for joy"),
    "clap": ("clapping enthusiastically with a big proud grin", "claps fast, bounces, the grin widens"),
    "approve": ("giving a confident thumbs up with a wink", "the thumb jabs forward twice, a wink, chest puffs"),
    "disapprove": ("giving a firm thumbs down with a frown", "the thumb points down, the head shakes slowly"),
    "thanks": ("hands pressed together in thanks, a small bow", "bows gently, the smile widens, a warm glow"),
    "hello": ("waving hello with a big friendly smile", "waves the raised hand in wide arcs, a happy bounce"),
    "hug": ("arms wide open, ready for a big warm hug", "opens the arms, squeezes an invisible hug, rocks"),
    "flex": ("flexing a muscle proudly, chest out, huge grin", "the arm flexes and pulses, the chest puffs, a nod"),
    "scheme": ("rubbing the hands together with a scheming grin", "rubs the hands, eyebrows wiggle, a sneaky giggle"),
    "facepalm": ("facepalming in disbelief, one hand over the face", "the hand slaps the face, the head shakes slowly"),
    "shrug": ("shrugging with both palms up and a crooked smile", "the shoulders lift and drop, the palms turn up"),
    "bored": ("bored, slumped with the chin on the hand, half-closed eyes", "eyelids droop, a slow exhale, a tiny yawn"),
    "dance": ("dancing with joyful moves, arms in the air", "shimmies the hips, the arms swing, spins once"),
    "plead": ("pleading with clasped hands and huge shiny puppy eyes", "wrings the hands, eyes shimmer, a hopeful bounce"),
    "salute": ("standing tall and giving a crisp salute", "snaps into the salute, chin up, a firm nod"),
    "cheers": ("raising a glass for a cheerful toast", "lifts the glass, it clinks, a merry nod"),
    "gift": ("holding out a wrapped gift box with a bow, delighted", "offers the box, the bow bounces, a happy gasp"),
    "star-struck": ("star-struck with huge starry eyes, hands on the cheeks", "eyes turn starry, the body wiggles with awe"),
}


def next_tokens(used, n: int = 9) -> list[str]:
    """The first `n` bank tokens (bank order) not in `used`; fewer when the bank runs out (the caller says the bank is complete)."""
    used = set(used or ())
    return [t for t in ACTION_BANK if t not in used][:n]


def token_cells(tokens, face: bool) -> list[tuple]:
    """`(token, label, emoji, motion)` for explicit tokens: face sentences for an emoji-style subject, whole-character sentences otherwise."""
    bank = FACE_SENTENCES if face else BODY_SENTENCES
    return [(t, *bank[t][:1], ACTION_BANK[t]["emoji"], bank[t][1]) for t in tokens]


def preset_name(text: str | None) -> str | None:
    """`core-v1` when the request names it (`core v1`, `core-v1`, …), else None."""
    flat = re.sub(r"[^a-z0-9]+", "", str(text or "").lower())
    for key in PRESETS:
        if re.sub(r"[^a-z0-9]+", "", key) in flat:
            return key
    return None


def preset_cells(preset: str, n: int) -> list[tuple]:
    """The first `n` cells of a preset grid as `(token, face label, emoji, motion)`."""
    if preset not in PRESETS:
        raise ValueError(f"unknown preset {preset}: {sorted(PRESETS)}")
    out = []
    for tok in PRESETS[preset][:n]:
        label, motion = FACE_SENTENCES[tok]
        out.append((tok, label, ACTION_BANK[tok]["emoji"], motion))
    return out
