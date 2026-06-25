from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class UnitTotals(BaseModel):
    kg: Decimal = Decimal("0")
    ea: Decimal = Decimal("0")


class SummaryKPIs(BaseModel):
    total_generated: UnitTotals
    total_accepted: UnitTotals
    total_rejected: UnitTotals
    accepted_percentage: float
    rejected_percentage: float
    total_sold: UnitTotals
    current_inventory: UnitTotals
    revenue_inr: Decimal
    avg_time_to_accept_days: Optional[float] = None
    transfer_count: int


class PlantGenerationItem(BaseModel):
    plant_id: int
    plant_name: str
    generated: UnitTotals
    accepted: UnitTotals
    rejected: UnitTotals


class RejectionReasonItem(BaseModel):
    reason_type: str
    kg: Decimal
    ea: Decimal
    percentage: float


class AcceptedVsSoldItem(BaseModel):
    label: str
    kg: Decimal
    ea: Decimal


class RecentTransferItem(BaseModel):
    id: int
    sent_on: Optional[int] = None
    item_code: str
    item_name: str
    quantity_kg: Optional[Decimal] = None
    quantity_ea: Optional[Decimal] = None
    status: str
