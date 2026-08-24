"""McuLog: receiving and writing diagnostic events forwarded from the MCU."""

import json

import pytest

from tests.conftest import BridgeStub


@pytest.fixture()
def mcu_log(backend, monkeypatch, tmp_path):
    """Fresh registered receiver, writing into a throwaway file.

    Returns:
        The receiver under test.
    """
    from app.deps import get_mcu_log
    monkeypatch.setattr(backend.settings, "mcu_log_file",
                        str(tmp_path / "mcu.jsonl"))
    instance = get_mcu_log()
    instance.register()
    return instance


def _lines(path) -> list[dict]:
    """Reads every JSON line from a file.

    Args:
        path: File to read.

    Returns:
        One dict per line.
    """
    with open(path, encoding="utf-8") as handle:
        return [json.loads(row) for row in handle if row.strip()]


class TestRegistration:
    """Bridge callback registration."""

    def test_registers_mcu_log(self, mcu_log):
        assert "mcu_log" in BridgeStub.provided


class TestWriting:
    """One event in, one JSON line out."""

    def test_writes_expected_fields(self, mcu_log, backend):
        mcu_log._on_log(2, "W5500 write-lock timeout",
                        "mcu.relay.write_lock_timeout", 3, 0, 120)
        rows = _lines(backend.settings.mcu_log_file)
        assert len(rows) == 1
        row = rows[0]
        assert row["level"] == "WARNING"
        assert row["message"] == "W5500 write-lock timeout"
        assert row["event"] == "mcu.relay.write_lock_timeout"
        assert row["arg1"] == 3
        assert row["arg2"] == 0
        assert row["mcu_uptime_s"] == 120
        assert "timestamp" in row

    def test_unknown_level_falls_back_to_info(self, mcu_log, backend):
        mcu_log._on_log(99, "weird", "mcu.weird", 0, 0, 0)
        assert _lines(backend.settings.mcu_log_file)[0]["level"] == "INFO"

    def test_appends_rather_than_overwrites(self, mcu_log, backend):
        mcu_log._on_log(1, "a", "e.a", 0, 0, 1)
        mcu_log._on_log(1, "b", "e.b", 0, 0, 2)
        rows = _lines(backend.settings.mcu_log_file)
        assert [row["message"] for row in rows] == ["a", "b"]

    def test_creates_missing_parent_directory(self, mcu_log, backend,
                                              monkeypatch, tmp_path):
        nested = tmp_path / "nested" / "dir" / "mcu.jsonl"
        monkeypatch.setattr(backend.settings, "mcu_log_file", str(nested))
        mcu_log._on_log(1, "a", "e.a", 0, 0, 0)
        assert nested.exists()


class TestRotation:
    """Size-based single-backup rotation."""

    def test_rotates_past_the_threshold(self, mcu_log, backend, monkeypatch):
        monkeypatch.setattr(backend.settings, "mcu_log_max_bytes", 1)
        mcu_log._on_log(1, "first", "e.first", 0, 0, 0)
        # The first write already exceeded the 1-byte threshold, so the
        # second write rotates it out of the way before writing its own line.
        mcu_log._on_log(1, "second", "e.second", 0, 0, 1)
        path = backend.settings.mcu_log_file
        assert [row["message"] for row in _lines(path)] == ["second"]
        assert [row["message"] for row in _lines(path + ".1")] == ["first"]

    def test_under_threshold_does_not_rotate(self, mcu_log, backend,
                                             monkeypatch):
        monkeypatch.setattr(backend.settings, "mcu_log_max_bytes", 10_000_000)
        mcu_log._on_log(1, "first", "e.first", 0, 0, 0)
        mcu_log._on_log(1, "second", "e.second", 0, 0, 1)
        import os
        assert not os.path.exists(backend.settings.mcu_log_file + ".1")
        assert len(_lines(backend.settings.mcu_log_file)) == 2

    def test_rotation_failure_is_swallowed(self, mcu_log, backend,
                                           monkeypatch):
        import os as os_module

        monkeypatch.setattr(backend.settings, "mcu_log_max_bytes", 1)

        def broken_replace(_src, _dst):
            raise OSError("rotation blocked")

        mcu_log._on_log(1, "first", "e.first", 0, 0, 0)
        monkeypatch.setattr(os_module, "replace", broken_replace)
        mcu_log._on_log(1, "second", "e.second", 0, 0, 1)  # must not raise
        rows = _lines(backend.settings.mcu_log_file)
        assert [row["message"] for row in rows] == ["first", "second"]


class TestDevComputerPath:
    """Behavior when the board runtime is absent (dev PC)."""

    def test_register_skips_cleanly_without_bridge(self, backend,
                                                    monkeypatch):
        import sys
        monkeypatch.setitem(sys.modules, "arduino.app_utils", None)
        from app.deps import get_mcu_log
        instance = get_mcu_log()
        instance.register()          # must not raise
        assert "mcu_log.register.skipped" in backend.logger.events()
