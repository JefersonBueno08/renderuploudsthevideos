# youtube-news-automation

Sistema 100% automático para **criar e publicar** conteúdo de **notícias** no YouTube (Shorts, vídeos longos e Community posts), com **fila**, **retries**, **auditoria** e **upload resiliente**.

## Stack

- **API**: FastAPI (Python)
- **Workers**: Celery + Redis
- **Banco**: PostgreSQL
- **Render**: FFmpeg (via container)
- **Upload**: YouTube Data API v3 (OAuth2)

## Rodar local (Docker)

Pré-requisitos: Docker Desktop.

Subir serviços:

```bash
docker compose up --build
```

URLs:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Rodar na web (recomendado se o PC é fraco)

### Opção A: Render (mais simples)

Este projeto já inclui `render.yaml` com:

- **1 Web Service** (API FastAPI)
- **1 Worker Service** (Celery)
- **PostgreSQL** + **Redis** gerenciados

Passo a passo:

1. Crie uma conta no Render e conecte seu GitHub.
2. Suba este projeto para um repositório no GitHub (pode ser “Upload files” pelo navegador).
3. No Render, escolha **New → Blueprint** e selecione o repo.
4. Aguarde o deploy.

Depois do deploy:

- Health: `https://SEU-SERVICO.onrender.com/health`

> Observação: o worker vai precisar de FFmpeg para render. Se o seu plano do Render não tiver pacotes do sistema disponíveis, a gente troca o deploy do worker para Docker ou para um provedor que permita instalar FFmpeg facilmente.

### Opção B: GitHub Codespaces (roda “na web”, mas é dev)

1. Suba o projeto para o GitHub.
2. Abra um Codespace.
3. Rode `docker compose up --build` lá dentro (sem pesar seu PC).

## Como funciona (alto nível)

1. `scheduler` cria uma `production` (formato + regras).
2. `collector` coleta notícias e cria `events`.
3. `script` gera roteiro.
4. `tts` gera narração.
5. `render` gera `final.mp4` e `thumb.png`.
6. `publisher` faz upload e agenda publicação.

## Configuração (YouTube)

Este repositório já deixa os pontos de integração prontos, mas você precisa:

1. Criar um projeto no Google Cloud.
2. Ativar **YouTube Data API v3**.
3. Configurar OAuth (Client ID/Secret).
4. Gerar e armazenar tokens (o sistema espera isso via env vars/arquivos).

> Observação: upload automatizado exige OAuth2 e respeita quota/rate limits.

