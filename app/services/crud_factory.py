from typing import Type, TypeVar, Generic, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.base import CRUDBase

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_crud_router(
    service: CRUDBase,
    create_schema: Type[CreateSchemaType],
    response_schema: Type[ResponseSchemaType],
    prefix: str,
    tags: List[str],
    entity_name: str = None
) -> APIRouter:
    """
    Factory function to create a complete CRUD router for any service.
    
    Args:
        service: The CRUD service instance
        create_schema: Pydantic schema for creation
        response_schema: Pydantic schema for responses
        prefix: Router prefix (e.g., "/v1/application")
        tags: Router tags for OpenAPI documentation
        entity_name: Human-readable entity name (defaults to model name)
        
    Returns:
        Configured APIRouter with all CRUD endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags)
    
    if not entity_name:
        entity_name = service.model.__name__.lower()
    
    @router.post("/new", response_model=response_schema, status_code=201)
    async def create_item(
        item: create_schema,
        db: Session = Depends(get_db)
    ):
        f"""Create a new {entity_name}."""
        return service.create(db, obj_in=item)
    
    @router.get("/all", response_model=List[response_schema])
    async def get_all_items(
        db: Session = Depends(get_db)
    ):
        f"""Get all active {entity_name}s."""
        return service.get_all(db)
    
    @router.get("/{item_id}", response_model=response_schema)
    async def get_item(
        item_id: int,
        db: Session = Depends(get_db)
    ):
        f"""Get a specific {entity_name} by ID."""
        return service.get_or_404(db, item_id)
    
    @router.patch("/{item_id}", response_model=response_schema)
    async def update_item(
        item_id: int,
        item: create_schema,
        db: Session = Depends(get_db)
    ):
        f"""Update an existing {entity_name}."""
        db_obj = service.get_or_404(db, item_id)
        return service.update(db, db_obj=db_obj, obj_in=item)
    
    @router.delete("/{item_id}", response_model=response_schema)
    async def delete_item(
        item_id: int,
        db: Session = Depends(get_db)
    ):
        f"""Soft delete a {entity_name}."""
        return service.remove(db, id=item_id)
    
    return router
