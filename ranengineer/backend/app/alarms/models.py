"""Alarm domain models for AI Telecom Copilot – RAN Engineer.

Alarm fields match the project specification (section 20).
Phase 1 supports only SUSPICIOUS_FILE_UPLOAD security alarms.
Future phases will add network/KPI alarms from OSS/EMS.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AlarmSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"
    INFO = "INFO"


class AlarmStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLEARED = "CLEARED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class AlarmType(str, Enum):
    # Network / KPI alarms (future integration with OSS/EMS)
    HIGH_PRB_UTILIZATION = "HIGH_PRB_UTILIZATION"
    LOW_THROUGHPUT = "LOW_THROUGHPUT"
    POOR_RADIO_QUALITY = "POOR_RADIO_QUALITY"
    HIGH_CALL_DROP = "HIGH_CALL_DROP"
    HANDOVER_FAILURE = "HANDOVER_FAILURE"
    CELL_UNAVAILABLE = "CELL_UNAVAILABLE"
    # Security alarms (Phase 1 active)
    SUSPICIOUS_FILE_UPLOAD = "SUSPICIOUS_FILE_UPLOAD"


class Alarm(BaseModel):
    """Alarm domain model.

    Clearly labelled as application-generated.
    synthetic=True means this is test/synthetic data.
    """

    alarm_id: str
    site_id: Optional[str] = None
    cell_id: Optional[str] = None
    technology: Optional[str] = None
    alarm_type: AlarmType
    severity: AlarmSeverity
    status: AlarmStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    description: str
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Extra context fields (not persisted to DB – stored in JSON blob)
    metadata: dict = Field(default_factory=dict)
    synthetic: bool = False


class AlarmCreate(BaseModel):
    """Input schema for creating an alarm."""

    site_id: Optional[str] = None
    cell_id: Optional[str] = None
    technology: Optional[str] = None
    alarm_type: AlarmType
    severity: AlarmSeverity
    status: AlarmStatus = AlarmStatus.ACTIVE
    description: str
    source: str
    metadata: dict = Field(default_factory=dict)
    synthetic: bool = False


__all__ = ["Alarm", "AlarmCreate", "AlarmSeverity", "AlarmStatus", "AlarmType"]

