import enum


class AppRole(str, enum.Enum):
    SHOPFLOOR = "shopfloor"
    SCRAPEYARD = "scrapeyard"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACKNOWLEDGED = "acknowledged"
    SOLD = "sold"


class RejectionReasonType(str, enum.Enum):
    QUANTITY_MISMATCH = "quantity_mismatch"
    WRONG_MATERIAL = "wrong_material"
    OTHERS = "others"


class TransferEventType(str, enum.Enum):
    DISPATCHED = "dispatched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACKNOWLEDGED = "acknowledged"


class ActorRole(str, enum.Enum):
    SHOPFLOOR = "shopfloor"
    SCRAPEYARD = "scrapeyard"
    ADMIN = "admin"
