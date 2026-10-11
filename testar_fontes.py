"""Testa todas as fontes e mostra quais funcionam. Rode: python testar_fontes.py"""
import time
from concurrent.futures import ThreadPoolExecutor

import feedparser
import requests

import sources


def check(feed):
    name, url, _ = feed
    try:
        r = requests.get(url, headers=sources.HEADERS, timeout=15)
        if r.status_code != 200:
            return name, False, f"HTTP {r.status_code}", ""
        parsed = feedparser.parse(r.content)
        n = len(parsed.entries)
        if n == 0:
            return name, False, "sem itens (feed vazio ou URL não é RSS)", ""
        title = sources.clean(parsed.entries[0].get("title", ""), 60)
        return name, True, f"{n} itens", title
    except Exception as e:
        return name, False, str(e)[:60], ""


print(f"Testando {len(sources.RSS_FEEDS)} feeds...\n")
with ThreadPoolExecutor(8) as ex:
    results = list(ex.map(check, sources.RSS_FEEDS))

ok = [r for r in results if r[1]]
bad = [r for r in results if not r[1]]
for name, _, info, title in ok:
    print(f"  OK   {name:<22} {info:<12} {title}")
for name, _, info, _ in bad:
    print(f"  FALHA {name:<21} {info}")

hn = sources.fetch_hn(5)
print(f"\n  {'OK  ' if hn else 'FALHA'} Hacker News (API)       {len(hn)} itens")
print(f"\nResumo: {len(ok)} feeds funcionando, {len(bad)} com problema.")
if bad:
    print("Apague (ou comente) as linhas das fontes com FALHA em sources.py; não afetam as demais.")
