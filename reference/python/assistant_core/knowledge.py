from __future__ import annotations
import math, re, unicodedata
from typing import Iterable

STOP = {"the", "and", "for", "are", "what", "when", "how", "who", "does", "with", "that", "this", "from", "our", "can", "you", "all", "any", "before", "after", "than", "more", "have", "has", "was", "were", "which", "into", "about", "need", "needs"}

def tokens(s: str) -> list[str]:
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    out = []
    for t in re.split(r"[^a-z0-9]+", s):
        if len(t) > 2 and t not in STOP:
            t = re.sub(r"ies$", "y", t); t = re.sub(r"(ing|ed|es|s)$", "", t); out.append(t)
    return out

def expand_query(q: str, glossary: Iterable[dict]) -> list[str]:
    out = list(tokens(q)); lq = q.lower()
    for g in glossary:
        names = [g["term"].lower(), *[s.lower() for s in g.get("synonyms", [])]]
        if any(n in lq for n in names):
            out += tokens(" ".join([g["term"], *g.get("synonyms", [])]))
    return list(dict.fromkeys(out))

def chunk_text(text: str, max_len: int = 700) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in paras:
        if len(p) <= max_len: out.append(p); continue
        cur = ""
        for s in re.findall(r"[^.!?]+[.!?]+", p) or [p]:
            if len(cur + s) > max_len - 100: out.append(cur.strip()); cur = ""
            cur += s
        if cur.strip(): out.append(cur.strip())
    return out

def extract_obligations(text: str) -> list[dict]:
    """Pattern-based extraction of dated obligations; the production enrichment step adds an LLM pass."""
    found = []
    for m in re.finditer(r"(by|before|until|no later than) the (\d{1,2})(st|nd|rd|th)( of (each|every|the following) month)?", text, re.I):
        found.append({"kind": "time", "detail": f"Due on day {m.group(2)} of the month", "due": {"day_of_month": int(m.group(2))}})
    for m in re.finditer(r"(\d{1,3}) (business )?days before (expiry|renewal|the deadline|the due date)", text, re.I):
        found.append({"kind": "lead", "detail": f"Lead time {m.group(1)} days before {m.group(3)}", "lead": int(m.group(1))})
    for m in re.finditer(r"more than (\d+) (days|hours)", text, re.I):
        found.append({"kind": "state", "detail": f"State threshold: more than {m.group(1)} {m.group(2)}", "n": int(m.group(1)), "unit": m.group(2)})
    return found

def search(query: str, docs: Iterable[dict], glossary: Iterable[dict] = (), department: str | None = None, limit: int = 5) -> list[dict]:
    """Keyword retrieval with glossary expansion. Production: hybrid vector + BM25 with a reranker and chunk ACLs."""
    terms = expand_query(query, glossary)
    if not terms: return []
    hits = []
    for d in docs:
        if department and d.get("dept") != department: continue
        title_t = tokens(d["title"])
        for ci, c in enumerate(d["chunks"]):
            head_t, body_t = tokens(c["heading"]), tokens(c["text"])
            score, matched = 0.0, []
            for t in terms:
                nb = sum(1 for x in body_t if x == t or (len(t) >= 4 and x.startswith(t)))
                s = nb + 2.5 * head_t.count(t) + 2 * title_t.count(t)
                if s: score += s; matched.append(t)
            if score:
                cov = len(matched) / len(terms)
                score = score * cov / math.log2(10 + len(body_t) / 40)
                hits.append({"doc": d["id"], "title": d["title"], "chunk": ci, "heading": c["heading"], "score": round(score, 3), "coverage": cov, "matched": matched})
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit]

def confidence(hit: dict) -> float:
    return min(0.98, 0.35 + 0.35 * hit["coverage"] + min(0.3, hit["score"] / 10))
