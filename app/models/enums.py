import enum


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    PENDING_GSO = "pending_gso"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACKNOWLEDGED = "acknowledged"
    GSO_REJECTED = "gso_rejected"
    GSO_ACKNOWLEDGED = "gso_acknowledged"
    SOLD = "sold"


class RejectionReasonType(str, enum.Enum):
    QUANTITY_MISMATCH = "quantity_mismatch"
    WRONG_MATERIAL = "wrong_material"
    OTHERS = "others"


class TransferEventType(str, enum.Enum):
    DISPATCHED = "dispatched"
    GSO_APPROVED = "gso_approved"
    GSO_AUTO_APPROVED = "gso_auto_approved"
    GSO_REJECTED = "gso_rejected"
    GSO_ACKNOWLEDGED = "gso_acknowledged"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACKNOWLEDGED = "acknowledged"


class ActorRole(str, enum.Enum):
    SHOPFLOOR = "shopfloor"
    GSO = "gso"
    SCRAPEYARD = "scrapeyard"
    SECURITY = "security"
    ADMIN = "admin"


class InventoryMovementType(str, enum.Enum):
    ACCEPT_NON_P = "accept_non_p"
    SHRED_OUTPUT = "shred_output"
    SALE_RESERVE = "sale_reserve"
    SALE_RELEASE = "sale_release"
    SALE_APPROVE = "sale_approve"


class MaterialSaleStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DispatchMethod(str, enum.Enum):
    QR = "qr"
    MANUAL = "manual"


class MaterialState(str, enum.Enum):
    SHREDDED = "shredded"
    NOT_SHREDDED = "not_shredded"
