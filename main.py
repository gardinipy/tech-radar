"""Loop principal do Tech Radar."""
import time
import traceback
import webbrowser

import config
import db
import notifier
import publisher
import scorer
import sources
import writer


def cycle():
    first_run = db.is_empty()
    items = sources.collect_all()
    known = db.known_sources()
    new = [i for i in items if not db.seen(i.id)]
    print(f"[ciclo] {len(items)} itens coletados, {len(new)} novos")
    for it in new:
        db.save_item(it)
    # Fonte que acabou de ser adicionada: só memoriza o que ela já tinha (evita enxurrada de rascunhos)
    boot = [i for i in new if i.source not in known and not i.source.startswith("Página:")]
    if boot and not first_run:
        print(f"[ciclo] {len(boot)} itens de fontes novas memorizados, sem rascunho")
        boot_ids = {i.id for i in boot}
        new = [i for i in new if i.id not in boot_ids]

    if first_run:
        print("[ciclo] Primeira execução: marquei o que já existe como visto (sem rascunhos).")
        return

    cutoff = time.time() - config.MAX_AGE_HOURS * 3600
    recent = db.recent_items(12)
    candidates, all_scored = [], []
    for it in new:
        if it.published and it.published < cutoff:
            continue
        s = scorer.score_item(it, recent)
        db.set_score(it.id, s)
        all_scored.append((s, it))
        if s >= config.MIN_SCORE:
            candidates.append((s, it))
    candidates.sort(key=lambda x: -x[0])
    all_scored.sort(key=lambda x: -x[0])
    for s, it in all_scored[:3]:
        print(f"   melhor nota {s} (mínima {config.MIN_SCORE}): [{it.source}] {it.title[:70]}")
    if not candidates:
        print("[ciclo] nenhuma notícia atingiu a nota mínima neste ciclo")

    for s, it in candidates:
        if db.drafts_last_hour() >= config.MAX_DRAFTS_PER_HOUR:
            print("[ciclo] limite de rascunhos por hora atingido")
            break
        if scorer.is_duplicate(it.title, db.recent_drafted_titles(12)):
            continue
        try:
            text = writer.draft(it)
        except Exception as e:
            print(f"[erro] IA falhou ({config.LLM_PROVIDER}): {e}")
            db.forget_item(it.id)  # tenta de novo no próximo ciclo
            continue
        if not text:
            continue
        did = db.add_draft(it.id, text, it.url)
        try:
            note = "⚠️ Gerado SEM IA (Gemini indisponível). Revise o texto antes de postar." if writer.last_fallback else ""
            notifier.send_draft(did, text, it, s, note)
            print(f"[ciclo] rascunho #{did} enviado: {it.title}")
            if config.AUTO_OPEN_BROWSER and s >= config.AUTO_OPEN_MIN_SCORE:
                webbrowser.open(notifier.intent_url(text))
                print(f"[ciclo] X aberto no navegador com o rascunho #{did} (é só clicar em Postar)")
        except Exception as e:
            print(f"[erro] Telegram falhou: {e}")


def handle_update(u):
    cb = u.get("callback_query")
    if not cb:
        return
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    if str(chat_id) != str(config.TELEGRAM_CHAT_ID):
        return  # ignora qualquer pessoa que não seja você
    try:
        action, did = cb["data"].split(":")
        did = int(did)
    except Exception:
        return
    mid = msg.get("message_id")

    if action == "no":
        db.set_draft_status(did, "rejected")
        notifier.answer_callback(cb["id"], "Descartado")
        notifier.remove_buttons(chat_id, mid)
        return

    if not db.claim_draft(did):
        notifier.answer_callback(cb["id"], "Esse rascunho já foi processado")
        return
    d = db.get_draft(did)
    notifier.remove_buttons(chat_id, mid)
    try:
        tweet_id = publisher.post(d["text"])
        db.set_draft_status(did, "posted", tweet_id)
        notifier.answer_callback(cb["id"], "Postado!")
        if tweet_id == "dry-run":
            notifier.send_text(f"🧪 (Simulação) Rascunho #{did} NÃO foi ao X porque DRY_RUN=true.")
        else:
            notifier.send_text(f"✅ Postado! https://x.com/i/status/{tweet_id}")
    except Exception as e:
        db.set_draft_status(did, "failed")
        notifier.answer_callback(cb["id"], "Erro ao postar")
        notifier.send_text(f"❌ Erro ao postar o rascunho #{did}: {e}")


def main():
    config.validate()
    db.init()
    print(f"Tech Radar rodando | IA={config.LLM_PROVIDER} | publicação={config.PUBLISH_MODE} | a cada {config.CHECK_INTERVAL_MIN} min | nota mínima {config.MIN_SCORE}")
    try:
        notifier.send_text("✅ Tech Radar iniciado! Vou te avisar aqui quando surgir notícia quente.")
        print("[ok] Telegram funcionando (mensagem de início enviada)")
    except Exception as e:
        print(f"[ERRO] Não consegui falar com o Telegram: {e}")
        print("       Confira TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, e se você deu Start no bot.")
    offset, last = None, 0.0
    while True:
        if time.time() - last >= config.CHECK_INTERVAL_MIN * 60:
            try:
                cycle()
            except Exception:
                traceback.print_exc()
            last = time.time()
        try:
            for u in notifier.get_updates(offset, timeout=20):
                offset = u["update_id"] + 1
                handle_update(u)
        except Exception as e:
            print(f"[aviso] Telegram polling: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
