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
        from app.deps import get_calibration_service, get_state_store
        # A fresh simulator sits at the bottom of the mechanism's travel,
        # so calibrating here strands one whole half - which one depends
        # on servo_direction, so pick by what's actually unreachable.
        get_calibration_service().calibrate()
        low, high = get_state_store().reachable_output_range_deg()
        unreachable = (backend.settings.output_min_deg
                       if low > backend.settings.output_min_deg
                       else backend.settings.output_max_deg)
        with pytest.raises(PositionOutOfRangeError):
            service.create("too far", "", unreachable)


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


class TestDismissReference:
    """Clearing the 'earlier reference' tag without editing the position."""

    def _make_stale(self, service):
        """Seeds a position saved before the datum, without touching the
        real clock - a dismissal always happens at real "now", so the
        position and the datum must both sit safely in the past relative
        to it for "dismissed_at >= datum_captured_at" to hold immediately.

        Returns:
            The SavedPositionView, already flagged stale_reference.
        """
        from app.deps import (get_app_state_repository,
                              get_saved_position_repository)
        from app.models.entities import SavedPosition
        get_saved_position_repository().add(SavedPosition(
            id=None, name="p", description="old note", raw_counts=1000,
            created_at="2000-01-01T00:00:00",
            updated_at="2000-01-01T00:00:00"))
        app_state = get_app_state_repository()
        app_state.set("datum_captured_at", "2010-01-01T00:00:00",
                      "2010-01-01T00:00:00")
        created = service.list_all()[0]
        assert created.stale_reference is True
        return created

    def test_dismiss_clears_the_flag(self, service):
        created = self._make_stale(service)
        dismissed = service.dismiss_reference(created.id, created.updated_at)
        assert dismissed.stale_reference is False

    def test_dismiss_does_not_change_what_the_position_stores(self, service):
        created = self._make_stale(service)
        dismissed = service.dismiss_reference(created.id, created.updated_at)
        assert dismissed.name == created.name
        assert dismissed.description == created.description
        assert dismissed.raw_counts == created.raw_counts
        assert dismissed.updated_at == created.updated_at

    def test_dismiss_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.dismiss_reference(999, "t")

    def test_dismiss_stale_concurrency_raises(self, service):
        created = self._make_stale(service)
        with pytest.raises(StalePositionError):
            service.dismiss_reference(created.id, "not-the-real-timestamp")

    def test_a_later_datum_reraises_a_dismissed_tag(self, service):
        from app.deps import get_app_state_repository
        created = self._make_stale(service)
        service.dismiss_reference(created.id, created.updated_at)
        app_state = get_app_state_repository()
        # Comfortably after "now" - re-dismissal must not survive a
        # recalibration that happens after the dismissal itself.
        app_state.set("datum_captured_at", "2222-01-01T00:00:00",
                      "2222-01-01T00:00:00")
        assert service.list_all()[0].stale_reference is True

    def test_revision_advances_on_dismiss(self, service):
        created = self._make_stale(service)
        start = service.revision()
        service.dismiss_reference(created.id, created.updated_at)
        assert service.revision() == start + 1


class TestDismissAllStaleReferences:
    """Clearing every currently-tagged position in one call."""

    def _seed(self, service):
        """Seeds one position saved before the datum and one saved after
        (this one created at real "now", so the datum sits in the past
        relative to it - "newer" stays fresh; see TestDismissReference's
        _make_stale for why "older" is inserted directly rather than
        through create(), which would put it at real "now" too).

        Returns:
            (stale_view, fresh_view) - list_all()'s views, newest first.
        """
        from app.deps import (get_app_state_repository,
                              get_saved_position_repository)
        from app.models.entities import SavedPosition
        get_saved_position_repository().add(SavedPosition(
            id=None, name="older", description="", raw_counts=1000,
            created_at="2000-01-01T00:00:00",
            updated_at="2000-01-01T00:00:00"))
        app_state = get_app_state_repository()
        app_state.set("datum_captured_at", "2010-01-01T00:00:00",
                      "2010-01-01T00:00:00")
        service.create("newer", "", 20.0)
        views = service.list_all()
        newer = next(v for v in views if v.name == "newer")
        older = next(v for v in views if v.name == "older")
        assert older.stale_reference is True
        assert newer.stale_reference is False
        return older, newer

    def test_clears_every_stale_position(self, service):
        self._seed(service)
        service.dismiss_all_stale_references()
        views = {v.name: v for v in service.list_all()}
        assert views["older"].stale_reference is False

    def test_leaves_a_never_stale_position_untouched(self, service):
        _, newer = self._seed(service)
        service.dismiss_all_stale_references()
        views = {v.name: v for v in service.list_all()}
        assert views["newer"].updated_at == newer.updated_at
        assert views["newer"].stale_reference is False

    def test_returns_the_count_cleared(self, service):
        self._seed(service)
        assert service.dismiss_all_stale_references() == 1

    def test_returns_zero_when_nothing_is_tagged(self, service):
        service.create("p", "", 10.0)
        assert service.dismiss_all_stale_references() == 0

    def test_revision_advances_once_per_position_cleared(self, service):
        self._seed(service)
        start = service.revision()
        service.dismiss_all_stale_references()
        assert service.revision() == start + 1
