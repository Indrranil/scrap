import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette import status

from app.auth.auth import require_roles
from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.pipeline_session import PipelineSession
from app.models.pipeline_session_output import (
    PipelineSessionOutput as PipelineSessionOutputModel,
)
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit
from app.schemas.pipeline_session_output import (
    PipelineSessionOutput,
    PipelineSessionOutputCreate,
)

router = APIRouter(
    prefix="/v1/pipeline-session-output", tags=["pipeline-session-output"]
)


@router.post("/new", response_model=PipelineSessionOutput, status_code=201)
async def create_pipeline_session_output(
    pipeline_session_output: PipelineSessionOutputCreate,
    manual: Optional[int] = Query(0),
    property_key: Optional[str] = Query(None, alias="property_key"),
    property_type: Optional[str] = Query(None, alias="property_type"),
    db: Session = Depends(get_db),
    _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    if manual and pipeline_session_output.pipeline_session_output_unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either manual mode or pipeline session output unit should be used",
        )
    try:
        db.begin()

        timestamp = int(time.time())

        # Create pipeline session output
        new_output = PipelineSessionOutputModel(
            pipeline_session_id=pipeline_session_output.pipeline_session_id,
            name=pipeline_session_output.name,
            created_at=timestamp,
            ended_at=pipeline_session_output.ended_at,
            is_usable=1,
        )

        db.add(new_output)
        db.flush()  # Flush to get the new output ID

        if pipeline_session_output.pipeline_session_output_unit:
            # Flush to ensure new_output.id is available
            db.flush()
            pipeline_session_output.pipeline_session_output_unit.pipeline_session_output_id = new_output.id  # type: ignore
            # Create pipeline session output unit
            new_output_unit = PipelineSessionOutputUnit(
                **pipeline_session_output.pipeline_session_output_unit.model_dump(),
                created_at=timestamp,
            )

            db.add(new_output_unit)

        # If manual mode, create output units using latest general properties
        if manual:
            # Get the pipeline session to find the pipeline_input_id
            pipeline_session = db.query(PipelineSession).filter(
                PipelineSession.id == pipeline_session_output.pipeline_session_id
            ).first()

            if not pipeline_session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Pipeline session with ID {pipeline_session_output.pipeline_session_id} not found"
                )

            # Get latest general properties for the pipeline input
            # Subquery to get the latest property for each (property_type, property_label, property_key) combination
            latest_properties_subquery = (
                db.query(
                    GeneralProperty.property_type,
                    GeneralProperty.property_label,
                    GeneralProperty.property_key,
                    func.max(GeneralProperty.created_at).label("max_created_at")
                )
                .filter(
                    GeneralProperty.referrer_id == pipeline_session.pipeline_input_id,
                    GeneralProperty.property_type == (property_type if property_type else "pipeline_input"),
                    GeneralProperty.is_usable == 1
                )
                .group_by(
                    GeneralProperty.property_type,
                    GeneralProperty.property_label,
                    GeneralProperty.property_key
                )
                .subquery()
            )

            # Get the actual latest properties
            latest_properties_query = (
                db.query(GeneralProperty)
                .join(
                    latest_properties_subquery,
                    (GeneralProperty.property_type == latest_properties_subquery.c.property_type) &
                    (GeneralProperty.property_label == latest_properties_subquery.c.property_label) &
                    (GeneralProperty.property_key == latest_properties_subquery.c.property_key) &
                    (GeneralProperty.created_at == latest_properties_subquery.c.max_created_at)
                )
                .filter(
                    GeneralProperty.referrer_id == pipeline_session.pipeline_input_id,
                    GeneralProperty.property_type == (property_type if property_type else "pipeline_input"),
                    GeneralProperty.is_usable == 1
                )
            )

            # Apply property key filter if provided
            if property_key:
                property_keys = [key.strip() for key in property_key.split(",")]
                latest_properties_query = latest_properties_query.filter(
                    GeneralProperty.property_key.in_(property_keys)
                )

            properties: List[GeneralProperty] = latest_properties_query.all()

            # Create output units for each latest property
            for prop in properties:
                output_unit = PipelineSessionOutputUnit(
                    pipeline_session_output_id=new_output.id,
                    property_reference_id=prop.id,
                    output_key=prop.property_key,
                    name=prop.property_label,
                    output_value=None,
                    status="idle",
                    created_at=timestamp,
                    is_usable=1,
                )
                db.add(output_unit)

        db.commit()
        db.refresh(new_output)

        return new_output

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error creating pipeline session output: {str(e)}"
        )


@router.get("/all")
async def get_all_pipeline_session_outputs(
    overview: int = Query(1),
    db: Session = Depends(get_db),
    _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        outputs = (
            db.query(PipelineSessionOutputModel)
            .filter(PipelineSessionOutputModel.is_usable == 1)
            .all()
        )

        # If overview=1, return just the outputs list
        if overview == 1:
            return outputs

        # If overview=0, include related output units for each output
        result = []
        for output in outputs:
            output_dict = dict(vars(output))

            # Get related output units
            units = (
                db.query(PipelineSessionOutputUnit)
                .filter(
                    PipelineSessionOutputUnit.pipeline_session_output_id == output.id,
                    PipelineSessionOutputUnit.is_usable == 1,
                )
                .all()
            )

            output_dict["units"] = [vars(unit) for unit in units]
            result.append(output_dict)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline session outputs: {str(e)}"
        )


@router.get("/{output_id}")
async def get_pipeline_session_output(
    output_id: int,

    overview: int = Query(1),
    db: Session = Depends(get_db),
    _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        # Get base output data
        output = (
            db.query(PipelineSessionOutputModel)
            .filter(
                PipelineSessionOutputModel.id == output_id,
                PipelineSessionOutputModel.is_usable == 1,
            )
            .first()
        )

        if not output:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output with ID {output_id} not found",
            )

        # If overview=1, return just the output data
        if overview == 1:
            return output

        # If overview=0, include related output units
        output_dict = dict(vars(output))

        # Get related output units
        units = (
            db.query(PipelineSessionOutputUnit)
            .filter(
                PipelineSessionOutputUnit.pipeline_session_output_id == output_id,
                PipelineSessionOutputUnit.is_usable == 1,
            )
            .all()
        )

        output_dict["units"] = [dict(vars(unit)) for unit in units]

        return output_dict

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline session output: {str(e)}"
        )
