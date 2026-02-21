from datetime import datetime

from app.models import ApiResponse, Case, CompareMetrics, Signal


def _dump(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def test_api_response_envelope_keys_present():
    payload = _dump(ApiResponse(ok=True, data={"x": 1}, error=None))
    assert set(payload.keys()) == {"ok", "data", "error"}


def test_signal_case_and_metrics_contract_parsing():
    signal = Signal(
        id="sig_001",
        source="311",
        timestamp=datetime.fromisoformat("2026-02-20T20:00:00+00:00"),
        charger_id="AUS_0123",
        lat=30.2672,
        lon=-97.7431,
        status="down",
        text="charger dead",
    )
    assert signal.source == "311"

    case = Case(
        id="case_001",
        charger_id="AUS_0123",
        priority_score=87,
        sla_hours=8,
        root_cause_tag="connector",
        confidence=0.72,
        recommended_action="dispatch_field_tech",
        evidence_ids=["sig_001"],
        grid_stress_level="elevated",
        explanation="Repeated down reports.",
        uncertainty_reasons=["status_conflict_recent"],
        verification_required=False,
    )
    assert case.confidence == 0.72

    metrics = CompareMetrics(
        false_dispatch_reduction_pct=18.5,
        triage_time_reduction_pct=34.2,
        critical_catch_rate_delta_pct=6.0,
    )
    assert metrics.false_dispatch_reduction_pct > 0
