import logging
import time
from typing import (Any, Dict, Generic, List, Optional, Protocol, Type,
                    TypeVar, Union)

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# Type variables for generic typing
class ModelWithIdUsable(Protocol):
    id: int
    is_usable: int


ModelType = TypeVar("ModelType", bound=ModelWithIdUsable)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = logging.getLogger(__name__)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD service base class that provides common database operations
    for any SQLAlchemy model with standardized patterns.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUD service with a specific model.

        Args:
            model: The SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a single record by ID.
        Returns:
            Model instance or None if not found
        """
        try:
            return (
                db.query(self.model)
                .filter(and_(self.model.id == id, self.model.is_usable == 1))  # type: ignore
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        Returns:
            List of model instances
        """
        try:
            return (
                db.query(self.model)
                .filter(self.model.is_usable == 1)  # type: ignore
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    def get_all(self, db: Session) -> List[ModelType]:
        """
        Get all active records.
        Returns:
            List of all active model instances
        """
        try:
            return db.query(self.model).filter(self.model.is_usable == 1).all()  # type: ignore
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        Returns:
            Created model instance
        """
        try:
            logger.debug(f"Creating {self.model.__name__} with data: {obj_in.dict()}")

            # Convert Pydantic model to dict and add standard fields
            obj_data = obj_in.dict()
            obj_data["created_at"] = int(time.time())

            # Set default is_usable if not provided
            if "is_usable" not in obj_data:
                obj_data["is_usable"] = 1

            # Create model instance
            db_obj = self.model(**obj_data)
            logger.debug(f"Created model instance: {vars(db_obj)}")

            db.add(db_obj)
            db.commit()
            logger.debug("Database commit successful")
            db.refresh(db_obj)
            logger.debug(f"Refreshed model instance: {vars(db_obj)}")

            return db_obj

        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error creating {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Update an existing record.

        Returns:
            Updated model instance
        """
        try:
            logger.debug(f"Updating {self.model.__name__} with id {db_obj.id}")

            # Convert to dict if it's a Pydantic model
            if isinstance(obj_in, BaseModel):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in

            # Update model attributes
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            db.commit()
            logger.debug("Database commit successful")
            db.refresh(db_obj)
            logger.debug(f"Updated model instance: {vars(db_obj)}")

            return db_obj

        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error updating {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Soft delete a record by setting is_usable to 0.

        Returns:
            Deleted model instance

        Raises:
            HTTPException: If record not found
        """
        try:
            logger.debug(f"Soft deleting {self.model.__name__} with id {id}")

            db_obj = self.get(db, id)
            if not db_obj:
                raise HTTPException(
                    status_code=404, detail=f"{self.model.__name__} not found"
                )

            db_obj.is_usable = 0
            db.commit()
            logger.debug("Database commit successful")
            db.refresh(db_obj)
            logger.debug(f"Soft deleted model instance: {vars(db_obj)}")

            return db_obj

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error deleting {self.model.__name__}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    def get_or_404(self, db: Session, id: int) -> ModelType:
        """
        Get a record by ID or raise 404 if not found.

        Returns:
            Model instance

        Raises:
            HTTPException: If record not found
        """
        db_obj = self.get(db, id)
        if not db_obj:
            raise HTTPException(
                status_code=404, detail=f"{self.model.__name__} not found"
            )
        return db_obj
