"""Tests for deterministic baseline and certainty triage behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import Signal
from app.triage.baseline import run_baseline_triage
from app.triage.certainty import run_certainty_triage


BASE_TS = datetime(2026, 2, 20, 20, 0, tzinfo=timezone.utc)


def _signal(
    signal_id: str,
    charger_id: str,
    status: str,
    source: str,
    minutes: int,
    text: str,
) -> Signal:
    return Signal(
        id=signal_id,
        source=source,
        timestamp=BASE_TS + timedelta(minutes=minutes),
        charger_id=charger_id,
        lat=30.2672,
        lon=-97.7431,
        status=status,
        text=text,
    )


def test_duplicate_signals_collapse_to_one_case_per_charger() -> None:
    signals = [
        _signal("sig_1", "AUS_1001", "down", "charger_api", 0, "charger offline"),
        _signal("sig_2", "AUS_1001", "down", "311", 2, "still down"),
        _signal("sig_3", "AUS_2002", "degraded", "ugc", 1, "slow charging"),
    ]

    cases = run_baseline_triage(signals)

    assert len(cases) == 2
    assert {case.charger_id for case in cases} == {"AUS_1001", "AUS_2002"}
    aus_1001 = next(case for case in cases if case.charger_id == "AUS_1001")
    assert set(aus_1001.evidence_ids) == {"sig_1", "sig_2"}


def test_low_confidence_case_generates_verification_task() -> None:
    signals = [
        _signal("sig_10", "AUS_3003", "down", "charger_api", 0, "offline timeout"),
        _signal("sig_11", "AUS_3003", "online", "311", 1, "came back online"),
        _signal("sig_12", "AUS_3003", "down", "ugc", 2, "offline again"),
    ]

    cases, tasks = run_certainty_triage(signals)

    assert len(cases) == 1
    assert len(tasks) == 1

    case = cases[0]
    assert case.verification_required is True
    assert case.recommended_action == "needs_verification"
    assert case.confidence < 0.65
    assert "status_conflict_recent" in case.uncertainty_reasons

    task = tasks[0]
    assert task.case_id == case.id
    assert task.status == "open"


def test_certainty_output_has_required_fields() -> None:
    signals = [
        _signal("sig_20", "AUS_4004", "down", "charger_api", 0, "connector bent"),
        _signal("sig_21", "AUS_4004", "down", "311", 3, "plug damaged"),
        _signal("sig_22", "AUS_4004", "down", "ugc", 5, "cable issue persists"),
    ]

    cases, tasks = run_certainty_triage(signals)

    assert len(cases) == 1
    assert tasks == []

    case = cases[0]
    assert isinstance(case.confidence, float)
    assert 0.0 <= case.confidence <= 1.0
    assert isinstance(case.uncertainty_reasons, list)
    assert case.verification_required is False
    assert case.root_cause_tag == "connector"
