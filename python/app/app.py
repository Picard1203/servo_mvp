"""FastAPI application assembly: routers and domain-error mapping.

Construction of services lives in deps.py (cached providers). This module
only builds the ASGI app and maps domain exceptions to HTTP responses.
Startup initialization (logging, background threads, relay) is done
explicitly in main.py.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import (ActiveZeroError, DatumZeroError,
                                 InvalidReadingError, LockedError,
                                 MovingError, NotFoundError,
                                 OutOfTravelError, StepError)
from app.routers import servo, stream, system, telemetry, zeros


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application.

    Returns:
        The configured application.
    """
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)
    app.include_router(servo.router)
    app.include_router(stream.router)
    app.include_router(zeros.router)
    app.include_router(telemetry.router)
    app.include_router(system.router)
    _register_error_handlers(app)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True),
                  name="static")

    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Maps domain exceptions to HTTP responses.

    Args:
        app: The FastAPI application.

    Returns:
        None.
    """

    def error(status: int, detail: str, **extra) -> JSONResponse:
        """Builds a JSON error body.

        Args:
            status: HTTP status code.
            detail: Error description.
            **extra: Additional response fields.

        Returns:
            The JSON response.
        """
        return JSONResponse(status_code=status,
                            content={"detail": detail, **extra})

    @app.exception_handler(LockedError)
    async def _locked(request: Request, exc: LockedError) -> JSONResponse:
        return error(409, str(exc), reason="locked")

    @app.exception_handler(MovingError)
    async def _moving(request: Request, exc: MovingError) -> JSONResponse:
        return error(409, str(exc), reason="moving")

    @app.exception_handler(NotFoundError)
    async def _missing(request: Request, exc: NotFoundError) -> JSONResponse:
        return error(404, str(exc))

    @app.exception_handler(ActiveZeroError)
    async def _active(request: Request, exc: ActiveZeroError) -> JSONResponse:
        return error(409, str(exc), reason="active_zero")

    @app.exception_handler(DatumZeroError)
    async def _datum(request: Request, exc: DatumZeroError) -> JSONResponse:
        return error(409, str(exc), reason="datum_zero")

    @app.exception_handler(OutOfTravelError)
    async def _travel(request: Request,
                      exc: OutOfTravelError) -> JSONResponse:
        return error(422, str(exc), reason="out_of_travel")

    @app.exception_handler(InvalidReadingError)
    async def _reading(request: Request,
                       exc: InvalidReadingError) -> JSONResponse:
        return error(409, str(exc), reason="invalid_reading")

    @app.exception_handler(StepError)
    async def _step(request: Request, exc: StepError) -> JSONResponse:
        return error(422, str(exc), reason="step")
