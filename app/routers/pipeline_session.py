from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import time

from database.connection import get_db
from schemas.pipeline_session import PipelineSessionCreate, PipelineSession
from models.pipeline_session import PipelineSession as PipelineSessionModel
from models.pipeline_session_output import PipelineSessionOutput
from models.pipeline_session_output_unit import PipelineSessionOutputUnit

router = APIRouter(prefix="/v1/pipeline-session", tags=["pipeline-session"])

@router.post("/new", response_model=PipelineSession, status_code=201)
async def create_pipeline_session(
    pipeline_session: PipelineSessionCreate,
    user: str = "",
    db: Session = Depends(get_db)
):
    try:
        db.begin()
        
        timestamp = int(time.time())
        new_session = PipelineSessionModel(
            pipeline_id=pipeline_session.pipeline_id,
            pipeline_input_id=pipeline_session.pipeline_input_id,
            name=pipeline_session.name,
            created_by=pipeline_session.created_by,
            created_at=timestamp,
            ended_at=pipeline_session.ended_at,
            is_usable=1
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating pipeline session: {str(e)}"
        )

@router.get("/{session_id}")
async def get_pipeline_session(
    session_id: int,
    overview: int = Query(1),
    db: Session = Depends(get_db)
):
    try:
        # Get base session data
        session = db.query(PipelineSessionModel).filter(
            PipelineSessionModel.id == session_id,
            PipelineSessionModel.is_usable == 1
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session with ID {session_id} not found"
            )
        
        # If overview=1, return just the session data
        if overview == 1:
            return session
            
        # If overview=0, include related outputs and units
        session_dict = vars(session)
        
        # Get related outputs
        outputs = db.query(PipelineSessionOutput).filter(
            PipelineSessionOutput.pipeline_session_id == session_id,
            PipelineSessionOutput.is_usable == 1
        ).all()
        
        outputs_list = []
        for output in outputs:
            output_dict = vars(output)
            # Get related output units for each output
            units = db.query(PipelineSessionOutputUnit).filter(
                PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                PipelineSessionOutputUnit.is_usable == 1
            ).all()
            
            output_dict['units'] = [vars(unit) for unit in units]
            outputs_list.append(output_dict)
            
        session_dict['outputs'] = outputs_list
        
        return session_dict
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session: {str(e)}"
        )

@router.get("/")
async def get_all_pipeline_sessions(
    overview: int = Query(1),
    db: Session = Depends(get_db)
):
    try:
        sessions = db.query(PipelineSessionModel).filter(
            PipelineSessionModel.is_usable == 1
        ).all()
        
        # If overview=1, return just the sessions list
        if overview == 1:
            return sessions
            
        # If overview=0, include related outputs and units for each session
        result = []
        for session in sessions:
            session_dict = vars(session)
            
            # Get related outputs
            outputs = db.query(PipelineSessionOutput).filter(
                PipelineSessionOutput.pipeline_session_id == session.id,
                PipelineSessionOutput.is_usable == 1
            ).all()
            
            outputs_list = []
            for output in outputs:
                output_dict = vars(output)
                # Get related output units for each output
                units = db.query(PipelineSessionOutputUnit).filter(
                    PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                    PipelineSessionOutputUnit.is_usable == 1
                ).all()
                
                output_dict['units'] = [vars(unit) for unit in units]
                outputs_list.append(output_dict)
                
            session_dict['outputs'] = outputs_list
            result.append(session_dict)
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline sessions: {str(e)}"
        )