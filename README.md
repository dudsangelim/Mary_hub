# Mary Education Hub

Repo base para o PRD "Mary Education Hub (MVP v0.1.1)".

## Fonte do PRD

- `/home/agent/agents/openclaw/config/media/inbound/MARY_EDUCATION_HUB_PRD---fe91c685-e326-4c79-b627-d2dd2bc3ece1.pdf`

## Escopo aplicado

- Implementar somente o escopo MVP Tier A funcional.
- Tier B deve existir apenas como estrutura/modelo, sem endpoints/UI/serviços.

## Stack

- FastAPI + SQLAlchemy 2 + Pydantic v2 + Alembic
- Next.js 14 App Router + TypeScript + Tailwind CSS
- PostgreSQL 16 + Redis 7
- Docker Compose

## Estrutura

- `backend/`: API, models, schemas, services, interfaces, seed e migrações
- `frontend/`: App Router, páginas do MVP, componentes e hooks
- `scripts/seed.sh`: roda seed manualmente
- `scripts/reset-db.sh`: reinicia stack e banco

## Subir localmente

1. Copie `.env.example` para `.env`.
2. Execute `docker compose up --build`.
3. Acesse `http://localhost:3100`.
4. Login seed: `eduardo@mary.local` / `mary2026`

## Observações

- Tier B existe apenas em modelos/migração/interfaces.
- Não há integração externa, scraping, IA ou planner avançado.
