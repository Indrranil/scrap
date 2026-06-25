from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.schemas.reporting import (
    AcceptedVsSoldItem,
    PlantGenerationItem,
    RecentTransferItem,
    RejectionReasonItem,
    SummaryKPIs,
)
from app.services.reporting import reporting_service

router = APIRouter(prefix="/v1/reporting", tags=["reporting"])


def _parse_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    except ValueError:
        return None


@router.get("/summary", response_model=SummaryKPIs)
def reporting_summary(
    plant_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Dashboard KPI summary."""
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    return reporting_service.get_summary(
        db, plant_id=plant_id, date_from=_parse_date(date_from), date_to=date_to_ts
    )


@router.get("/plant-generation", response_model=List[PlantGenerationItem])
def plant_generation(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Plant-wise generation bar chart data."""
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    return reporting_service.get_plant_generation(
        db, date_from=_parse_date(date_from), date_to=date_to_ts
    )


@router.get("/rejection-reasons", response_model=List[RejectionReasonItem])
def rejection_reasons(
    plant_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Rejection reason donut chart data."""
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    return reporting_service.get_rejection_reasons(
        db, plant_id=plant_id, date_from=_parse_date(date_from), date_to=date_to_ts
    )


@router.get("/accepted-vs-sold", response_model=List[AcceptedVsSoldItem])
def accepted_vs_sold(
    plant_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Accepted vs sold bar chart data."""
    date_to_ts = _parse_date(date_to)
    if date_to_ts:
        date_to_ts += 86399
    return reporting_service.get_accepted_vs_sold(
        db, plant_id=plant_id, date_from=_parse_date(date_from), date_to=date_to_ts
    )


@router.get("/recent-transfers", response_model=List[RecentTransferItem])
def recent_transfers(
    plant_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    _: bool = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    """Recent transfers table."""
    return reporting_service.get_recent_transfers(db, plant_id=plant_id, limit=limit)
