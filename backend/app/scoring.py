"""Deterministic scoring helpers for baseline and certainty triage."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple

from app.models import GridStressLevel, RootCauseTag, Signal

STATUS_WEIGHTS = {
    "down": 1.0,
    "degraded": 0.65,
    "unknown": 0.4,
    "online": 0.0,
}

ROOT_CAUSE_KEYWORDS = {
    "payment_terminal": ("payment", "card", "tap", "terminal", "reader"),
    "connector": ("connector", "plug", "cable", "port", "bent"),
    "network": ("network", "timeout", "offline", "latency", "ping", "modem", "router"),
}


def group_signals_by_charger(signals: Sequence[Signal]) -> Dict[str, List[Signal]]:
    """Group signals by charger id, newest signal first within each group."""
    grouped: Dict[str, List[Signal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.charger_id].append(signal)

    for charger_signals in grouped.values():
        charger_signals.sort(key=lambda item: item.timestamp, reverse=True)

    return dict(sorted(grouped.items(), key=lambda item: item[0]))


def status_weight(status: str) -> float:
    """Map status to deterministic severity weight."""
    return STATUS_WEIGHTS.get(status, STATUS_WEIGHTS["unknown"])


def compute_priority_score(signals: Sequence[Signal]) -> int:
    """Compute a 0-100 priority score from statuses, source diversity, and volume."""
    if not signals:
        return 0

    weights = [status_weight(signal.status) for signal in signals]
    max_component = max(weights) * 70
    average_component = (sum(weights) / len(weights)) * 20
    source_diversity_bonus = min(len({signal.source for signal in signals}), 3) * 3
    volume_bonus = min(len(signals), 5) * 2

    score = round(max_component + average_component + source_diversity_bonus + volume_bonus)
    return max(0, min(100, score))


def compute_sla_hours(priority_score: int) -> int:
    """Map priority to response SLA hours."""
    if priority_score >= 85:
        return 2
    if priority_score >= 70:
        return 4
    if priority_score >= 50:
        return 8
    return 24


def compute_grid_stress_level(priority_score: int) -> GridStressLevel:
    """Approximate local grid stress from case severity for MVP demo purposes."""
    if priority_score >= 80:
        return "high"
    if priority_score >= 60:
        return "elevated"
    return "normal"


def infer_root_cause_tag(signals: Sequence[Signal]) -> RootCauseTag:
    """Infer root cause from signal text using keyword voting."""
    text_blob = " ".join(signal.text.lower() for signal in signals)
    best_tag: RootCauseTag = "unknown"
    best_hits = 0

    for tag, keywords in ROOT_CAUSE_KEYWORDS.items():
        hits = sum(text_blob.count(keyword) for keyword in keywords)
        if hits > best_hits:
            best_tag = tag  # type: ignore[assignment]
            best_hits = hits

    return best_tag


def _is_flapping(signals: Sequence[Signal]) -> bool:
    ordered = sorted(signals, key=lambda item: item.timestamp)
    transitions = 0
    for index in range(1, len(ordered)):
        if ordered[index].status != ordered[index - 1].status:
            transitions += 1
    return transitions >= 2


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def compute_confidence(signals: Sequence[Signal]) -> Tuple[float, List[str]]:
    """Compute confidence and explicit uncertainty reasons for certainty triage."""
    if not signals:
        return 0.0, ["no_evidence"]

    confidence = 0.88
    reasons: List[str] = []
    statuses = {signal.status for signal in signals}

    if len(signals) == 1:
        confidence -= 0.24
        reasons.append("low_evidence_volume")
    elif len(signals) == 2:
        confidence -= 0.10
        reasons.append("limited_evidence_volume")

    if len(statuses) > 1:
        confidence -= 0.16
        reasons.append("cross_source_disagreement")

    if "online" in statuses and ({"down", "degraded"} & statuses):
        confidence -= 0.24
        reasons.append("status_conflict_recent")

    if "unknown" in statuses and len(statuses) > 1:
        confidence -= 0.08
        reasons.append("ambiguous_unknown_status")

    if _is_flapping(signals):
        confidence -= 0.20
        reasons.append("status_flapping")

    if all(signal.status == "down" for signal in signals):
        confidence += 0.07

    if len(signals) >= 3 and len(statuses) == 1:
        confidence += 0.05

    if len({signal.source for signal in signals}) >= 2:
        confidence += 0.03

    confidence = max(0.05, min(0.99, confidence))
    return round(confidence, 2), _dedupe_preserve_order(reasons)


def choose_recommended_action(priority_score: int, verification_required: bool) -> str:
    """Select a contract-valid recommended action."""
    if verification_required:
        return "needs_verification"
    if priority_score >= 65:
        return "dispatch_field_tech"
    return "remote_reset"


def make_case_id(charger_id: str) -> str:
    """Create deterministic case identifiers from charger ids."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", charger_id.strip()).strip("_").lower()
    return f"case_{slug or 'unknown'}"


def make_verification_task_id(case_id: str) -> str:
    """Create deterministic verification task ids from case ids."""
    suffix = case_id[5:] if case_id.startswith("case_") else case_id
    return f"ver_{suffix}"


def build_baseline_explanation(charger_id: str, priority_score: int, root_cause_tag: RootCauseTag) -> str:
    """Human-readable deterministic baseline explanation."""
    return (
        f"Baseline triage scored charger {charger_id} at {priority_score} "
        f"from severity-only rules (root cause hint: {root_cause_tag})."
    )


def build_certainty_explanation(
    charger_id: str,
    priority_score: int,
    confidence: float,
    reasons: Sequence[str],
) -> str:
    """Human-readable deterministic certainty explanation."""
    if reasons:
        reason_blob = ", ".join(reasons)
        return (
            f"Certainty triage scored charger {charger_id} at {priority_score} "
            f"with confidence {confidence:.2f}; uncertainty drivers: {reason_blob}."
        )

    return (
        f"Certainty triage scored charger {charger_id} at {priority_score} "
        f"with confidence {confidence:.2f} and no material uncertainty flags."
    )
