# 🎬 yt-watcher

O **yt-watcher** é um sistema em Python para monitorar canais do YouTube via feeds RSS e gerar uma página web estática responsiva (`docs/index.html`) com o histórico de vídeos novos agrupados por dia.

Possui controle de estado via `localStorage` (marcar o que já foi visto/copiado, copiar links com 1 clique), indicadores de status/falhas e suporte a notificações no Telegram.

---

## 🛠️ Como Adicionar Novos Canais

Edite o arquivo `canais.json` e adicione objetos com o nome e o handle do canal (com `@`):

```json
[
  {
    "nome": "Renato P",
    "handle": "@renatop1986"
  },
  {
    "nome": "Perfumorista",
    "handle": "@Perfumorista"
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
   *(Na primeira execução, ele busca vídeos dos últimos 2 dias. Nas próximas, adiciona novos vídeos salvando o status em `data/status.json`).*

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
2. Obtenha o seu **Chat ID** (enviando uma mensagem para o bot).
3. No seu repositório no GitHub, vá em **Settings** > **Secrets and variables** > **Actions**.
4. Adicione os seguintes Secrets/Vars:
   - Secret `TELEGRAM_TOKEN`: Token do seu Bot.
   - Secret `TELEGRAM_CHAT_ID`: Seu ID numérico no Telegram.
   - Var `PAGES_URL`: URL pública da sua página no GitHub Pages (ex: `https://<usuario>.github.io/yt-watcher/`).

---

## 🤖 Automação e Agendamento

O workflow do GitHub Actions (`.github/workflows/watch.yml`) é executado **diariamente às 20h no horário de Brasília (23:07 UTC)** e também pode ser disparado manualmente na aba **Actions** (`workflow_dispatch`).

Em caso de falha completa de todos os canais em uma verificação, o script aborta com código de erro, sinalizando a execução no GitHub Actions para envio de alertas por e-mail.
