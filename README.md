# Astro Window

A mobile-first UK web app that answers two questions for beginner astrophotographers:

1. When should I go outside?
2. What should I point at?

Anonymous use is the whole product. Sign-in is only for saving places and watching how a forecast changes.

## Local run

```bash
cp .env.example .env   # optional; Compose already has safe local defaults
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080).

- Try **Brighton & Hove** on the home screen (real coordinates, live weather — not a fake forecast).
- Or search `Hove`, `Brighton`, or a postcode such as `BN3 2AB`.
- Magic-link emails appear in MailHog: [http://localhost:8025](http://localhost:8025).

The first backend start runs migrations and imports the bundled catalogue + UK places.

### Without Docker

Backend (Python 3.12+ / 3.13):

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
export DATABASE_URL=sqlite+pysqlite:///./astro_window.db
alembic upgrade head
python -m app.importers.seed
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Celery (needs Redis):

```bash
celery -A app.celery_app.celery_app worker -l info
celery -A app.celery_app.celery_app beat -l info
```

## Tests

No live weather or catalogue APIs. Fixtures and fakes only.

```bash
cd backend && pytest -q
cd frontend && npm test
```

```bash
cd backend && ruff check app tests && black --check app tests
cd frontend && npm run lint && npm run typecheck
```

## Architecture

- **Frontend:** React, Vite, TypeScript, TanStack Query, React Router.
- **Backend:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2.
- **Data:** PostgreSQL (app state) + Redis (cache locks, magic links, Celery, rate limits).
- **Weather:** one `WeatherProvider` call per uncached ~5 km geohash cell, covering the three-night horizon. Fresh TTL 30 minutes; stale-but-usable for 2 hours if the provider is down.
- **Sky:** Astropy, local/offline. No live ephemeris API.
- **Jobs:** Celery Beat hourly refresh of saved locations, grouped by weather cell. Identical assessments are not written again.

Public API (also at `/docs` outside production):

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/health` | no |
| GET | `/api/v1/locations/search?q=` | no |
| GET | `/api/v1/forecast/windows?lat=&lon=` | no |
| GET | `/api/v1/forecast/targets?lat=&lon=&start=&end=` | no |
| POST | `/api/v1/auth/magic-link` | no |
| GET | `/api/v1/auth/verify` | no |
| GET | `/api/v1/me` | cookie |
| CRUD | `/api/v1/me/locations` | yes |

## Environment variables

See [`.env.example`](.env.example). Important keys:

- `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`
- `SECRET_KEY` — session HMAC
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_FROM`
- `FRONTEND_BASE_URL` — used in magic-link emails
- `OPEN_METEO_BASE_URL`
- `VITE_API_BASE_URL` — baked into the frontend image (`/api/v1` behind the gateway)

## Catalogue import

Default seed: `data/catalogue/beginner_dsos.json` (Andromeda, Orion Nebula, Pleiades, Double Cluster, and other northern beginner objects).

```bash
python -m app.importers.seed
python -m app.importers.openngc   # optional, if you add OpenNGC NGC.csv
```

## Deployment

- **Local:** Docker Compose as above.
- **Staging:** Railway — see [docs/railway.md](docs/railway.md).
- **Production target:** AWS — see [docs/aws.md](docs/aws.md). Domain code has no Railway-specific behaviour.

## Data licences

See [data/licences/ATTRIBUTION.md](data/licences/ATTRIBUTION.md). Footer credit is required for Open-Meteo, GeoNames, and OpenNGC.
