# Wine Cellar

A personal wine-collection tracker with an AI sommelier. Catalog bottles, track
drinking windows and consumption, and get streamed pairing advice and
recommendations powered by Claude.

## Architecture

```
frontend/   Next.js 16 (App Router) + Tailwind 4 + TanStack Query + Clerk — deployed on Vercel
backend/    FastAPI + psycopg2 (pooled) + Anthropic SDK               — deployed on Railway
            Postgres                                                  — Railway managed
```

- **Auth**: Clerk issues JWTs in the browser; the backend verifies them against
  Clerk's JWKS (`auth.py`). Every row is scoped to the verified `user_id`.
- **AI**: free-text features (pairings, recommendations, what's-for-dinner)
  stream token-by-token over Server-Sent Events; the structured wine lookup
  returns JSON that's parsed into form fields.
- **DB access**: a `ThreadedConnectionPool` with dead-connection recycling and
  TCP keepalives (`database.py`); schema/indexes are created idempotently at
  startup.

## Environment variables

### Backend (required — startup fails fast if missing)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `ANTHROPIC_API_KEY` | Claude API key for sommelier features |
| `CLERK_JWKS_URL` | Clerk instance JWKS endpoint for JWT verification |

### Backend (optional)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Model for the free-text sommelier features |
| `ANTHROPIC_VALUE_MODEL` | `claude-haiku-4-5` | Model for web-search market-value lookups (cheap extraction) |
| `AI_RATE_LIMIT_PER_MINUTE` | `20` | Per-user cap on AI calls (wallet protection) |
| `BULK_VALUE_LIMIT` | `60` | Max bottles priced per bulk valuation run |
| `VALUE_CONCURRENCY` | `5` | Bottles valued in parallel during a bulk run |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated exact CORS origins |
| `ALLOWED_ORIGIN_REGEX` | `https://wine-cellar.*\.vercel\.app` | CORS regex for Vercel deploys |

Market-value lookups use Claude's web search tool, which the org admin must
enable in the Claude Console and which bills ~$10 per 1,000 searches.

### Frontend

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend base URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` | Clerk |

## Local development

```bash
# Backend
cd backend
cp .env.example .env               # then fill in real values
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload          # http://localhost:8000

# Frontend
cd frontend
cp .env.example .env.local         # then fill in real values
npm install
npm run dev                        # http://localhost:3000
```

Real `.env` / `.env.local` files are gitignored and never committed — they
live only on your machine (and in the Railway/Vercel dashboards in production).
The committed `.env.example` files document what each one needs.

## Tests

```bash
cd backend && pytest               # API surface, pool recycling, prompt builders
cd frontend && npx tsc --noEmit && npx eslint && npm run build
```

## Operational notes

- **Streaming**: the SSE endpoints set `Cache-Control: no-transform`; anything
  placed in front of the backend must pass streamed bodies through unbuffered.
- **Rate limiter** is in-process; if the backend ever runs multiple
  workers/instances, move it to a shared store (Redis).
- **Legacy rows**: rows created before auth have `user_id IS NULL` and are
  intentionally invisible/immutable via the API. To claim them:
  `UPDATE bottles SET user_id = '<your_clerk_user_id>' WHERE user_id IS NULL;`

## Future-proofing roadmap (pre-commercialization)

- Replace startup DDL with real migrations (Alembic).
- `user_id` → `NOT NULL` once legacy rows are claimed.
- Shared rate limiting + per-plan quotas; usage metering for AI calls.
- CI running the backend/frontend checks above on PRs.
- Frontend component tests (Vitest + Testing Library).
