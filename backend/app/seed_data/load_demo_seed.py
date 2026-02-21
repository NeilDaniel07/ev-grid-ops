"""Load demo seed data into persistence-backed store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from app import store
from app.models import Signal, VerificationResult
from app.triage.baseline import run_baseline_triage
from app.triage.certainty import run_certainty_triage

SEED_DIR = Path(__file__).resolve().parent


def _read_json(name: str) -> Any:
    path = SEED_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_signals() -> list[Signal]:
    rows = _read_json("signals.json")
    return [Signal(**row) for row in rows]


def _apply_verification_outcomes() -> int:
    rows = _read_json("verification_outcomes.json")
    applied = 0
    for row in rows:
        result = row.get("result")
        if result not in {"confirmed_issue", "false_alarm", "needs_more_data"}:
            continue
        store.complete_verification(
            case_id=row["case_id"],
            result=result,  # type: ignore[arg-type]
            notes=row.get("notes"),
        )
        applied += 1
    return applied


def load_demo_seed() -> dict[str, int]:
    """Reset state and load deterministic demo dataset."""
    signals = _load_signals()
    store.reset_store()
    store.set_signals(signals)

    baseline_cases = run_baseline_triage(signals)
    certainty_cases, verification_tasks = run_certainty_triage(signals)
    store.set_baseline_cases(baseline_cases)
    store.set_certainty_cases(certainty_cases, verification_tasks)
    outcome_count = _apply_verification_outcomes()

    return {
        "signals": len(signals),
        "baseline_cases": len(baseline_cases),
        "certainty_cases": len(certainty_cases),
        "verification_tasks": len(verification_tasks),
        "verification_outcomes": outcome_count,
    }


def main() -> None:
    summary = load_demo_seed()
    print("Demo seed loaded:")
    for key, value in summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()

