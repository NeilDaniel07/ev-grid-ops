"""Canonical API models for contract-locked interfaces."""

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

SignalSource = Literal["charger_api", "311", "ugc"]
SignalStatus = Literal["down", "degraded", "online", "unknown"]
RootCauseTag = Literal["payment_terminal", "connector", "network", "unknown"]
RecommendedAction = Literal["dispatch_field_tech", "remote_reset", "needs_verification"]
GridStressLevel = Literal["normal", "elevated", "high"]
WorkOrderState = Literal["created", "in_progress", "done"]
VerificationStatus = Literal["open", "done"]
VerificationResult = Literal["confirmed_issue", "false_alarm", "needs_more_data"]
CaseMode = Literal["baseline", "certainty"]


class ApiResponse(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class Signal(BaseModel):
    id: str
    source: SignalSource
    timestamp: datetime
    charger_id: str
    lat: float
    lon: float
    status: SignalStatus
    text: str


class Case(BaseModel):
    id: str
    charger_id: str
    priority_score: int
    sla_hours: int
    root_cause_tag: RootCauseTag
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: RecommendedAction
    evidence_ids: List[str]
    grid_stress_level: GridStressLevel
    explanation: str
    uncertainty_reasons: List[str] = Field(default_factory=list)
    verification_required: bool = False


class VerificationTask(BaseModel):
    id: str
    case_id: str
    question: str
    owner: str
    status: VerificationStatus = "open"
    result: Optional[VerificationResult] = None


class WorkOrder(BaseModel):
    id: str
    case_id: str
    assigned_team: str
    due_at: datetime
    state: WorkOrderState = "created"


class CompareMetrics(BaseModel):
    false_dispatch_reduction_pct: float
    triage_time_reduction_pct: float
    critical_catch_rate_delta_pct: float


class TriageRequest(BaseModel):
    signals: List[Signal]


class BaselineTriageResponseData(BaseModel):
    cases: List[Case]


class CertaintyTriageResponseData(BaseModel):
    cases: List[Case]
    verification_tasks: List[VerificationTask] = Field(default_factory=list)


class CasesResponseData(BaseModel):
    mode: CaseMode
    cases: List[Case]


class DispatchRequest(BaseModel):
    assigned_team: str
    due_at: datetime
    state: WorkOrderState = "created"


class DispatchResponseData(BaseModel):
    work_order: WorkOrder


class VerifyRequest(BaseModel):
    result: VerificationResult
    notes: Optional[str] = None


class VerifyResponseData(BaseModel):
    verification_task: VerificationTask
