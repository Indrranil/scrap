from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
import time

from database.connection import get_db
from schemas.pipeline_session_output import PipelineSessionOutputCreate, PipelineSessionOutput
from models.pipeline_session_output import PipelineSessionOutput as PipelineSessionOutputModel
from models.pipeline_session_output_unit import PipelineSessionOutputUnit
from models.general_property import GeneralProperty

router = APIRouter(prefix="/v1/pipeline-session-output", tags=["pipeline-session-output"])

@router.post("/new", response_model=PipelineSessionOutput, status_code=201)
async def create_pipeline_session_output(
    pipeline_session_output: PipelineSessionOutputCreate,
    manual: Optional[int] = Query(0),
    property_key: Optional[str] = Query(None, alias="property-key"),
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        timestamp = int(time.time())
        
        # Create pipeline session output
        new_output = PipelineSessionOutputModel(
            pipeline_session_id=pipeline_session_output.pipeline_session_id,
            name=pipeline_session_output.name,
            created_at=timestamp,
            ended_at=pipeline_session_output.ended_at,
            is_usable=1
        )
        
        db.add(new_output)
        db.flush()  # Flush to get the new output ID
        
        # If manual mode, create output units
        if manual:
            # Get relevant properties query
            query = db.query(GeneralProperty).filter(
                GeneralProperty.is_usable == 1
            )
            
            # Apply property key filter if provided
            if property_key:
                property_keys = [key.strip() for key in property_key.split(',')]
                query = query.filter(GeneralProperty.property_key.in_(property_keys))
                
            properties = query.all()
            
            # Create output units for each property
            for prop in properties:
                output_unit = PipelineSessionOutputUnit(
                    pipeline_session_output_id=new_output.id,
                    property_reference_id=prop.id,
                    output_key=prop.property_key,
                    output_value=None,
                    status='idle',
                    created_at=timestamp,
                    is_usable=1
                )
                db.add(output_unit)
        
        db.commit()
        db.refresh(new_output)
        
        return new_output
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating pipeline session output: {str(e)}"
        )

@router.get("/{output_id}")
async def get_pipeline_session_output(
    output_id: int,
    overview: int = Query(1),
    db: Session = Depends(get_db)
):
    try:
        # Get base output data
        output = db.query(PipelineSessionOutputModel).filter(
            PipelineSessionOutputModel.id == output_id,
            PipelineSessionOutputModel.is_usable == 1
        ).first()
        
        if not output:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output with ID {output_id} not found"
            )
            
        # If overview=1, return just the output data
        if overview == 1:
            return output
        
        # If overview=0, include related output units
        output_dict = vars(output)
        
        # Get related output units
        units = db.query(PipelineSessionOutputUnit).filter(
            PipelineSessionOutputUnit.pipeline_session_output_id == output_id,
            PipelineSessionOutputUnit.is_usable == 1
        ).all()
        
        output_dict['units'] = [vars(unit) for unit in units]
        
        return output_dict
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session output: {str(e)}"
        )

@router.get("/")
async def get_all_pipeline_session_outputs(
    overview: int = Query(1),
    db: Session = Depends(get_db)
):
    try:
        outputs = db.query(PipelineSessionOutputModel).filter(
            PipelineSessionOutputModel.is_usable == 1
        ).all()
        
        # If overview=1, return just the outputs list
        if overview == 1:
            return outputs
            
        # If overview=0, include related output units for each output
        result = []
        for output in outputs:
            output_dict = vars(output)
            
            # Get related output units
            units = db.query(PipelineSessionOutputUnit).filter(
                PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                PipelineSessionOutputUnit.is_usable == 1
            ).all()
            
            output_dict['units'] = [vars(unit) for unit in units]
            result.append(output_dict)
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session outputs: {str(e)}"
        )