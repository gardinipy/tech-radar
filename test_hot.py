"""Simula uma notícia MUITO quente (nota 9.0) para testar o fluxo completo:
IA escreve o rascunho -> Telegram recebe -> navegador abre o X com o texto pronto.

ATENÇÃO: é uma notícia FALSA. Não clique em Postar no X! (o texto vem marcado como TESTE)
"""
import webbrowser

import config
import db
import notifier
import sources
import writer

config.validate()
db.init()

fake = sources.Item(
    source="Teste",
    title="Nvidia announces new GPU that doubles AI performance and halves power use",
    url="https://example.com/teste-noticia-falsa",
    summary="The company unveiled the new chip today and said it will ship next quarter.",
)
SCORE = 9.0

text = writer.draft(fake)
if not text:
    raise SystemExit("A IA respondeu SKIP; rode de novo.")
text = "🧪 TESTE - NÃO POSTAR\n\n" + text

did = db.add_draft("teste-hot-" + str(id(fake)), text, fake.url)
notifier.send_draft(did, text, fake, SCORE, "⚠️ Gerado SEM IA (Gemini indisponível)." if writer.last_fallback else "")
print(f"Rascunho #{did} enviado ao Telegram (nota {SCORE}).")

if config.AUTO_OPEN_BROWSER and SCORE >= config.AUTO_OPEN_MIN_SCORE:
    webbrowser.open(notifier.intent_url(text))
    print("Navegador aberto com o X. Feche a aba SEM postar.")
else:
    print("AUTO_OPEN_BROWSER está false no .env, então o navegador não abriu.")
