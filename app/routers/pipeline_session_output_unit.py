from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import time

from database.connection import get_db
from schemas.pipeline_session_output_unit import (
    PipelineSessionOutputUnitCreate, 
    PipelineSessionOutputUnit,
    PipelineSessionOutputUnitUpdate
)
from models.pipeline_session_output_unit import PipelineSessionOutputUnit as PipelineSessionOutputUnitModel

router = APIRouter(prefix="/v1/pipeline-session-output-unit", tags=["pipeline-session-output-unit"])

@router.post("/new", response_model=PipelineSessionOutputUnit, status_code=201)
async def create_pipeline_session_output_unit(
    unit: PipelineSessionOutputUnitCreate,
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        timestamp = int(time.time())
        new_unit = PipelineSessionOutputUnitModel(
            pipeline_session_output_id=unit.pipeline_session_output_id,
            property_reference_id=unit.property_reference_id,
            name=unit.name,
            output_key=unit.output_key,
            output_value=unit.output_value,
            status=unit.status,
            created_at=timestamp,
            is_usable=1
        )
        
        db.add(new_unit)
        db.commit()
        db.refresh(new_unit)
        
        return new_unit
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating pipeline session output unit: {str(e)}"
        )

@router.get("/{unit_id}", response_model=PipelineSessionOutputUnit)
async def get_pipeline_session_output_unit(
    unit_id: int,
    db: Session = Depends(get_db)
):
    try:
        unit = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.id == unit_id,
            PipelineSessionOutputUnitModel.is_usable == 1
        ).first()
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output unit with ID {unit_id} not found"
            )
            
        return unit
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session output unit: {str(e)}"
        )

@router.get("/", response_model=List[PipelineSessionOutputUnit])
async def get_all_pipeline_session_output_units(
    pipeline_session_output_id: int = Query(...),
    db: Session = Depends(get_db)
):
    try:
        units = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.pipeline_session_output_id == pipeline_session_output_id,
            PipelineSessionOutputUnitModel.is_usable == 1
        ).all()
        
        return units
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session output units: {str(e)}"
        )

@router.patch("/{unit_id}", response_model=PipelineSessionOutputUnit)
async def update_pipeline_session_output_unit(
    unit_id: int,
    unit_update: PipelineSessionOutputUnitUpdate,
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        unit = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.id == unit_id,
            PipelineSessionOutputUnitModel.is_usable == 1
        ).first()
        
        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output unit with ID {unit_id} not found"
            )
            
        # Update fields if provided
        for key, value in unit_update.dict(exclude_unset=True).items():
            setattr(unit, key, value)
            
        db.commit()
        db.refresh(unit)  # Refresh to get updated data
        
        return unit  # Return the updated unit
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating pipeline session output unit: {str(e)}"
        )

@router.patch("/all", response_model=List[PipelineSessionOutputUnit])
async def update_all_pipeline_session_output_units(
    unit_update: PipelineSessionOutputUnitUpdate,
    pipeline_session_output_id: Optional[int] = None,
    output_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        # Build query based on parameters
        query = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.is_usable == 1
        )
        
        if pipeline_session_output_id:
            query = query.filter(
                PipelineSessionOutputUnitModel.pipeline_session_output_id == pipeline_session_output_id
            )
            
        if output_key:
            query = query.filter(
                PipelineSessionOutputUnitModel.output_key == output_key
            )
            
        units = query.all()
        
        if not units:
            raise HTTPException(
                status_code=404,
                detail="No matching pipeline session output units found"
            )
            
        # Update all matching units
        update_data = unit_update.dict(exclude_unset=True)
        for unit in units:
            for key, value in update_data.items():
                setattr(unit, key, value)
            
        db.commit()
        
        # Refresh and return updated units
        updated_units = query.all()
        return updated_units
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating pipeline session output units: {str(e)}"
        )