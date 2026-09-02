#!/bin/sh
set -eu
PORT="${PORT:-80}"
cat > /etc/nginx/conf.d/default.conf <<EOF
server {
    listen ${PORT};
    listen [::]:${PORT} ipv6only=on;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
exec nginx -g "daemon off;"
