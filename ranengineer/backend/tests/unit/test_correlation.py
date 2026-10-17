from datetime import datetime, timezone
from app.alarms.models import Alarm, AlarmSeverity, AlarmStatus, AlarmType
from app.analytics.correlation.engine import CorrelationEngine
from app.analytics.correlation.models import CorrelationConfidence


def _make_alarm(
    alarm_id: str,
    alarm_type: AlarmType,
    severity: AlarmSeverity = AlarmSeverity.CRITICAL,
    cell_id: str | None = None,
    site_id: str | None = None,
) -> Alarm:
    now = datetime.now(timezone.utc)
    return Alarm(
        alarm_id=alarm_id,
        site_id=site_id,
        cell_id=cell_id,
        technology="LTE",
        alarm_type=alarm_type,
        severity=severity,
        status=AlarmStatus.ACTIVE,
        started_at=now,
        description=f"Synthetic alarm {alarm_type.value}",
        source="TEST",
        created_at=now,
    )


def test_correlation_direct_cell_high_confidence():
    engine = CorrelationEngine()
    cell = {
        "cell_id": "CELL_ALPHA",
        "site_id": "SITE_01",
        "health_score": 35,
        "status": "CRITICAL",
        "kpi_statuses": {"PRB_UTILIZATION": "CRITICAL", "THROUGHPUT_DL": "WARNING"},
        "probable_causes": [{"category": "Congestion", "recommended_checks": ["Check PRB loading"]}],
    }
    alarm = _make_alarm("ALM-01", AlarmType.HIGH_PRB_UTILIZATION, cell_id="CELL_ALPHA", site_id="SITE_01")
    
    result = engine.correlate_cell_with_alarms(cell, [alarm])
    assert len(result.correlated_alarms) == 1
    assert result.correlated_alarms[0].confidence == CorrelationConfidence.HIGH
    assert "PRB_UTILIZATION" in result.correlated_alarms[0].matched_kpis
    assert result.primary_hypothesis is not None
    assert "HIGH_PRB_UTILIZATION" in result.primary_hypothesis


def test_correlation_site_level_medium_confidence():
    engine = CorrelationEngine()
    cell = {
        "cell_id": "CELL_BETA",
        "site_id": "SITE_02",
        "health_score": 40,
        "status": "CRITICAL",
        "kpi_statuses": {"PRB_UTILIZATION": "CRITICAL"},
        "probable_causes": [],
    }
    # Alarm is at the site level, not specific to CELL_BETA
    alarm = _make_alarm("ALM-02", AlarmType.HIGH_PRB_UTILIZATION, site_id="SITE_02", cell_id=None)
    
    result = engine.correlate_cell_with_alarms(cell, [alarm])
    assert len(result.correlated_alarms) == 1
    assert result.correlated_alarms[0].confidence == CorrelationConfidence.MEDIUM


def test_correlation_co_located_site_low_confidence():
    engine = CorrelationEngine()
    cell = {
        "cell_id": "CELL_GAMMA",
        "site_id": "SITE_03",
        "health_score": 85,
        "status": "HEALTHY",
        "kpi_statuses": {"PRB_UTILIZATION": "HEALTHY", "RSRP": "HEALTHY"},
        "probable_causes": [],
    }
    # Alarm is on same site but cell has no degraded KPIs matching the alarm
    alarm = _make_alarm("ALM-03", AlarmType.HIGH_CALL_DROP, site_id="SITE_03", cell_id="OTHER_CELL")
    
    result = engine.correlate_cell_with_alarms(cell, [alarm])
    assert len(result.correlated_alarms) == 1
    assert result.correlated_alarms[0].confidence == CorrelationConfidence.LOW


def test_correlation_unrelated_alarm_ignored():
    engine = CorrelationEngine()
    cell = {
        "cell_id": "CELL_DELTA",
        "site_id": "SITE_04",
        "health_score": 90,
        "status": "HEALTHY",
        "kpi_statuses": {},
        "probable_causes": [],
    }
    # Alarm is on completely different site and cell
    alarm = _make_alarm("ALM-04", AlarmType.HIGH_PRB_UTILIZATION, site_id="SITE_99", cell_id="CELL_99")
    
    result = engine.correlate_cell_with_alarms(cell, [alarm])
    assert len(result.correlated_alarms) == 0

