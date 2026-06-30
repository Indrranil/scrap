from app.models.enums import MaterialSaleStatus, TransferStatus
from app.models.transfer import Transfer


def compute_transfer_display_status(status: TransferStatus) -> str:
    mapping = {
        TransferStatus.PENDING: "Pending",
        TransferStatus.PENDING_GSO: "Pending GSO",
        TransferStatus.DISPATCHED: "Dispatched",
        TransferStatus.ACCEPTED: "Accepted by SY",
        TransferStatus.REJECTED: "Rejected by SY",
        TransferStatus.ACKNOWLEDGED: "SY Rejection Acknowledged",
        TransferStatus.GSO_REJECTED: "Rejected by GSO",
        TransferStatus.GSO_ACKNOWLEDGED: "GSO Rejection Acknowledged",
        TransferStatus.SOLD: "Sold",
    }
    return mapping.get(status, status.value)


def compute_gso_display_status(transfer: Transfer) -> str:
    if transfer.gso_auto_approved:
        return "Auto Approved"
    if transfer.gso_approved_at:
        return "Approved by GSO"
    if transfer.status in (TransferStatus.GSO_REJECTED, TransferStatus.GSO_ACKNOWLEDGED):
        return "Rejected by GSO"
    return compute_transfer_display_status(transfer.status)


def compute_scrapeyard_display_status(status: TransferStatus) -> str:
    if status == TransferStatus.ACCEPTED:
        return "Accepted by SY"
    if status == TransferStatus.REJECTED:
        return "Rejected by SY"
    return compute_transfer_display_status(status)


def compute_sale_display_status(status: MaterialSaleStatus) -> str:
    mapping = {
        MaterialSaleStatus.PENDING: "Material Sale",
        MaterialSaleStatus.APPROVED: "Approved",
        MaterialSaleStatus.REJECTED: "Rejected",
    }
    return mapping.get(status, status.value)


def rejection_source_for_status(status: TransferStatus) -> str | None:
    if status == TransferStatus.REJECTED:
        return "scrapeyard"
    if status == TransferStatus.GSO_REJECTED:
        return "gso"
    return None
