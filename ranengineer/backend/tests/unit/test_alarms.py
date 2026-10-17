"""Tests for the Alarm model and AlarmStore (Phase 1 in-memory store)."""
from app.alarms.models import AlarmSeverity, AlarmStatus, AlarmType, AlarmCreate
from app.alarms.store import AlarmStore


def _store() -> AlarmStore:
    """Return a fresh AlarmStore for each test."""
    return AlarmStore()


def test_create_alarm_returns_alarm_with_id() -> None:
    store = _store()
    alarm = store.create(AlarmCreate(
        alarm_type=AlarmType.HIGH_PRB_UTILIZATION,
        severity=AlarmSeverity.CRITICAL,
        description="PRB > 90%",
        source="TEST",
    ))
    assert alarm.alarm_id.startswith("ALM-")
    assert alarm.status == AlarmStatus.ACTIVE
    assert alarm.severity == AlarmSeverity.CRITICAL
    assert alarm.alarm_type == AlarmType.HIGH_PRB_UTILIZATION


def test_get_alarm_by_id() -> None:
    store = _store()
    alarm = store.create(AlarmCreate(
        alarm_type=AlarmType.LOW_THROUGHPUT,
        severity=AlarmSeverity.MAJOR,
        description="DL low",
        source="TEST",
    ))
    fetched = store.get(alarm.alarm_id)
    assert fetched is not None
    assert fetched.alarm_id == alarm.alarm_id


def test_list_all_alarms() -> None:
    store = _store()
    store.create(AlarmCreate(alarm_type=AlarmType.HIGH_CALL_DROP, severity=AlarmSeverity.MAJOR, description="CDR high", source="TEST"))
    store.create(AlarmCreate(alarm_type=AlarmType.POOR_RADIO_QUALITY, severity=AlarmSeverity.CRITICAL, description="RSRP poor", source="TEST"))
    assert len(store.list_all()) == 2


def test_list_active_excludes_cleared() -> None:
    store = _store()
    alarm = store.create(AlarmCreate(alarm_type=AlarmType.CELL_UNAVAILABLE, severity=AlarmSeverity.CRITICAL, description="Cell down", source="TEST"))
    store.clear(alarm.alarm_id)
    assert all(a.status == AlarmStatus.ACTIVE for a in store.list_active())


def test_acknowledge_alarm() -> None:
    store = _store()
    alarm = store.create(AlarmCreate(alarm_type=AlarmType.HIGH_PRB_UTILIZATION, severity=AlarmSeverity.CRITICAL, description="PRB high", source="TEST"))
    updated = store.acknowledge(alarm.alarm_id)
    assert updated is not None
    assert updated.status == AlarmStatus.ACKNOWLEDGED


def test_clear_alarm_sets_ended_at() -> None:
    store = _store()
    alarm = store.create(AlarmCreate(alarm_type=AlarmType.HIGH_PRB_UTILIZATION, severity=AlarmSeverity.CRITICAL, description="PRB high", source="TEST"))
    cleared = store.clear(alarm.alarm_id)
    assert cleared is not None
    assert cleared.status == AlarmStatus.CLEARED
    assert cleared.ended_at is not None


def test_create_security_alarm() -> None:
    store = _store()
    alarm = store.create_security_alarm(filename="evil.csv", reason="Malware detected", request_id="req-123")
    assert alarm.alarm_type == AlarmType.SUSPICIOUS_FILE_UPLOAD
    assert alarm.severity == AlarmSeverity.CRITICAL
    assert alarm.metadata["filename"] == "evil.csv"
    assert alarm.metadata["action"] == "BLOCKED"
    assert "evil.csv" in alarm.description


def test_list_critical_alarms() -> None:
    store = _store()
    store.create(AlarmCreate(alarm_type=AlarmType.HIGH_PRB_UTILIZATION, severity=AlarmSeverity.CRITICAL, description="Critical", source="TEST"))
    store.create(AlarmCreate(alarm_type=AlarmType.LOW_THROUGHPUT, severity=AlarmSeverity.MAJOR, description="Major", source="TEST"))
    criticals = store.list_critical()
    assert len(criticals) == 1
    assert criticals[0].severity == AlarmSeverity.CRITICAL

