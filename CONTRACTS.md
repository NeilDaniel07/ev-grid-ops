# API Contracts (Locked v1)

This file is the source of truth for backend/frontend interfaces.

## Freeze Rules
- Do not rename fields without updating this file and both type systems.
- Every endpoint returns the same envelope shape.
- If a field is added, it must be additive (backward compatible).

## Standard Response Envelope

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

- `ok`: boolean
- `data`: endpoint-specific payload (nullable on failure)
- `error`: string or null

## Canonical Types

### Signal
```json
{
  "id": "sig_001",
  "source": "charger_api",
  "timestamp": "2026-02-20T20:00:00Z",
  "charger_id": "AUS_0123",
  "lat": 30.2672,
  "lon": -97.7431,
  "status": "down",
  "text": "user report..."
}
```

### Case
```json
{
  "id": "case_001",
  "charger_id": "AUS_0123",
  "priority_score": 87,
  "sla_hours": 8,
  "root_cause_tag": "connector",
  "confidence": 0.72,
  "recommended_action": "dispatch_field_tech",
  "evidence_ids": ["sig_001", "sig_003"],
  "grid_stress_level": "elevated",
  "explanation": "Repeated down signals from multiple sources.",
  "uncertainty_reasons": ["status_conflict_recent"],
  "verification_required": false
}
```

### VerificationTask
```json
{
  "id": "ver_001",
  "case_id": "case_001",
  "question": "Is charger AUS_0123 physically offline?",
  "owner": "FieldOps",
  "status": "open",
  "result": null
}
```

### WorkOrder
```json
{
  "id": "wo_001",
  "case_id": "case_001",
  "assigned_team": "FieldOps",
  "due_at": "2026-02-21T04:00:00Z",
  "state": "created"
}
```

### CompareMetrics
```json
{
  "false_dispatch_reduction_pct": 18.5,
  "triage_time_reduction_pct": 34.2,
  "critical_catch_rate_delta_pct": 6.0
}
```

## Endpoints

### `POST /api/triage/baseline`
Request:
```json
{
  "signals": [
    {
      "id": "sig_001",
      "source": "311",
      "timestamp": "2026-02-20T20:00:00Z",
      "charger_id": "AUS_0123",
      "lat": 30.2672,
      "lon": -97.7431,
      "status": "down",
      "text": "charger dead"
    }
  ]
}
```
Response:
```json
{
  "ok": true,
  "data": {
    "cases": []
  },
  "error": null
}
```

### `POST /api/triage/certainty`
Request: same as baseline.
Response:
```json
{
  "ok": true,
  "data": {
    "cases": [],
    "verification_tasks": []
  },
  "error": null
}
```

### `GET /api/cases?mode=baseline|certainty`
Response:
```json
{
  "ok": true,
  "data": {
    "mode": "certainty",
    "cases": []
  },
  "error": null
}
```

### `POST /api/cases/{id}/dispatch`
Request:
```json
{
  "assigned_team": "FieldOps",
  "due_at": "2026-02-21T04:00:00Z",
  "state": "created"
}
```
Response:
```json
{
  "ok": true,
  "data": {
    "work_order": {
      "id": "wo_001",
      "case_id": "case_001",
      "assigned_team": "FieldOps",
      "due_at": "2026-02-21T04:00:00Z",
      "state": "created"
    }
  },
  "error": null
}
```

### `POST /api/cases/{id}/verify`
Request:
```json
{
  "result": "confirmed_issue",
  "notes": "Connector bent, needs replacement"
}
```
Response:
```json
{
  "ok": true,
  "data": {
    "verification_task": {
      "id": "ver_001",
      "case_id": "case_001",
      "question": "Is charger AUS_0123 physically offline?",
      "owner": "FieldOps",
      "status": "done",
      "result": "confirmed_issue"
    }
  },
  "error": null
}
```

### `GET /api/metrics/compare`
Response:
```json
{
  "ok": true,
  "data": {
    "false_dispatch_reduction_pct": 18.5,
    "triage_time_reduction_pct": 34.2,
    "critical_catch_rate_delta_pct": 6.0
  },
  "error": null
}
```
