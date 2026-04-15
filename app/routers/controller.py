import time

from fastapi import APIRouter, Query, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from app.database.connection import get_db
from app.models.pipeline_session import PipelineSession
from app.models.pipeline_session_output import PipelineSessionOutput
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit

router = APIRouter(prefix="/v1/controller", tags=["Controller"])


@router.post("/pipeline-session-output-unit", status_code=201)
async def process_payload(request: Request, pipeline_id: int | None = Query(default=None),
                          pipeline_session_id: int | None = Query(default=None),
                          payload: dict = Body(...), db: Session = Depends(get_db)):
    user_id = request.state.user["id"]
    if pipeline_id is None and pipeline_session_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pipeline or pipeline session id is required")
    if pipeline_id is not None:
        new_pipeline_session_payload = {"pipeline_id": pipeline_id, "name": "", "created_by": user_id,
                                        "created_at": int(time.time()), "is_usable": 1}
        new_pipeline_session = PipelineSession(**new_pipeline_session_payload)
        db.add(new_pipeline_session)
        db.commit()
        current_pipeline_session_id = new_pipeline_session.id
        new_pipeline_session_output_payload = {"pipeline_session_id": current_pipeline_session_id,
                                               "created_at": int(time.time()),
                                               "is_usable": 1}
        new_pipeline_session_output = PipelineSessionOutput(**new_pipeline_session_output_payload)
        db.add(new_pipeline_session_output)
        db.commit()
        current_pipeline_session_output_id = new_pipeline_session_output.id
    else:
        current_pipeline_session_id = pipeline_session_id
        pipeline_session_output: PipelineSessionOutput = db.query(PipelineSessionOutput).filter(PipelineSessionOutput.pipeline_session_id == pipeline_session_id).first()
        if pipeline_session_output is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline session output not found for session id [{pipeline_session_id}]")
        current_pipeline_session_output_id = pipeline_session_output.id

    pipeline_session_output_units = []
    for key, value in payload.items():
        p = {
            "pipeline_session_output_id": current_pipeline_session_output_id,
            "name": str(key),
            "output_key": str(key),
            "output_value": str(value),
            "status": "success",
            "verdict": "1",
            "created_at": int(time.time()),
            "is_usable": 1
        }
        pipeline_session_output_units.append(PipelineSessionOutputUnit(**p))
    db.add_all(pipeline_session_output_units)
    db.commit()

    return {
        "status": "success",
        "data": {
            "pipeline_session_id": current_pipeline_session_id,
            "pipeline_session_output_id": current_pipeline_session_output_id
        }
    }
