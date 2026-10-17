from app.incidents.models import IncidentCreate, IncidentSeverity, IncidentStatus
from app.incidents.store import IncidentStore


def test_create_and_get_incident():
    store = IncidentStore()
    payload = IncidentCreate(
        title="High Degradation at Site 101",
        description="Multiple cells reporting excessive PRB utilization and drop rates.",
        severity=IncidentSeverity.CRITICAL,
        affected_cells=["CELL_101_A", "CELL_101_B"],
        related_alarms=["ALM-20261008-001"],
    )
    incident = store.create(payload)
    assert incident.id.startswith("INC-")
    assert incident.title == payload.title
    assert incident.status == IncidentStatus.OPEN
    assert len(incident.affected_cells) == 2

    fetched = store.get(incident.id)
    assert fetched is not None
    assert fetched.id == incident.id
    assert fetched.severity == IncidentSeverity.CRITICAL


def test_list_and_filter_open_incidents():
    store = IncidentStore()
    inc1 = store.create(
        IncidentCreate(
            title="Incident 1",
            description="Active outage",
            severity=IncidentSeverity.MAJOR,
            affected_cells=["CELL_A"],
        )
    )
    inc2 = store.create(
        IncidentCreate(
            title="Incident 2",
            description="Minor interference",
            severity=IncidentSeverity.MINOR,
            affected_cells=["CELL_B"],
        )
    )
    
    all_incidents = store.list_all()
    assert len(all_incidents) >= 2
    
    # Resolve inc1
    resolved = store.resolve(inc1.id, "Re-tuned tilt angles and restarted RRU.")
    assert resolved is not None
    assert resolved.status == IncidentStatus.RESOLVED
    assert resolved.resolution == "Re-tuned tilt angles and restarted RRU."
    
    open_incidents = store.list_open()
    open_ids = [i.id for i in open_incidents]
    assert inc1.id not in open_ids
    assert inc2.id in open_ids

