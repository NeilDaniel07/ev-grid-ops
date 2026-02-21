"""FastAPI application wiring for EV Grid Ops backend."""

from fastapi import FastAPI

from app.routes import cases, metrics

app = FastAPI(title="EV Grid Ops API", version="0.1.0")

app.include_router(cases.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")

# Member 2 owns triage routes; include them when their router is available.
try:
    from app.routes import triage

    if hasattr(triage, "router"):
        app.include_router(triage.router, prefix="/api")
except Exception:
    pass
