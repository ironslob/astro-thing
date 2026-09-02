#!/bin/sh
set -eu
export PORT="${PORT:-80}"
export BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-http://backend:8000}"
export FRONTEND_UPSTREAM="${FRONTEND_UPSTREAM:-http://frontend:80}"
envsubst '${PORT} ${BACKEND_UPSTREAM} ${FRONTEND_UPSTREAM}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
