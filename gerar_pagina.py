import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil import parser as dateparser

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

DATA_DIR = "data"
VIDEOS_FILE = os.path.join(DATA_DIR, "videos.json")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
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


def carregar_status() -> tuple[str, str]:
    """Carrega data/status.json e retorna (ultima_verificacao_fmt, banner_html)."""
    status_data = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8-sig") as f:
                status_data = json.load(f)
        except Exception as e:
            print(f"[gerar_pagina] Erro ao ler status.json: {e}")

    ultima_execucao_iso = status_data.get("ultima_execucao", "")
    status_canais = status_data.get("canais", [])

    agora_sp = datetime.now(SAO_PAULO_TZ)

    ultima_verificacao_str = "Desconhecida"
    atrasado = False

    if ultima_execucao_iso:
        try:
            dt_exec = dateparser.parse(ultima_execucao_iso).astimezone(SAO_PAULO_TZ)
            ultima_verificacao_str = dt_exec.strftime("%d/%m %H:%M")
            horas_passadas = (agora_sp - dt_exec).total_seconds() / 3600.0
            if horas_passadas > 36:
                atrasado = True
        except Exception:
            pass

    canais_com_falha = [c for c in status_canais if not c.get("ok")]

    alertas_html = []

    if atrasado:
        alertas_html.append(f"<li>⚠️ <strong>Aviso de Atraso:</strong> A última verificação ocorreu há mais de 36 horas ({ultima_verificacao_str}).</li>")

    for c in canais_com_falha:
        nome = c.get("nome", "Canal")
        erro = c.get("erro", "Erro desconhecido")
        u_suc = c.get("ultimo_sucesso")
        u_suc_str = "nunca"
        if u_suc:
            try:
                u_suc_dt = dateparser.parse(u_suc).astimezone(SAO_PAULO_TZ)
                u_suc_str = u_suc_dt.strftime("%d/%m %H:%M")
            except Exception:
                u_suc_str = u_suc

        alertas_html.append(f"<li>🔴 <strong>Falha no canal '{nome}':</strong> {erro} (Último sucesso: {u_suc_str})</li>")

    banner_html = ""
    if alertas_html:
        items_alertas = "\n".join(alertas_html)
        banner_html = f"""
        <div class="status-alert-banner">
            <div class="status-alert-header">⚠️ Alerta de Monitoramento</div>
            <ul class="status-alert-list">
                {items_alertas}
            </ul>
        </div>
        """

    return ultima_verificacao_str, banner_html


def gerar_html(videos: list) -> str:
    ultima_verificacao_str, banner_html = carregar_status()

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
                    <div class="day-action-buttons">
                        <button class="btn-copy-day" data-day="{dia_key}">Copiar pendentes e marcar como pegos</button>
                        <button class="btn-uncheck-day" data-day="{dia_key}">Desmarcar dia</button>
                    </div>
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
            --secondary-color: #6c757d;
            --secondary-hover: #5c636a;
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
                --secondary-color: #71717a;
                --secondary-hover: #52525b;
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
            justify-content: space-between;
            gap: 0.5rem;
            font-size: 0.95rem;
            color: var(--text-muted);
            flex-wrap: wrap;
            padding-top: 0.5rem;
            border-top: 1px solid var(--border-color);
            margin-top: 0.5rem;
        }}

        .controls-bar label {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            cursor: pointer;
            user-select: none;
        }}

        .controls-bar input {{
            width: 1.1rem;
            height: 1.1rem;
            cursor: pointer;
        }}

        .last-check-info {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        /* Banner de Alerta de Status */
        .status-alert-banner {{
            background-color: #fff3cd;
            color: #664d03;
            border: 1px solid #ffecb5;
            border-left: 5px solid #ffc107;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }}

        @media (prefers-color-scheme: dark) {{
            .status-alert-banner {{
                background-color: #332701;
                color: #ffda6a;
                border: 1px solid #664d03;
                border-left: 5px solid #ffc107;
            }}
        }}

        .status-alert-header {{
            font-weight: 700;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }}

        .status-alert-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            font-size: 0.9rem;
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

        .day-action-buttons {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
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

        .btn-uncheck-day {{
            background-color: var(--secondary-color);
            color: #ffffff;
            border: none;
            padding: 0.4rem 0.85rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.15s ease;
        }}

        .btn-uncheck-day:hover {{
            background-color: var(--secondary-hover);
        }}

        .copy-feedback {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--success-color);
        }}

        /* Toast Container e Estilos */
        .toast-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 90vw;
        }}

        .toast {{
            background-color: var(--card-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.9rem;
            font-weight: 500;
            animation: toast-slide-in 0.25s ease-out;
        }}

        @keyframes toast-slide-in {{
            from {{ transform: translateY(20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        .btn-toast-undo {{
            background-color: transparent;
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.15s ease, color 0.15s ease;
        }}

        .btn-toast-undo:hover {{
            background-color: var(--primary-color);
            color: #ffffff;
        }}

        /* Rodapé */
        footer {{
            margin-top: 2.5rem;
            padding: 1.5rem 0;
            text-align: center;
            border-top: 1px solid var(--border-color);
        }}

        .footer-actions {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .footer-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 0.85rem;
            cursor: pointer;
            text-decoration: underline;
            opacity: 0.85;
            transition: opacity 0.2s ease, color 0.2s ease;
        }}

        .footer-btn:hover {{
            opacity: 1;
            color: var(--primary-color);
        }}

        .footer-btn.btn-clear-all:hover {{
            color: #dc3545;
        }}

        /* Lista de Vídeos */
        .video-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
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
            <div class="last-check-info">
                Última verificação: <strong>{ultima_verificacao_str}</strong>
            </div>
        </div>
    </header>

    {banner_html}

    <main id="dias-container">
        {conteudo_dias}
    </main>

    <footer>
        <div class="footer-actions">
            <button id="btn-export-ytw" class="footer-btn">Exportar marcações</button>
            <button id="btn-import-ytw" class="footer-btn">Importar marcações</button>
            <button id="btn-clear-all-ytw" class="footer-btn btn-clear-all">Limpar todas as marcações</button>
            <input type="file" id="file-import-ytw" accept=".json" style="display: none;">
        </div>
    </footer>

    <div id="toast-container" class="toast-container"></div>

    <script>
        document.addEventListener("DOMContentLoaded", () => {{
            // 1. Migração de chaves do localStorage para o novo formato 'ytw:'
            const keysToMigrate = [];
            for (let i = 0; i < localStorage.length; i++) {{
                const key = localStorage.key(i);
                if (key) keysToMigrate.push(key);
            }}

            keysToMigrate.forEach(key => {{
                if (key.startsWith("ytw_checked_")) {{
                    const vid = key.replace("ytw_checked_", "");
                    const val = localStorage.getItem(key);
                    localStorage.setItem("ytw:done:" + vid, val);
                    localStorage.removeItem(key);
                }} else if (key === "ytw_hide_completed") {{
                    const val = localStorage.getItem(key);
                    localStorage.setItem("ytw:hide_completed", val);
                    localStorage.removeItem(key);
                }}
            }});

            const toggleOcultar = document.getElementById("toggle-ocultar-concluidos");

            const savedHideCompleted = localStorage.getItem("ytw:hide_completed") === "1";
            toggleOcultar.checked = savedHideCompleted;
            if (savedHideCompleted) {{
                document.body.classList.add("hide-completed");
            }}

            toggleOcultar.addEventListener("change", (e) => {{
                const isChecked = e.target.checked;
                localStorage.setItem("ytw:hide_completed", isChecked ? "1" : "0");
                if (isChecked) {{
                    document.body.classList.add("hide-completed");
                }} else {{
                    document.body.classList.remove("hide-completed");
                }}
            }});

            const videoCheckboxes = document.querySelectorAll(".video-checkbox");
            videoCheckboxes.forEach(cb => {{
                const id = cb.getAttribute("data-id");
                const state = localStorage.getItem("ytw:done:" + id);
                if (state === "1") {{
                    cb.checked = true;
                }}
                cb.addEventListener("change", () => {{
                    localStorage.setItem("ytw:done:" + id, cb.checked ? "1" : "0");
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
                        localStorage.setItem("ytw:done:" + id, cb.checked ? "1" : "0");
                    }});
                    updateUI();
                }});
            }});

            // Toast Informativo genérico
            function showInfoToast(message) {{
                const container = document.getElementById("toast-container");
                const toast = document.createElement("div");
                toast.className = "toast";

                const textSpan = document.createElement("span");
                textSpan.textContent = message;

                toast.appendChild(textSpan);
                container.appendChild(toast);

                setTimeout(() => {{
                    toast.remove();
                }}, 4000);
            }}

            // Toast de Desfazer
            let toastTimer = null;
            function showUndoToast(message, onUndo) {{
                const container = document.getElementById("toast-container");
                container.innerHTML = ""; // Limpa toasts anteriores

                const toast = document.createElement("div");
                toast.className = "toast";

                const textSpan = document.createElement("span");
                textSpan.textContent = message;

                const undoBtn = document.createElement("button");
                undoBtn.className = "btn-toast-undo";
                undoBtn.textContent = "Desfazer";

                undoBtn.addEventListener("click", () => {{
                    if (toastTimer) clearTimeout(toastTimer);
                    onUndo();
                    toast.remove();
                }});

                toast.appendChild(textSpan);
                toast.appendChild(undoBtn);
                container.appendChild(toast);

                if (toastTimer) clearTimeout(toastTimer);
                toastTimer = setTimeout(() => {{
                    toast.remove();
                }}, 8000);
            }}

            // Event Listeners para 'Copiar pendentes e marcar como pegos'
            const copyButtons = document.querySelectorAll(".btn-copy-day");
            copyButtons.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    const dayKey = btn.getAttribute("data-day");
                    const dayGroup = document.querySelector(`.day-group[data-day="${{dayKey}}"]`);
                    const feedbackEl = document.getElementById(`feedback-${{dayKey}}`);
                    if (!dayGroup) return;

                    const dayCbs = Array.from(dayGroup.querySelectorAll(".video-checkbox"));
                    const uncheckedCbs = dayCbs.filter(cb => !cb.checked);

                    if (uncheckedCbs.length === 0) {{
                        if (feedbackEl) {{
                            feedbackEl.textContent = "Nenhum link pendente!";
                            setTimeout(() => {{ feedbackEl.textContent = ""; }}, 2500);
                        }}
                        return;
                    }}

                    // Salva estado anterior dos checkboxes do dia para o desfazer
                    const previousStates = dayCbs.map(cb => ({{
                        cb: cb,
                        id: cb.getAttribute("data-id"),
                        wasChecked: cb.checked
                    }}));

                    const urlsToCopy = uncheckedCbs.map(cb => cb.getAttribute("data-url")).filter(Boolean);
                    const urlsText = urlsToCopy.join("\\n");

                    navigator.clipboard.writeText(urlsText).then(() => {{
                        uncheckedCbs.forEach(cb => {{
                            cb.checked = true;
                            const id = cb.getAttribute("data-id");
                            localStorage.setItem("ytw:done:" + id, "1");
                        }});

                        updateUI();

                        showUndoToast(`${{urlsToCopy.length}} link(s) copiado(s) — `, () => {{
                            previousStates.forEach(item => {{
                                item.cb.checked = item.wasChecked;
                                localStorage.setItem("ytw:done:" + item.id, item.wasChecked ? "1" : "0");
                            }});
                            updateUI();
                        }});

                    }}).catch(err => {{
                        console.error("Erro ao copiar para clipboard:", err);
                        if (feedbackEl) {{
                            feedbackEl.textContent = "Erro ao copiar!";
                        }}
                    }});
                }});
            }});

            // Event Listeners para 'Desmarcar dia'
            const uncheckButtons = document.querySelectorAll(".btn-uncheck-day");
            uncheckButtons.forEach(btn => {{
                btn.addEventListener("click", () => {{
                    const dayKey = btn.getAttribute("data-day");
                    const dayGroup = document.querySelector(`.day-group[data-day="${{dayKey}}"]`);
                    if (!dayGroup) return;

                    const dayCbs = dayGroup.querySelectorAll(".video-checkbox");
                    dayCbs.forEach(cb => {{
                        cb.checked = false;
                        const id = cb.getAttribute("data-id");
                        localStorage.setItem("ytw:done:" + id, "0");
                    }});
                    updateUI();
                }});
            }});

            // Exportar Marcações
            const btnExport = document.getElementById("btn-export-ytw");
            if (btnExport) {{
                btnExport.addEventListener("click", () => {{
                    const data = {{}};
                    for (let i = 0; i < localStorage.length; i++) {{
                        const key = localStorage.key(i);
                        if (key && key.startsWith("ytw:")) {{
                            data[key] = localStorage.getItem(key);
                        }}
                    }}
                    const jsonStr = JSON.stringify(data, null, 2);
                    const blob = new Blob([jsonStr], {{ type: "application/json" }});
                    const url = URL.createObjectURL(blob);

                    const now = new Date();
                    const year = now.getFullYear();
                    const month = String(now.getMonth() + 1).padStart(2, "0");
                    const day = String(now.getDate()).padStart(2, "0");

                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `ytw-marcacoes-${{year}}-${{month}}-${{day}}.json`;
                    a.click();
                    URL.revokeObjectURL(url);

                    showInfoToast("Marcações exportadas com sucesso!");
                }});
            }}

            // Importar Marcações
            const btnImport = document.getElementById("btn-import-ytw");
            const fileInput = document.getElementById("file-import-ytw");

            if (btnImport && fileInput) {{
                btnImport.addEventListener("click", () => {{
                    fileInput.click();
                }});

                fileInput.addEventListener("change", (e) => {{
                    const file = e.target.files[0];
                    if (!file) return;

                    const reader = new FileReader();
                    reader.onload = (event) => {{
                        try {{
                            const importedData = JSON.parse(event.target.result);
                            if (typeof importedData !== "object" || importedData === null) {{
                                throw new Error("Formato inválido");
                            }}

                            let count = 0;
                            for (const [key, val] of Object.entries(importedData)) {{
                                if (!key.startsWith("ytw:")) continue;

                                const existingVal = localStorage.getItem(key);
                                // MERGE: nunca substitui '1' por '0' ou ausência
                                if (key.startsWith("ytw:done:")) {{
                                    if (existingVal === "1") {{
                                        continue;
                                    }}
                                    if (val === "1") {{
                                        localStorage.setItem(key, "1");
                                        count++;
                                    }}
                                }} else {{
                                    localStorage.setItem(key, String(val));
                                    count++;
                                }}
                            }}

                            // Atualiza os checkboxes em tela sem recarregar
                            document.querySelectorAll(".video-checkbox").forEach(cb => {{
                                const id = cb.getAttribute("data-id");
                                if (localStorage.getItem("ytw:done:" + id) === "1") {{
                                    cb.checked = true;
                                }}
                            }});

                            // Atualiza preference do toggle se houver
                            const savedHideCompleted = localStorage.getItem("ytw:hide_completed") === "1";
                            if (toggleOcultar) {{
                                toggleOcultar.checked = savedHideCompleted;
                                if (savedHideCompleted) {{
                                    document.body.classList.add("hide-completed");
                                }} else {{
                                    document.body.classList.remove("hide-completed");
                                }}
                            }}

                            updateUI();
                            showInfoToast(`${{count}} marcação(ões) importada(s) com sucesso!`);
                        }} catch (err) {{
                            console.error("Erro na importação:", err);
                            alert("Erro ao importar o arquivo JSON. Certifique-se de que é um backup válido.");
                        }} finally {{
                            fileInput.value = "";
                        }}
                    }};
                    reader.readAsText(file);
                }});
            }}

            // Limpar todas as marcações salvas (apenas chaves com prefixo ytw:)
            const btnClearAll = document.getElementById("btn-clear-all-ytw");
            if (btnClearAll) {{
                btnClearAll.addEventListener("click", () => {{
                    if (confirm("Tem certeza que deseja limpar todas as marcações salvas?")) {{
                        const keysToRemove = [];
                        for (let i = 0; i < localStorage.length; i++) {{
                            const key = localStorage.key(i);
                            if (key && key.startsWith("ytw:")) {{
                                keysToRemove.push(key);
                            }}
                        }}
                        keysToRemove.forEach(k => localStorage.removeItem(k));

                        document.querySelectorAll(".video-checkbox").forEach(cb => {{
                            cb.checked = false;
                        }});
                        updateUI();
                    }}
                }});
            }}

            function updateUI() {{
                const dayGroups = document.querySelectorAll(".day-group");
                let totalPendentesGeral = 0;

                dayGroups.forEach(group => {{
                    const dayCbs = Array.from(group.querySelectorAll(".video-checkbox"));
                    const totalNoDia = dayCbs.length;
                    const pendentesNoDia = dayCbs.filter(cb => !cb.checked).length;
                    totalPendentesGeral += pendentesNoDia;

                    const pendingEl = group.querySelector(".day-pending");
                    if (pendingEl) {{
                        pendingEl.textContent = pendentesNoDia;
                    }}

                    const saCb = group.querySelector(".select-all-day");
                    if (saCb) {{
                        saCb.checked = (pendentesNoDia === 0 && totalNoDia > 0);
                    }}

                    if (pendentesNoDia === 0 && totalNoDia > 0) {{
                        group.classList.add("completed");
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

                dayGroups.forEach(group => {{
                    if (!group.hasAttribute("data-listener-added")) {{
                        group.setAttribute("data-listener-added", "true");
                        group.addEventListener("toggle", () => {{
                            group.setAttribute("data-user-toggled", "true");
                        }});
                    }}
                }});

                const totalGeralEl = document.getElementById("total-pendentes");
                if (totalGeralEl) {{
                    totalGeralEl.textContent = totalPendentesGeral;
                }}
            }}

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
