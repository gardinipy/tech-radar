import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name, default):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "sim")


# Quem escreve os rascunhos: "gemini" (grátis), "anthropic" (pago) ou "none" (sem IA, grátis)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# Se a IA falhar (sobrecarga/limite), gera um rascunho simples sem IA em vez de perder a notícia
LLM_FALLBACK_TO_TEMPLATE = _bool("LLM_FALLBACK_TO_TEMPLATE", "true")

# Como publicar: "manual" (grátis: botão abre o X com o texto pronto) ou "api" (paga a API do X)
PUBLISH_MODE = os.getenv("PUBLISH_MODE", "manual").strip().lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")

DRY_RUN = _bool("DRY_RUN", "true")
INCLUDE_LINK = _bool("INCLUDE_LINK", "true")
# Abre sozinho o X no seu navegador, com o texto pronto, quando surgir notícia muito quente.
# Você só clica em "Postar". (Exige o computador ligado e você logado no X no navegador.)
AUTO_OPEN_BROWSER = _bool("AUTO_OPEN_BROWSER", "false")
AUTO_OPEN_MIN_SCORE = float(os.getenv("AUTO_OPEN_MIN_SCORE", "7"))
CHECK_INTERVAL_MIN = int(os.getenv("CHECK_INTERVAL_MIN", "5"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "4"))
MAX_DRAFTS_PER_HOUR = int(os.getenv("MAX_DRAFTS_PER_HOUR", "4"))
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "6"))
POST_LANGUAGE = os.getenv("POST_LANGUAGE", "português do Brasil")
PROFILE_STYLE = os.getenv("PROFILE_STYLE", "direto, informativo e com leve toque de humor")

# Palavras que aumentam a nota de relevância (edite à vontade)
KEYWORDS = [
    "openai", "anthropic", "claude", "chatgpt", "gpt", "gemini", "llama", "deepseek",
    "nvidia", "apple", "google", "microsoft", "meta", "amazon", "tesla", "spacex",
    "samsung", "intel", "amd", "iphone", "android", "windows", "linux",
    "ai", "ia", "inteligência artificial", "chip", "gpu", "quantum", "quântico",
    "launch", "launches", "launched", "lança", "lançamento", "lançou",
    "announces", "announced", "anuncia", "anunciou", "released", "release",
    "vazamento", "leak", "leaked", "breach", "hack", "hacked", "vulnerability",
    "vulnerabilidade", "acquires", "acquisition", "adquire", "funding",
    "layoffs", "demissões", "open source", "código aberto", "ban", "banned",
    "lawsuit", "processo", "outage", "fora do ar", "robot", "robô",
]


def validate():
    missing = []
    need = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    if LLM_PROVIDER == "gemini":
        need.append("GEMINI_API_KEY")
    elif LLM_PROVIDER == "anthropic":
        need.append("ANTHROPIC_API_KEY")
    elif LLM_PROVIDER != "none":
        raise SystemExit("LLM_PROVIDER deve ser: gemini, anthropic ou none")
    if PUBLISH_MODE == "api" and not DRY_RUN:
        need += ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    elif PUBLISH_MODE not in ("manual", "api"):
        raise SystemExit("PUBLISH_MODE deve ser: manual ou api")
    for name in need:
        if not globals()[name]:
            missing.append(name)
    if missing:
        raise SystemExit("Faltam variáveis no arquivo .env: " + ", ".join(missing))
