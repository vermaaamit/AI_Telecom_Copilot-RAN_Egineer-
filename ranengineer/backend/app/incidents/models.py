from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class Incident(BaseModel):
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolution: Optional[str] = None
    affected_cells: list[str] = Field(default_factory=list)
    related_alarms: list[str] = Field(default_factory=list)


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    affected_cells: list[str] = Field(default_factory=list)
    related_alarms: list[str] = Field(default_factory=list)


