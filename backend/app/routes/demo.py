"""Demo utility routes for reseeding deterministic hackathon data."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models import ApiResponse
from app.seed_data.load_demo_seed import load_demo_seed

router = APIRouter(prefix="/demo", tags=["demo"])


def _dump(model: ApiResponse) -> dict:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


@router.post("/reset", response_model=ApiResponse)
def reset_demo_state():
    try:
        summary = load_demo_seed()
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content=_dump(ApiResponse(ok=False, data=None, error=f"demo reset failed: {exc}")),
        )

    return ApiResponse(ok=True, data=summary, error=None)

