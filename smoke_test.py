"""Teste rápido: gera um rascunho FALSO com o Claude e manda pro seu Telegram."""
import config
import db
import notifier
import sources
import writer

config.validate()
db.init()
fake = sources.Item(
    source="Teste",
    title="OpenAI announces new open-weight model that runs on a laptop",
    url="https://example.com/teste",
    summary="The company said the model matches last year's flagship on several benchmarks and can run locally.",
)
text = writer.draft(fake)
print("Claude respondeu:", text)
if text:
    did = db.add_draft("teste-" + str(id(fake)), text, fake.url)
    notifier.send_draft(did, text, fake, 99)
    print("Enviado ao Telegram. Clique em Postar para testar o fluxo (com DRY_RUN=true nada vai ao X).")
