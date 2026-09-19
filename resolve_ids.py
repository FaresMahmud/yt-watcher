import json
import os
import re
import urllib.request

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def fetch_channel_id(handle: str) -> str | None:
    """Busca a página do canal e extrai o channel_id."""
    clean_handle = handle.strip()
    if not clean_handle.startswith("@"):
        clean_handle = f"@{clean_handle}"
    
    url = f"https://www.youtube.com/{clean_handle}"
    req = urllib.request.Request(url, headers=HEADERS)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
            patterns = [
                r'itemprop="identifier" content="([A-Za-z0-9_-]+)"',
                r'channel_id=([A-Za-z0-9_-]+)',
                r'"channelId":"([A-Za-z0-9_-]+)"',
                r'href="https://www.youtube.com/channel/([A-Za-z0-9_-]+)"',
            ]
            
            for pat in patterns:
                match = re.search(pat, html)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"[resolve_ids] Erro ao buscar canal {clean_handle}: {e}")
    
    return None

def resolve_channel_ids(filepath: str = "canais.json") -> None:
    """Carrega canais.json, resolve IDs faltantes e salva o arquivo de volta."""
    if not os.path.exists(filepath):
        print(f"[resolve_ids] Arquivo {filepath} não encontrado.")
        return

    with open(filepath, "r", encoding="utf-8-sig") as f:
        canais = json.load(f)

    alterado = False
    for canal in canais:
        if not canal.get("channel_id"):
            handle = canal.get("handle", "")
            print(f"[resolve_ids] Buscando channel_id para {handle}...")
            cid = fetch_channel_id(handle)
            if cid:
                canal["channel_id"] = cid
                alterado = True
                print(f"[resolve_ids] Sucesso: {handle} -> {cid}")
            else:
                print(f"[resolve_ids] Não foi possível resolver ID para {handle}")

    if alterado:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(canais, f, indent=2, ensure_ascii=False)
        print(f"[resolve_ids] {filepath} atualizado.")
    else:
        print(f"[resolve_ids] Todos os canais já possuem channel_id.")

if __name__ == "__main__":
    resolve_channel_ids()
