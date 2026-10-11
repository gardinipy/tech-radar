import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "radar.db"


@contextmanager
def db():
    DB_PATH.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with db() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS items(
                id TEXT PRIMARY KEY, source TEXT, title TEXT, url TEXT, summary TEXT,
                points INTEGER DEFAULT 0, score REAL DEFAULT 0, first_seen REAL);
            CREATE TABLE IF NOT EXISTS drafts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT, text TEXT, url TEXT,
                status TEXT DEFAULT 'pending', tweet_id TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT);
            """
        )


def is_empty():
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0


def seen(item_id):
    with db() as c:
        return c.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone() is not None


def save_item(it):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO items(id,source,title,url,summary,points,first_seen) VALUES(?,?,?,?,?,?,?)",
            (it.id, it.source, it.title, it.url, it.summary, it.points, time.time()),
        )


def set_score(item_id, score):
    with db() as c:
        c.execute("UPDATE items SET score=? WHERE id=?", (score, item_id))


def recent_items(hours=12):
    with db() as c:
        return c.execute(
            "SELECT id,source,title FROM items WHERE first_seen>?", (time.time() - hours * 3600,)
        ).fetchall()


def add_draft(item_id, text, url):
    with db() as c:
        cur = c.execute(
            "INSERT INTO drafts(item_id,text,url,created) VALUES(?,?,?,?)",
            (item_id, text, url, time.time()),
        )
        return cur.lastrowid


def get_draft(draft_id):
    with db() as c:
        return c.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()


def set_draft_status(draft_id, status, tweet_id=None):
    with db() as c:
        c.execute("UPDATE drafts SET status=?, tweet_id=COALESCE(?,tweet_id) WHERE id=?", (status, tweet_id, draft_id))


def claim_draft(draft_id):
    """Marca como 'posting' só se ainda estiver pendente (evita clique duplo)."""
    with db() as c:
        cur = c.execute("UPDATE drafts SET status='posting' WHERE id=? AND status='pending'", (draft_id,))
        return cur.rowcount == 1


def drafts_last_hour():
    with db() as c:
        return c.execute("SELECT COUNT(*) FROM drafts WHERE created>?", (time.time() - 3600,)).fetchone()[0]


def recent_drafted_titles(hours=12):
    with db() as c:
        rows = c.execute(
            "SELECT i.title FROM drafts d JOIN items i ON i.id=d.item_id WHERE d.created>?",
            (time.time() - hours * 3600,),
        ).fetchall()
        return [r["title"] for r in rows]


def kv_get(k):
    with db() as c:
        r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r else None


def kv_set(k, v):
    with db() as c:
        c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))


def forget_item(item_id):
    """Remove o item para ele ser reavaliado no próximo ciclo (usado quando a IA falha)."""
    with db() as c:
        c.execute("DELETE FROM items WHERE id=?", (item_id,))


def known_sources():
    with db() as c:
        return {r["source"] for r in c.execute("SELECT DISTINCT source FROM items").fetchall()}
