import calendar
import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import feedparser
import requests
from dateutil import parser as dateparser

from resolve_ids import resolve_channel_ids

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
DIAS_INICIAIS = 2

DATA_DIR = "data"
VIDEOS_FILE = os.path.join(DATA_DIR, "videos.json")
CANAIS_FILE = "canais.json"


def get_published_datetime(entry) -> datetime:
    """Extrai e converte a data de publicação da entrada para fuso America/Sao_Paulo."""
    if hasattr(entry, "published") and entry.published:
        dt = dateparser.parse(entry.published)
    elif hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime.fromtimestamp(calendar.timegm(entry.published_parsed), tz=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(SAO_PAULO_TZ)


def enviar_notificacao_telegram(novos_videos_qtd: int) -> None:
    """Envia notificação pelo Telegram se as variáveis de ambiente existirem."""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    pages_url = os.environ.get("PAGES_URL", "")

    if not token or not chat_id:
        print("[monitor] Variáveis TELEGRAM_TOKEN e/ou TELEGRAM_CHAT_ID não encontradas. Notificação pulada.")
        return

    mensagem = f"🎬 <b>{novos_videos_qtd} vídeo(s) novo(s)</b> no YT-Watcher!"
    if pages_url:
        mensagem += f"\n\n🔗 Acesse em: {pages_url}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("[monitor] Notificação enviada para o Telegram com sucesso!")
        else:
            print(f"[monitor] Erro ao enviar notificação Telegram (status {resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"[monitor] Exceção ao enviar notificação Telegram: {e}")


def executar_monitor() -> None:
    # 1. Garante que os canais possuem channel_id
    resolve_channel_ids(CANAIS_FILE)

    if not os.path.exists(CANAIS_FILE):
        print(f"[monitor] {CANAIS_FILE} não existe.")
        return

    with open(CANAIS_FILE, "r", encoding="utf-8") as f:
        canais = json.load(f)

    # 2. Carrega vídeos existentes
    os.makedirs(DATA_DIR, exist_ok=True)
    videos_existentes = []
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            try:
                videos_existentes = json.load(f)
            except json.JSONDecodeError:
                videos_existentes = []

    primeira_execucao = len(videos_existentes) == 0
    ids_conhecidos = {v["id"] for v in videos_existentes}

    agora_sp = datetime.now(SAO_PAULO_TZ)
    descoberto_em_iso = agora_sp.isoformat()

    if primeira_execucao:
        data_corte = (agora_sp - timedelta(days=DIAS_INICIAIS)).date()
    else:
        datas_gravadas = [dateparser.parse(v["publicado_em"]).date() for v in videos_existentes if "publicado_em" in v]
        data_corte = min(datas_gravadas) if datas_gravadas else (agora_sp - timedelta(days=DIAS_INICIAIS)).date()

    novos_videos = []

    print(f"[monitor] Primeira execução? {primeira_execucao} (Data de corte: {data_corte})")

    for canal in canais:
        cid = canal.get("channel_id")
        nome_canal = canal.get("nome", "Canal sem nome")

        if not cid:
            print(f"[monitor] Pulando {nome_canal}: sem channel_id.")
            continue

        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        print(f"[monitor] Buscando feed do canal '{nome_canal}' ({cid})...")

        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            print(f"[monitor] Aviso: falha ao ler feed de {nome_canal}: {feed.get('bozo_exception', 'Erro desconhecido')}")
            continue

        for entry in feed.entries:
            vid = entry.get("id", entry.get("link", ""))
            if hasattr(entry, "yt_videoid"):
                vid = entry.yt_videoid

            if vid in ids_conhecidos:
                continue

            pub_dt = get_published_datetime(entry)

            # Ignora vídeos anteriores à data de corte
            if pub_dt.date() < data_corte:
                continue

            titulo = entry.get("title", "Sem título")
            url = entry.get("link", f"https://www.youtube.com/watch?v={vid}")

            novo_video = {
                "id": vid,
                "canal": nome_canal,
                "titulo": titulo,
                "url": url,
                "publicado_em": pub_dt.isoformat(),
                "descoberto_em": descoberto_em_iso
            }

            novos_videos.append(novo_video)
            ids_conhecidos.add(vid)

    if novos_videos:
        todos_videos = novos_videos + videos_existentes
        # Ordena por publicado_em decrescente
        todos_videos.sort(key=lambda v: v.get("publicado_em", ""), reverse=True)

        with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
            json.dump(todos_videos, f, indent=2, ensure_ascii=False)

        print(f"[monitor] {len(novos_videos)} novos vídeos adicionados em {VIDEOS_FILE}.")

        enviar_notificacao_telegram(len(novos_videos))
    else:
        print("[monitor] Nenhum vídeo novo encontrado nesta execução.")


if __name__ == "__main__":
    executar_monitor()
