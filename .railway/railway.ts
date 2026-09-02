import {
  defineRailway,
  github,
  group,
  postgres,
  project,
  redis,
  service,
} from "railway/iac";

const REPO = "ironslob/astro-thing";
const BRANCH = "main";

export default defineRailway((ctx) => {
  const db = postgres("Postgres");
  const cache = redis("Redis");

  const appEnv = {
    ENVIRONMENT: "staging",
    LOG_LEVEL: "INFO",
    SECRET_KEY: ctx.randomString("app-secret"),
    SCORING_VERSION: "1.0.0",
    DATABASE_URL: db.env.DATABASE_URL,
    REDIS_URL: cache.env.REDIS_URL,
    CELERY_BROKER_URL: cache.env.REDIS_URL,
    CELERY_RESULT_BACKEND: cache.env.REDIS_URL,
    FRONTEND_BASE_URL: "https://${{gateway.RAILWAY_PUBLIC_DOMAIN}}",
    SESSION_COOKIE_NAME: "astro_session",
    SESSION_COOKIE_SECURE: "true",
    OPEN_METEO_BASE_URL: "https://api.open-meteo.com",
    OPEN_METEO_GEOCODING_BASE_URL: "https://geocoding-api.open-meteo.com",
    POSTCODES_IO_BASE_URL: "https://api.postcodes.io",
  };

  const backendSource = github(REPO, { branch: BRANCH });
  const backendBuild = {
    builder: "DOCKERFILE" as const,
    dockerfilePath: "backend/Dockerfile",
    watchPatterns: ["backend/**", "data/catalogue/**"],
  };

  const backend = service("backend", {
    source: backendSource,
    build: backendBuild,
    start: "/app/entrypoint.sh uvicorn app.main:app --host 0.0.0.0 --port 8000",
    healthcheck: "/health",
    healthcheckTimeout: 600,
    env: appEnv,
  });

  const worker = service("worker", {
    source: github(REPO, { branch: BRANCH }),
    build: backendBuild,
    start: "celery -A app.celery_app.celery_app worker -l info",
    env: appEnv,
  });

  const beat = service("beat", {
    source: github(REPO, { branch: BRANCH }),
    build: backendBuild,
    start: "celery -A app.celery_app.celery_app beat -l info",
    env: appEnv,
  });

  const frontend = service("frontend", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "frontend" }),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "Dockerfile",
      watchPatterns: ["frontend/**"],
    },
    env: {
      VITE_API_BASE_URL: "/api/v1",
    },
  });

  const gateway = service("gateway", {
    source: github(REPO, { branch: BRANCH, rootDirectory: "gateway" }),
    build: {
      builder: "DOCKERFILE",
      dockerfilePath: "Dockerfile",
      watchPatterns: ["gateway/**"],
    },
    healthcheck: "/health",
    healthcheckTimeout: 300,
    env: {
      BACKEND_UPSTREAM: "http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}",
      FRONTEND_UPSTREAM: "http://${{frontend.RAILWAY_PRIVATE_DOMAIN}}:${{frontend.PORT}}",
    },
  });

  return project("shimmering-quietude", {
    resources: [
      group("Data", [db, cache]),
      group("App", [backend, worker, beat]),
      group("Web", [frontend, gateway]),
    ],
  });
});
