from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.catalogue import router as catalogue_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.locations import router as locations_router
from app.api.v1.me import router as me_router
from app.core.config import settings
from app.core.logging import configure_logging, new_request_id, request_id_ctx

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or new_request_id()
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["x-request-id"] = rid
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    logger.info("startup environment=%s scoring=%s", settings.environment, settings.scoring_version)
    yield


def create_app() -> FastAPI:
    docs = None if settings.environment == "production" else "/docs"
    redoc = None if settings.environment == "production" else "/redoc"
    application = FastAPI(
        title="Astro Window",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=docs,
        redoc_url=redoc,
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_base_url,
            "http://localhost:8080",
            "http://localhost:5173",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(locations_router, prefix="/api/v1")
    application.include_router(catalogue_router, prefix="/api/v1")
    application.include_router(forecast_router, prefix="/api/v1")
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(me_router, prefix="/api/v1")
    return application


app = create_app()
