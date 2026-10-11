"""Coleta de notícias: RSS, Hacker News e monitor de mudança de páginas."""
import calendar
import hashlib
import html
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional

import feedparser
import requests

import db

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechRadarBot/1.0)"}

# (nome, url, peso). Peso maior = fonte mais confiável/rápida para você.
# Se algum feed falhar, o programa só avisa e segue. Edite à vontade.
RSS_FEEDS = [
    # --- Notícias gerais de tech (EN) ---
    ("TechCrunch", "https://techcrunch.com/feed/", 1.5),
    ("The Verge", "https://www.theverge.com/rss/index.xml", 1.5),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", 1.5),
    ("Wired", "https://www.wired.com/feed/rss", 1.0),
    ("Engadget", "https://www.engadget.com/rss.xml", 1.0),
    ("Gizmodo", "https://gizmodo.com/rss", 1.0),
    ("CNET", "https://www.cnet.com/rss/news/", 1.0),
    ("ZDNet", "https://www.zdnet.com/news/rss.xml", 1.0),
    ("The Next Web", "https://thenextweb.com/feed", 1.0),
    ("VentureBeat", "https://venturebeat.com/feed/", 1.0),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/", 1.0),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all", 1.0),
    ("Slashdot", "http://rss.slashdot.org/Slashdot/slashdotMain", 1.0),
    ("Techmeme", "https://www.techmeme.com/feed.xml", 2.0),  # agregador: costuma ser rápido
    # --- Apple / Android ---
    ("9to5Mac", "https://9to5mac.com/feed/", 1.0),
    ("9to5Google", "https://9to5google.com/feed/", 1.0),
    ("MacRumors", "https://feeds.macrumors.com/MacRumors-All", 1.0),
    ("Android Authority", "https://www.androidauthority.com/feed/", 1.0),
    ("XDA", "https://www.xda-developers.com/feed/", 1.0),
    # --- Segurança ---
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/", 1.5),
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews", 1.5),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/", 1.5),
    ("The Register", "https://www.theregister.com/headlines.atom", 1.0),
    # --- Devs / comunidade ---
    ("Lobsters", "https://lobste.rs/rss", 1.0),
    ("Product Hunt", "https://www.producthunt.com/feed", 0.5),
    ("GitHub Blog", "https://github.blog/feed/", 1.5),
    ("Cloudflare Blog", "https://blog.cloudflare.com/rss/", 1.0),
    # --- Fontes oficiais de empresas (quem anuncia primeiro) ---
    ("OpenAI", "https://openai.com/news/rss.xml", 2.5),
    ("Google Blog", "https://blog.google/rss/", 1.5),
    ("Microsoft Blog", "https://blogs.microsoft.com/feed/", 1.5),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/", 1.5),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml", 1.5),
    # --- Brasil (PT) ---
    ("Tecnoblog", "https://tecnoblog.net/feed/", 1.5),
    ("Canaltech", "https://canaltech.com.br/rss/", 1.5),
    ("TecMundo", "https://rss.tecmundo.com.br/feed", 1.5),
    ("Olhar Digital", "https://olhardigital.com.br/feed/", 1.5),
    ("Showmetech", "https://www.showmetech.com.br/feed/", 1.0),
    # --- Releases no GitHub (formato: https://github.com/DONO/REPO/releases.atom) ---
    ("GitHub ollama", "https://github.com/ollama/ollama/releases.atom", 1.0),
    ("GitHub vscode", "https://github.com/microsoft/vscode/releases.atom", 1.0),
]

# Páginas para monitorar mudanças (lançamentos "silenciosos", preços, status).
# Exemplo: ("Página de preços X", "https://exemplo.com/pricing")
PAGES = []


@dataclass
class Item:
    source: str
    title: str
    url: str
    summary: str = ""
    points: int = 0
    weight: float = 1.0
    published: Optional[float] = None
    uid: str = ""

    @property
    def id(self):
        return self.uid or hashlib.sha1(self.url.encode()).hexdigest()[:16]


def clean(text, limit=600):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:limit]


def fetch_rss(feed):
    name, url, weight = feed
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        parsed = feedparser.parse(r.content)
    except Exception as e:
        print(f"[aviso] feed '{name}' falhou: {e}")
        return []
    out = []
    for e in parsed.entries[:25]:
        link, title = e.get("link"), clean(e.get("title"), 200)
        if not link or not title:
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        published = calendar.timegm(ts) if ts else None
        summary = clean(e.get("summary", ""))
        out.append(Item(name, title, link, summary, 0, weight, published))
    return out


def fetch_hn(limit=30):
    base = "https://hacker-news.firebaseio.com/v0"
    try:
        ids = requests.get(f"{base}/topstories.json", timeout=15).json()[:limit]
    except Exception as e:
        print(f"[aviso] Hacker News falhou: {e}")
        return []

    def one(i):
        try:
            d = requests.get(f"{base}/item/{i}.json", timeout=10).json()
            if not d or d.get("type") != "story" or d.get("dead") or d.get("deleted"):
                return None
            url = d.get("url") or f"https://news.ycombinator.com/item?id={i}"
            return Item("Hacker News", clean(d["title"], 200), url, "", d.get("score", 0), 1.5, d.get("time"))
        except Exception:
            return None

    with ThreadPoolExecutor(8) as ex:
        return [r for r in ex.map(one, ids) if r]


def fetch_pages():
    out = []
    for name, url in PAGES:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            body = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", r.text)
            text = clean(body, 200000)
            h = hashlib.sha1(text.encode()).hexdigest()
            key = "page:" + url
            old = db.kv_get(key)
            db.kv_set(key, h)
            if old and old != h:
                out.append(
                    Item(
                        f"Página: {name}",
                        f"Mudança detectada em: {name}",
                        url,
                        text[:500],
                        0,
                        2.0,
                        None,
                        uid=hashlib.sha1((url + h).encode()).hexdigest()[:16],
                    )
                )
        except Exception as e:
            print(f"[aviso] página '{name}' falhou: {e}")
    return out


def collect_all():
    items = []
    with ThreadPoolExecutor(8) as ex:
        for res in ex.map(fetch_rss, RSS_FEEDS):
            items.extend(res)
    items.extend(fetch_hn())
    items.extend(fetch_pages())
    return items
