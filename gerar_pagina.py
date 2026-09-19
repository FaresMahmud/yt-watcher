import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil import parser as dateparser

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

DATA_DIR = "data"
VIDEOS_FILE = os.path.join(DATA_DIR, "videos.json")
DOCS_DIR = "docs"
INDEX_HTML = os.path.join(DOCS_DIR, "index.html")

DIAS_DA_SEMANA = [
    "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"
]


def formatar_data_cabecalho(dt_iso: str) -> tuple[str, str]:
    """Retorna a chave da data (YYYY-MM-DD) e o título formatado (ex: 'Sexta, 19/09')."""
    try:
        dt = dateparser.parse(dt_iso).astimezone(SAO_PAULO_TZ)
    except Exception:
        dt = datetime.now(SAO_PAULO_TZ)

    chave_data = dt.strftime("%Y-%m-%d")
    nome_dia = DIAS_DA_SEMANA[dt.weekday()]
    dataFormatada = dt.strftime("%d/%m")
    titulo_dia = f"{nome_dia}, {dataFormatada}"

    return chave_data, titulo_dia


def gerar_html(videos: list) -> str:
    # Agrupa vídeos por dia de publicação
    grupos_por_dia = {}
    
    for v in videos:
        chave_data, titulo_dia = formatar_data_cabecalho(v.get("publicado_em", ""))
        if chave_data not in grupos_por_dia:
            grupos_por_dia[chave_data] = {
                "titulo": titulo_dia,
                "videos": []
            }
        grupos_por_dia[chave_data]["videos"].append(v)

    # Ordena os dias do mais recente para o mais antigo
    dias_ordenados = sorted(grupos_por_dia.keys(), reverse=True)

    html_grupos = []

    for dia_key in dias_ordenados:
        grupo = grupos_por_dia[dia_key]
        titulo_dia = grupo["titulo"]
        v_list = grupo["videos"]
        qtd_total = len(v_list)

        items_html = []
        for v in v_list:
            vid = v.get("id", "")
            canal = v.get("canal", "Canal")
            titulo = v.get("titulo", "Sem título")
            url = v.get("url", "#")

            items_html.append(f"""
            <li class="video-item" data-id="{vid}">
                <div class="video-row">
                    <input type="checkbox" class="video-checkbox" data-id="{vid}" data-day="{dia_key}" data-url="{url}">
                    <div class="video-content">
                        <div class="video-header">
                            <span class="channel-badge">{canal}</span>
                            <a href="{url}" target="_blank" rel="noopener" class="video-title-link">{titulo}</a>
                        </div>
                        <div class="video-url-container">
                            <a href="{url}" target="_blank" rel="noopener" class="video-url-link">{url}</a>
                        </div>
                    </div>
                </div>
            </li>
            """)

        items_str = "\n".join(items_html)

        grupo_html = f"""
        <details class="day-group" data-day="{dia_key}" open>
            <summary class="day-summary">
                <span class="day-title">{titulo_dia}</span>
                <span class="day-counter">
                    <strong class="day-total">{qtd_total}</strong> vídeos 
                    (<span class="day-pending">{qtd_total}</span> pendentes)
                </span>
            </summary>
            <div class="day-content">
                <div class="day-actions">
                    <label class="select-all-label">
                        <input type="checkbox" class="select-all-day" data-day="{dia_key}"> Marcar dia todo
                    </label>
                    <button class="btn-copy-day" data-day="{dia_key}">Copiar pendentes e marcar como pegos</button>
                    <span class="copy-feedback" id="feedback-{dia_key}"></span>
                </div>
                <ul class="video-list">
                    {items_str}
                </ul>
            </div>
        </details>
        """
        html_grupos.append(grupo_html)

    conteudo_dias = "\n".join(html_grupos) if html_grupos else "<p class='empty-msg'>Nenhum vídeo encontrado.</p>"

    html_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YT-Watcher — Monitor de Vídeos</title>
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #212529;
            --text-muted: #6c757d;
            --border-color: #dee2e6;
            --primary-color: #0d6efd;
            --primary-hover: #0b5ed7;
            --success-color: #198754;
            --badge-bg: #e9ecef;
            --badge-text: #495057;
            --accent-bg: #f1f3f5;
            --completed-opacity: 0.55;
            --shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #121214;
                --card-bg: #1c1c1f;
                --text-color: #e1e1e6;
                --text-muted: #a1a1aa;
                --border-color: #2e2e32;
                --primary-color: #3b82f6;
                --primary-hover: #2563eb;
                --success-color: #22c55e;
                --badge-bg: #27272a;
                --badge-text: #d4d4d8;
                --accent-bg: #27272a;
                --completed-opacity: 0.5;
                --shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }}
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.5;
            padding: 1rem;
            max-width: 800px;
            margin: 0 auto;
        }}

        header {{
            background-color: var(--card-bg);
            padding: 1.25rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
        }}

        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .total-badge {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--primary-color);
            background: var(--badge-bg);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
        }}

        .controls-bar {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.95rem;
            color: var(--text-muted);
            cursor: pointer;
            user-select: none;
        }}

        .controls-bar input {{
            width: 1.1rem;
            height: 1.1rem;
            cursor: pointer;
        }}

        /* Container de Dias */
        .day-group {{
            background-color: var(--card-bg);
            border-radius: 10px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            overflow: hidden;
            transition: opacity 0.2s ease, transform 0.2s ease;
        }}

        .day-group.completed {{
            opacity: var(--completed-opacity);
        }}

        body.hide-completed .day-group.completed {{
            display: none !important;
        }}

        .day-summary {{
            padding: 1rem;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: var(--accent-bg);
            user-select: none;
        }}

        .day-summary:hover {{
            opacity: 0.95;
        }}

        .day-counter {{
            font-size: 0.9rem;
            font-weight: normal;
            color: var(--text-muted);
        }}

        .day-content {{
            padding: 1rem;
        }}

        .day-actions {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            padding-bottom: 0.75rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .select-all-label {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
        }}

        .select-all-label input {{
            width: 1rem;
            height: 1rem;
            cursor: pointer;
        }}

        .btn-copy-day {{
            background-color: var(--primary-color);
            color: #ffffff;
            border: none;
            padding: 0.4rem 0.85rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.15s ease;
        }}

        .btn-copy-day:hover {{
            background-color: var(--primary-hover);
        }}

        .copy-feedback {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--success-color);
        }}

        /* Lista de Vídeos */
        .video-list {{
            list-style: none;
            display: flex;
            flex-direction: flex-column;
            gap: 0.75rem;
        }}

        .video-item {{
            padding: 0.6rem;
            border-radius: 8px;
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            transition: background-color 0.15s ease;
        }}

        .video-row {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .video-checkbox {{
            width: 1.25rem;
            height: 1.25rem;
            margin-top: 0.2rem;
            cursor: pointer;
            flex-shrink: 0;
        }}

        .video-content {{
            flex: 1;
            min-width: 0;
        }}

        .video-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 0.2rem;
        }}

        .channel-badge {{
            font-size: 0.75rem;
            font-weight: 700;
            background-color: var(--badge-bg);
            color: var(--badge-text);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            white-space: nowrap;
        }}

        .video-title-link {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-color);
            text-decoration: none;
            word-break: break-word;
        }}

        .video-title-link:hover {{
            color: var(--primary-color);
            text-decoration: underline;
        }}

        .video-url-container {{
            margin-top: 0.15rem;
        }}

        .video-url-link {{
            font-size: 0.8rem;
            color: var(--text-muted);
            word-break: break-all;
            text-decoration: none;
            font-family: monospace;
        }}

        .video-url-link:hover {{
            text-decoration: underline;
        }}

        .empty-msg {{
            text-align: center;
            color: var(--text-muted);
            padding: 2rem;
        }}
    </style>
</head>
<body>

    <header>
        <div class="header-top">
            <h1>🎬 YT-Watcher</h1>
            <div class="total-badge" id="total-pendentes-badge">
                <span id="total-pendentes">0</span> links pendentes no total
            </div>
        </div>
        <div class="controls-bar">
            <label class="select-all-label">
                <input type="checkbox" id="toggle-ocultar-concluidos">
                Ocultar dias concluídos
            </label>
        </div>
    </header>

    <main id="dias-container">
        {conteudo_dias}
    </main>

    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            const toggleOcultar = document.getElementById("toggle-ocultar-concluidos");

            // Carrega preferência do toggle de ocultar concluídos
            const savedHideCompleted = localStorage.getItem("ytw_hide_completed") === "1";
            toggleOcultar.checked = savedHideCompleted;
            if (savedHideCompleted) {{
                document.body.classList.add("hide-completed");
            }}

            toggleOcultar.addEventListener("change", (e) => {{
                const isChecked = e.target.checked;
                localStorage.setItem("ytw_hide_completed", isChecked ? "1" : "0");
                if (isChecked) {{
                    document.body.classList.add("hide-completed");
                }} else {{
                    document.body.classList.remove("hide-completed");
                }}
            }});

            // Carrega estado de todos os checkboxes de vídeos por ID
            const videoCheckboxes = document.querySelectorAll(".video-checkbox");
            videoCheckboxes.forEach(cb => {{
                const id = cb.getAttribute("data-id");
                const state = localStorage.getItem("ytw_checked_" + id);
                if (state === "1") {{
                    cb.checked = true;
                }}
                cb.addEventListener("change", () => {{
                    localStorage.setItem("ytw_checked_" + id, cb.checked ? "1" : "0");
                    updateUI();
                }});
            }});

            // Event Listeners para 'Marcar dia todo'
            const selectAllCheckboxes = document.querySelectorAll(".select-all-day");
            selectAllCheckboxes.forEach(saCb => {{
                saCb.addEventListener("change", (e) => {{
                    const dayKey = saCb.getAttribute("data-day");
                    const dayGroup = document.querySelector(`.day-group[data-day="${{dayKey}}"]`);
                    if (!dayGroup) return;

                    const dayCbs = dayGroup.querySelectorAll(".video-checkbox");
                    dayCbs.forEach(cb => {{
                        cb.checked = e.target.checked;
                        const id = cb.getAttribute("data-id");
                        localStorage.setItem("ytw_checked_" + id, cb.checked ? "1" : "0");
                    }});
                    updateUI();
                }});
            }});

            // Event Listeners para 'Copiar pendentes e marcar como pegos'
            const copyButtons = document.querySelectorAll(".btn-copy-day");
            copyButtons.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    const dayKey = btn.getAttribute("data-day");
                    const dayGroup = document.querySelector(`.day-group[data-day="${{dayKey}}"]`);
                    const feedbackEl = document.getElementById(`feedback-${{dayKey}}`);
                    if (!dayGroup) return;

                    const uncheckedCbs = Array.from(dayGroup.querySelectorAll(".video-checkbox:not(:checked)"));
                    if (uncheckedCbs.length === 0) {{
                        if (feedbackEl) {{
                            feedbackEl.textContent = "Nenhum link pendente!";
                            setTimeout(() => {{ feedbackEl.textContent = ""; }}, 2500);
                        }}
                        return;
                    }}

                    const urlsToCopy = uncheckedCbs.map(cb => cb.getAttribute("data-url")).filter(Boolean);
                    const urlsText = urlsToCopy.join("\\n");

                    navigator.clipboard.writeText(urlsText).then(() => {{
                        uncheckedCbs.forEach(cb => {{
                            cb.checked = true;
                            const id = cb.getAttribute("data-id");
                            localStorage.setItem("ytw_checked_" + id, "1");
                        }});

                        updateUI();

                        if (feedbackEl) {{
                            feedbackEl.textContent = `${{urlsToCopy.length}} link(s) copiado(s)!`;
                            setTimeout(() => {{ feedbackEl.textContent = ""; }}, 3000);
                        }}
                    }}).catch(err => {{
                        console.error("Erro ao copiar para clipboard:", err);
                        if (feedbackEl) {{
                            feedbackEl.textContent = "Erro ao copiar!";
                        }}
                    }});
                }});
            }});

            function updateUI() {{
                const dayGroups = document.querySelectorAll(".day-group");
                let totalPendentesGeral = 0;

                dayGroups.forEach(group => {{
                    const dayCbs = Array.from(group.querySelectorAll(".video-checkbox"));
                    const totalNoDia = dayCbs.length;
                    const pendentesNoDia = dayCbs.filter(cb => !cb.checked).length;
                    totalPendentesGeral += pendentesNoDia;

                    // Atualiza contador no cabeçalho do dia
                    const pendingEl = group.querySelector(".day-pending");
                    if (pendingEl) {{
                        pendingEl.textContent = pendentesNoDia;
                    }}

                    // Atualiza checkbox 'Marcar dia todo'
                    const saCb = group.querySelector(".select-all-day");
                    if (saCb) {{
                        saCb.checked = (pendentesNoDia === 0 && totalNoDia > 0);
                    }}

                    // Se o dia estiver 100% marcado
                    if (pendentesNoDia === 0 && totalNoDia > 0) {{
                        group.classList.add("completed");
                        // Recolhe o details apenas se ele não foi fechado manualmente pelo usuário antes
                        if (!group.hasAttribute("data-user-toggled")) {{
                            group.removeAttribute("open");
                        }}
                    }} else {{
                        group.classList.remove("completed");
                        if (!group.hasAttribute("data-user-toggled")) {{
                            group.setAttribute("open", "");
                        }}
                    }}
                }});

                // Marca data-user-toggled quando o usuário abre/fecha manualmente
                dayGroups.forEach(group => {{
                    if (!group.hasAttribute("data-listener-added")) {{
                        group.setAttribute("data-listener-added", "true");
                        group.addEventListener("toggle", () => {{
                            group.setAttribute("data-user-toggled", "true");
                        }});
                    }}
                }});

                // Atualiza contador geral no topo
                const totalGeralEl = document.getElementById("total-pendentes");
                if (totalGeralEl) {{
                    totalGeralEl.textContent = totalPendentesGeral;
                }}
            }}

            // Executa updateUI inicial
            updateUI();
        }});
    </script>
</body>
</html>
"""
    return html_completo


def gerar_pagina() -> None:
    videos = []
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8-sig") as f:
            try:
                videos = json.load(f)
            except json.JSONDecodeError:
                videos = []

    os.makedirs(DOCS_DIR, exist_ok=True)
    html_content = gerar_html(videos)

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[gerar_pagina] Página gerada com sucesso em {INDEX_HTML} ({len(videos)} vídeos).")


if __name__ == "__main__":
    gerar_pagina()
