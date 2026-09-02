#!/bin/sh
set -eu
export PORT="${PORT:-80}"
export BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-http://backend:8000}"
export FRONTEND_UPSTREAM="${FRONTEND_UPSTREAM:-http://frontend:80}"

# nginx treats unbracketed IPv6 nameservers as host:port (fd12::10 → port 10).
resolver=""
for ns in $(awk '/^nameserver/{print $2}' /etc/resolv.conf); do
  case "$ns" in
    *:*) ns="[$ns]" ;;
  esac
  resolver="${resolver}${resolver:+ }${ns}"
done
export RESOLVER="${resolver:-1.1.1.1}"

envsubst '${PORT} ${BACKEND_UPSTREAM} ${FRONTEND_UPSTREAM} ${RESOLVER}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
