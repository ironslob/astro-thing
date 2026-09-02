# Railway staging

Astro Window is a set of ordinary containers plus Postgres and Redis. Nothing in application code depends on Railway.

Suggested services in one Railway project:

| Railway service | Image / source | Notes |
| --- | --- | --- |
| `backend` | `backend/Dockerfile` | Start command is the image default. Health check `/health`. The image entrypoint runs `alembic upgrade head` then seeds empty catalogues for non-Celery commands. Set `RUN_DB_INIT=0` if you move that to a release command. |
| `worker` | same image | `celery -A app.celery_app.celery_app worker -l info` — entrypoint skips migrate/seed. |
| `beat` | same image | `celery -A app.celery_app.celery_app beat -l info` — entrypoint skips migrate/seed. |
| `frontend` | `frontend/Dockerfile` | Build arg `VITE_API_BASE_URL=/api/v1` if you put API and UI on one domain, or the public backend URL. |
| Postgres | Railway plugin | Set `DATABASE_URL=postgresql+psycopg://...` |
| Redis | Railway plugin | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |

Variables to copy from `.env.example`: `SECRET_KEY`, `SMTP_*`, `FRONTEND_BASE_URL`, `OPEN_METEO_BASE_URL`, `ENVIRONMENT=staging`.

Point a public domain at a reverse proxy (Railway edge, or a small nginx service using `gateway/nginx.conf`) so cookies are first-party: UI on `/`, API on `/api`.

Migrations: only the API process should run `alembic upgrade head` and catalogue seed. Worker and beat share the image but skip that when the command is `celery`. That avoids Alembic lock races and a 14k-row OpenNGC import on every scheduler start.
