"""Baseline vs certainty KPI comparison logic."""

from __future__ import annotations

from typing import Dict, Iterable

from app import store
from app.models import Case, CompareMetrics


def _pct_reduction(baseline_value: float, certainty_value: float) -> float:
    if baseline_value <= 0:
        return 0.0
    return ((baseline_value - certainty_value) / baseline_value) * 100.0


def _critical_cases(cases: Iterable[Case]) -> list[Case]:
    return [case for case in cases if case.priority_score >= 80]


def compare_metrics() -> CompareMetrics:
    """Return baseline vs certainty metric deltas derived from in-memory state."""
    baseline = store.get_cases("baseline")
    certainty = store.get_cases("certainty")

    baseline_dispatches = sum(1 for case in baseline if case.recommended_action == "dispatch_field_tech")
    certainty_dispatches = sum(1 for case in certainty if case.recommended_action == "dispatch_field_tech")
    false_dispatch_reduction_pct = _pct_reduction(float(baseline_dispatches), float(certainty_dispatches))

    baseline_triage_minutes = float(len(baseline) * 6)
    certainty_triage_minutes = float((len(certainty) * 4) + int(len(store.verification_tasks) * 2))
    triage_time_reduction_pct = _pct_reduction(baseline_triage_minutes, certainty_triage_minutes)

    outcomes_by_case: Dict[str, str] = {
        outcome["case_id"]: outcome["result"] for outcome in store.verification_outcomes
    }

    baseline_critical = _critical_cases(baseline)
    certainty_critical = _critical_cases(certainty)

    baseline_caught = sum(
        1 for case in baseline_critical if case.recommended_action == "dispatch_field_tech"
    )
    certainty_caught = 0
    for case in certainty_critical:
        if case.recommended_action == "dispatch_field_tech":
            certainty_caught += 1
            continue
        if outcomes_by_case.get(case.id) == "confirmed_issue":
            certainty_caught += 1

    baseline_catch_rate = (
        baseline_caught / len(baseline_critical) if baseline_critical else 0.0
    )
    certainty_catch_rate = (
        certainty_caught / len(certainty_critical) if certainty_critical else 0.0
    )
    critical_catch_rate_delta_pct = (certainty_catch_rate - baseline_catch_rate) * 100.0

    return CompareMetrics(
        false_dispatch_reduction_pct=round(false_dispatch_reduction_pct, 2),
        triage_time_reduction_pct=round(triage_time_reduction_pct, 2),
        critical_catch_rate_delta_pct=round(critical_catch_rate_delta_pct, 2),
    )
