from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth.auth import require_roles
from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.pipeline_input import PipelineInput
from app.models.pipeline_session import PipelineSession as PipelineSessionModel
from app.models.pipeline_session_output import PipelineSessionOutput
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit
from app.schemas.pipeline_session import (
    BasicFilter,
    PipelineSession,
    PipelineSessionCreate,
)
from app.services.pipeline_session import pipeline_session_service

router = APIRouter(prefix="/v1/pipeline-session", tags=["pipeline-session"])


@router.post("/new", response_model=PipelineSession, status_code=201)
async def create_pipeline_session(
        request: Request,
        pipeline_session: PipelineSessionCreate,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin"])),
):
    """Create a new pipeline session with authentication."""
    user_id = request.state.user["id"]
    return pipeline_session_service.create_with_user(
        db, obj_in=pipeline_session, user_id=user_id
    )


@router.get("/all")
async def get_all_pipeline_sessions(
        overview: int = Query(1, required=False),
        pipeline_id: int = Query(None, required=False),
        name: str = Query(None, required=False),
        status: bool = Query(None, required=False),
        verdict: int = Query(None, required=False),
        start_date: int = Query(None, required=False),
        end_date: int = Query(None, required=False),
        filters: BasicFilter = Depends(),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        if filters.sort == 0:
            sort = PipelineSessionModel.id.asc()
        else:
            sort = PipelineSessionModel.id.desc()
        # Build base query with filters
        base_query = db.query(PipelineSessionModel).filter(PipelineSessionModel.is_usable == 1)

        # Add pipeline_id filter if provided
        if pipeline_id is not None:
            base_query = base_query.filter(PipelineSessionModel.pipeline_id == pipeline_id)

        # Add name filter if provided
        if name is not None:
            base_query = base_query.filter(PipelineSessionModel.name == name)

        # Add status filter if provided - filter sessions that have status property
        if status is not None and status:
            status_session_ids = (
                db.query(GeneralProperty.referrer_id)
                .filter(
                    GeneralProperty.property_type == "pipeline_session",
                    GeneralProperty.property_key == "status",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )
            session_ids_list = [row[0] for row in status_session_ids]
            base_query = base_query.filter(PipelineSessionModel.id.in_(session_ids_list))

        # Add date range filters if provided
        if start_date is not None:
            base_query = base_query.filter(PipelineSessionModel.created_at >= start_date)
        if end_date is not None:
            base_query = base_query.filter(PipelineSessionModel.created_at <= end_date)
        if filters.limit > 0:
            sessions = base_query.order_by(sort).limit(filters.limit).all()
        else:
            sessions = base_query.order_by(sort).all()
        # If overview=1, return just the session data with general properties
        if overview == 1:
            sessions_with_properties = []
            for session in sessions:
                session_dict = dict(vars(session))
                # Get general properties for this pipeline session
                general_properties = (
                    db.query(GeneralProperty)
                    .filter(
                        GeneralProperty.referrer_id == session.id,
                        GeneralProperty.property_type == "pipeline_session",
                        GeneralProperty.is_usable == 1,
                    )
                    .all()
                )
                # Add general properties to session data
                session_dict["general_properties"] = [
                    {
                        "id": prop.id,
                        "property_label": prop.property_label,
                        "property_key": prop.property_key,
                        "property_value": prop.property_value,
                        "tags": prop.tags,
                        "created_at": prop.created_at,
                    }
                    for prop in general_properties
                ]

                # Get pipeline input row if pipeline_input_id exists
                if session.pipeline_input_id:
                    pipeline_input = db.query(PipelineInput).filter(
                        PipelineInput.id == session.pipeline_input_id,
                        PipelineInput.is_usable == 1
                    ).first()
                    if pipeline_input:
                        session_dict["pipeline_input"] = {
                            "id": pipeline_input.id,
                            "name": pipeline_input.name,
                            "created_at": pipeline_input.created_at,
                            "is_usable": pipeline_input.is_usable
                        }
                    else:
                        session_dict["pipeline_input"] = None
                else:
                    session_dict["pipeline_input"] = None
                sessions_with_properties.append(session_dict)
            return {"total": len(sessions), "data": sessions_with_properties}
        # If overview=0, include related outputs and units
        sessions_arr = [dict(vars(session)) for session in sessions]
        if filters.last_index is None or filters.last_index <= 0:
            condition = PipelineSessionOutput.id > 0
        else:
            condition = PipelineSessionOutput.id < filters.last_index
        for index, session in enumerate(sessions):
            # Get general properties for this pipeline session
            general_properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == session.id,
                    GeneralProperty.property_type == "pipeline_session",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )
            # Add general properties to session data
            sessions_arr[index]["general_properties"] = [
                {
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "tags": prop.tags,
                    "created_at": prop.created_at,
                }
                for prop in general_properties
            ]

            # Get pipeline input row if pipeline_input_id exists
            if session.pipeline_input_id:
                pipeline_input = db.query(PipelineInput).filter(
                    PipelineInput.id == session.pipeline_input_id,
                    PipelineInput.is_usable == 1
                ).first()
                if pipeline_input:
                    sessions_arr[index]["pipeline_input"] = {
                        "id": pipeline_input.id,
                        "name": pipeline_input.name,
                        "created_at": pipeline_input.created_at,
                        "is_usable": pipeline_input.is_usable
                    }
                else:
                    sessions_arr[index]["pipeline_input"] = None
            else:
                sessions_arr[index]["pipeline_input"] = None
            # Get related outputs with eager loading
            outputs_query = (
                db.query(PipelineSessionOutput).outerjoin(PipelineSessionOutputUnit)
                .filter(
                    PipelineSessionOutput.pipeline_session_id == session.id,
                    condition,
                    PipelineSessionOutput.is_usable == 1,
                )
            )
            if verdict is not None:
                outputs_query = outputs_query.filter(PipelineSessionOutputUnit.verdict == verdict)

            outputs = outputs_query.order_by(PipelineSessionOutput.id.desc()).limit(15).all()
            outputs_list = []
            for output in outputs:
                output_dict = dict(vars(output))
                # Get related output units for each output
                units = (
                    db.query(PipelineSessionOutputUnit)
                    .filter(
                        PipelineSessionOutputUnit.pipeline_session_output_id
                        == output.id,
                        PipelineSessionOutputUnit.is_usable == 1,
                    )
                    .all()
                )

                # Enhance units with property reference data
                enhanced_units = []
                for unit in units:
                    unit_dict = dict(vars(unit))

                    # Get the referenced general property if property_reference_id exists
                    if unit.property_reference_id:
                        property_ref = (
                            db.query(GeneralProperty)
                            .filter(GeneralProperty.id == unit.property_reference_id)
                            .first()
                        )

                        if property_ref:
                            unit_dict["property_reference"] = {
                                "id": property_ref.id,
                                "property_label": property_ref.property_label,
                                "property_key": property_ref.property_key,
                                "property_value": property_ref.property_value,
                                "tags": property_ref.tags,
                                "created_at": property_ref.created_at,
                            }
                        else:
                            unit_dict["property_reference"] = None
                    else:
                        unit_dict["property_reference"] = None

                    enhanced_units.append(unit_dict)

                output_dict["units"] = enhanced_units
                outputs_list.append(output_dict)
            sessions_arr[index]["outputs"] = outputs_list  # type: ignore
        return {"total": len(sessions), "data": sessions_arr}
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline sessions: {str(e)}"
        )


@router.get("/{session_id}")
async def get_pipeline_session(
        session_id: int,
        overview: int = Query(1),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        # Get base session data
        session = (
            db.query(PipelineSessionModel)
            .filter(
                PipelineSessionModel.id == session_id,
                PipelineSessionModel.is_usable == 1,
            )
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session with ID {session_id} not found",
            )
        # If overview=1, return just the session data with general properties
        if overview == 1:
            session_dict = dict(vars(session))
            # Get general properties for this pipeline session
            general_properties = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == session_id,
                    GeneralProperty.property_type == "pipeline_session",
                    GeneralProperty.is_usable == 1,
                )
                .all()
            )
            # Add general properties to session data
            session_dict["general_properties"] = [
                {
                    "id": prop.id,
                    "property_label": prop.property_label,
                    "property_key": prop.property_key,
                    "property_value": prop.property_value,
                    "tags": prop.tags,
                    "created_at": prop.created_at,
                }
                for prop in general_properties
            ]
            # Add pipeline input row if pipeline_input_id exists
            if session.pipeline_input_id:
                pipeline_input = db.query(PipelineInput).filter(
                    PipelineInput.id == session.pipeline_input_id,
                    PipelineInput.is_usable == 1
                ).first()
                if pipeline_input:
                    session_dict["pipeline_input"] = {
                        "id": pipeline_input.id,
                        "name": pipeline_input.name,
                        "created_at": pipeline_input.created_at,
                        "is_usable": pipeline_input.is_usable
                    }
                else:
                    session_dict["pipeline_input"] = None
            else:
                session_dict["pipeline_input"] = None
            return session_dict
        # If overview=0, include related outputs and units
        session_dict = dict(vars(session))
        # Get general properties for this pipeline session
        general_properties = (
            db.query(GeneralProperty)
            .filter(
                GeneralProperty.referrer_id == session_id,
                GeneralProperty.property_type == "pipeline_session",
                GeneralProperty.is_usable == 1,
            )
            .all()
        )
        # Add general properties to session data
        session_dict["general_properties"] = [
            {
                "id": prop.id,
                "property_label": prop.property_label,
                "property_key": prop.property_key,
                "property_value": prop.property_value,
                "tags": prop.tags,
                "created_at": prop.created_at,
            }
            for prop in general_properties
        ]
        # Get related outputs with eager loading
        outputs = (
            db.query(PipelineSessionOutput)
            .filter(
                PipelineSessionOutput.pipeline_session_id == session_id,
                PipelineSessionOutput.is_usable == 1,
            )
            .all()
        )
        outputs_list = []
        for output in outputs:
            output_dict = dict(vars(output))
            # Get related output units for each output
            units = (
                db.query(PipelineSessionOutputUnit)
                .filter(
                    PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                    PipelineSessionOutputUnit.is_usable == 1,
                )
                .all()
            )

            # Enhance units with property reference data
            enhanced_units = []
            for unit in units:
                unit_dict = dict(vars(unit))

                # Get the referenced general property if property_reference_id exists
                if unit.property_reference_id:
                    property_ref = (
                        db.query(GeneralProperty)
                        .filter(GeneralProperty.id == unit.property_reference_id)
                        .first()
                    )

                    if property_ref:
                        unit_dict["property_reference"] = {
                            "id": property_ref.id,
                            "property_label": property_ref.property_label,
                            "property_key": property_ref.property_key,
                            "property_value": property_ref.property_value,
                            "tags": property_ref.tags,
                            "created_at": property_ref.created_at,
                        }
                    else:
                        unit_dict["property_reference"] = None
                else:
                    unit_dict["property_reference"] = None

                enhanced_units.append(unit_dict)

            output_dict["units"] = enhanced_units
            outputs_list.append(output_dict)
        session_dict["outputs"] = outputs_list  # type: ignore
        return session_dict
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline session: {str(e)}"
        )
