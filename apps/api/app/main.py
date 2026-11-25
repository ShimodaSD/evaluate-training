import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

log = logging.getLogger("app")


def setup_logging(log_file: str) -> None:
    """Erros da API, da IA e da Garmin no console e em LOG_FILE (rotativo, 5 x 1 MB)."""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    log.handlers.clear()
    for handler in (
        logging.StreamHandler(),
        RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"),
    ):
        handler.setFormatter(formatter)
        log.addHandler(handler)
    log.setLevel(logging.INFO)


async def _log_http_error(request: Request, exc: HTTPException):
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    log.log(level, "%s %s -> %s: %s", request.method, request.url.path, exc.status_code, exc.detail)
    return await http_exception_handler(request, exc)


async def _log_validation_error(request: Request, exc: RequestValidationError):
    log.warning("%s %s -> 422: %s", request.method, request.url.path, exc.errors())
    return await request_validation_exception_handler(request, exc)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_file)
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(HTTPException, _log_http_error)
    app.add_exception_handler(RequestValidationError, _log_validation_error)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
