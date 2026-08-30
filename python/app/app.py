"""FastAPI application assembly: routers and domain-error mapping."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from Logger461 import logger

from app.core.config import get_settings
from app.core.exceptions import ServoAppException
from app.routers import saved_positions, servo, stream, system, telemetry


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Returns:
        FastAPI: The configured application.
    """
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.include_router(servo.router)
    app.include_router(stream.router)
    app.include_router(saved_positions.router)
    app.include_router(telemetry.router)
    app.include_router(system.router)
    _register_error_handlers(app)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir() is True:
        app.mount("/", StaticFiles(directory=static_dir, html=True),
                  name="static")

    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Maps every domain exception to its HTTP response and log line.

    Args:
        app (FastAPI): The FastAPI application.
    """

    @app.exception_handler(ServoAppException)
    async def _domain_error(request: Request,
                           exc: ServoAppException) -> JSONResponse:
        """Builds the JSON error body and logs from the exception itself.

        Args:
            request (Request): The incoming HTTP request.
            exc (ServoAppException): The raised domain exception.

        Returns:
            JSONResponse: The JSON response.
        """
        logger.warning(exc.message,
                       metadata={"event": "domain_error",
                                 "error_code": exc.error_code,
                                 "reason": exc.reason},
                       extra=exc.metadata)
        return JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.message,
                                     "reason": exc.reason})
