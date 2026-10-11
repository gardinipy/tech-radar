"""Dá uma nota de relevância para cada notícia."""
import re
import time

from config import KEYWORDS

SIMILARITY = 0.3  # similaridade de títulos para considerar "mesma notícia"
STOP = set("the a an of to in for and on with is are de da do em um uma para com e o os as que na no por se at by from it its".split())
_KW = [re.compile(r"\b" + re.escape(k) + r"\b") for k in KEYWORDS]


def tokens(text):
    return {w for w in re.findall(r"[a-z0-9áéíóúãõâêôçà]+", text.lower()) if len(w) > 2 and w not in STOP}


def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def score_item(item, recent):
    text = f"{item.title} {item.summary}".lower()
    hits = sum(1 for k in _KW if k.search(text))
    s = item.weight + min(hits, 4) * 1.0
    s += min(item.points / 150, 4)  # esquentando no Hacker News
    others = {
        r["source"]
        for r in recent
        if r["id"] != item.id and r["source"] != item.source and similarity(item.title, r["title"]) >= SIMILARITY
    }
    s += 2.0 * len(others)  # várias fontes falando = notícia quente
    if item.published and time.time() - item.published < 3600:
        s += 1.0
    return round(s, 1)


def is_duplicate(title, drafted_titles):
    return any(similarity(title, t) >= SIMILARITY for t in drafted_titles)
