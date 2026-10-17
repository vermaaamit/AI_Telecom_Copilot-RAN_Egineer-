from fastapi import APIRouter, Depends
from sqlalchemy import text, func, select
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.cache import get_cache_store
from app.security import get_scanner
from app.analytics.rules.engine import RanRuleEngine
from app.ai.rag import get_knowledge_retriever
from app.models.dataset import DatasetModel, CellModel
from app.models.alarm import AlarmModel
from app.models.incident import IncidentModel

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ranengineer-backend"}


@router.get("/diagnostics", summary="Comprehensive Production Diagnostics & Telemetry Status")
def diagnostics(db: Session = Depends(get_db)) -> dict[str, object]:
    # 1. Database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "HEALTHY"
    except Exception as e:
        db_status = f"UNHEALTHY: {str(e)}"

    # 2. Counts
    try:
        datasets_count = db.scalar(select(func.count(DatasetModel.id))) or 0
        cells_count = db.scalar(select(func.count(CellModel.id))) or 0
        alarms_count = db.scalar(select(func.count(AlarmModel.id))) or 0
        incidents_count = db.scalar(select(func.count(IncidentModel.id))) or 0
    except Exception:
        datasets_count = cells_count = alarms_count = incidents_count = -1

    # 3. Cache readiness
    cache = get_cache_store()
    cache.set("diag_ping", "pong", ttl=5)
    cache_ok = (cache.get("diag_ping") == "pong")

    # 4. Rules & Knowledge loaded
    rule_engine = RanRuleEngine()
    rag_retriever = get_knowledge_retriever()
    scanner = get_scanner()

    return {
        "status": "OPERATIONAL" if db_status == "HEALTHY" and cache_ok else "DEGRADED",
        "service": "AI Telecom Copilot – RAN Engineer",
        "version": "1.0.0",
        "database": {
            "status": db_status,
            "engine": "PostgreSQL 16",
            "datasets_count": datasets_count,
            "cells_count": cells_count,
            "alarms_count": alarms_count,
            "incidents_count": incidents_count,
        },
        "cache": {
            "status": "HEALTHY" if cache_ok else "DEGRADED",
            "type": cache.__class__.__name__,
        },
        "security": {
            "scanner": scanner.__class__.__name__,
            "mode": "ACTIVE_SIGNATURE_INSPECTION",
        },
        "analytics": {
            "ran_rules_loaded": len(rule_engine.rules),
            "rag_standards_loaded": len(rag_retriever._documents),
        },
    }
