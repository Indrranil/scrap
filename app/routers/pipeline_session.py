import time

from app.auth.auth import require_roles
from app.database.connection import get_db
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.models.pipeline_session_output import PipelineSessionOutput
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit
from app.schemas.pipeline_session import PipelineSessionCreate, PipelineSession, BasicFilter
from sqlalchemy.orm import Session

router = APIRouter(prefix="/v1/pipeline-session", tags=["pipeline-session"])


@router.post("/new", response_model=PipelineSession, status_code=201)
async def create_pipeline_session(
        request: Request,
        pipeline_session: PipelineSessionCreate,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin"]))
):
    try:
        user_id = request.state.user["id"]
        db.begin()
        timestamp = int(time.time())

        new_session = PipelineSessionModel(
            pipeline_id=pipeline_session.pipeline_id,
            pipeline_input_id=pipeline_session.pipeline_input_id,
            name=pipeline_session.name,
            created_by=user_id,
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_pipeline_sessions(
        overview: int = Query(1, required=False),
        pipeline_id: int = Query(None, required=False),
        filters: BasicFilter = Depends(),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
):
    try:
        if filters.sort == 0:
            sort = PipelineSessionModel.id.asc()
        else:
            sort = PipelineSessionModel.id.desc()

        base_query = db.query(PipelineSessionModel).filter(PipelineSessionModel.is_usable == 1) if pipeline_id is None else db.query(PipelineSessionModel).filter(PipelineSessionModel.is_usable == 1, PipelineSessionModel.pipeline_id == pipeline_id)

        if filters.limit > 0:
            sessions = base_query.order_by(sort).limit(filters.limit).all()
        else:
            sessions = base_query.order_by(sort).all()

        # If overview=1, return just the session data
        if overview == 1:
            return {
                "total": len(sessions),
                "data": sessions
            }

        # If overview=0, include related outputs and units
        sessions_arr = [vars(session) for session in sessions]

        for index, session in enumerate(sessions):
            # Get related outputs with eager loading
            outputs = (
                db.query(PipelineSessionOutput)
                .filter(
                    PipelineSessionOutput.pipeline_session_id == session.id,
                    PipelineSessionOutput.id > filters.last_index,
                    PipelineSessionOutput.is_usable == 1
                ).limit(15)
                .all()
            )

            outputs_list = []
            for output in outputs:
                output_dict = vars(output)
                # Get related output units for each output
                units = (
                    db.query(PipelineSessionOutputUnit)
                    .filter(
                        PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                        PipelineSessionOutputUnit.is_usable == 1
                    )
                    .all()
                )

                output_dict['units'] = [vars(unit) for unit in units]
                outputs_list.append(output_dict)

            sessions_arr[index]['outputs'] = outputs_list

        return {
            "total": len(sessions),
            "data": sessions
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline sessions: {str(e)}"
        )


@router.get("/{session_id}")
async def get_pipeline_session(
        session_id: int,
        overview: int = Query(1),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
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

        # Get related outputs with eager loading
        outputs = (
            db.query(PipelineSessionOutput)
            .filter(
                PipelineSessionOutput.pipeline_session_id == session_id,
                PipelineSessionOutput.is_usable == 1
            )
            .all()
        )

        outputs_list = []
        for output in outputs:
            output_dict = vars(output)
            # Get related output units for each output
            units = (
                db.query(PipelineSessionOutputUnit)
                .filter(
                    PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                    PipelineSessionOutputUnit.is_usable == 1
                )
                .all()
            )

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
