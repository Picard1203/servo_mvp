"""Composition root: cached provider functions that construct and wire."""

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.events import EventService
from app.db.database import Database
from app.relay.bridge_relay import BridgeRelay
from app.relay.mcu_log import McuLog
from app.repositories.abstract.app_state_repository import AppStateRepository
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.telemetry_repository import TelemetryRepository
from app.repositories.abstract.zero_repository import ZeroRepository
from app.repositories.concrete.bridge_servo_repository import (
    BridgeServoRepository,
)
from app.repositories.concrete.simulated_servo_repository import (
    SimulatedServoRepository,
)
from app.repositories.concrete.sqlite_app_state_repository import (
    SqliteAppStateRepository,
)
from app.repositories.concrete.sqlite_telemetry_repository import (
    SqliteTelemetryRepository,
)
from app.repositories.concrete.sqlite_zero_repository import (
    SqliteZeroRepository,
)
from app.services.isolation_service import IsolationService
from app.services.motion_service import MotionService
from app.services.servo_state import ServoStateStore
from app.services.telemetry_service import TelemetryService
from app.services.zero_service import ZeroService


@lru_cache
def get_event_service() -> EventService:
    """Returns the shared event buffer.

    Returns:
        EventService: The process-wide event service.
    """
    return EventService(get_settings().event_buffer_size)


@lru_cache
def get_database() -> Database:
    """Returns the shared database wrapper.

    Returns:
        Database: The process-wide database.
    """
    return Database(get_settings().db_path)


@lru_cache
def get_servo_repository() -> ServoRepository:
    """Returns the servo repository chosen by use_hardware_servo.

    Returns:
        ServoRepository: The process-wide servo repository.
    """
    settings = get_settings()
    if settings.use_hardware_servo is True:
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
        ZeroRepository: The process-wide zero repository.
    """
    return SqliteZeroRepository(get_database())


@lru_cache
def get_telemetry_repository() -> TelemetryRepository:
    """Returns the telemetry repository.

    Returns:
        TelemetryRepository: The process-wide telemetry repository.
    """
    return SqliteTelemetryRepository(get_database())


@lru_cache
def get_app_state_repository() -> AppStateRepository:
    """Returns the persisted operator-intent repository.

    Returns:
        AppStateRepository: The process-wide app-state repository.
    """
    return SqliteAppStateRepository(get_database())


@lru_cache
def get_state_store() -> ServoStateStore:
    """Returns the atomic servo/lock/baseline/isolation state store.

    Returns:
        ServoStateStore: The process-wide state store.
    """
    settings = get_settings()
    return ServoStateStore(
        servo=get_servo_repository(), zeros=get_zero_repository(),
        app_state=get_app_state_repository(),
        settling_seconds=settings.settling_seconds,
        counts_per_turn=settings.counts_per_turn,
        servo_deg_per_output_deg=settings.servo_deg_per_output_deg,
        servo_direction=settings.servo_direction,
        isolation_idle_timeout_s=settings.isolation_idle_timeout_s)


@lru_cache
def get_motion_service() -> MotionService:
    """Returns the motion service.

    Returns:
        MotionService: The process-wide motion service.
    """
    return MotionService(get_servo_repository(), get_state_store(),
                         get_event_service(), get_settings())


@lru_cache
def get_isolation_service() -> IsolationService:
    """Returns the motor-isolation service.

    Returns:
        IsolationService: The process-wide isolation service.
    """
    return IsolationService(get_servo_repository(), get_state_store(),
                            get_app_state_repository(), get_event_service(),
                            get_settings())


@lru_cache
def get_zero_service() -> ZeroService:
    """Returns the zero service.

    Returns:
        ZeroService: The process-wide zero service.
    """
    return ZeroService(get_zero_repository(), get_servo_repository(),
                       get_event_service(), get_state_store())


@lru_cache
def get_telemetry_service() -> TelemetryService:
    """Returns the telemetry service.

    Returns:
        TelemetryService: The process-wide telemetry service.
    """
    return TelemetryService(get_telemetry_repository(), get_state_store(),
                            get_settings(), isolation=get_isolation_service())


@lru_cache
def get_relay() -> BridgeRelay:
    """Returns the Bridge relay.

    Returns:
        BridgeRelay: The process-wide relay.
    """
    return BridgeRelay(get_settings())


@lru_cache
def get_mcu_log() -> McuLog:
    """Returns the MCU diagnostic log receiver.

    Returns:
        McuLog: The process-wide receiver.
    """
    return McuLog(get_settings())
