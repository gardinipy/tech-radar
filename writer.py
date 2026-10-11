"""Gera o rascunho do post: Gemini (grátis), Claude (pago) ou template simples (sem IA)."""
import re
import time

import requests

import config

_anthropic_client = None


def _system_prompt(max_chars):
    return (
        f"Você é o editor de um perfil de notícias de tecnologia no X, escrevendo em {config.POST_LANGUAGE}. "
        f"Estilo: {config.PROFILE_STYLE}.\n"
        "Regras:\n"
        "- Use SOMENTE informações presentes no título/resumo fornecidos. Nunca invente fatos, números ou citações.\n"
        "- Se parecer rumor ou vazamento não confirmado, deixe isso claro no texto.\n"
        "- Sem clickbait exagerado. No máximo 1-2 emojis e no máximo 1 hashtag relevante.\n"
        f"- Máximo de {max_chars - 30} caracteres no total.\n"
        + ("" if config.INCLUDE_LINK else "- Termine citando a fonte, no formato: 'Fonte: NOME'.\n")
        + "- Se a notícia for irrelevante para público de tecnologia, fraca ou repetitiva, responda exatamente: SKIP\n"
        "Responda apenas com o texto do post, sem aspas e sem explicações."
    )


def _user_prompt(item):
    return f"Fonte: {item.source}\nTítulo: {item.title}\nResumo: {item.summary or '(sem resumo)'}\nURL: {item.url}"


_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_gemini_model = None  # modelo em uso (pode ser trocado automaticamente)


def _discover_flash_models():
    """Pergunta ao Google quais modelos Flash existem hoje, do mais novo/estável ao menos."""
    r = requests.get(f"{_GEMINI_BASE}/models", headers={"x-goog-api-key": config.GEMINI_API_KEY},
                     params={"pageSize": 200}, timeout=30)
    r.raise_for_status()
    bad = ("image", "tts", "live", "audio", "embedding", "thinking", "robotics", "computer", "learnlm", "native")
    cands = []
    for m in r.json().get("models", []):
        name = m["name"].replace("models/", "")
        if "generateContent" not in m.get("supportedGenerationMethods", []):
            continue
        if "flash" not in name or any(b in name for b in bad):
            continue
        v = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
        ver = float(v.group(1)) if v else 0.0
        preview = any(x in name for x in ("preview", "exp"))
        lite = "lite" in name
        cands.append(((preview, lite, -ver), name))
    if not cands:
        raise RuntimeError("nenhum modelo Flash disponível para a sua chave no Google AI Studio")
    cands.sort()
    return [name for _, name in cands]


def _gemini_request(model, system, user):
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"maxOutputTokens": 2048, "temperature": 0.7},
    }
    return requests.post(
        f"{_GEMINI_BASE}/models/{model}:generateContent",
        headers={"x-goog-api-key": config.GEMINI_API_KEY},
        json=body,
        timeout=60,
    )


def _call_gemini(system, user):
    """Chama o Gemini com repetição em caso de sobrecarga (503) e troca de modelo se preciso."""
    global _gemini_model
    primary = _gemini_model or config.GEMINI_MODEL
    models, alts, i = [primary], None, 0
    primary_missing, last = False, None

    while i < len(models):
        model = models[i]
        r = None
        for attempt in range(2):
            r = _gemini_request(model, system, user)
            if r.status_code in (500, 502, 503, 504):
                last = r
                print(f"[aviso] Gemini ({model}) sobrecarregado ({r.status_code}); tentando de novo...")
                time.sleep(3 * (attempt + 1))
                r = None
                continue
            break

        if r is None or r.status_code == 404:  # sobrecarregado ou modelo inexistente: tenta outro
            if r is not None and model == primary:
                primary_missing = True
            if alts is None:
                try:
                    alts = [m for m in _discover_flash_models() if m != primary]
                except Exception:
                    alts = []
                models += alts[:3]
            i += 1
            continue

        if r.status_code == 429:
            raise RuntimeError("limite grátis do Gemini atingido (429); tento de novo no próximo ciclo")
        if r.status_code >= 400:
            raise RuntimeError(f"Gemini respondeu {r.status_code}: {r.text[:200]}")

        if model != primary and primary_missing:
            _gemini_model = model
            print(f"[aviso] modelo '{primary}' não existe mais; usando '{model}'. "
                  f"Para fixar, ponha GEMINI_MODEL={model} no .env")
        cands = r.json().get("candidates") or []
        parts = (cands[0].get("content", {}).get("parts") if cands else None) or []
        return "".join(p.get("text", "") for p in parts).strip()

    detail = f" (último erro: {last.status_code})" if last is not None else ""
    raise RuntimeError("Gemini indisponível no momento" + detail + ". É temporário; tente de novo em alguns minutos.")


def _call_anthropic(system, user):
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic

        _anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = _anthropic_client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


last_fallback = False  # True se o último rascunho foi feito sem IA por falha do provedor


def _template(item):
    text = f"📰 {item.title}"
    if not config.INCLUDE_LINK:
        text += f"\n\nFonte: {item.source}"
    return text


def draft(item):
    """Retorna o texto final do post, ou None se a IA decidir pular."""
    global last_fallback
    last_fallback = False
    max_chars = 280 - (25 if config.INCLUDE_LINK else 0)

    if config.LLM_PROVIDER == "none":
        text = _template(item)
    else:
        system, user = _system_prompt(max_chars), _user_prompt(item)
        try:
            raw = _call_gemini(system, user) if config.LLM_PROVIDER == "gemini" else _call_anthropic(system, user)
        except Exception as e:
            if not config.LLM_FALLBACK_TO_TEMPLATE:
                raise
            print(f"[aviso] IA indisponível ({e}). Usando rascunho simples, sem IA.")
            last_fallback = True
            text = _template(item)
        else:
            text = raw.strip().strip('"').strip()
            if not text or text.upper().startswith("SKIP"):
                return None
            text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    if config.INCLUDE_LINK:
        text = f"{text}\n\n{item.url}"
    return text
