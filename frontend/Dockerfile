# syntax=docker/dockerfile:1
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.30-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY railway-entrypoint.sh /railway-entrypoint.sh
COPY --from=build /app/dist /usr/share/nginx/html
RUN chmod +x /railway-entrypoint.sh
EXPOSE 80
CMD ["/railway-entrypoint.sh"]
