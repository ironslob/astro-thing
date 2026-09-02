#!/bin/sh
set -eu
cd /app

# Migrate/seed only for the API process. Worker and beat share this image and
# would otherwise race Alembic and re-import the catalogue on every start.
run_init=0
case "${RUN_DB_INIT:-auto}" in
  1|true|yes) run_init=1 ;;
  0|false|no) run_init=0 ;;
  *)
    case "${1:-}" in
      celery) run_init=0 ;;
      *) run_init=1 ;;
    esac
    ;;
esac

if [ "$run_init" = 1 ]; then
  python -m alembic upgrade head
  python -m app.importers.seed
fi

# Railway injects PORT but does not expand ${PORT:-8000} in start commands.
# Ignore any --port the platform passed and bind the API ourselves.
if [ "${1:-}" = "uvicorn" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi

exec "$@"
