"""EventService: recording, ordering, capacity, thread safety."""

from threading import Thread

from app.core.events import EventService


class TestEventService:
    """Behavior of the operator-event ring buffer."""

    def test_record_and_recent_newest_first(self):
        events = EventService(capacity=10)
        events.record("a.b", "first")
        events.record("c.d", "second", {"k": 1})
        recent = events.recent(10)
        assert [e.event for e in recent] == ["c.d", "a.b"]
        assert recent[0].data == {"k": 1}
        assert recent[1].data == {}

    def test_limit_respected(self):
        events = EventService(capacity=10)
        for i in range(5):
            events.record("e", str(i))
        assert len(events.recent(3)) == 3

    def test_capacity_evicts_oldest(self):
        events = EventService(capacity=3)
        for i in range(5):
            events.record("e", str(i))
        messages = [e.message for e in events.recent(10)]
        assert messages == ["4", "3", "2"]

    def test_timestamp_carries_an_explicit_utc_offset(self):
        """D33: an offset-less timestamp is read as local time by a
        browser, and the container's clock is UTC - so a naive
        datetime.now() shows hours behind the operator's real local time.
        """
        events = EventService(capacity=10)
        events.record("a.b", "first")
        timestamp = events.recent(1)[0].timestamp
        assert timestamp.endswith("+00:00") or timestamp.endswith("Z")

    def test_concurrent_records_do_not_corrupt(self):
        events = EventService(capacity=1000)

        def writer(tag):
            for i in range(100):
                events.record("t", f"{tag}-{i}")

        threads = [Thread(target=writer, args=(t,)) for t in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(events.recent(1000)) == 500
