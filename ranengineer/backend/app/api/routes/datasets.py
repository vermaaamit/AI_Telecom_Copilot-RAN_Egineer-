"""Dataset API routes for AI Telecom Copilot – RAN Engineer.

Upload flow (Phase 1):
  CSV → filename validation → size check → security scan → CSV parsing → analysis → persist
  Suspicious files are BLOCKED, a security alarm is raised, and the event is logged.
  Files do not proceed to parsing or analytics if the security scan fails.
"""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.alarms.store import get_alarm_store
from app.analytics.ingestion.csv_parser import InvalidKPIFileError
from app.api.dependencies import get_dataset_or_404
from app.config.database import get_db
from app.logging import audit, security
from app.repositories.dataset_repository import DatasetRepository
from app.security.scanner import ScanResult, get_scanner
from app.services.dataset_service import analyse_dataset, find_underperforming_cells

router = APIRouter(prefix="/datasets", tags=["datasets"])
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB – development limit


@router.post("/upload", status_code=201, summary="Upload and analyze a KPI CSV")
async def upload_dataset(
    request: Request,
    file: UploadFile = File(...),
    technology: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    filename = file.filename or ""

    # ── 1. Filename / extension validation ────────────────────────────────
    audit("FILE_UPLOAD", request_id=request_id, filename=filename, status="STARTED")

    if not filename or not filename.lower().endswith(".csv"):
        audit("FILE_VALIDATION", request_id=request_id, filename=filename, status="REJECTED", reason="Invalid extension")
        raise HTTPException(
            422,
            detail={"error": {"code": "INVALID_KPI_FILE", "message": "Only CSV files are supported.", "details": []}},
        )

    # ── 2. Read content ────────────────────────────────────────────────────
    content = await file.read()

    # ── 3. File size validation ────────────────────────────────────────────
    if len(content) > MAX_FILE_BYTES:
        audit("FILE_VALIDATION", request_id=request_id, filename=filename, status="REJECTED", reason="File too large")
        raise HTTPException(
            413,
            detail={"error": {"code": "FILE_TOO_LARGE", "message": "CSV exceeds the 10 MB development limit.", "details": []}},
        )

    # ── 4. Security / antivirus scan ───────────────────────────────────────
    audit("CLAMAV_SCAN", request_id=request_id, filename=filename, status="SCANNING")
    scanner = get_scanner()
    try:
        report = scanner.scan(content, filename)
    except RuntimeError as exc:
        # Scanner unavailable – block upload rather than silently proceeding
        security(
            "CLAMAV_SCAN",
            request_id=request_id,
            filename=filename,
            status="SCANNER_UNAVAILABLE",
            error=str(exc),
        )
        audit("FILE_BLOCKED", request_id=request_id, filename=filename, reason="Scanner unavailable")
        raise HTTPException(
            503,
            detail={"error": {"code": "SCANNER_UNAVAILABLE", "message": "Security scanning is currently unavailable. Upload blocked.", "details": []}},
        ) from exc

    if report.result != ScanResult.CLEAN:
        # BLOCK the upload, raise security alarm, audit log
        alarm = get_alarm_store().create_security_alarm(
            filename=filename,
            reason=report.details or "Security scan failed",
            request_id=request_id,
        )
        security(
            "SUSPICIOUS_FILE_UPLOAD",
            request_id=request_id,
            filename=filename,
            action="BLOCKED",
            result="REJECTED",
            reason=report.details,
            alarm_id=alarm.alarm_id,
        )
        audit(
            "FILE_BLOCKED",
            request_id=request_id,
            filename=filename,
            alarm_id=alarm.alarm_id,
            reason="Security scan detected a potentially unsafe file",
        )
        # Return generic user-facing message – do NOT expose scanner details
        raise HTTPException(
            422,
            detail={
                "error": {
                    "code": "SUSPICIOUS_FILE_UPLOAD",
                    "message": "Upload blocked — security scanning detected a potentially unsafe file.",
                    "details": [],
                }
            },
        )

    audit("CLAMAV_SCAN", request_id=request_id, filename=filename, status="CLEAN")

    # ── 5. CSV parsing and KPI analysis ───────────────────────────────────
    audit("KPI_VALIDATION", request_id=request_id, filename=filename, status="STARTED")
    try:
        dataset = analyse_dataset(content, filename, technology)
    except InvalidKPIFileError as error:
        audit("KPI_VALIDATION", request_id=request_id, filename=filename, status="FAILED", reason=str(error))
        raise HTTPException(
            422,
            detail={"error": {"code": "INVALID_KPI_FILE", "message": str(error), "details": []}},
        ) from error

    audit(
        "KPI_ANALYSIS",
        request_id=request_id,
        filename=filename,
        status="COMPLETED",
        cell_count=dataset.get("cell_count", 0),
    )

    return DatasetRepository(db).save(dataset)


@router.get("", summary="List analyzed datasets")
def list_datasets(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return DatasetRepository(db).list()


@router.get("/{dataset_id}", summary="Get an analyzed dataset")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return get_dataset_or_404(db, dataset_id)


@router.get("/{dataset_id}/summary", summary="Get dataset KPI summary")
def get_summary(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    dataset = get_dataset_or_404(db, dataset_id)
    return {
        "dataset_id": dataset_id,
        "summary": dataset["summary"],
        "available_kpis": dataset["available_kpis"],
        "unsupported_columns": dataset["unsupported_columns"],
        "invalid_values": dataset["invalid_values"],
    }


@router.get("/{dataset_id}/cells", summary="List cells in a dataset")
def get_cells(dataset_id: str, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)) -> dict[str, object]:
    dataset = get_dataset_or_404(db, dataset_id)
    return {"dataset_id": dataset_id, "items": dataset["cells"][:limit], "total": len(dataset["cells"])}


@router.get("/{dataset_id}/bad-cells", summary="Find underperforming cells")
def get_bad_cells(
    dataset_id: str,
    limit: int = Query(10, ge=1, le=100),
    status: str | None = None,
    kpi: str | None = None,
    site_id: str | None = None,
    technology: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    dataset = get_dataset_or_404(db, dataset_id)
    items = find_underperforming_cells(dataset, limit, status, kpi, site_id, technology)
    return {"dataset_id": dataset_id, "items": items, "total": len(items)}


@router.get("/{dataset_id}/anomalies", summary="Get cells with critical KPI evidence")
def get_anomalies(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    dataset = get_dataset_or_404(db, dataset_id)
    items = [cell for cell in dataset["cells"] if cell["status"] == "CRITICAL"]
    return {"dataset_id": dataset_id, "items": items, "total": len(items)}


@router.get("/{dataset_id}/sites", summary="Site-level aggregation for a dataset")
def get_sites(dataset_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """Return per-site health aggregation derived from actual cell data.

    Never invent site health — always computed from cell KPI results.
    """
    dataset = get_dataset_or_404(db, dataset_id)
    sites: dict[str, dict] = {}
    for cell in dataset["cells"]:
        site_id = cell.get("site_id") or "UNKNOWN"
        if site_id not in sites:
            sites[site_id] = {
                "site_id": site_id,
                "total_cells": 0,
                "healthy_cells": 0,
                "warning_cells": 0,
                "critical_cells": 0,
                "unknown_cells": 0,
                "health_scores": [],
            }
        entry = sites[site_id]
        entry["total_cells"] += 1
        status = cell.get("status", "UNKNOWN")
        key = f"{status.lower()}_cells"
        if key in entry:
            entry[key] += 1
        else:
            entry["unknown_cells"] += 1
        if cell.get("health_score") is not None:
            entry["health_scores"].append(cell["health_score"])

    # Compute per-site average health score
    result = []
    for entry in sites.values():
        scores = entry.pop("health_scores")
        entry["average_health_score"] = round(sum(scores) / len(scores), 1) if scores else None
        entry["site_status"] = (
            "CRITICAL" if entry["critical_cells"] > 0
            else "WARNING" if entry["warning_cells"] > 0
            else "HEALTHY" if entry["healthy_cells"] > 0
            else "UNKNOWN"
        )
        result.append(entry)

    result.sort(key=lambda s: (s["average_health_score"] is None, s["average_health_score"] or 0))
    return {"dataset_id": dataset_id, "sites": result, "total": len(result)}
