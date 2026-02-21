"""In-memory state for hackathon MVP workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, TypedDict

from app.models import (
    Case,
    CaseMode,
    Signal,
    VerificationResult,
    VerificationTask,
    WorkOrder,
    WorkOrderState,
)


class VerificationOutcome(TypedDict):
    case_id: str
    result: VerificationResult
    notes: Optional[str]
    timestamp: datetime


signals: List[Signal] = []
baseline_cases: Dict[str, Case] = {}
certainty_cases: Dict[str, Case] = {}
work_orders: Dict[str, WorkOrder] = {}
verification_tasks: Dict[str, VerificationTask] = {}
verification_outcomes: List[VerificationOutcome] = []


def reset_store() -> None:
    """Clear all in-memory state. Mainly used by tests."""
    signals.clear()
    baseline_cases.clear()
    certainty_cases.clear()
    work_orders.clear()
    verification_tasks.clear()
    verification_outcomes.clear()


def set_baseline_cases(cases: Sequence[Case]) -> None:
    baseline_cases.clear()
    for case in cases:
        baseline_cases[case.id] = case


def set_certainty_cases(cases: Sequence[Case], tasks: Sequence[VerificationTask]) -> None:
    certainty_cases.clear()
    verification_tasks.clear()
    for case in cases:
        certainty_cases[case.id] = case
    for task in tasks:
        verification_tasks[task.case_id] = task


def get_cases(mode: CaseMode) -> List[Case]:
    if mode == "baseline":
        return sorted(baseline_cases.values(), key=lambda case: case.priority_score, reverse=True)
    if mode == "certainty":
        return sorted(certainty_cases.values(), key=lambda case: case.priority_score, reverse=True)
    raise ValueError(f"Unsupported case mode: {mode}")


def find_case(case_id: str) -> Optional[Case]:
    return certainty_cases.get(case_id) or baseline_cases.get(case_id)


def create_or_update_work_order(
    case_id: str,
    assigned_team: str,
    due_at: datetime,
    state: WorkOrderState = "created",
) -> WorkOrder:
    existing = work_orders.get(case_id)
    work_order_id = existing.id if existing is not None else f"wo_{len(work_orders) + 1:03d}"
    work_order = WorkOrder(
        id=work_order_id,
        case_id=case_id,
        assigned_team=assigned_team,
        due_at=due_at,
        state=state,
    )
    work_orders[case_id] = work_order
    return work_order


def complete_verification(
    case_id: str,
    result: VerificationResult,
    notes: Optional[str],
) -> VerificationTask:
    task = verification_tasks.get(case_id)
    if task is None:
        case = find_case(case_id)
        charger_id = case.charger_id if case is not None else case_id
        task = VerificationTask(
            id=f"ver_{len(verification_tasks) + 1:03d}",
            case_id=case_id,
            question=f"Is charger {charger_id} physically offline?",
            owner="FieldOps",
        )

    completed_task = VerificationTask(
        id=task.id,
        case_id=task.case_id,
        question=task.question,
        owner=task.owner,
        status="done",
        result=result,
    )
    verification_tasks[case_id] = completed_task
    verification_outcomes.append(
        {
            "case_id": case_id,
            "result": result,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc),
        }
    )
    return completed_task
