#!/bin/sh
set -eu
cd /app
python -m alembic upgrade head
python -m app.importers.seed
exec "$@"
