"""Typed application settings loaded from the environment / .env file."""

import pathlib
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = pathlib.Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Backend configuration, overridable via environment or .env.

    Attributes:
        app_name (str): Human-readable service name.
        version (str): Service version surfaced in /health.
        api_host (str): Bind address for uvicorn service.
        api_port (int): FastAPI service port.
        relay_chunk_bytes (int): Maximum payload bytes per Bridge message.
        db_path (str): SQLite database file path.
        log_file (str): Application JSON-lines log file path.
        log_level (str): Minimum logging severity level.
        mcu_log_file (str): MCU diagnostic JSON-lines log file path.
        mcu_log_max_bytes (int): Rotation size threshold for MCU log file.
        event_buffer_size (int): Number of recent events stored for UI.
        counts_per_turn (int): Encoder counts per full servo revolution.
        servo_deg_per_output_deg (float): Ratio in servo deg per output deg.
        output_min_deg (float): Minimum allowable output angle limit.
        output_max_deg (float): Maximum allowable output angle limit.
        output_step_deg (float): Commanded angle resolution step.
        default_speed_dps (float): Fixed move speed in output deg per second.
        servo_direction (int): Motion direction multiplier (+1 or -1).
        use_hardware_servo (bool): True for hardware servo, False for mock.
        multi_turn_enabled (bool): True for multi-turn servo positioning.
        angle_resolution (int): Multi-turn resolution amplification factor.
        settling_seconds (float): Settle delay before commencing motion.
        guard_move_to_lock (bool): True to refuse lock changes while moving.
        servo_deadband_counts (int): Dead-zone threshold in encoder counts.
        default_acceleration (int): Default servo acceleration parameter.
        max_acceleration (int): Maximum allowable acceleration parameter.
        fine_approach_enabled (bool): True to enable anti-backlash approach.
        fine_approach_overshoot_deg (float): Overshoot angle in output degrees.
        fine_approach_timeout_seconds (float): Timeout for overshoot approach.
        sampler_interval_seconds (float): Telemetry sampling interval.
        telemetry_retention_days (int): Telemetry retention window in days.
        telemetry_purge_interval_seconds (float): Retention purge interval.
        export_max_rows (int): Maximum row limit for telemetry exports.
        isolation_idle_timeout_s (float): Inactivity timeout for isolation.
    """

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
    output_min_deg: float = -90.0
    output_max_deg: float = 90.0
    output_step_deg: float = 0.06
    default_speed_dps: float = 30.0
    servo_direction: int = 1
    use_hardware_servo: bool = False
    multi_turn_enabled: bool = False
    angle_resolution: int = 1
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
    export_max_rows: int = 10_000_000
    isolation_idle_timeout_s: float = 900.0


@lru_cache
def get_settings() -> Settings:
    """Returns the process-wide settings singleton.

    Returns:
        Settings: The cached settings instance.
    """
    return Settings()
