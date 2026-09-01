"""Settings: defaults, environment override, caching."""


class TestSettings:
    """Behavior of the pydantic-settings configuration."""

    def test_defaults_present(self, backend):
        settings = backend.settings
        assert settings.counts_per_turn == 4096
        assert abs(settings.servo_deg_per_output_deg - 44.0 / 30.0) < 1e-9
        assert settings.output_step_deg == 0.06
        assert settings.output_min_deg == -90.0
        assert settings.output_max_deg == 90.0
        assert settings.servo_direction in (1, -1)
        assert settings.multi_turn_enabled is False
        assert 1 <= settings.angle_resolution <= 3
        assert settings.servo_deadband_counts == 0
        assert 0 <= settings.default_acceleration <= settings.max_acceleration
        assert settings.fine_approach_final_speed_dps is None
        assert settings.fine_approach_final_acceleration is None

    def test_environment_overrides(self, monkeypatch, backend):
        from app.core.config import get_settings
        monkeypatch.setenv("SERVO_DEADBAND_COUNTS", "3")
        monkeypatch.setenv("API_PORT", "9123")
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.servo_deadband_counts == 3
        assert settings.api_port == 9123

    def test_settings_cached(self, backend):
        from app.core.config import get_settings
        assert get_settings() is get_settings()
