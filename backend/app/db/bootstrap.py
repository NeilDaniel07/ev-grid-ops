"""Demo data bootstrap helpers for local hackathon environments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, cast

from app import store
from app.models import Signal
from app.triage.baseline import run_baseline_triage
from app.triage.certainty import run_certainty_triage

MIN_DEMO_CASES = 6
SEED_SIGNALS_PATH = Path(__file__).resolve().parents[1] / "seed_data" / "signals.json"


def _load_seed_signals() -> List[Signal]:
    if not SEED_SIGNALS_PATH.exists():
        return []

    try:
        payload = json.loads(SEED_SIGNALS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(payload, list):
        return []

    signals: List[Signal] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            signals.append(Signal.model_validate(cast(dict[str, Any], item)))
        except Exception:
            continue
    return signals


def ensure_demo_cases(min_cases: int = MIN_DEMO_CASES) -> bool:
    """
    Ensure the database has enough cases for demo UX.

    Returns True if seed data was written, False otherwise.
    """
    baseline_existing = store.get_cases("baseline")
    certainty_existing = store.get_cases("certainty")
    if len(baseline_existing) >= min_cases and len(certainty_existing) >= min_cases:
        return False

    signals = _load_seed_signals()
    if not signals:
        return False

    store.set_signals(signals)
    baseline_cases = run_baseline_triage(signals)
    certainty_cases, verification_tasks = run_certainty_triage(signals)
    store.set_baseline_cases(baseline_cases)
    store.set_certainty_cases(certainty_cases, verification_tasks)
    return True
