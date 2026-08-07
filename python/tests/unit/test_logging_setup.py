"""Logging setup: Logger461 wiring."""


class TestSetupLogging:
    """setup_logging passes the configured sink values to Logger461."""

    def test_setup_called_with_settings_values(self, backend):
        from app.core.logging_setup import setup_logging
        setup_logging(backend.settings)
        setups = [record for record in backend.logger.records
                  if record[0] == "setup"]
        assert len(setups) == 1
        kwargs = setups[0][1]
        assert kwargs["file"] == backend.settings.log_file
        assert kwargs["level"] == backend.settings.log_level
