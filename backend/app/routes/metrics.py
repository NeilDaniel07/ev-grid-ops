"""Metrics routes for /api/metrics endpoints."""

from fastapi import APIRouter

from app.models import ApiResponse
from app.services.metrics_service import compare_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/compare", response_model=ApiResponse)
def get_compare_metrics():
    metrics = compare_metrics()
    return ApiResponse(ok=True, data=metrics, error=None)
