# Mary Education Hub

Hub escolar familiar para Lucas (1º ano) e Malu (7º ano).

## PRD de referência

`/home/agent/agents/openclaw/config/media/inbound/MARY_EDUCATION_HUB_PRD---fe91c685-e326-4c79-b627-d2dd2bc3ece1.pdf`

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + SQLAlchemy 2 (async) + Pydantic v2 + Alembic |
| Frontend | Next.js 14 App Router + TypeScript + Tailwind CSS |
| Banco | PostgreSQL 16 (porta 55433 na VPS) |
| Cache | Redis 7 (porta 6381 na VPS) |
| Container | Docker Compose |
| IA | Claude Haiku via OpenRouter (`OPENROUTER_API_KEY`) |

## Acesso

```
Frontend:  http://178.104.16.39:3100
API:       http://178.104.16.39:8100/api/v1
API docs:  http://178.104.16.39:8100/docs
Login:     eduardo@mary.local / mary2026
```

## Subir / reiniciar

```bash
cd /home/agent/agents/openclaw/workspace/mary-education-hub
docker compose up -d            # subir (sem rebuild)
docker compose up -d --build    # rebuild completo
docker compose restart backend  # só o backend
docker compose logs -f backend  # acompanhar logs
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
POSTGRES_PASSWORD=mary_edu_2026
JWT_SECRET=<troque em produção>
OPENCLAW_INGEST_SECRET=mary-openclaw-telegram-2026
OPENROUTER_API_KEY=<sua chave OpenRouter>
OPENROUTER_MODEL=anthropic/claude-haiku-4-5
```

## Histórico de versões

### v0.1.1 — MVP Tier A (13/04/2026)
- Família, guardiões, alunos (Lucas + Malu) com perfis e interesses
- CRUD de materiais (upload, texto, links) com soft delete
- CRUD de tarefas com filtros por aluno/disciplina/status/data
- Dashboard: resumo por aluno + visão do dia (vence hoje, atrasadas, em andamento)
- Auth JWT (access 30min + refresh 7d, armazenado no Redis)
- Seed idempotente: família, guardiões, alunos, disciplinas, currículo, tarefas demo
- Tier B estrutural: `classified_tasks`, `study_plans`, `study_sessions`, `provider_accounts`, `provider_sync_logs`, `mary_reports`

### v0.2 — Integração OpenClaw + AI Classification (15/04/2026)

**Integração OpenClaw ↔ Mary:**
- `POST /api/v1/ingestion/openclaw/agenda` — ingestão de agenda do Telegram via OpenClaw
- `GET  /api/v1/ingestion/openclaw/summary` — resumo do dia para todos os alunos (auth via secret header)
- `PATCH /api/v1/ingestion/openclaw/tasks/{id}/status` — marcar tarefa como feita via OpenClaw
- Skill `mj-mary` criada em `workspace/skills/mj-mary/` — CLI com comandos: `hoje`, `resumo`, `tarefas`, `marcar-feita`, `ingerir`
- Provider Plurall: upsert de conta + sync manual do snapshot do portal
- `mary_provider.py` adicionado ao `mj-briefing` → seção `🎒 EDUCAÇÃO — LUCAS & MALU` no briefing matinal

**AI Classification (Claude Haiku via OpenRouter):**
- `classification_service.py` — implementa `IClassificationService`; classifica tarefas em itens curriculares, avalia dificuldade (fácil/normal/difícil), estima duração e confiança
- `POST /tasks/{id}/classify` — classificar uma tarefa via guardian JWT
- `POST /tasks/classify-pending` — batch: classifica todas as pendentes
- Auto-classificação na ingestão: novas tarefas do OpenClaw são classificadas automaticamente
- Frontend: botão "Classificar IA" no TaskCard + badge com resultado; botão "Classificar pendentes" no Dashboard

## Estrutura do projeto

```
mary-education-hub/
├── docker-compose.yml
├── .env / .env.example
│
├── backend/
│   ├── app/
│   │   ├── api/          # auth, families, students, materials, tasks,
│   │   │   │               curriculum, dashboard, providers, ingestion
│   │   ├── models/       # SQLAlchemy (Tier A funcional + Tier B estrutural)
│   │   ├── schemas/      # Pydantic v2
│   │   ├── services/     # auth, material, task, curriculum, upload,
│   │   │                   provider, classification
│   │   └── interfaces/   # contratos IClassificationService, IPlanningService,
│   │                       ISchoolProvider, IEnglishProvider, IReportingService
│   └── alembic/          # migrações (1 migration inicial, 15 tabelas)
│
├── frontend/
│   └── src/
│       ├── app/          # dashboard, today, students, materials, tasks,
│       │                   integrations, layout raiz + login
│       ├── components/   # layout, tasks, materials, students, filters, ui
│       ├── hooks/        # useAuth, useStudents, useMaterials, useTasks, useSubjects
│       └── lib/          # api.ts, auth.ts, types.ts, labels.ts
│
└── scripts/
    ├── seed.sh
    └── reset-db.sh
```

## Endpoints principais

### Auth
| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Email + senha → JWT |
| POST | `/auth/refresh` | Renovar token |
| GET  | `/auth/me` | Perfil do guardião atual |

### Ingestão OpenClaw (auth via `X-OpenClaw-Secret`)
| Método | Path | Descrição |
|--------|------|-----------|
| POST  | `/ingestion/openclaw/agenda` | Ingerir itens de agenda do Telegram |
| GET   | `/ingestion/openclaw/summary` | Resumo do dia (todos os alunos) |
| PATCH | `/ingestion/openclaw/tasks/{id}/status` | Atualizar status de tarefa |

### Classificação IA
| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/tasks/{id}/classify` | Classificar tarefa com Claude |
| POST | `/tasks/classify-pending` | Batch: classificar todas pendentes |

## Roadmap

| Versão | Escopo | Status |
|--------|--------|--------|
| v0.1.1 | MVP Tier A (CRUD completo, dashboard, auth, seed) | ✅ done |
| v0.2 | Integração OpenClaw, AI Classification | ✅ done |
| v0.3 | Reports semanais (IReportingService), BNCC import, notificações | pendente |
| v0.4 | Planner inteligente (IPlanningService), study_plans/sessions | pendente |
| v0.5 | TellMe/Plurall adapters reais, MacmillanAdapter | pendente |
| v0.6 | Multi-família (SaaS), student self-service, gamificação | pendente |
