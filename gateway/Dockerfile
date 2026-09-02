FROM nginx:1.30-alpine
COPY nginx.railway.template /etc/nginx/templates/default.conf.template
COPY railway-entrypoint.sh /railway-entrypoint.sh
RUN chmod +x /railway-entrypoint.sh
EXPOSE 80
CMD ["/railway-entrypoint.sh"]
