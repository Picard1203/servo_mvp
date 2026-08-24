"""Composition root: cached provider functions that construct and wire.

This is the ONLY module that names concrete classes. Each provider is
cached, so every component is a process-wide singleton built on first
use. Routers depend on the service providers via FastAPI's Depends;
main.py calls the same providers at startup to initialize eagerly and
to start background work.

Sprint-2 hardware swap happens in one place: get_servo_repository.
"""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.events import EventService
from app.db.database import Database
from app.relay.bridge_relay import BridgeRelay
from app.relay.mcu_log import McuLog
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.telemetry_repository import TelemetryRepository
from app.repositories.abstract.zero_repository import ZeroRepository
from app.repositories.concrete.bridge_servo_repository import (
    BridgeServoRepository)
from app.repositories.concrete.simulated_servo_repository import (
    SimulatedServoRepository)
from app.repositories.concrete.sqlite_telemetry_repository import (
    SqliteTelemetryRepository)
from app.repositories.concrete.sqlite_zero_repository import (
    SqliteZeroRepository)
from app.services.motion_service import MotionService
from app.services.servo_state import ServoStateStore
from app.services.telemetry_service import TelemetryService
from app.services.zero_service import ZeroService


@lru_cache
def get_event_service() -> EventService:
    """Returns the shared event buffer.

    Returns:
        The process-wide event service.
    """
    return EventService(get_settings().event_buffer_size)


@lru_cache
def get_database() -> Database:
    """Returns the shared database wrapper.

    Returns:
        The process-wide database.
    """
    return Database(get_settings().db_path)


@lru_cache
def get_servo_repository() -> ServoRepository:
    """Returns the servo repository chosen by use_hardware_servo.

    Simulated by default so the dev machine and the test suite need no
    hardware; the board sets USE_HARDWARE_SERVO=true in its .env. Range and
    dead zone are applied at construction either way, so the startup path is
    identical for both backends.

    Returns:
        The process-wide servo repository.
    """
    settings = get_settings()
    if settings.use_hardware_servo:
        repository: ServoRepository = BridgeServoRepository()
    else:
        repository = SimulatedServoRepository()
    repository.configure_range(settings.multi_turn_enabled,
                               settings.angle_resolution)
    repository.set_deadband(settings.servo_deadband_counts)
    return repository


@lru_cache
def get_zero_repository() -> ZeroRepository:
    """Returns the zero repository.

    Returns:
        The process-wide zero repository.
    """
    return SqliteZeroRepository(get_database())


@lru_cache
def get_telemetry_repository() -> TelemetryRepository:
    """Returns the telemetry repository.

    Returns:
        The process-wide telemetry repository.
    """
    return SqliteTelemetryRepository(get_database())


@lru_cache
def get_state_store() -> ServoStateStore:
    """Returns the atomic servo/lock/baseline state store.

    Returns:
        The process-wide state store.
    """
    settings = get_settings()
    return ServoStateStore(
        servo=get_servo_repository(), zeros=get_zero_repository(),
        settling_seconds=settings.settling_seconds,
        counts_per_turn=settings.counts_per_turn,
        servo_deg_per_output_deg=settings.servo_deg_per_output_deg,
        servo_direction=settings.servo_direction)


@lru_cache
def get_motion_service() -> MotionService:
    """Returns the motion service.

    Returns:
        The process-wide motion service.
    """
    return MotionService(get_servo_repository(), get_state_store(),
                         get_event_service(), get_settings())


@lru_cache
def get_zero_service() -> ZeroService:
    """Returns the zero service.

    Returns:
        The process-wide zero service.
    """
    return ZeroService(get_zero_repository(), get_servo_repository(),
                       get_event_service(), get_state_store())


@lru_cache
def get_telemetry_service() -> TelemetryService:
    """Returns the telemetry service.

    Returns:
        The process-wide telemetry service.
    """
    return TelemetryService(get_telemetry_repository(), get_state_store(),
                            get_settings())


@lru_cache
def get_relay() -> BridgeRelay:
    """Returns the Bridge relay.

    Returns:
        The process-wide relay.
    """
    return BridgeRelay(get_settings())


@lru_cache
def get_mcu_log() -> McuLog:
    """Returns the MCU diagnostic-log receiver (backlog D3).

    Returns:
        The process-wide receiver.
    """
    return McuLog(get_settings())
