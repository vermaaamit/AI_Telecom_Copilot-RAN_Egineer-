"""Operational Shift Handover Reports API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.reports.generator import ShiftHandoverGenerator
from app.reports.models import ShiftHandoverReport
from app.security.auth import User, get_current_user

router = APIRouter(prefix="/reports", tags=["Operational Reports & Shift Handover"])


@router.get("/handover", response_model=ShiftHandoverReport)
async def get_shift_handover_report(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID to analyze"),
    shift_title: str = Query("NOC RAN Operational Shift Handover", description="Shift title / designation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an operational shift handover report consolidating alarms, incidents, degraded cells, and predictive warnings."""
    generator = ShiftHandoverGenerator(db)
    report = generator.generate(
        dataset_id=dataset_id,
        prepared_by=f"{current_user.full_name} ({current_user.role.value})",
        shift_title=shift_title,
    )
    return report


@router.get("/handover/export")
async def export_shift_handover_markdown(
    dataset_id: Optional[str] = Query(None, description="Optional dataset ID to analyze"),
    shift_title: str = Query("NOC RAN Operational Shift Handover", description="Shift title / designation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export the shift handover report in markdown format suitable for shift-change logs."""
    generator = ShiftHandoverGenerator(db)
    report = generator.generate(
        dataset_id=dataset_id,
        prepared_by=f"{current_user.full_name} ({current_user.role.value})",
        shift_title=shift_title,
    )
    markdown_content = generator.format_markdown(report)
    return Response(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=shift_handover_{report.report_id}.md"},
    )

