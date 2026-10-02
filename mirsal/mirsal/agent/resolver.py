"""Intent rules and the reference resolver. DETERMINISTIC FIRST: regex and rules handle numbers, `#3`, ordinals, lists ("2 and 7"),
exclusions ("but not 3 and 4"), explicit ids (`G012/S3`), "it / that one" (the focus), "previous" (the parent in THIS branch, not the
highest id) and a semantic word match against the focused generation's names ("the shocked one"). Only what these cannot settle goes
to the model (agent/graph.py), and a clear mapping is never turned into a question.

Priority: explicit id > the UI selection > a number > a semantic concept > the current focus > the most recent generation.
Ambiguity: when two candidates are equally plausible, ask ONE short question; when the mapping is clear, never ask."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9,
            "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5, "6th": 6, "7th": 7, "8th": 8, "9th": 9}
CARDINALS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
STOP = set("the a an of that this these those one ones which is are was it its them make made more less very just to for with and or in on "
           "sticker stickers number show me you i my please can could would like want".split())
POS = r"(?:like|love|liked|loved|keep|prefer|good|great|nice|perfect|awesome|favou?rite|best)"
NEG = r"(?:hate|hated|dislike|disliked|don'?t like|do not like|dont like|not|no|bad|ugly|worst|remove|drop|ditch|skip|except|without)"
ROLES = {"style": "STYLE", "pose": "POSE", "expression": "EXPRESSION", "face": "EXPRESSION", "colour": "COLOR", "color": "COLOR",
         "composition": "COMPOSITION", "subject": "SUBJECT", "character": "SUBJECT", "animation": "ANIMATION", "motion": "ANIMATION"}


@dataclass
class Resolution:
    stickers: list = field(default_factory=list)       # ['G012/S3', ...]
    positive: list = field(default_factory=list)
    negative: list = field(default_factory=list)
    generation: str | None = None
    references: list = field(default_factory=list)     # [{'source': 'G012/S2', 'target': 'G012/S5', 'role': 'STYLE'}]
    needs_clarification: bool = False
    clarification: str = ""
    options: list = field(default_factory=list)
    how: str = ""                                      # which rule settled it (shown in the step trace)

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def _gid(n) -> str:
    return f"G{int(n):03d}"


def _numbers(clause: str, n: int) -> list:
    """The sticker numbers named in a clause: digits, `#3`, `number three`, ordinals, `last`, ranges. Grid sizes (3x3) are not numbers."""
    c = re.sub(r"\b\d+\s*x\s*\d+\b", " ", clause.lower())
    c = re.sub(r"\bg\d{1,4}\s*/?\s*s(\d)", r" \1 ", c)                 # G12/S3 -> 3
    c = re.sub(r"\bs(\d)\b", r" \1 ", c)                                # S3 -> 3
    before_last = bool(re.search(r"\b(?:second to last|2nd to last|next to last|one before (?:the )?last|before (?:the )?last)\b", c))
    c = re.sub(r"\b(?:second to last|2nd to last|next to last|one before (?:the )?last|before (?:the )?last)\b", " ", c)
    last_sticker = bool(re.search(r"\blast\s+(?:one|sticker|stickers|image|picture|pic|cell|card|tile)\b|^\s*(?:the\s+)?last\s*$", c))          # "last guy", "the last batch", "the last change" are not sticker 9
    c = re.sub(r"\blast\b", " ", c)
    found = []
    for m in re.finditer(r"(\d+)\s*(?:-|to|through)\s*(\d+)", c):          # 3-5, 3 to 5
        a, b = int(m[1]), int(m[2])
        if 1 <= a <= b <= n:
            found += list(range(a, b + 1))
    c = re.sub(r"(\d+)\s*(?:-|to|through)\s*(\d+)", " ", c)
    for tok in re.finditer(r"(?<![\w.])#?(\d+)(?:st|nd|rd|th)?\b|\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)\b|\b(last)\b"
                           r"|(?:number|no\.?|sticker|#)\s*(one|two|three|four|five|six|seven|eight|nine)\b", c):
        if tok[1]:
            v = int(tok[1])
        elif tok[2]:
            v = ORDINALS[tok[2]]
        elif tok[3]:
            v = n
        else:
            v = CARDINALS[tok[4]]
        if 1 <= v <= n:
            found.append(v)
    if last_sticker and n not in found:
        found.append(n)
    if before_last and n > 1 and (n - 1) not in found:
        found.append(n - 1)
    return list(dict.fromkeys(found))


def _semantic(text: str, stickers: list) -> list:
    """Stickers whose key / name / tags share the user's content words ('the shocked one' -> *_shocked_*). Unique top score or nothing."""
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2]
    if not words:
        return []
    scored = []
    for s in stickers:
        hay = set(re.findall(r"[a-z]+", " ".join([s.get("key", ""), s.get("name", "")] + list(s.get("tags") or [])).lower()))
        stem = {h[:5] for h in hay}
        sc = sum(1 for w in words if w in hay or w[:5] in stem)
        if sc:
            scored.append((sc, s["index"]))
    if not scored:
        return []
    scored.sort(reverse=True)
    top = sorted(i for sc, i in scored if sc == scored[0][0])
    return top if len(top) <= 3 else []


def resolve(text: str, ctx: dict) -> Resolution:
    """ctx: {generation: 'G012'|None, n: sticker count, stickers: [{index,key,name,tags}], focus_stickers: ['G012/S3'], selected: ['G012/S3'],
    parent: 'G011'|None, latest: 'G013'|None, known: {'G012': n_stickers}}."""
    r = Resolution()
    t = text.strip()
    low = t.lower()
    gen = ctx.get("generation")
    n = int(ctx.get("n") or 9)
    known = ctx.get("known") or {}

    # 1. explicit ids: G012/S3, G12 S3, S3 of G12
    ex = [(f"G{int(m[1]):03d}", int(m[2])) for m in re.finditer(r"\bg0*(\d{1,4})\s*/?\s*s(\d)\b", low)]
    ex += [(f"G{int(m[2]):03d}", int(m[1])) for m in re.finditer(r"\bs(\d)\s+of\s+g0*(\d{1,4})\b", low)]
    if ex:
        r.stickers = [f"{g}/S{i}" for g, i in dict.fromkeys(ex)]
        r.generation = r.stickers[0].split("/")[0]
        r.how = "explicit id"
    else:
        g_only = re.search(r"\bg0*(\d{1,4})\b", low)
        if g_only and f"G{int(g_only[1]):03d}" in known:
            r.generation = f"G{int(g_only[1]):03d}"
            r.how = "explicit generation"

    base = r.generation or gen
    base_n = int(known.get(base, n)) if base else n

    # 2. "make 5 like 2" and "the style from 2 and the pose from 7"
    m = re.search(r"\b(?:make|turn|redo|do)\s+(?:number\s+|#)?(\d)\s+(?:look\s+)?(?:like|match|the same as|similar to)\s+(?:number\s+|#)?(\d)\b", low)
    if m and base:
        r.references = [{"source": f"{base}/S{m[2]}", "target": f"{base}/S{m[1]}", "role": "STYLE"}]
        r.stickers = [f"{base}/S{m[1]}"]
        r.generation, r.how = base, "make A like B"
    for m in re.finditer(r"\b(style|pose|expression|face|colou?r|composition|subject|character|animation|motion)\s+(?:from|of)\s+(?:the\s+)?(?:number\s+|#)?(\d|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|last)\b", low):
        num = _numbers(m[2], base_n)
        if num and base:
            r.references.append({"source": f"{base}/S{num[0]}", "target": None, "role": ROLES[m[1]]})
            r.how = r.how or "role references"

    # 3. polarity by clause: "I like 2 and 7 but not 3 and 4"
    if base and not ex:
        pos, neg = [], []
        cur = None
        for clause in re.split(r"\bbut\b|;|\.|,\s*(?=(?:not|no|i hate|i don'?t)\b)", low):
            has_neg = re.search(rf"\b{NEG}\b", clause)
            has_pos = re.search(rf"\b{POS}\b", clause) and not re.search(r"\b(?:don'?t|do not|dont|not)\s+" + POS, clause)
            cur = "neg" if has_neg and not has_pos else "pos" if has_pos else cur
            nums = _numbers(clause, base_n)
            if nums and cur:
                (neg if cur == "neg" else pos).extend(f"{base}/S{i}" for i in nums)
        r.positive, r.negative = list(dict.fromkeys(pos)), list(dict.fromkeys(neg))
        if (pos or neg) and not r.stickers:
            r.stickers = list(dict.fromkeys(pos + neg))
            r.how = r.how or "feedback clauses"

    # 4. plain numbers ("make number 3 happier", "animate 2 and 5")
    if base and not r.stickers:
        nums = _numbers(low, base_n)
        if nums:
            r.stickers = [f"{base}/S{i}" for i in nums]
            r.how = "number"
    # 5. the UI selection
    if not r.stickers and ctx.get("selected") and re.search(r"\b(these|this|those|selected|them|it)\b", low):
        r.stickers = list(ctx["selected"])
        r.how = "selection"
    if not r.stickers and ctx.get("selected") and not _numbers(low, base_n):
        r.stickers = list(ctx["selected"])
        r.how = "selection"
    # 6. a semantic concept ("the shocked one")
    if base and not r.stickers:
        hit = _semantic(re.sub(r"\b(make|animate|redo|regenerate|which|what)\b", " ", low), ctx.get("stickers") or [])
        if len(hit) == 1:
            r.stickers = [f"{base}/S{hit[0]}"]
            r.how = "concept"
        elif len(hit) > 1:
            r.needs_clarification = True
            r.options = [f"{base}/S{i}" for i in hit]
            r.clarification = "Which one: " + ", ".join(f"#{i}" for i in hit) + "?"
    # 7. "it / that one" -> the focus
    if not r.stickers and not r.needs_clarification and re.search(r"\b(it|that|this)(?:\s+one)?\b", low) and ctx.get("focus_stickers"):
        r.stickers = list(ctx["focus_stickers"])[:1]
        r.how = "focus"
    # 8. "the previous one" = the parent generation in this branch
    if re.search(r"\b(previous|prior|before|earlier|original|old(?:er)?)\s+(?:one|version|batch|generation|set|pass)\b|\bgo back\b", low) \
            and ctx.get("parent") and not r.generation:
        r.generation = ctx["parent"]
        r.how = r.how or "previous in branch"
    if not r.generation and r.stickers:
        r.generation = r.stickers[0].split("/")[0]
    if not r.generation:
        r.generation = gen or ctx.get("latest")
    return r


def polarity_of(text: str) -> str | None:
    """'NEGATIVE' / 'POSITIVE' / None for a whole message ("this is bad", "I like this one"), the same words and the same negation rule as the clause
    reader in `resolve`. Used when the stickers were found by the selection or the focus, so no number sat beside the opinion."""
    low = text.lower()
    neg = re.search(rf"\b{NEG}\b", low)
    pos = re.search(rf"\b{POS}\b", low) and not re.search(r"\b(?:don'?t|do not|dont|not)\s+" + POS, low)
    return "NEGATIVE" if neg and not pos else "POSITIVE" if pos else None


_ANSWER_FILLER = {"number", "no", "nr", "sticker", "stickers", "and", "the", "one", "ones", "please", "just", "only", "also", "plus", "it", "is", "its",
                  "this", "that", "these", "those", "them", "selected", "mean", "meant", "i", "it's"}
_ANSWER_PRONOUNS = {"this", "that", "these", "those", "them", "it", "selected"}
_NUMBERISH = re.compile(r"#?\d+(?:st|nd|rd|th)?|s\d|g\d+|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|last|two|three|four|five|six|seven|eight|nine")


def is_sticker_answer(text: str, has_selection: bool = False) -> bool:
    """True when the message is only a "which sticker" answer: numbers, ordinals, `#3`, `number three`, or (with stickers selected) "this one" / "these".
    Anything with another content word ("make me a falcon") is a request of its own, never an answer."""
    words = re.findall(r"[a-z0-9#']+", text.lower())
    if not words or len(words) > 8:
        return False
    if not all(w in _ANSWER_FILLER or _NUMBERISH.fullmatch(w) for w in words):
        return False
    return any(_NUMBERISH.fullmatch(w) for w in words) or (has_selection and any(w in _ANSWER_PRONOUNS for w in words))


DESCRIBE = (r"\b(?:describe|caption|captions|transcribe)\b|\bwhat(?:'s| is| are)?\s+(?:in|on|visible|shown)\b|\bwhat do\b.{0,40}\b(?:show|look like|depict)\b|\blook at\b")
"""A request to LOOK at the pictures ("describe the stickers", "what do they show", "what is in number 3"): it needs AI vision, so it needs the person's yes (vision/consent.py)."""


# ---- intent rules ---------------------------------------------------------------------------------------------------------------
# A go-ahead is a WHOLE message from a short closed list (audit 2026-10-02: the first word alone was enough, so "create a dragon pack", "yes make it red" and "start over" spent the OLD plan).
YES_PHRASES = ("yes please", "go ahead", "do it", "create it", "generate it", "let's go", "lets go", "make it", "looks good", "sounds good", "yes", "yep", "yeah", "yup", "ya", "y", "ok", "okay", "sure",
               "go", "create", "generate", "confirm", "start", "perfect", "great", "nice", "please", "yalla", "👍", "✅", "ايوه", "أيوه", "نعم", "تمام", "ماشي", "اوكي", "أوكي", "ايه", "إيه", "tamam", "aywa", "aiwa", "naam")
NO_PHRASES = ("no thanks", "no thank you", "not now", "never mind", "nevermind", "no", "nope", "nah", "na", "n", "cancel", "stop", "don't", "dont", "لا", "لأ", "مش دلوقتي", "خلاص", "👎", "❌", "la", "laa")


def _closed(text: str, phrases) -> bool:
    """True when the whole message is made only of phrases of the list (at most 4 of them), punctuation aside."""
    s = re.sub(r"[\s,.!?؟،]+", " ", text.strip().lower()).strip()
    if not s or len(s.split()) > 6:
        return False
    for _ in range(4):
        for ph in sorted(phrases, key=len, reverse=True):
            if s == ph:
                return True
            if s.startswith(ph + " "):
                s = s[len(ph) + 1:]
                break
        else:
            return False
    return not s


def is_yes(text: str) -> bool:
    return _closed(text, YES_PHRASES)


def is_no(text: str) -> bool:
    return _closed(text, NO_PHRASES)


ACK_STRONG = {"ok", "okay", "nice", "cool", "great", "thanks", "thank", "thx", "ty", "cheers", "lol", "haha", "wow", "awesome", "amazing", "good", "fine", "alright", "noted", "gotcha", "understood", "k", "kk",
              "sweet", "brilliant", "neat", "yay", "shukran", "شكرا", "👍", "🙏", "❤️", "😊", "🙌", "👌", "😂", "🔥", "perfect", "lovely"}
ACK_FILL = {"you", "so", "much", "very", "bro", "mate", "man", "dude", "for", "that", "this", "it", "all", "your", "help", "the", "a", "lot", "many", "is", "was", "really", "got", "appreciate", "thank", "again", "sir", "boss"}


def is_ack(text: str) -> bool:
    """An acknowledgement ("ok", "nice", "thanks bro", "okay cool", "thank you so much for that", "👍"): there is nothing to make or change, and it must never become a plan."""
    words = re.findall(r"[^\W\d_]+(?:'[a-z]+)?|[^\w\s]", text.lower())
    words = [w for w in words if w not in ("!", ".", ",", "?", "…")]
    return bool(words) and len(words) <= 7 and any(w in ACK_STRONG for w in words) and all(w in ACK_STRONG or w in ACK_FILL for w in words)


def smalltalk_kind(text: str) -> str:
    """Which small talk it is, so the answer fits: thanks | bye | ack | hello."""
    low = text.lower()
    if re.search(r"\b(thanks|thank|thx|ty|cheers|shukran)\b|شكرا", low):
        return "thanks"
    if re.search(r"\b(bye|goodbye|see you|cya)\b", low):
        return "bye"
    if is_ack(text) and not re.search(r"\b(hi|hello|hey|hola|salam|marhaba)\b", low):
        return "ack"
    return "hello"
PRON = r"(?:the|that|this|it|them|these|those|him|her|he|she|they|everyone|everything|all of them|all (?:the )?stickers|the (?:guy|man|woman|girl|boy|character|dude|lady|bird|cat|dog))"
WEARISH = r"\b(?:wear|wearing|wears|put on|hold|holding|carry|carrying|ride|riding|eat|eating|drink|drinking|become|turn into|look like|looks like|have|has|hat|coat|jacket|glasses|sunglasses|cape|crown|scarf|shoes|mask|beard)\b"
COLOURS = r"\b(?:red|blue|green|yellow|pink|purple|orange|black|white|brown|gold|golden|silver|dark|light|pastel|neon)\b"
COMPARATIVE = r"\b(?:\w+er|more|less|bigger|smaller|happier|sadder|funnier|cuter|bolder|brighter|softer|rounder|different|livelier)\b"
NEW_VERBS = r"\b(make|create|generate|give|draw|design|build|i want|i need|i'd like|can you make|stickers? (?:of|for|with)|pack of|set of)\b"


GREETING_WORDS = ("hi", "hiya", "hii", "hello", "hallo", "hey", "heya", "hola", "yo", "sup", "howdy", "salam", "salaam", "marhaba", "mrhba", "ahlan", "ahla", "thanks", "thank", "thx", "ty",
                  "cheers", "bye", "goodbye", "morning", "evening", "afternoon", "night", "good", "there", "again", "everyone", "all", "how", "are", "you", "whats", "what's", "up",
                  "assistant", "bot", "mirsal", "so", "much", "very", "a", "lot", "many", "morning", "ok", "okay", "cool", "great", "nice", "lovely", "awesome", "perfect", "welcome", "pleased", "meet",
                  "مرحبا", "اهلا", "أهلا", "السلام", "عليكم", "شكرا", "هلا")
GREETING_STARTERS = ("hi", "hiya", "hello", "hallo", "hey", "heya", "hola", "yo", "sup", "howdy", "salam", "salaam", "marhaba", "ahlan", "thanks", "thank", "thx", "good", "bye", "goodbye", "cheers",
                     "how", "whats", "what's", "مرحبا", "اهلا", "أهلا", "السلام", "شكرا", "هلا")


def is_smalltalk(text: str) -> bool:
    """A greeting or a thank-you ("hi", "hellow", "heyy there", "good morning", "thanks!", "salam", "how are you"), typos included. At most 5 words, every one of them a
    greeting word (or within one slip of one), and the first a greeting starter: "hello kitty" (a subject) and "hi, make me a falcon" (a request) are not small talk."""
    import difflib
    words = re.findall(r"[^\W\d_]+(?:'[a-z]+)?", text.lower())
    if not words or len(words) > 5:
        return False

    def near(w, pool):
        short = re.sub(r"(.)\1+", r"\1", w)                      # heyyyy -> hey, hii -> hi, hellooo -> helo
        if w in pool or short in pool:
            return True
        return any(len(c) >= 5 and len(w) >= 5 and difflib.SequenceMatcher(None, c, w).ratio() >= 0.8 for c in pool) or             any(len(c) >= 5 and len(short) >= 4 and difflib.SequenceMatcher(None, re.sub(r"(.)\1+", r"\1", c), short).ratio() >= 0.85 for c in pool)
    return near(words[0], GREETING_STARTERS) and all(near(w, GREETING_WORDS) for w in words) and "kitty" not in words


NAMES_RX = (r"\b(?:rename|re-name|better names?|new names?|nicer names?|suggest (?:some |better )?names?|propose (?:some |better )?names?|check (?:the |their )?names?"
            r"|name (?:them|these|the stickers|each)|give (?:them|these|the stickers) (?:new |better )?names?)\b")
"""A request to look at the pictures and propose better names ("suggest better names", "rename them"): it needs AI vision, so it needs the person's yes like a description does."""


def classify(text: str, has_pending: bool, has_generation: bool, has_selection: bool = False) -> tuple[list, float]:
    """Intents in order of importance, with a confidence. Below 0.6 the graph asks the model to classify."""
    t = text.strip().lower()
    if not t:
        return ["AMBIGUOUS"], 0.0
    if has_pending and is_yes(t):
        return ["CONFIRM"], 0.95
    if has_pending and is_no(t):
        return ["CANCEL"], 0.95
    polite = re.match(r"^(?:please\s+)?(?:can|could|would|will) you\s+(?:please\s+)?(.*?)\s*\??$", t)
    if polite and re.match(r"^(?:make|create|generate|give|draw|design|build|redo|regenerate|change|fix|replace|swap|improve|animate|add|remove|turn|put)\b", polite.group(1)):
        t = polite.group(1)                                          # "can you make me a falcon?" is a request, not a question about me
    if re.match(r"^(?:how much|how many credits|what(?:'s| is| would) (?:it|that|this) cost|what'?s the (?:price|cost)|price|cost)\b", t):
        return ["ASK"], 0.85                                         # a price question is never small talk ("how much?" used to answer "Hi!")
    if (is_smalltalk(t) or is_ack(t)) and not re.search(NEW_VERBS, t):
        return ["SMALLTALK"], 0.95
    if has_generation and re.search(NAMES_RX, t):
        return ["NAMES"], 0.9
    intents: list = []
    conf = 0.5
    counted = re.sub(r"\b(?:make|create|generate|draw|give|design|build)\s+(?:me\s+)?(?:a\s+)?(?:pack of\s+)?\d+\s+(?:\w+\s+){0,2}?(?:stickers?|emoji|packs?|sets?|dogs?|cats?|\w+s)\b|\bpack of \d+\b|\b\d+\s+(?:different\s+)?(?:\w+\s+){0,2}stickers?\b", " ", t)
    refs = bool(re.search(r"\b(?:number|no\.?|#)\s*\d|\b\d\b|\bs\d\b|\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth)\b|\blast\s+(?:one|sticker|image|picture|pic|cell)\b|\bg\d+\s*/?\s*s\d", counted)) \
        or bool(has_selection and re.search(r"\b(these|this|those|them|it|selected)\b", t))
    concept_edit = bool(has_generation and re.search(rf"\b(make|turn|give|put|let|get)\s+{PRON}\b", t) and (re.search(COMPARATIVE, t) or re.search(WEARISH, t) or re.search(COLOURS, t))
                        and not re.search(r"\b(?:a|an|some|\d+)\s+(?:\w+\s+)?(?:stickers?|emoji|packs?|sets?)\b", t))
    if len(t.split()) <= 8 and re.search(r"\b(grid|2x2|3x3|style|no animation|without animation|with animation|ask before|don'?t ask|ask me|instant|auto[- ]?create|ai vision)\b", t) \
            and re.search(r"\b(use|set|switch|change|make it|go|turn|please|from now|always|stop|no|with|without|don'?t|do not|ask|just|allow|enable|disable)\b", t) \
            and not re.search(NEW_VERBS, t.replace("make it", "")):
        intents, conf = ["CHANGE_SETTINGS"], 0.8
    elif re.search(r"\b(animate|animation of|make (?:it|them|number \d|\d) (?:move|dance|alive)|bring (?:it|them) to life|add motion)\b", t):
        intents, conf = ["ANIMATE"], 0.85
    elif has_generation and re.search(DESCRIBE, t):
        intents, conf = ["ASK"], 0.85
    elif re.match(r"^(?:which|what|where|who|how many|how much|do i have|did we|show me which|tell me|is there|are there)\b", t) or t.endswith("?"):
        intents, conf = ["ASK"], 0.8 if re.match(r"^(?:which|what|where|who|how many)\b", t) else 0.65
        if re.search(r"\b(find|search)\b", t):
            intents = ["SEARCH"]
    elif re.search(r"\b(find|search|look for|do i have|show me my|from before|old one)\b", t):
        intents, conf = ["SEARCH"], 0.75
    elif re.search(r"\b(another|more of|again|new batch|different (?:set|batch|ones)|try again)\b", t) and has_generation:
        intents, conf = ["ANOTHER"], 0.8
    elif has_generation and (refs or concept_edit) and re.search(r"\b(make|redo|regenerate|change|fix|replace|swap|improve|less|more|bigger|smaller|happier|sadder|funnier|cuter|different|give|put|add|remove|let|get|turn)\b", t):
        intents, conf = ["EDIT_STICKERS"], 0.8
        if re.search(rf"\b{POS}\b|\b{NEG}\b", t) and re.search(r"\b(i|but)\b", t) and re.search(r"\b(like|love|hate|dislike|keep)\b", t):
            intents = ["FEEDBACK", "EDIT_STICKERS"]
    elif has_generation and refs and re.search(rf"\b{POS}\b|\b{NEG}\b", t):
        intents, conf = ["FEEDBACK"], 0.85
    elif has_generation and not t.endswith("?") and len(t.split()) <= 8 and re.search(r"\b(?:this|it|that|these|those|they|them)\b", t) \
            and re.search(rf"\b{POS}\b|\b{NEG}\b", t) and not re.search(NEW_VERBS, t):
        intents, conf = ["FEEDBACK"], 0.75                       # "this is bad", "I like this one": an opinion about what is on screen, not a new subject
    elif re.search(NEW_VERBS, t):
        intents, conf = ["NEW"], 0.85
    elif has_generation and re.search(r"^(?:i )?(?:like|love|hate|dislike|keep)\b", t):
        intents, conf = ["FEEDBACK"], 0.6
    elif has_generation and len(t.split()) <= 5 and (re.search(COMPARATIVE, t) or re.search(COLOURS, t) or re.match(r"^(?:same|again|more|one more|undo|revert|redo)\b", t)) and not re.search(NEW_VERBS, t):
        intents, conf = ["EDIT_STICKERS"], 0.7        # "bigger", "same but red", "happier": a change to what is open, never a new subject (the next question is which sticker)
    elif len(t.split()) <= 8 and not t.endswith("?") and not re.match(r"^(?:undo|revert|ok|okay|yes|no)\b", t):
        intents, conf = ["NEW"], 0.62                 # "falcon dancing", "teddy bear with a book": a bare subject is a request
    elif not t.endswith("?") and re.search(r"\b(?:in|with|on|of|holding|wearing|sitting|standing|style|and|for|a|an|the)\b", t) \
            and not re.search(r"\b(?:it|them|this|that|these|those|number|sticker|batch|previous|last|same|again)\b|\b(?:like|love|hate|dislike|keep)\b", t):
        intents, conf = ["NEW"], 0.62                 # a long description with nothing to point back at ("a cute cat in pixar style holding an umbrella...") is a request
    else:
        intents, conf = ["AMBIGUOUS"], 0.3
    return intents, conf


SETTING_RULES = [
    (r"\b2\s*x\s*2\b", ("grid", "2x2")), (r"\b3\s*x\s*3\b", ("grid", "3x3")),
    (r"\b(don'?t|do not|stop)\s+ask|\binstant|\bauto[- ]?create|\bjust (?:do|make) it", ("ask_before_spending", False)),
    (r"\bask (?:me )?before|\bconfirm before", ("ask_before_spending", True)),
    (r"\b(?:allow|enable|turn on)\s+(?:the\s+)?(?:ai\s+)?vision\b", ("allow_vlm", True)),
    (r"\b(?:don'?t|do not|never|stop|disable|turn off)\s+(?:use\s+|using\s+)?(?:the\s+)?(?:ai\s+)?vision\b", ("allow_vlm", False)),
]
STYLE_WORDS = {"flat": "flat_vector", "vector": "flat_vector", "pixar": "pixar_3d", "3d": "pixar_3d", "toon": "toon_cel", "cel": "toon_cel", "glossy": "glossy_3d"}


def settings_from(text: str, style_ids: list | None = None) -> dict:
    t = text.lower()
    out = {}
    for pat, (k, v) in SETTING_RULES:
        if re.search(pat, t) and k not in out:          # the first rule wins: "don't ask me before spending" is one rule, not two
            out[k] = v
    for w, sid in STYLE_WORDS.items():
        if re.search(rf"\b{w}\b", t) and (style_ids is None or sid in style_ids):
            out["style_id"] = sid
            break
    return out
