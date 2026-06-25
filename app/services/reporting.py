import time
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import RejectionReasonType, TransferStatus
from app.models.plant import Plant
from app.models.rejection_detail import RejectionDetail
from app.models.scrap_sale import ScrapSale
from app.models.transfer import Transfer
from app.schemas.reporting import (
    AcceptedVsSoldItem,
    PlantGenerationItem,
    RecentTransferItem,
    RejectionReasonItem,
    SummaryKPIs,
    UnitTotals,
)
from app.schemas.sale import SaleCreate, SaleResponse


def _add_to_totals(totals: UnitTotals, uom: str, qty: Decimal) -> None:
    if uom.upper() == "KG":
        totals.kg += qty
    else:
        totals.ea += qty


class ReportingService:
    def _base_transfer_query(
        self,
        db: Session,
        plant_id: Optional[int],
        date_from: Optional[int],
        date_to: Optional[int],
    ):
        query = db.query(Transfer).filter(
            Transfer.status.in_(
                [
                    TransferStatus.DISPATCHED,
                    TransferStatus.ACCEPTED,
                    TransferStatus.REJECTED,
                    TransferStatus.ACKNOWLEDGED,
                    TransferStatus.SOLD,
                ]
            )
        )
        if plant_id:
            query = query.filter(Transfer.shopfloor_plant_id == plant_id)
        if date_from:
            query = query.filter(Transfer.dispatched_at >= date_from)
        if date_to:
            query = query.filter(Transfer.dispatched_at <= date_to)
        return query

    def get_summary(
        self,
        db: Session,
        plant_id: Optional[int] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> SummaryKPIs:
        transfers = self._base_transfer_query(db, plant_id, date_from, date_to).all()

        generated = UnitTotals()
        accepted = UnitTotals()
        rejected = UnitTotals()

        accept_times: List[float] = []
        for t in transfers:
            _add_to_totals(generated, t.uom, t.quantity_sent)
            if t.status in (TransferStatus.ACCEPTED, TransferStatus.SOLD):
                _add_to_totals(accepted, t.uom, t.quantity_received or t.quantity_sent)
                if t.dispatched_at and t.processed_at:
                    accept_times.append((t.processed_at - t.dispatched_at) / 86400)
            if t.status in (TransferStatus.REJECTED, TransferStatus.ACKNOWLEDGED):
                _add_to_totals(
                    rejected, t.uom, t.quantity_received or t.quantity_sent
                )

        gen_total = float(generated.kg + generated.ea)
        acc_pct = (float(accepted.kg + accepted.ea) / gen_total * 100) if gen_total else 0
        rej_pct = (float(rejected.kg + rejected.ea) / gen_total * 100) if gen_total else 0

        sales_query = db.query(ScrapSale)
        if plant_id:
            sales_query = sales_query.filter(ScrapSale.plant_id == plant_id)
        if date_from:
            sales_query = sales_query.filter(ScrapSale.sold_at >= date_from)
        if date_to:
            sales_query = sales_query.filter(ScrapSale.sold_at <= date_to)
        sales = sales_query.all()

        sold = UnitTotals(
            kg=sum(s.quantity_kg or Decimal("0") for s in sales),
            ea=sum(s.quantity_ea or Decimal("0") for s in sales),
        )
        revenue = sum(s.amount_inr for s in sales)

        inventory = UnitTotals(
            kg=accepted.kg - sold.kg,
            ea=accepted.ea - sold.ea,
        )

        avg_time = sum(accept_times) / len(accept_times) if accept_times else None

        return SummaryKPIs(
            total_generated=generated,
            total_accepted=accepted,
            total_rejected=rejected,
            accepted_percentage=round(acc_pct, 1),
            rejected_percentage=round(rej_pct, 1),
            total_sold=sold,
            current_inventory=inventory,
            revenue_inr=revenue,
            avg_time_to_accept_days=round(avg_time, 1) if avg_time else None,
            transfer_count=len(transfers),
        )

    def get_plant_generation(
        self,
        db: Session,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> List[PlantGenerationItem]:
        plants = db.query(Plant).filter(Plant.is_active.is_(True)).all()
        results = []
        for plant in plants:
            transfers = self._base_transfer_query(
                db, plant.id, date_from, date_to
            ).all()
            gen = UnitTotals()
            acc = UnitTotals()
            rej = UnitTotals()
            for t in transfers:
                _add_to_totals(gen, t.uom, t.quantity_sent)
                if t.status in (TransferStatus.ACCEPTED, TransferStatus.SOLD):
                    _add_to_totals(acc, t.uom, t.quantity_received or t.quantity_sent)
                if t.status in (TransferStatus.REJECTED, TransferStatus.ACKNOWLEDGED):
                    _add_to_totals(rej, t.uom, t.quantity_received or t.quantity_sent)
            if gen.kg or gen.ea:
                results.append(
                    PlantGenerationItem(
                        plant_id=plant.id,
                        plant_name=plant.name,
                        generated=gen,
                        accepted=acc,
                        rejected=rej,
                    )
                )
        return results

    def get_rejection_reasons(
        self,
        db: Session,
        plant_id: Optional[int] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> List[RejectionReasonItem]:
        query = (
            db.query(RejectionDetail, Transfer)
            .join(Transfer, RejectionDetail.transfer_id == Transfer.id)
            .filter(Transfer.status.in_([TransferStatus.REJECTED, TransferStatus.ACKNOWLEDGED]))
        )
        if plant_id:
            query = query.filter(Transfer.shopfloor_plant_id == plant_id)
        if date_from:
            query = query.filter(Transfer.dispatched_at >= date_from)
        if date_to:
            query = query.filter(Transfer.dispatched_at <= date_to)

        totals: dict = {}
        total_qty = Decimal("0")
        for detail, transfer in query.all():
            key = detail.reason_type.value
            if key not in totals:
                totals[key] = UnitTotals()
            qty = transfer.quantity_received or transfer.quantity_sent
            _add_to_totals(totals[key], transfer.uom, qty)
            total_qty += qty

        results = []
        for reason, unit in totals.items():
            qty = unit.kg + unit.ea
            pct = float(qty / total_qty * 100) if total_qty else 0
            results.append(
                RejectionReasonItem(
                    reason_type=reason,
                    kg=unit.kg,
                    ea=unit.ea,
                    percentage=round(pct, 1),
                )
            )
        return results

    def get_accepted_vs_sold(
        self,
        db: Session,
        plant_id: Optional[int] = None,
        date_from: Optional[int] = None,
        date_to: Optional[int] = None,
    ) -> List[AcceptedVsSoldItem]:
        summary = self.get_summary(db, plant_id, date_from, date_to)
        return [
            AcceptedVsSoldItem(
                label="Accepted", kg=summary.total_accepted.kg, ea=summary.total_accepted.ea
            ),
            AcceptedVsSoldItem(
                label="Sold", kg=summary.total_sold.kg, ea=summary.total_sold.ea
            ),
        ]

    def get_recent_transfers(
        self,
        db: Session,
        plant_id: Optional[int] = None,
        limit: int = 10,
    ) -> List[RecentTransferItem]:
        query = db.query(Transfer).order_by(Transfer.dispatched_at.desc())
        if plant_id:
            query = query.filter(Transfer.shopfloor_plant_id == plant_id)
        transfers = query.limit(limit).all()
        return [
            RecentTransferItem(
                id=t.id,
                sent_on=t.dispatched_at,
                item_code=t.item_code,
                item_name=t.item_name,
                quantity_kg=t.quantity_sent if t.uom.upper() == "KG" else None,
                quantity_ea=t.quantity_sent if t.uom.upper() != "KG" else None,
                status=t.status.value,
            )
            for t in transfers
        ]


class SaleService:
    def create_sale(self, db: Session, data: SaleCreate) -> SaleResponse:
        transfer = db.query(Transfer).filter(Transfer.id == data.transfer_id).first()
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer not found")
        if transfer.status != TransferStatus.ACCEPTED:
            raise HTTPException(
                status_code=400, detail="Only accepted transfers can be sold"
            )

        now = int(time.time())
        sale = ScrapSale(
            transfer_id=data.transfer_id,
            plant_id=data.plant_id,
            quantity_kg=data.quantity_kg or Decimal("0"),
            quantity_ea=data.quantity_ea or Decimal("0"),
            amount_inr=data.amount_inr,
            sold_at=now,
            notes=data.notes,
        )
        transfer.status = TransferStatus.SOLD
        db.add(sale)
        db.commit()
        db.refresh(sale)
        return SaleResponse.model_validate(sale)

    def list_sales(
        self, db: Session, plant_id: Optional[int] = None, skip: int = 0, limit: int = 50
    ) -> tuple[int, List[SaleResponse]]:
        query = db.query(ScrapSale)
        if plant_id:
            query = query.filter(ScrapSale.plant_id == plant_id)
        total = query.count()
        sales = query.order_by(ScrapSale.sold_at.desc()).offset(skip).limit(limit).all()
        return total, [SaleResponse.model_validate(s) for s in sales]


reporting_service = ReportingService()
sale_service = SaleService()
