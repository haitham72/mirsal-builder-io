"""Phase 3B pool, lexical pass: every APPROVED sticker is indexed by topic; a request first
fetches matching stickers (free, instant) and only the missing count goes to paid generation.
Vectors (`subject_vec/action_vec`) land with the embedding pass; scoring keeps the same shape
(0.5 subject + 0.4 action + 0.1 lexical) so the hybrid upgrade swaps the scorer, not the callers."""
from __future__ import annotations

import json
import re
import time

THRESH = 0.3          # trigram gate, same default as pg_trgm
PER_GEN = 2           # diversity: at most 2 hits per generation


def normalize_topic(s: str) -> str:
    s = str(s or "").lower().replace("'", "").replace("’", "")
    s = re.sub(r"[^\w\s\u0600-\u06FF]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def _trigrams(s: str) -> set:
    p = f"  {s} "
    return {p[i:i + 3] for i in range(len(p) - 2)} if p.strip() else set()


def _sim(a: str, b: str) -> float:
    A, B = _trigrams(a), _trigrams(b)
    return 2 * len(A & B) / (len(A) + len(B)) if (A or B) else 0.0


def _words(s: str) -> list:
    return [w for w in re.findall(r"[a-z0-9\u0600-\u06FF]+", str(s or "").lower()) if w]


def parse_query(q: str) -> dict:
    """Deterministic patterns first; Arabic/Arabizi/unmatched stay whole-as-subject (an LLM
    parser plugs in here later behind the same return shape)."""
    q = str(q or "").strip()
    m = re.match(r"(.+?)\s+doing\s+(.+)", q, re.I)
    if m:
        return {"subject": m.group(1).strip(), "action": m.group(2).strip(), "topics": []}
    m = re.match(r"(.+?)\s+([a-z]+ing)$", q, re.I)
    if m and len(m.group(1).split()) <= 4:
        return {"subject": m.group(1).strip(), "action": m.group(2).strip(), "topics": []}
    return {"subject": q, "action": "", "topics": []}


def _subject_action(gen: dict, st: dict) -> tuple:
    plan = gen.get("plan") or {}
    ext = (plan.get("extraction") or {}) if isinstance(plan, dict) else {}
    subject = ext.get("subject") or str(gen.get("subject") or "").replace("_", " ") or str(gen.get("task") or "")
    key = st.get("key") or ""
    subj_slug = re.sub(r"\W+", "_", subject.lower()).strip("_")
    action = re.sub(r"^" + re.escape(subj_slug) + r"_?", "", key).replace("_", " ") or st.get("concept") or key
    return subject.strip(), action.strip()


def index_row(gen: dict, st: dict) -> dict:
    subject, action = _subject_action(gen, st)
    emoji = "".join(st.get("emoji") or [])
    style = ((gen.get("plan") or {}).get("slots") or {}).get("style_id", "") if isinstance(gen.get("plan"), dict) else ""
    search_text = f"{subject} \u2014 {action} \u2014 {st.get('name') or ''} \u2014 {emoji} \u2014 {style}"
    topics = sorted({normalize_topic(t) for t in (st.get("tags") or []) if normalize_topic(t)})
    shared = (gen.get("source") or "") != "photo"  # uploaded-reference stickers never join the shared pool
    return {"sticker_id": st["id"], "subject": subject, "action": action, "search_text": search_text,
            "topics": topics, "shared": shared}


def reindex(conn) -> int:
    """Backfill every APPROVED sticker (incl. Phase 1-2 prepared runs). Idempotent. Returns new rows."""
    n = 0
    with conn.cursor() as cur:
        cur.execute(
            """SELECT g.*, s.id AS sid, s.key, s.name, s.tags, s.concept, s.emoji, s.generation_id
               FROM stickers s JOIN generations g ON g.id = s.generation_id
               WHERE s.still_review = 'APPROVED' AND s.id NOT IN (SELECT sticker_id FROM sticker_index)""")
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            row = dict(zip(cols, r))
            st = {"id": row.pop("sid"), "key": row["key"], "name": row["name"], "tags": row["tags"],
                  "concept": row["concept"], "emoji": row["emoji"]}
            idx = index_row(row, st)
            cur.execute(
                """INSERT INTO sticker_index (sticker_id, subject, action, search_text, topics, shared)
                   VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (sticker_id) DO NOTHING""",
                (idx["sticker_id"], idx["subject"], idx["action"], idx["search_text"], idx["topics"], idx["shared"]))
            n += 1
    conn.commit()
    return n


def hide(conn, sticker_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("UPDATE sticker_index SET hidden = true WHERE sticker_id = %s", (sticker_id,))
        hit = cur.rowcount > 0
    conn.commit()
    return hit


def _cover(words: list, hay: list) -> tuple:
    """(all_covered, mean_best): every query word must resemble a hay word (the zero-results rule)."""
    if not words:
        return True, 1.0
    best = [max([_sim(w, h) for h in hay] or [0.0]) for w in words]
    return all(b >= THRESH for b in best), sum(best) / len(best)


def search(conn, query: str, count: int = 9, style: str | None = None) -> dict:
    """Pool-first search. Returns {parsed, hits, found, missing} — never spends, never generates."""
    t0 = time.perf_counter()
    parsed = parse_query(query)
    sw, aw = _words(parsed["subject"]), _words(parsed["action"])
    hits = []
    with conn.cursor() as cur:
        cur.execute(
            """SELECT si.sticker_id, si.subject, si.action, si.search_text, si.topics,
                      s.key, s.emoji, s.generation_id, s.animation_status,
                      (SELECT object_key FROM assets WHERE sticker_id = s.id AND kind IN ('PNG','WEBP') LIMIT 1) AS png
               FROM sticker_index si JOIN stickers s ON s.id = si.sticker_id
               WHERE si.hidden = false AND si.shared = true AND s.still_review = 'APPROVED'""")
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            cand = dict(zip(cols, r))
            ok_s, m_s = _cover(sw, _words(cand["subject"]) + _words(" ".join(cand["topics"])))
            if not ok_s:
                continue
            if aw:
                ok_a, m_a = _cover(aw, _words(cand["action"]) + _words(" ".join(cand["topics"])))
                if not ok_a:
                    continue
                rank = 0.5 * m_s + 0.4 * m_a + 0.1 * _sim(query.lower(), cand["search_text"].lower())
            else:
                rank = 0.6 * m_s + 0.1 * _sim(query.lower(), cand["search_text"].lower())
            cand["rank"] = round(rank, 4)
            hits.append(cand)
    hits.sort(key=lambda h: -h["rank"])
    seen, per_gen, final = set(), {}, []
    for h in hits:  # diversity + near-duplicate collapse (same text -> the better rank wins)
        if h["search_text"] in seen:
            continue
        seen.add(h["search_text"])
        per_gen[h["generation_id"]] = per_gen.get(h["generation_id"], 0) + 1
        if per_gen[h["generation_id"]] <= PER_GEN:
            final.append(h)
        if len(final) >= count:
            break
    ms = int((time.perf_counter() - t0) * 1000)
    with conn.cursor() as cur:
        cur.execute("INSERT INTO search_log (query, filters, hit_ids, latency_ms, parsed, gap_generated)"
                    " VALUES (%s,%s,%s,%s,%s,%s)",
                    (query, json.dumps({"pool": True, "count": count}),
                     [h["sticker_id"] for h in final], ms, json.dumps(parsed), 0))
    conn.commit()
    return {"parsed": parsed, "hits": final, "found": len(final), "missing": max(0, count - len(final))}
