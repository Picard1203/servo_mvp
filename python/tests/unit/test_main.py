"""main.py: the board entry point's own guards (D8, D29).

conftest.py installs a stub Logger461 before any app import, so
main.py's own _ensure_logger461() sees the import succeed and never
installs its _DevLogger stand-in inside the test suite - these tests
exercise the two pieces of main.py that do not depend on that: the
silent-simulator refusal and the level-gating logic the stand-in uses.
"""

import pytest

import main
from app.core.config import Settings


class TestRefuseSilentSimulator:
    """D8: the board must not run the simulator by accident."""

    def test_hardware_explicitly_chosen_starts_fine(self):
        settings = Settings(_env_file=None, use_hardware_servo=True)
        main._refuse_silent_simulator(settings)  # must not raise

    def test_simulator_explicitly_chosen_starts_fine(self):
        settings = Settings(_env_file=None, use_hardware_servo=False)
        main._refuse_silent_simulator(settings)  # must not raise

    def test_unset_default_refuses_to_start(self, monkeypatch):
        # conftest.py sets USE_HARDWARE_SERVO=false as a real env var so the
        # suite never touches hardware by accident - remove it here so this
        # test can observe the case it exists to keep hermetic elsewhere:
        # truly nothing set, neither file nor environment.
        monkeypatch.delenv("USE_HARDWARE_SERVO", raising=False)
        settings = Settings(_env_file=None)
        assert "use_hardware_servo" not in settings.model_fields_set
        with pytest.raises(SystemExit):
            main._refuse_silent_simulator(settings)


class TestLevelGating:
    """D29: the Logger461 stand-in must honour LOG_LEVEL."""

    def test_a_record_at_the_minimum_level_is_enabled(self):
        assert main._level_enabled("WARNING", "WARNING") is True

    def test_a_record_above_the_minimum_level_is_enabled(self):
        assert main._level_enabled("ERROR", "WARNING") is True

    def test_a_record_below_the_minimum_level_is_not_enabled(self):
        assert main._level_enabled("DEBUG", "WARNING") is False

    def test_default_minimum_is_info_so_debug_is_gated_out(self):
        assert main._level_enabled("DEBUG", "INFO") is False
        assert main._level_enabled("INFO", "INFO") is True
