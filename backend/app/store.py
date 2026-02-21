"""Persistence-backed state helpers for case lifecycle and metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, TypedDict, cast

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    CaseRecord,
    SignalRecord,
    VerificationOutcomeRecord,
    VerificationTaskRecord,
    WorkOrderRecord,
)
from app.db.session import session_scope
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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_tz(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _case_to_record(case: Case, mode: CaseMode) -> CaseRecord:
    return CaseRecord(
        case_id=case.id,
        mode=mode,
        charger_id=case.charger_id,
        priority_score=case.priority_score,
        sla_hours=case.sla_hours,
        root_cause_tag=case.root_cause_tag,
        confidence=case.confidence,
        recommended_action=case.recommended_action,
        evidence_ids=list(case.evidence_ids),
        grid_stress_level=case.grid_stress_level,
        explanation=case.explanation,
        uncertainty_reasons=list(case.uncertainty_reasons),
        verification_required=case.verification_required,
    )


def _record_to_case(record: CaseRecord) -> Case:
    return Case(
        id=record.case_id,
        charger_id=record.charger_id,
        priority_score=record.priority_score,
        sla_hours=record.sla_hours,
        root_cause_tag=record.root_cause_tag,  # type: ignore[arg-type]
        confidence=record.confidence,
        recommended_action=record.recommended_action,  # type: ignore[arg-type]
        evidence_ids=list(record.evidence_ids or []),
        grid_stress_level=record.grid_stress_level,  # type: ignore[arg-type]
        explanation=record.explanation,
        uncertainty_reasons=list(record.uncertainty_reasons or []),
        verification_required=record.verification_required,
    )


def _record_to_work_order(record: WorkOrderRecord) -> WorkOrder:
    return WorkOrder(
        id=record.id,
        case_id=record.case_id,
        assigned_team=record.assigned_team,
        due_at=_ensure_tz(record.due_at),
        state=record.state,  # type: ignore[arg-type]
    )


def _record_to_verification_task(record: VerificationTaskRecord) -> VerificationTask:
    return VerificationTask(
        id=record.id,
        case_id=record.case_id,
        question=record.question,
        owner=record.owner,
        status=record.status,  # type: ignore[arg-type]
        result=record.result,  # type: ignore[arg-type]
    )


def _next_work_order_id(session: Session) -> str:
    current = session.scalar(select(func.count()).select_from(WorkOrderRecord)) or 0
    return f"wo_{int(current) + 1:03d}"


def _next_verification_task_id(session: Session) -> str:
    current = session.scalar(select(func.count()).select_from(VerificationTaskRecord)) or 0
    return f"ver_{int(current) + 1:03d}"


def _find_case_record(session: Session, case_id: str) -> Optional[CaseRecord]:
    for mode in ("certainty", "baseline"):
        record = session.scalar(
            select(CaseRecord).where(CaseRecord.case_id == case_id, CaseRecord.mode == mode)
        )
        if record is not None:
            return record
    return None


def reset_store() -> None:
    """Clear persisted state. Intended for unit tests."""
    with session_scope() as session:
        session.execute(delete(VerificationOutcomeRecord))
        session.execute(delete(VerificationTaskRecord))
        session.execute(delete(WorkOrderRecord))
        session.execute(delete(CaseRecord))
        session.execute(delete(SignalRecord))


def set_signals(items: Sequence[Signal]) -> None:
    """Upsert incoming triage signals for traceability."""
    with session_scope() as session:
        for signal in items:
            existing = session.get(SignalRecord, signal.id)
            if existing is None:
                session.add(
                    SignalRecord(
                        id=signal.id,
                        source=signal.source,
                        timestamp=_ensure_tz(signal.timestamp),
                        charger_id=signal.charger_id,
                        lat=signal.lat,
                        lon=signal.lon,
                        status=signal.status,
                        text=signal.text,
                    )
                )
            else:
                existing.source = signal.source
                existing.timestamp = _ensure_tz(signal.timestamp)
                existing.charger_id = signal.charger_id
                existing.lat = signal.lat
                existing.lon = signal.lon
                existing.status = signal.status
                existing.text = signal.text


def set_baseline_cases(cases: Sequence[Case]) -> None:
    with session_scope() as session:
        session.execute(delete(CaseRecord).where(CaseRecord.mode == "baseline"))
        for case in cases:
            session.add(_case_to_record(case, "baseline"))


def set_certainty_cases(cases: Sequence[Case], tasks: Sequence[VerificationTask]) -> None:
    with session_scope() as session:
        session.execute(delete(CaseRecord).where(CaseRecord.mode == "certainty"))
        session.execute(delete(VerificationTaskRecord))

        for case in cases:
            session.add(_case_to_record(case, "certainty"))

        for task in tasks:
            session.add(
                VerificationTaskRecord(
                    id=task.id,
                    case_id=task.case_id,
                    question=task.question,
                    owner=task.owner,
                    status=task.status,
                    result=task.result,
                )
            )


def get_cases(mode: CaseMode) -> List[Case]:
    with session_scope() as session:
        records = session.scalars(
            select(CaseRecord)
            .where(CaseRecord.mode == mode)
            .order_by(CaseRecord.priority_score.desc(), CaseRecord.updated_at.desc())
        ).all()
    return [_record_to_case(record) for record in records]


def find_case(case_id: str) -> Optional[Case]:
    with session_scope() as session:
        record = _find_case_record(session, case_id)
    return _record_to_case(record) if record is not None else None


def create_or_update_work_order(
    case_id: str,
    assigned_team: str,
    due_at: datetime,
    state: WorkOrderState = "created",
) -> WorkOrder:
    with session_scope() as session:
        record = session.scalar(select(WorkOrderRecord).where(WorkOrderRecord.case_id == case_id))

        if record is None:
            record = WorkOrderRecord(
                id=_next_work_order_id(session),
                case_id=case_id,
                assigned_team=assigned_team,
                due_at=_ensure_tz(due_at),
                state=state,
            )
            session.add(record)
        else:
            record.assigned_team = assigned_team
            record.due_at = _ensure_tz(due_at)
            record.state = state

        session.flush()
        session.refresh(record)
        return _record_to_work_order(record)


def complete_verification(
    case_id: str,
    result: VerificationResult,
    notes: Optional[str],
) -> VerificationTask:
    with session_scope() as session:
        record = session.scalar(
            select(VerificationTaskRecord).where(VerificationTaskRecord.case_id == case_id)
        )

        if record is None:
            case_record = _find_case_record(session, case_id)
            charger_id = case_record.charger_id if case_record is not None else case_id
            record = VerificationTaskRecord(
                id=_next_verification_task_id(session),
                case_id=case_id,
                question=f"Is charger {charger_id} physically offline?",
                owner="FieldOps",
                status="open",
                result=None,
            )
            session.add(record)
            session.flush()

        record.status = "done"
        record.result = result

        session.add(
            VerificationOutcomeRecord(
                case_id=case_id,
                result=result,
                notes=notes,
                timestamp=_utc_now(),
            )
        )

        session.flush()
        session.refresh(record)
        return _record_to_verification_task(record)


def get_work_orders_map() -> Dict[str, WorkOrder]:
    with session_scope() as session:
        records = session.scalars(select(WorkOrderRecord)).all()
    return {record.case_id: _record_to_work_order(record) for record in records}


def get_verification_tasks_map() -> Dict[str, VerificationTask]:
    with session_scope() as session:
        records = session.scalars(select(VerificationTaskRecord)).all()
    return {record.case_id: _record_to_verification_task(record) for record in records}


def get_verification_outcomes() -> List[VerificationOutcome]:
    with session_scope() as session:
        records = session.scalars(
            select(VerificationOutcomeRecord).order_by(VerificationOutcomeRecord.id.asc())
        ).all()
    return [
        {
            "case_id": record.case_id,
            "result": cast(VerificationResult, record.result),
            "notes": record.notes,
            "timestamp": _ensure_tz(record.timestamp),
        }
        for record in records
    ]

