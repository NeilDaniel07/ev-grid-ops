"""Deterministic certainty-aware triage pipeline."""

from __future__ import annotations

from typing import List, Sequence, Tuple

from app.models import Case, Signal, VerificationTask
from app.scoring import (
    build_certainty_explanation,
    choose_recommended_action,
    compute_confidence,
    compute_grid_stress_level,
    compute_priority_score,
    compute_sla_hours,
    group_signals_by_charger,
    infer_root_cause_tag,
    make_case_id,
    make_verification_task_id,
)

CONFIDENCE_THRESHOLD = 0.65


def run_certainty_triage(
    signals: Sequence[Signal],
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> Tuple[List[Case], List[VerificationTask]]:
    """Return certainty-scored cases and generated verification tasks."""
    grouped = group_signals_by_charger(signals)
    cases: List[Case] = []
    verification_tasks: List[VerificationTask] = []

    for charger_id, charger_signals in grouped.items():
        priority_score = compute_priority_score(charger_signals)
        confidence, reasons = compute_confidence(charger_signals)
        verification_required = confidence < confidence_threshold
        case_id = make_case_id(charger_id)

        cases.append(
            Case(
                id=case_id,
                charger_id=charger_id,
                priority_score=priority_score,
                sla_hours=compute_sla_hours(priority_score),
                root_cause_tag=infer_root_cause_tag(charger_signals),
                confidence=confidence,
                recommended_action=choose_recommended_action(
                    priority_score=priority_score,
                    verification_required=verification_required,
                ),
                evidence_ids=[signal.id for signal in charger_signals],
                grid_stress_level=compute_grid_stress_level(priority_score),
                explanation=build_certainty_explanation(
                    charger_id=charger_id,
                    priority_score=priority_score,
                    confidence=confidence,
                    reasons=reasons,
                ),
                uncertainty_reasons=reasons,
                verification_required=verification_required,
            )
        )

        if verification_required:
            verification_tasks.append(
                VerificationTask(
                    id=make_verification_task_id(case_id),
                    case_id=case_id,
                    question=f"Is charger {charger_id} physically offline right now?",
                    owner="FieldOps",
                    status="open",
                    result=None,
                )
            )

    cases.sort(key=lambda item: item.priority_score, reverse=True)
    verification_tasks.sort(key=lambda item: item.case_id)
    return cases, verification_tasks
