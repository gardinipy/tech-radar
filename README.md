# Tech Radar (versão 100% grátis)

Monitora fontes de tecnologia, avalia o que está "quente", gera um rascunho e te manda no
Telegram. Você toca em **Abrir no X**, o texto já vem preenchido, e só confirma o post.

## Custo: R$ 0
- Fontes (RSS, Hacker News, Reddit, GitHub): grátis.
- Telegram bot: grátis.
- IA: Gemini (camada gratuita do Google AI Studio) ou `LLM_PROVIDER=none` (sem IA).
- Publicação: manual via botão (a API do X é paga, então não usamos).
- Rodar: no seu próprio computador.

## Instalação

    python -m venv venv
    # Windows:  venv\Scripts\activate
    # Mac/Linux: source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env      # Windows: copy .env.example .env

## Chaves (todas grátis)
1. **Gemini**: aistudio.google.com > Get API key > `GEMINI_API_KEY`.
   Observação: na camada grátis o Google pode usar o conteúdo enviado para melhorar seus modelos
   (aqui só vão títulos e resumos de notícias públicas, então não é problema).
   Se der erro de modelo, troque `GEMINI_MODEL` por um modelo Flash listado no AI Studio.
2. **Telegram**: @BotFather > /newbot > `TELEGRAM_BOT_TOKEN`. Mande "oi" ao bot e rode
   `python get_chat_id.py` > `TELEGRAM_CHAT_ID`.

## Testar e rodar

    python smoke_test.py     # rascunho de teste no seu Telegram
    python main.py           # deixe rodando

Na primeira execução ele só memoriza o que já existe, sem gerar rascunhos.

## Ajustes
- Poucos rascunhos? Baixe `MIN_SCORE` (ex.: 4). Muitos? Suba (ex.: 8).
- Fontes: `RSS_FEEDS` e `PAGES` em `sources.py`. Palavras-chave: `KEYWORDS` em `config.py`.
- O limite grátis do Gemini é por minuto/dia; `MAX_DRAFTS_PER_HOUR` ajuda a ficar dentro dele.

## Upgrades pagos (opcionais)
- `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`: rascunhos escritos pelo Claude.
- `PUBLISH_MODE=api` + chaves do X + `DRY_RUN=false`: posta sozinho ao tocar em "Postar".
  A API do X cobra por uso (post comum ~US$ 0,015; com link, bem mais), então use `INCLUDE_LINK=false` nesse modo.
