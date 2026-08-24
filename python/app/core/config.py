"""Typed application settings loaded from the environment / .env file."""

import pathlib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# python/.env - two levels up from app/core/config.py
_ENV_FILE = pathlib.Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Backend configuration, overridable via environment or .env.

    Attributes:
        app_name: Human-readable service name.
        version: Service version, surfaced in /health.
        api_host: Bind address for uvicorn; localhost only (the relay and
            adb port-forward are the two doors to the service).
        api_port: FastAPI port; must match the sketch listen port.
        relay_chunk_bytes: Max payload per Bridge message; must match the
            sketch and stay under the Bridge frame limit (128 verified).
        db_path: SQLite database file path on the board.
        log_file: JSON-lines log file path.
        log_level: Minimum log level.
        mcu_log_file: JSON-lines file for events forwarded from the MCU
            side (backlog D3). Deliberately separate from log_file: the two
            sources are sized and rotated independently, so a volume spike
            on one side cannot evict the other's history, and either file
            can be included or dropped from a handover bundle on its own.
        mcu_log_max_bytes: Rotation threshold for mcu_log_file. This file is
            written directly, not through Logger461 - see
            app/relay/mcu_log.py - so its rotation is explicit rather than
            inherited from the main logger's configuration.
        event_buffer_size: Number of recent events kept for the UI.
        counts_per_turn: Encoder counts per full servo turn.
        servo_deg_per_output_deg: Belt ratio 44:30 expressed as servo
            degrees required per one output degree.
        output_min_deg: Lower output soft limit.
        output_max_deg: Upper output soft limit.
        output_step_deg: Commanded-angle granularity.
        default_speed_dps: Default output speed, degrees/second.
        max_speed_dps: Maximum accepted output speed.
        settling_seconds: Seconds a move waits after a lock-state change so
            the physical lock settles before motion.
        guard_move_to_lock: When True, lock changes are refused while a
            move is in progress; default False until mechanics decide.
        use_hardware_servo: When True the real servo is driven through
            the MCU Bridge; when False the simulator is used. Default
            False so the test suite and the dev machine need no
            hardware; the board turns it on in its .env.
        servo_direction: +1 or -1. Inverts the sense of commanded motion
            when the servo is mounted reversed relative to the output.
            Bench-confirmed +1 for our mounting.
        multi_turn_enabled: When True the startup path configures the servo
            for multi-turn absolute positioning (angle limits 0, angle
            resolution amplification, phase BIT4). Not needed while the
            travel window fits inside one servo turn; kept so a wider
            window can be enabled without code changes.
        angle_resolution: Angle-resolution amplification factor, 1..3. Only
            meaningful with multi_turn_enabled. Higher values widen the
            range but coarsen every step by the same factor.
        servo_deadband_counts: Servo dead-zone width in encoder counts
            (firmware default 10 = ~0.6 deg at the output). Written to the
            servo's dead-zone registers in sprint 2; the simulator honors
            it now. Lower = finer positioning, too low = hunting.
        default_acceleration: Servo acceleration parameter (native
            WritePosEx units, 0-254) used when a move does not specify one.
        max_acceleration: Upper bound accepted for acceleration.
        fine_approach_enabled: When True, moves arrive from a consistent
            (positive) direction to cancel belt backlash: targets below
            the current position are approached by overshooting low, then
            coming back up.
        fine_approach_overshoot_deg: How far below the target the
            overshoot leg goes, in output degrees.
        fine_approach_timeout_seconds: Safety timeout for the overshoot
            leg before the final leg is commanded anyway.
        sampler_interval_seconds: Telemetry persistence period.
        telemetry_retention_days: Telemetry rows older than this are purged.
        telemetry_purge_interval_seconds: How often retention runs.
        export_max_rows: Safety cap for a single CSV export.
    """

    # ABSOLUTE path, anchored to this module. A relative "env_file" is
    # resolved against the process working directory, and on the board the
    # app runs inside a container whose CWD is not python/ - so a .env
    # sitting next to main.py was silently never read, and every setting
    # quietly fell back to its default (including use_hardware_servo, which
    # left the simulator driving while the real servo never moved).
    model_config = SettingsConfigDict(env_file=_ENV_FILE,
                                      env_file_encoding="utf-8",
                                      extra="ignore")

    app_name: str = "Servo Control MVP"
    version: str = "0.2.0"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    relay_chunk_bytes: int = 224
    db_path: str = "/home/arduino/servo_mvp.db"
    log_file: str = "/home/arduino/logs/app.jsonl"
    log_level: str = "INFO"
    mcu_log_file: str = "/home/arduino/logs/mcu.jsonl"
    mcu_log_max_bytes: int = 10_000_000
    event_buffer_size: int = 200
    counts_per_turn: int = 4096
    servo_deg_per_output_deg: float = 44.0 / 30.0
    # Travel window. Bench-confirmed default is the +/-90 deg the operators
    # asked for: 180 deg output = 264 servo deg = 3004 counts, which fits
    # inside ONE servo turn (4096) with room to spare. Widen these two
    # numbers alone to change the window; if the span ever needs more than
    # one servo turn, also set multi_turn_enabled.
    output_min_deg: float = -90.0
    output_max_deg: float = 90.0
    # One encoder count at the output = (360/4096) * (30/44) = 0.0599 deg.
    # 0.06 is that value rounded; commands are absolute so there is no
    # accumulating drift - each target rounds to the nearest count.
    output_step_deg: float = 0.06
    default_speed_dps: float = 30.0
    # Measured ceiling: the servo saturates near 1100 counts/s regardless of
    # the commanded value, which is ~66 deg/s at the output. 60 keeps the
    # accepted range inside what the hardware can actually deliver.
    max_speed_dps: float = 60.0
    servo_direction: int = 1        # +1 or -1; bench-confirmed +1
    use_hardware_servo: bool = False  # True on the board
    multi_turn_enabled: bool = False
    angle_resolution: int = 1       # 1..3; only meaningful with multi-turn
    settling_seconds: float = 1.5
    guard_move_to_lock: bool = False
    servo_deadband_counts: int = 0
    default_acceleration: int = 50
    max_acceleration: int = 254
    fine_approach_enabled: bool = False
    fine_approach_overshoot_deg: float = 1.0
    fine_approach_timeout_seconds: float = 30.0
    sampler_interval_seconds: float = 0.5
    telemetry_retention_days: int = 30
    telemetry_purge_interval_seconds: float = 3600.0
    export_max_rows: int = 50_000


@lru_cache
def get_settings() -> Settings:
    """Returns the singleton settings instance.

    Returns:
        The process-wide Settings, constructed once and cached.
    """
    return Settings()
