from sqlalchemy.orm import Session
from models.application import Application as ApplicationModel
from typing import Optional

def check_duplicate_name(db: Session, name: str, exclude_id: Optional[int] = None) -> bool:
    """Check if an application with the given name already exists"""
    query = db.query(ApplicationModel).filter(
        ApplicationModel.name == name,
        ApplicationModel.is_usable == 1
    )
    if exclude_id:
        query = query.filter(ApplicationModel.id != exclude_id)
    return db.query(query.exists()).scalar() 