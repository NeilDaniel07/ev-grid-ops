"""FastAPI application wiring for EV Grid Ops backend."""

from fastapi import FastAPI

from app.db.session import init_database
from app.routes import cases, demo, metrics

app = FastAPI(title="EV Grid Ops API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_database()

app.include_router(cases.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(demo.router, prefix="/api")

# Member 2 owns triage routes; include them when their router is available.
try:
    from app.routes import triage

    if hasattr(triage, "router"):
        app.include_router(triage.router, prefix="/api")
except Exception:
    pass
