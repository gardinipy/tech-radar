"""Mostra o seu TELEGRAM_CHAT_ID. Mande uma mensagem qualquer ao seu bot e rode este script."""
import requests

import config

r = requests.get(f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates", timeout=15).json()
if not r.get("ok"):
    raise SystemExit(f"Erro: {r} (confira TELEGRAM_BOT_TOKEN no .env)")
chats = {}
for u in r.get("result", []):
    m = u.get("message") or {}
    if "chat" in m:
        chats[m["chat"]["id"]] = m["chat"].get("first_name", "")
if not chats:
    raise SystemExit("Nada encontrado. Abra o seu bot no Telegram, mande 'oi' e rode de novo.")
for cid, name in chats.items():
    print(f"TELEGRAM_CHAT_ID={cid}   ({name})")
