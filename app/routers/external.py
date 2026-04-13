import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query, Body, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql.selectable import and_

from app.database.connection import get_db
from app.models.pipeline_session import PipelineSession
from app.models.pipeline_session_output import PipelineSessionOutput
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit

router = APIRouter(prefix="/v1/external", tags=["External"])

tz = ZoneInfo("Asia/Kolkata")


def get_shift_start_time():
    loop_start_time = datetime.now(tz=tz)
    day_shift = 1 if 0 <= loop_start_time.hour < 6 else 0
    shift_start_time = (
        datetime(year=loop_start_time.year, month=loop_start_time.month,
                 day=loop_start_time.day - day_shift, hour=7, tzinfo=tz))
    shift_end_time = shift_start_time + timedelta(days=1)
    return shift_start_time, shift_end_time


@router.post("/pipeline-session-output-unit", status_code=201)
async def process_payload(pipeline_id: int = Query(...), payload: dict = Body(...), db: Session = Depends(get_db)):
    shift_start_time, shift_end_time = get_shift_start_time()
    current_session = db.query(PipelineSession).filter(
        and_(PipelineSession.pipeline_id == pipeline_id, PipelineSession.created_at > shift_start_time.timestamp(),
             PipelineSession.created_at < shift_end_time.timestamp())).first()

    if current_session is None:
        new_pipeline_session_payload = {"pipeline_id": pipeline_id, "name": "", "created_by": "external",
                                        "created_at": int(time.time()), "is_usable": 1}
        new_pipeline_session = PipelineSession(**new_pipeline_session_payload)
        db.add(new_pipeline_session)
        db.commit()
        current_session_id = new_pipeline_session.id
    else:
        current_session_id = current_session.id
    new_pipeline_session_output_payload = {"pipeline_session_id": current_session_id, "created_at": int(time.time()),
                                           "is_usable": 1}
    new_pipeline_session_output = PipelineSessionOutput(**new_pipeline_session_output_payload)
    db.add(new_pipeline_session_output)
    db.commit()
    new_pipeline_session_output_id = new_pipeline_session_output.id

    pipeline_session_output_units = []
    for key, value in payload.items():
        p = {
            "pipeline_session_output_id": new_pipeline_session_output_id,
            "name": key,
            "output_key": key,
            "output_value": value,
            "status": "success",
            "verdict": "1",
            "created_at": int(time.time()),
            "is_usable": value
        }
        pipeline_session_output_units.append(PipelineSessionOutputUnit(**p))
    db.add_all(pipeline_session_output_units)
    db.commit()

    return {
        "status": "success",
        "message": "Payload received",
    }
