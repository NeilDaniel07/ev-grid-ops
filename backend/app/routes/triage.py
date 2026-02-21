"""FastAPI triage routes for baseline and certainty pipelines."""

from __future__ import annotations

from typing import Iterable

from fastapi import APIRouter

from app import store
from app.models import (
    ApiResponse,
    BaselineTriageResponseData,
    CertaintyTriageResponseData,
    Case,
    TriageRequest,
    VerificationTask,
)
from app.triage.baseline import run_baseline_triage
from app.triage.certainty import run_certainty_triage

router = APIRouter(prefix="/triage", tags=["triage"])


def _safe_set_attr(name: str, values: Iterable[object]) -> None:
    if hasattr(store, name):
        setattr(store, name, list(values))


def _persist_baseline_cases(cases: list[Case]) -> None:
    """Persist baseline triage output using Member 1 store helpers when available."""
    setter = getattr(store, "set_baseline_cases", None)
    if callable(setter):
        setter(cases)
        return

    # Compatibility fallback for scaffold store state.
    _safe_set_attr("baseline_cases", cases)
    _safe_set_attr("CASES", cases)


def _persist_certainty_cases(cases: list[Case], tasks: list[VerificationTask]) -> None:
    """Persist certainty triage output using Member 1 store helpers when available."""
    setter = getattr(store, "set_certainty_cases", None)
    if callable(setter):
        setter(cases, tasks)
        return

    # Compatibility fallback for scaffold store state.
    _safe_set_attr("certainty_cases", cases)
    _safe_set_attr("VERIFICATION_TASKS", tasks)


@router.post("/baseline", response_model=ApiResponse)
def triage_baseline(payload: TriageRequest) -> ApiResponse:
    signal_setter = getattr(store, "set_signals", None)
    if callable(signal_setter):
        signal_setter(payload.signals)
    cases = run_baseline_triage(payload.signals)
    _persist_baseline_cases(cases)
    return ApiResponse(ok=True, data=BaselineTriageResponseData(cases=cases), error=None)


@router.post("/certainty", response_model=ApiResponse)
def triage_certainty(payload: TriageRequest) -> ApiResponse:
    signal_setter = getattr(store, "set_signals", None)
    if callable(signal_setter):
        signal_setter(payload.signals)
    cases, verification_tasks = run_certainty_triage(payload.signals)
    _persist_certainty_cases(cases, verification_tasks)
    return ApiResponse(
        ok=True,
        data=CertaintyTriageResponseData(cases=cases, verification_tasks=verification_tasks),
        error=None,
    )
