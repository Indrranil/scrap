import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from starlette import status

from app.auth.auth import require_roles
from app.database.connection import get_db
from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit as PipelineSessionOutputUnitModel
from app.schemas.pipeline_session_output_unit import (
    PipelineSessionOutputUnitCreate,
    PipelineSessionOutputUnit,
    PipelineSessionOutputUnitUpdate,
    PipelineSessionOutputUnitResponse,
    BatchUpdateResponse
)

router = APIRouter(prefix="/v1/pipeline-session-output-unit", tags=["pipeline-session-output-unit"])


@router.post("/new", response_model=PipelineSessionOutputUnit, status_code=201)
async def create_pipeline_session_output_unit(
        unit: PipelineSessionOutputUnitCreate,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
):
    try:
        db.begin()

        timestamp = int(time.time())
        new_unit = PipelineSessionOutputUnitModel(
            pipeline_session_output_id=unit.pipeline_session_output_id,
            property_reference_id=unit.property_reference_id,
            verdict=unit.verdict,
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
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
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


@router.get("/", response_model=PipelineSessionOutputUnitResponse)
async def get_all_pipeline_session_output_units(
        pipeline_session_output_id: int = Query(...),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
):
    try:
        units = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.pipeline_session_output_id == pipeline_session_output_id,
            PipelineSessionOutputUnitModel.is_usable == 1
        ).all()

        response_payload = {
            "total": len(units),
            "items": units
        }
        print(response_payload)
        return response_payload

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/", status_code=status.HTTP_200_OK, response_model=PipelineSessionOutputUnit)
async def update_pipeline_session_output_unit(
        unit_update: PipelineSessionOutputUnitUpdate,
        unit_id: int = Query(...),  # Using ... makes it required
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
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
        for key, value in unit_update.model_dump(exclude_unset=True).items():
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


@router.patch("/all", response_model=BatchUpdateResponse)
async def update_batch_pipeline_session_output_units(
        unit_update: PipelineSessionOutputUnitUpdate,
        pipeline_session_output_id: Optional[int] = Query(None),
        output_key: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"]))
):
    try:
        db.begin()
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
            raise HTTPException(status_code=404, detail="No matching units found")

        update_data = unit_update.model_dump(exclude_unset=True)
        query.update(update_data)
        db.commit()

        # Refresh the query to get updated units
        updated_units = query.all()

        return BatchUpdateResponse(
            status="success",
            updated_count=len(updated_units),
            items=updated_units
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
