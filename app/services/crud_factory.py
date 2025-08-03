from typing import List, Sequence, Type, TypeVar

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.base import CRUDBase, ModelWithIdUsable

# TypeVars with constraints
ModelType = TypeVar("ModelType", bound=ModelWithIdUsable)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_crud_router(
    service: CRUDBase[ModelType, CreateSchemaType, ResponseSchemaType],
    create_schema: Type[CreateSchemaType],
    response_schema: Type[ResponseSchemaType],
    prefix: str,
    tags: Sequence[str],
    entity_name: str = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=list(tags))

    if not entity_name:
        entity_name = service.model.__name__.lower()

    @router.post("/new", response_model=response_schema, status_code=201)
    async def create_item(item: create_schema, db: Session = Depends(get_db)):  # type: ignore
        """Create a new item."""
        return service.create(db, obj_in=item)

    @router.get("/all", response_model=List[response_schema])  # type: ignore
    async def get_all_items(db: Session = Depends(get_db)):
        """Get all active items."""
        return service.get_all(db)

    @router.get("/{item_id}", response_model=response_schema)  # type: ignore
    async def get_item(item_id: int, db: Session = Depends(get_db)):
        """Get item by ID."""
        return service.get_or_404(db, item_id)

    @router.patch("/{item_id}", response_model=response_schema)  # type: ignore
    async def update_item(item_id: int, item: create_schema, db: Session = Depends(get_db)):  # type: ignore
        """Update item."""
        db_obj = service.get_or_404(db, item_id)
        return service.update(db, db_obj=db_obj, obj_in=item)

    @router.delete("/{item_id}", response_model=response_schema)  # type: ignore
    async def delete_item(item_id: int, db: Session = Depends(get_db)):
        """Soft delete item."""
        return service.remove(db, id=item_id)

    return router
