"""SavedPositionService: create, edit, delete, go, and their refusals."""

import pytest

from app.core.exceptions import (
    DuplicateNameError,
    NotFoundError,
    PositionOutOfRangeError,
    StalePositionError,
)
from tests.conftest import wait_until


@pytest.fixture()
def service(backend):
    """Fresh saved-position service.

    Returns:
        The service under test.
    """
    from app.deps import get_saved_position_service
    return get_saved_position_service()


class TestCreate:
    """Creating a saved position."""

    def test_create_stores_raw_counts_and_computes_output_deg(self, service):
        view = service.create("gate open", "clears the frame", 30.0)
        assert abs(view.output_deg - 30.0) < 0.06
        assert isinstance(view.raw_counts, int)

    def test_create_duplicate_name_raises(self, service):
        service.create("a", "", 10.0)
        with pytest.raises(DuplicateNameError):
            service.create("a", "", 20.0)

    def test_create_refuses_unreachable_angle(self, service, backend):
        from app.deps import get_calibration_service
        # A fresh simulator sits at the bottom of the mechanism's travel,
        # so calibrating here strands the entire negative half.
        get_calibration_service().calibrate()
        with pytest.raises(PositionOutOfRangeError):
            service.create("too far", "", backend.settings.output_min_deg)


class TestUpdate:
    """Editing a saved position."""

    def test_update_overwrites_fields(self, service):
        created = service.create("p", "old", 10.0)
        updated = service.update(created.id, "renamed", "new", 20.0,
                                 created.updated_at)
        assert updated.name == "renamed"
        assert updated.description == "new"
        assert abs(updated.output_deg - 20.0) < 0.06

    def test_update_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.update(999, "x", "", 1.0, "t")

    def test_update_stale_raises(self, service):
        created = service.create("p", "", 10.0)
        with pytest.raises(StalePositionError):
            service.update(created.id, "p", "", 20.0, "not-the-real-timestamp")


class TestDelete:
    """Deleting a saved position."""

    def test_delete_removes_it(self, service):
        created = service.create("p", "", 10.0)
        service.delete(created.id, created.updated_at)
        assert service.list_all() == []

    def test_delete_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.delete(999, "t")

    def test_delete_stale_raises(self, service):
        created = service.create("p", "", 10.0)
        with pytest.raises(StalePositionError):
            service.delete(created.id, "not-the-real-timestamp")


class TestGo:
    """Moving to a saved position."""

    def test_go_moves_the_servo(self, service, sim):
        sim.set_deadband(1)
        created = service.create("p", "", 12.0)
        service.go(created.id)
        assert wait_until(
            lambda: abs(sim.read_raw_counts() - created.raw_counts) <= 2,
            timeout=8)

    def test_go_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.go(999)


class TestRevision:
    """The change counter the SSE stream polls."""

    def test_revision_advances_on_every_mutation(self, service):
        start = service.revision()
        created = service.create("p", "", 10.0)
        assert service.revision() == start + 1
        service.update(created.id, "p", "", 11.0, created.updated_at)
        assert service.revision() == start + 2
        updated = service.list_all()[0]
        service.delete(created.id, updated.updated_at)
        assert service.revision() == start + 3


class TestStaleReference:
    """The 'earlier reference' signal shown beside a drifted angle."""

    def test_false_when_never_calibrated(self, service):
        service.create("p", "", 10.0)
        assert service.list_all()[0].stale_reference is False

    def test_true_once_the_datum_postdates_the_position(self, service):
        from app.deps import get_app_state_repository
        service.create("p", "", 10.0)
        app_state = get_app_state_repository()
        app_state.set("datum_captured_at", "2099-01-01T00:00:00",
                      "2099-01-01T00:00:00")
        assert service.list_all()[0].stale_reference is True

    def test_false_when_the_datum_predates_the_position(self, service):
        from app.deps import get_app_state_repository
        app_state = get_app_state_repository()
        app_state.set("datum_captured_at", "2000-01-01T00:00:00",
                      "2000-01-01T00:00:00")
        service.create("p", "", 10.0)
        assert service.list_all()[0].stale_reference is False
