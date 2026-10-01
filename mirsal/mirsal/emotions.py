"""A wide bank of expressive emotions for the built-in (no-AI) sets. Every entry is (key suffix, label, emoji, motion):
the label is the expression plus body language the image model draws; the motion is what the video model animates.
`pick` chooses one entry per mood group, deterministically from the request text, so the same request always gives the same
nine, different requests give different mixes, and a sheet never repeats a mood."""
from __future__ import annotations

import hashlib

GROUPS = {
    "greet": [
        ("waving", "waving hello with a big happy grin", "👋", "waves the raised hand in wide arcs while bouncing on tiptoes"),
        ("blowing_a_kiss", "blowing a kiss with a wink, a small heart floating away", "😘", "kisses the air, the heart floats off, a playful wink"),
        ("open_arms", "arms wide open, ready for a big hug, warm smile", "🤗", "leans in with open arms, rocks side to side, squeezes an invisible hug"),
    ],
    "joy": [
        ("laughing", "laughing so hard tears of joy fly out, mouth wide open", "😂", "doubles over, shoulders shaking, tiny hops, wipes a tear"),
        ("excited", "bursting with excitement, star-sparkle eyes, fists shaking", "🤩", "vibrates with joy, jumps up and down, claps"),
        ("dancing", "dancing with joyful moves, eyes closed, big smile", "💃", "shimmies the hips, arms swing, spins once"),
    ],
    "love": [
        ("in_love", "hugging a big red heart, eyes sparkling, blushing cheeks", "😍", "the heart pulses, sways side to side, squeezes the heart"),
        ("puppy_eyes", "huge shiny puppy eyes, hands clasped, begging please", "🥺", "wrings the hands, eyes shimmer, small hopeful bounce"),
        ("thank_you", "hands pressed together in thanks, eyes closed, grateful smile", "🙏", "bows slightly, gentle sway, smile widens"),
    ],
    "approve": [
        ("thumbs_up", "winking and giving a confident thumbs up", "👍", "thumb jabs forward twice, a wink, proud chest puff"),
        ("flexing", "flexing a muscle proudly, chest out, huge grin", "💪", "the arm flexes and pulses, chest puffs, nods"),
        ("winner", "holding a golden trophy overhead, triumphant", "🏆", "lifts the trophy, it shines, jumps with joy"),
        ("ok_sign", "making an OK sign with a cheerful squint", "👌", "bobs the hand, nods approvingly, tilts the head"),
    ],
    "doubt": [
        ("thinking", "thinking hard, chin in hand, one eyebrow raised", "🤔", "taps the chin, eyes glance up and to the side, a slow nod"),
        ("shrugging", "shrugging with open palms and a clueless face", "🤷", "shoulders rise and fall, head tilts, palms turn up"),
        ("eye_roll", "rolling eyes with a bored deadpan face", "🙄", "eyes circle slowly, head tilts back with a sigh"),
    ],
    "sad": [
        ("crying", "bawling with big streaming tears and a trembling lip", "😭", "sobs with heaving shoulders, tears stream in two arcs"),
        ("sad", "sad and drooping, a single tear, slumped shoulders", "😞", "sighs, shoulders sag, droops slowly lower"),
        ("sneezing", "mid-sneeze with a tissue, watery eyes", "🤧", "head tips back, bursts forward with the sneeze, sniffles"),
    ],
    "anger": [
        ("angry", "furious, steaming, fists clenched, deep scowl", "😡", "stomps in place, steam puffs from the head, body shakes with rage"),
        ("facepalm", "facepalming in disbelief, eyes closed, sighing", "🤦", "slowly drops the face into the palm, shakes the head"),
        ("grumpy", "grumpy with arms crossed, pouting, turned slightly away", "😤", "huffs, taps a foot, puffs the cheeks"),
    ],
    "shock": [
        ("shocked", "shocked, jaw dropped, eyes huge, hands on cheeks", "😱", "recoils with a jolt, trembles, hands slam onto the cheeks"),
        ("scared", "terrified, trembling, peeking through hands, wide eyes", "😨", "shivers fast, knees knock, cowers lower"),
        ("mind_blown", "mind blown, hands on the head, eyes spiralling wide", "🤯", "hands fly off the head as it bursts into sparks"),
        ("dizzy", "dizzy with spiral eyes, wobbling on the spot", "😵‍💫", "sways in circles, little stars orbit the head"),
    ],
    "chill": [
        ("cool", "wearing sunglasses, smirking, arms crossed, ultra cool", "😎", "slow confident head nod, the sunglasses glint"),
        ("sleeping", "fast asleep sitting up, drool bubble, snoring", "😴", "head nods down and jerks up, the bubble inflates and shrinks"),
        ("embarrassed", "embarrassed and blushing, hiding the face behind paws, peeking", "😳", "shy sway, peeks through the fingers then hides again"),
        ("scheming", "scheming grin, rubbing hands together, eyebrows wiggling", "😏", "rubs the hands, eyebrows wiggle, sneaky giggle"),
        ("hungry", "drooling with a fork and knife, wide hungry eyes", "🤤", "licks the lips, drool drips, utensils tap the table"),
        ("yawning", "yawning widely, sleepy eyes, stretching the arms up", "🥱", "stretches up, big yawn, shudders and settles"),
    ],
}
ORDER9 = ["greet", "joy", "love", "approve", "doubt", "sad", "anger", "shock", "chill"]
ORDER4 = ["joy", "sad", "anger", "shock"]


def _seed(text: str) -> int:
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest(), 16)


def pick(n: int, seed_text: str = "") -> list[tuple]:
    """n entries, one per mood group (9 and 4 use fixed group orders; other n cycle the groups), deterministic in `seed_text`."""
    s = _seed(seed_text)
    order = ORDER9 if n >= 9 else ORDER4 if n >= 4 else ["joy"]
    out = []
    for i in range(n):
        g = order[i % len(order)]
        items = GROUPS[g]
        out.append(items[(s >> (i * 3)) % len(items)] if i < len(order) else items[((s >> (i * 3)) + 1) % len(items)])
    return out


def moods() -> int:
    return sum(len(v) for v in GROUPS.values())
