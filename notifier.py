"""Telegram: envia rascunhos com botões e recebe os cliques."""
import json
from urllib.parse import quote

import requests

import config

API = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def _check(r):
    """Levanta erro mostrando o motivo que o Telegram devolveu (sem expor o token)."""
    if r.status_code >= 400:
        try:
            desc = r.json().get("description", r.text)
        except Exception:
            desc = r.text
        raise RuntimeError(f"Telegram respondeu {r.status_code}: {desc}")


def intent_url(text):
    return "https://x.com/intent/post?text=" + quote(text, safe="")


def build_keyboard(draft_id, text):
    discard = {"text": "🗑 Descartar", "callback_data": f"no:{draft_id}"}
    if config.PUBLISH_MODE == "manual":
        # Botão que abre o X com o texto já preenchido: é só tocar em "Postar" (grátis, sem API)
        intent = intent_url(text)
        return {"inline_keyboard": [[{"text": "📝 Abrir no X (texto pronto)", "url": intent}], [discard]]}
    return {"inline_keyboard": [[{"text": "✅ Postar", "callback_data": f"ok:{draft_id}"}, discard]]}


def send_draft(draft_id, text, item, score, note=""):
    msg = (
        f"📰 Rascunho #{draft_id}  (nota {score})\n"
        + (f"{note}\n" if note else "")
        + f"\n{text}\n\n"
        f"— {len(text)} caracteres\nFonte: {item.source}\n{item.url}"
    )
    r = requests.post(
        f"{API}/sendMessage",
        json={"chat_id": config.TELEGRAM_CHAT_ID, "text": msg, "reply_markup": build_keyboard(draft_id, text)},
        timeout=15,
    )
    _check(r)
    return r.json()["result"]["message_id"]


def send_text(text):
    r = requests.post(f"{API}/sendMessage", json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    _check(r)


def get_updates(offset=None, timeout=20):
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": timeout, "allowed_updates": json.dumps(["callback_query"])},
            timeout=timeout + 25,
        )
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
        return []  # normal em long polling / rede lenta
    _check(r)
    return r.json().get("result", [])


def answer_callback(callback_id, text):
    requests.post(f"{API}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": text}, timeout=15)


def remove_buttons(chat_id, message_id):
    requests.post(
        f"{API}/editMessageReplyMarkup",
        json={"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": []}},
        timeout=15,
    )
