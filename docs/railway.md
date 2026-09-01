# Railway staging

Astro Window is a set of ordinary containers plus Postgres and Redis. Nothing in application code depends on Railway.

Suggested services in one Railway project:

| Railway service | Image / source | Notes |
| --- | --- | --- |
| `backend` | `backend/Dockerfile` | Start command is the image default. Health check `/health`. Run `alembic upgrade head` as a release command if you disable the image entrypoint. |
| `worker` | same image | `celery -A app.celery_app.celery_app worker -l info` |
| `beat` | same image | `celery -A app.celery_app.celery_app beat -l info` |
| `frontend` | `frontend/Dockerfile` | Build arg `VITE_API_BASE_URL=/api/v1` if you put API and UI on one domain, or the public backend URL. |
| Postgres | Railway plugin | Set `DATABASE_URL=postgresql+psycopg://...` |
| Redis | Railway plugin | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |

Variables to copy from `.env.example`: `SECRET_KEY`, `SMTP_*`, `FRONTEND_BASE_URL`, `OPEN_METEO_BASE_URL`, `ENVIRONMENT=staging`.

Point a public domain at a reverse proxy (Railway edge, or a small nginx service using `gateway/nginx.conf`) so cookies are first-party: UI on `/`, API on `/api`.

Migrations: the backend entrypoint already runs `alembic upgrade head` then seeds empty catalogues. That is safe to repeat.
