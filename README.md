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

Compose images: PostgreSQL 18, Redis 8, nginx 1.30, Mailpit, Python 3.14, Node 24. If you already ran an older Compose stack, recreate volumes once so Postgres 18 can initialise (`docker compose down -v`).

- Try **Brighton & Hove** on the home screen (real coordinates, live weather — not a fake forecast).
- Or search `Hove`, `Brighton`, or a postcode such as `BN3 2AB`.
- Magic-link emails appear in Mailpit: [http://localhost:8025](http://localhost:8025).

The first backend start runs migrations and imports the OpenNGC catalogue plus bright named stars.

Location search uses live Open-Meteo Geocoding (place names) and postcodes.io (UK postcodes), cached in Redis. This is a documented exception to the spec preference for a bundled UK place dataset. Browser geolocation still does not call a geocoder.

### Without Docker

Backend (Python 3.12+; images and CI use 3.14):

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

No live weather, geocoding, or catalogue APIs. Fixtures and fakes only.

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
| GET | `/api/v1/catalogue/search?q=` | no |
| GET | `/api/v1/forecast/windows?lat=&lon=` | no |
| GET | `/api/v1/forecast/targets?lat=&lon=&start=&end=&object=` | no |
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
- `OPEN_METEO_GEOCODING_BASE_URL`, `POSTCODES_IO_BASE_URL`
- `VITE_API_BASE_URL` — baked into the frontend image (`/api/v1` behind the gateway)

## Catalogue import

Default seed: OpenNGC `data/catalogue/NGC.csv` + `addendum.csv`, plus `data/catalogue/bright_stars.json`. Auto-rank uses objects with a beginner prior of 55 or higher (Andromeda, Orion Nebula, Pleiades, and other northern beginner targets still lead).

```bash
python -m app.importers.seed
```

## Deployment

- **Local:** Docker Compose as above.
- **Staging:** Railway — see [docs/railway.md](docs/railway.md).
- **Production target:** AWS — see [docs/aws.md](docs/aws.md). Domain code has no Railway-specific behaviour.

## Data licences

See [data/licences/ATTRIBUTION.md](data/licences/ATTRIBUTION.md). Footer credit is required for Open-Meteo (weather and geocoding / GeoNames), postcodes.io, and OpenNGC.
