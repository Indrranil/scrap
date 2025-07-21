import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.schemas.pipeline_session import PipelineSessionCreate, PipelineSession
from app.services.base import CRUDBase


class PipelineSessionService(CRUDBase[PipelineSessionModel, PipelineSessionCreate, PipelineSessionCreate]):
    """
    Pipeline Session-specific CRUD service with authentication support.
    """
    
    def __init__(self):
        super().__init__(PipelineSessionModel)
    
    def create_with_user(self, db: Session, *, obj_in: PipelineSessionCreate, user_id: int) -> PipelineSessionModel:
        """
        Create a new pipeline session with user information.
            
        Returns:
            Created pipeline session instance
        """
        try:
            # Create model instance with user info
            # Exclude created_by from original data to avoid type conflicts
            session_data = obj_in.dict(exclude={'created_by'})
            session_data['created_by'] = str(user_id)  # Explicitly set as string
            session_data['created_at'] = int(time.time())
            session_data['is_usable'] = 1
            
            db_obj = self.model(**session_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            return db_obj
            
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Create a singleton instance
pipeline_session_service = PipelineSessionService()
