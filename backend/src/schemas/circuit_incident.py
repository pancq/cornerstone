from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CircuitIncidentCreate(BaseModel):
    title: str
    severity: str = "minor"
    started_at: datetime
    symptom: str
    affected_sites: List[str] = []
    ticket_no: Optional[str] = None
    reported_by: Optional[str] = None


class CircuitIncidentUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    symptom: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    affected_sites: Optional[List[str]] = None
    ticket_no: Optional[str] = None


class CircuitIncidentResolve(BaseModel):
    root_cause: Optional[str] = None
    resolution: Optional[str] = None


class CircuitIncidentLogCreate(BaseModel):
    content: str


class CircuitIncidentLogResponse(BaseModel):
    id: int
    incident_id: int
    content: str
    operator: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CircuitIncidentResponse(BaseModel):
    id: int
    circuit_id: int
    title: str
    severity: str
    status: str
    started_at: datetime
    resolved_at: Optional[datetime]
    duration_minutes: Optional[int]
    symptom: str
    root_cause: Optional[str]
    resolution: Optional[str]
    affected_sites: List[str]
    reported_by: Optional[str]
    ticket_no: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CircuitIncidentStats(BaseModel):
    current_count: int
    monthly_count: int
    avg_duration_hours: float
    last_incident_at: Optional[datetime]