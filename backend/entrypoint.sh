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

exec "$@"
