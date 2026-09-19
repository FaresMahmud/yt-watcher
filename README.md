# 🎬 yt-watcher

O **yt-watcher** é um sistema em Python para monitorar canais do YouTube via feeds RSS e gerar uma página web estática responsiva (`docs/index.html`) com o histórico de vídeos novos agrupados por dia.

Possui controle de estado via `localStorage` (marcar o que já foi visto/copiado, copiar links com 1 clique) e suporte a notificações no Telegram.

---

## 🛠️ Como Adicionar Novos Canais

Edite o arquivo `canais.json` e adicione objetos com o nome e o handle do canal (com `@`):

```json
[
  {
    "nome": "Fireship",
    "handle": "@Fireship"
  },
  {
    "nome": "Marques Brownlee",
    "handle": "@mkbhd"
  }
]
```

> **Nota:** Não é necessário descobrir o `channel_id` manualmente. O script `resolve_ids.py` busca a página do canal e insere automaticamente a chave `"channel_id": "UC..."` em `canais.json`.

---

## 💻 Como Rodar Localmente

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute o monitoramento:**
   ```bash
   python monitor.py
   ```
   *(Na primeira execução, ele busca vídeos dos últimos 2 dias. Nas próximas, apenas adiciona os novos vídeos).*

3. **Gere a página HTML:**
   ```bash
   python gerar_pagina.py
   ```

4. Abra o arquivo `docs/index.html` no seu navegador.

---

## 🌐 Como Ativar o GitHub Pages

1. Envie este repositório para o **GitHub**.
2. No seu repositório no GitHub, vá em **Settings** > **Pages**.
3. Em **Build and deployment** > **Source**, selecione **Deploy from a branch**.
4. Em **Branch**, selecione a branch `main` e a pasta `/docs`, e clique em **Save**.
5. Sua página ficará acessível na URL do GitHub Pages (ex: `https://<seu-usuario>.github.io/<repositorio>/`).

---

## 🔔 Como Configurar Notificações no Telegram (Opcional)

Se desejar receber uma mensagem no Telegram sempre que houver novos vídeos:

1. Crie um Bot no Telegram via [@BotFather](https://t.me/BotFather) e guarde o **Token**.
2. Obtenha o seu **Chat ID** (enviando uma mensagem para o bot e consultando via `https://api.telegram.org/bot<TOKEN>/getUpdates` ou usando um bot como `@userinfobot`).
3. No seu repositório no GitHub, vá em **Settings** > **Secrets and variables** > **Actions**.
4. Adicione os seguintes Repository Secrets:
   - `TELEGRAM_TOKEN`: Token do seu Bot.
   - `TELEGRAM_CHAT_ID`: Seu ID numérico no Telegram.
   - `PAGES_URL`: URL pública da sua página no GitHub Pages (ex: `https://<usuario>.github.io/yt-watcher/`).

Se essas variáveis não forem cadastradas, o script continuará rodando normalmente sem enviar notificações.

---

## 🤖 Automação

O workflow do GitHub Actions (`.github/workflows/watch.yml`) é executado **a cada 3 horas** e também pode ser disparado manualmente na aba **Actions** (`workflow_dispatch`). Ele busca os vídeos novos, atualiza o `data/videos.json` e gera a página `docs/index.html` atualizada.
