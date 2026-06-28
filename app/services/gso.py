from sqlalchemy.orm import Session

from app.models.gso import Gso


class GsoService:
    def get_active(self, db: Session) -> Gso:
        gso = (
            db.query(Gso)
            .filter(Gso.is_active.is_(True))
            .order_by(Gso.id.asc())
            .first()
        )
        if not gso:
            raise ValueError("No active GSO configured")
        return gso


gso_service = GsoService()
