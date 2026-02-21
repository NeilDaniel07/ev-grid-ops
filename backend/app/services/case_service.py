"""Case lifecycle service operations."""

from app import store
from app.models import (
    CaseMode,
    CasesResponseData,
    DispatchRequest,
    DispatchResponseData,
    VerifyRequest,
    VerifyResponseData,
)


def list_cases(mode: CaseMode) -> CasesResponseData:
    return CasesResponseData(mode=mode, cases=store.get_cases(mode))


def dispatch_case(case_id: str, payload: DispatchRequest) -> DispatchResponseData:
    case = store.find_case(case_id)
    if case is None:
        raise ValueError(f"Case not found: {case_id}")

    work_order = store.create_or_update_work_order(
        case_id=case.id,
        assigned_team=payload.assigned_team,
        due_at=payload.due_at,
        state=payload.state,
    )
    return DispatchResponseData(work_order=work_order)


def verify_case(case_id: str, payload: VerifyRequest) -> VerifyResponseData:
    case = store.find_case(case_id)
    if case is None:
        raise ValueError(f"Case not found: {case_id}")

    verification_task = store.complete_verification(
        case_id=case.id,
        result=payload.result,
        notes=payload.notes,
    )
    return VerifyResponseData(verification_task=verification_task)
