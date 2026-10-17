"""AI Telecom Copilot – RAN Engineer – FastAPI application entry point."""
import time
import uuid

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import agents, alarms, anomalies, auth, cells, chat, datasets, digital_twin, health, incidents, knowledge, kpis, oran, reports, security
from app.config.database import Base, engine
from app.logging import app_logger, audit
from app.models import dataset as dataset_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    app_logger.info("AI Telecom Copilot – RAN Engineer starting up.")
    yield
    app_logger.info("AI Telecom Copilot – RAN Engineer shutting down.")


app = FastAPI(
    title="AI Telecom Copilot — RAN Engineer",
    version="0.1.0",
    description=(
        "Deterministic KPI CSV analysis API.\n\n"
        "**ANALYTICS CALCULATES. RULES INTERPRET. AI EXPLAINS. ENGINEER DECIDES.**\n\n"
        "AI integrations must use controlled results from this service. "
        "The LLM must never invent KPI values, cells, sites, alarms, or RCA."
    ),
    lifespan=lifespan,
)


# ── Exception handlers ────────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail), "details": []}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "details": exc.errors()}},
    )


# ── Request context middleware ────────────────────────────────────────────
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        app_logger.info(
            "request_id={} method={} path={} status={} duration_ms={}",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for route in (
    health.router,
    datasets.router,
    alarms.router,
    cells.router,
    kpis.router,
    anomalies.router,
    chat.router,
    incidents.router,
    knowledge.router,
    agents.router,
    auth.router,
    oran.router,
    reports.router,
    digital_twin.router,
    security.router,
):
    app.include_router(route, prefix="/api/v1")
