from datetime import datetime
from math import isfinite

from app import store
from app.models import Case, DispatchRequest, VerificationTask, VerifyRequest
from app.routes.metrics import get_compare_metrics
from app.services import case_service
from app.services.metrics_service import compare_metrics


def _seed_state() -> None:
    store.reset_store()

    baseline_cases = [
        Case(
            id="case_baseline_001",
            charger_id="AUS_0123",
            priority_score=92,
            sla_hours=4,
            root_cause_tag="connector",
            confidence=0.84,
            recommended_action="dispatch_field_tech",
            evidence_ids=["sig_001"],
            grid_stress_level="high",
            explanation="Repeated hard-down signal.",
            uncertainty_reasons=[],
            verification_required=False,
        ),
        Case(
            id="case_baseline_002",
            charger_id="AUS_0144",
            priority_score=71,
            sla_hours=8,
            root_cause_tag="network",
            confidence=0.65,
            recommended_action="dispatch_field_tech",
            evidence_ids=["sig_011"],
            grid_stress_level="elevated",
            explanation="Intermittent outages in busy corridor.",
            uncertainty_reasons=[],
            verification_required=False,
        ),
    ]
    certainty_cases = [
        Case(
            id="case_certainty_001",
            charger_id="AUS_0123",
            priority_score=92,
            sla_hours=4,
            root_cause_tag="connector",
            confidence=0.91,
            recommended_action="dispatch_field_tech",
            evidence_ids=["sig_001"],
            grid_stress_level="high",
            explanation="High confidence physical connector issue.",
            uncertainty_reasons=[],
            verification_required=False,
        ),
        Case(
            id="case_certainty_002",
            charger_id="AUS_0144",
            priority_score=71,
            sla_hours=8,
            root_cause_tag="network",
            confidence=0.45,
            recommended_action="needs_verification",
            evidence_ids=["sig_011"],
            grid_stress_level="elevated",
            explanation="Conflicting network telemetry; verify before dispatch.",
            uncertainty_reasons=["signal_conflict"],
            verification_required=True,
        ),
    ]
    tasks = [
        VerificationTask(
            id="ver_001",
            case_id="case_certainty_002",
            question="Is charger AUS_0144 physically offline?",
            owner="FieldOps",
            status="open",
            result=None,
        )
    ]

    store.set_baseline_cases(baseline_cases)
    store.set_certainty_cases(certainty_cases, tasks)
    store.complete_verification(
        case_id="case_certainty_002",
        result="false_alarm",
        notes="Remote reset stabilized charger.",
    )


def _seed_case_lifecycle_state() -> None:
    store.reset_store()
    store.set_baseline_cases(
        [
            Case(
                id="case_baseline_001",
                charger_id="AUS_0123",
                priority_score=92,
                sla_hours=4,
                root_cause_tag="connector",
                confidence=0.84,
                recommended_action="dispatch_field_tech",
                evidence_ids=["sig_001"],
                grid_stress_level="high",
                explanation="Repeated hard-down signal.",
                uncertainty_reasons=[],
                verification_required=False,
            )
        ]
    )
    store.set_certainty_cases(
        [
            Case(
                id="case_certainty_001",
                charger_id="AUS_0123",
                priority_score=92,
                sla_hours=4,
                root_cause_tag="connector",
                confidence=0.91,
                recommended_action="dispatch_field_tech",
                evidence_ids=["sig_001"],
                grid_stress_level="high",
                explanation="High confidence physical connector issue.",
                uncertainty_reasons=[],
                verification_required=False,
            ),
            Case(
                id="case_certainty_002",
                charger_id="AUS_0144",
                priority_score=71,
                sla_hours=8,
                root_cause_tag="network",
                confidence=0.45,
                recommended_action="needs_verification",
                evidence_ids=["sig_011"],
                grid_stress_level="elevated",
                explanation="Conflicting network telemetry; verify before dispatch.",
                uncertainty_reasons=["signal_conflict"],
                verification_required=True,
            ),
        ],
        [
            VerificationTask(
                id="ver_001",
                case_id="case_certainty_002",
                question="Is charger AUS_0144 physically offline?",
                owner="FieldOps",
                status="open",
                result=None,
            )
        ],
    )


def test_compare_metrics_non_null_numeric_values():
    _seed_state()
    metrics = compare_metrics()

    values = [
        metrics.false_dispatch_reduction_pct,
        metrics.triage_time_reduction_pct,
        metrics.critical_catch_rate_delta_pct,
    ]
    for value in values:
        assert value is not None
        assert isinstance(value, float)
        assert isfinite(value)


def test_compare_metrics_endpoint_envelope_shape():
    _seed_state()
    payload = get_compare_metrics().model_dump()
    assert set(payload.keys()) == {"ok", "data", "error"}
    assert payload["ok"] is True
    assert payload["error"] is None

    data = payload["data"]
    assert set(data.keys()) == {
        "false_dispatch_reduction_pct",
        "triage_time_reduction_pct",
        "critical_catch_rate_delta_pct",
    }
    for key in data:
        assert data[key] is not None
        assert isinstance(data[key], (int, float))


def test_dispatch_case_creates_and_updates_work_order():
    _seed_case_lifecycle_state()
    first = case_service.dispatch_case(
        "case_certainty_001",
        DispatchRequest(
            assigned_team="FieldOps",
            due_at=datetime.fromisoformat("2026-02-21T04:00:00+00:00"),
            state="created",
        ),
    )
    second = case_service.dispatch_case(
        "case_certainty_001",
        DispatchRequest(
            assigned_team="FieldOps",
            due_at=datetime.fromisoformat("2026-02-21T05:00:00+00:00"),
            state="in_progress",
        ),
    )

    assert first.work_order.case_id == "case_certainty_001"
    assert second.work_order.id == first.work_order.id
    assert store.get_work_orders_map()["case_certainty_001"].state == "in_progress"


def test_verify_case_marks_task_done_and_persists_outcome():
    _seed_case_lifecycle_state()
    response = case_service.verify_case(
        "case_certainty_002",
        VerifyRequest(result="confirmed_issue", notes="Connector bent."),
    )

    task = store.get_verification_tasks_map()["case_certainty_002"]
    outcomes = store.get_verification_outcomes()
    assert response.verification_task.status == "done"
    assert task.status == "done"
    assert task.result == "confirmed_issue"
    assert outcomes[-1]["case_id"] == "case_certainty_002"
