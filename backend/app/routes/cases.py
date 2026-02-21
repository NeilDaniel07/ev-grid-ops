"""Case lifecycle routes for /api/cases endpoints."""

from typing import cast

from fastapi import APIRouter, Body, Path, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import ApiResponse, CaseMode, DispatchRequest, VerifyRequest
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["cases"])


def _dump(model: ApiResponse) -> dict:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _error_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_dump(ApiResponse(ok=False, data=None, error=message)),
    )


@router.get("", response_model=ApiResponse)
def get_cases(mode: str = Query(..., description="baseline or certainty")):
    if mode not in {"baseline", "certainty"}:
        return _error_response(400, "mode must be 'baseline' or 'certainty'")

    try:
        data = case_service.list_cases(cast(CaseMode, mode))
    except ValueError as exc:
        return _error_response(400, str(exc))
    return ApiResponse(ok=True, data=data, error=None)


@router.post("/{id}/dispatch", response_model=ApiResponse)
def dispatch_case(
    payload: dict = Body(...),
    id: str = Path(..., description="Case identifier"),
):
    try:
        request = DispatchRequest(**payload)
    except ValidationError as exc:
        return _error_response(400, str(exc))

    try:
        data = case_service.dispatch_case(id, request)
    except ValueError as exc:
        return _error_response(404, str(exc))
    return ApiResponse(ok=True, data=data, error=None)


@router.post("/{id}/verify", response_model=ApiResponse)
def verify_case(
    payload: dict = Body(...),
    id: str = Path(..., description="Case identifier"),
):
    try:
        request = VerifyRequest(**payload)
    except ValidationError as exc:
        return _error_response(400, str(exc))

    try:
        data = case_service.verify_case(id, request)
    except ValueError as exc:
        return _error_response(404, str(exc))
    return ApiResponse(ok=True, data=data, error=None)
