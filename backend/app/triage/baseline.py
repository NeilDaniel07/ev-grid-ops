"""Deterministic baseline triage pipeline."""

from __future__ import annotations

from typing import List, Sequence

from app.models import Case, Signal
from app.scoring import (
    build_baseline_explanation,
    choose_recommended_action,
    compute_grid_stress_level,
    compute_priority_score,
    compute_sla_hours,
    group_signals_by_charger,
    infer_root_cause_tag,
    make_case_id,
)


def _baseline_confidence(priority_score: int) -> float:
    """Simple severity-only confidence proxy for baseline mode."""
    confidence = 0.55 + (priority_score / 200.0)
    return round(max(0.05, min(0.99, confidence)), 2)


def run_baseline_triage(signals: Sequence[Signal]) -> List[Case]:
    """Return one case per charger with severity-only scoring."""
    grouped = group_signals_by_charger(signals)
    cases: List[Case] = []

    for charger_id, charger_signals in grouped.items():
        priority_score = compute_priority_score(charger_signals)
        root_cause_tag = infer_root_cause_tag(charger_signals)

        cases.append(
            Case(
                id=make_case_id(charger_id),
                charger_id=charger_id,
                priority_score=priority_score,
                sla_hours=compute_sla_hours(priority_score),
                root_cause_tag=root_cause_tag,
                confidence=_baseline_confidence(priority_score),
                recommended_action=choose_recommended_action(
                    priority_score=priority_score,
                    verification_required=False,
                ),
                evidence_ids=[signal.id for signal in charger_signals],
                grid_stress_level=compute_grid_stress_level(priority_score),
                explanation=build_baseline_explanation(
                    charger_id=charger_id,
                    priority_score=priority_score,
                    root_cause_tag=root_cause_tag,
                ),
                uncertainty_reasons=[],
                verification_required=False,
            )
        )

    return sorted(cases, key=lambda item: item.priority_score, reverse=True)
