import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from app.auth.auth import require_roles
from app.database.connection import get_db
from app.models.general_property import GeneralProperty
from app.models.pipeline_session_output_unit import (
    PipelineSessionOutputUnit as PipelineSessionOutputUnitModel,
)
from app.schemas.pipeline_session import BasicFilter
from app.schemas.pipeline_session_output_unit import (
    BatchUpdateResponse,
    PipelineSessionOutputUnit,
    PipelineSessionOutputUnitCreate,
    PipelineSessionOutputUnitResponse,
    PipelineSessionOutputUnitUpdate,
)

router = APIRouter(
    prefix="/v1/pipeline-session-output-unit", tags=["pipeline-session-output-unit"]
)


def _compute_verdict(output_value: str, reference_property: GeneralProperty, db: Session) -> Optional[int]:
    """Compute verdict based on output value and reference property"""
    if output_value is None:
        return None

    if reference_property.property_label == "Factory Code":
        if output_value.lower().startswith("b"):
            return 1
    elif reference_property.property_label == "Weight":
        try:
            weight_value = float(output_value)

            # Get min and max weight properties for the same referrer_id
            min_weight_property = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == reference_property.referrer_id,
                    GeneralProperty.property_type == reference_property.property_type,
                    GeneralProperty.property_label == "Min Weight",
                    GeneralProperty.is_usable == 1,
                )
                .first()
            )

            max_weight_property = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.referrer_id == reference_property.referrer_id,
                    GeneralProperty.property_type == reference_property.property_type,
                    GeneralProperty.property_label == "Max Weight",
                    GeneralProperty.is_usable == 1,
                )
                .first()
            )

            # If both min and max weight are available, check range
            if min_weight_property and max_weight_property:
                try:
                    min_weight = float(min_weight_property.property_value)
                    max_weight = float(max_weight_property.property_value)

                    # Weight should be between min and max (inclusive)
                    if min_weight <= weight_value <= max_weight:
                        return 1
                    else:
                        return 0
                except ValueError:
                    # If min/max values are not valid numbers, fall back to old logic
                    pass

            # Fallback to original logic if min/max not available or invalid
            if float(output_value) > float(reference_property.property_value):
                return 1

        except ValueError:
            # Log error if needed, but continue with default logic
            pass
    elif output_value == reference_property.property_value:
        return 1

    return 0


@router.post("/new", response_model=PipelineSessionOutputUnit, status_code=201)
async def create_pipeline_session_output_unit(
        unit: PipelineSessionOutputUnitCreate,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
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
            is_usable=1,
        )

        db.add(new_unit)
        db.commit()
        db.refresh(new_unit)

        return new_unit

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating pipeline session output unit: {str(e)}",
        )


@router.get("/all")
async def get_all_pipeline_session_output_units(
        pipeline_session_output_id: int = Query(default=None),
        status_: str = Query(default=None, alias="status"),
        filters: BasicFilter = Depends(),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        units = (
            db.query(PipelineSessionOutputUnitModel)
            .filter(
                PipelineSessionOutputUnitModel.is_usable == 1,
            )
        )

        if pipeline_session_output_id is not None:
            units = units.filter(PipelineSessionOutputUnitModel.pipeline_session_output_id
                                 == pipeline_session_output_id)

        if status_ is not None:
            units = units.filter(PipelineSessionOutputUnitModel.status == status_)

        if filters.limit <= 0:
            units = units.limit(15)

        units_list = units.all()

        response_payload = {"total": len(units_list), "items": [vars(unit) for unit in units_list]}
        return response_payload

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{unit_id}", response_model=PipelineSessionOutputUnit)
async def get_pipeline_session_output_unit(
        unit_id: int,
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        unit = (
            db.query(PipelineSessionOutputUnitModel)
            .filter(
                PipelineSessionOutputUnitModel.id == unit_id,
                PipelineSessionOutputUnitModel.is_usable == 1,
            )
            .first()
        )

        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output unit with ID {unit_id} not found",
            )

        return unit

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pipeline session output unit: {str(e)}",
        )


@router.patch(
    "/", status_code=status.HTTP_200_OK, response_model=PipelineSessionOutputUnit
)
async def update_pipeline_session_output_unit(
        unit_update: PipelineSessionOutputUnitUpdate,
        unit_id: int = Query(...),  # Using ... makes it required
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        db.begin()

        unit = (
            db.query(PipelineSessionOutputUnitModel)
            .filter(
                PipelineSessionOutputUnitModel.id == unit_id,
                PipelineSessionOutputUnitModel.is_usable == 1,
            )
            .first()
        )

        if not unit:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline session output unit with ID {unit_id} not found",
            )

        update_data = unit_update.model_dump(exclude_unset=True)

        # Check if output_value is in payload and verdict is not provided
        if "output_value" in update_data and "verdict" not in update_data:
            # Get the reference property to compute verdict
            reference_property = (
                db.query(GeneralProperty)
                .filter(
                    GeneralProperty.id == unit.property_reference_id,
                    GeneralProperty.is_usable == 1,
                )
                .first()
            )

            if reference_property:
                computed_verdict = _compute_verdict(update_data["output_value"], reference_property, db)
                if computed_verdict is not None:
                    update_data["verdict"] = computed_verdict

        # Update fields
        for key, value in update_data.items():
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
            detail=f"Error updating pipeline session output unit: {str(e)}",
        )


@router.patch("/all", response_model=BatchUpdateResponse)
async def update_batch_pipeline_session_output_units(
        unit_update: PipelineSessionOutputUnitUpdate,
        pipeline_session_output_id: Optional[int] = Query(None),
        output_key: Optional[str] = Query(None),
        db: Session = Depends(get_db),
        _: bool = Depends(require_roles(["app_admin", "app_user"])),
):
    try:
        db.begin()
        query = db.query(PipelineSessionOutputUnitModel).filter(
            PipelineSessionOutputUnitModel.is_usable == 1
        )

        if pipeline_session_output_id:
            query = query.filter(
                PipelineSessionOutputUnitModel.pipeline_session_output_id
                == pipeline_session_output_id
            )

        if output_key:
            query = query.filter(
                PipelineSessionOutputUnitModel.output_key == output_key
            )

        units = query.all()
        if not units:
            raise HTTPException(status_code=404, detail="No matching units found")

        update_data = unit_update.model_dump(exclude_unset=True)
        # Convert dict keys to proper column references
        update_dict = {getattr(PipelineSessionOutputUnitModel, key): value for key, value in update_data.items()}
        query.update(update_dict)
        db.commit()

        # Refresh the query to get updated units
        updated_units = query.all()

        # Convert model instances to schema instances
        schema_items = [PipelineSessionOutputUnit.model_validate(unit) for unit in updated_units]
        return BatchUpdateResponse(
            status="success", updated_count=len(updated_units), items=schema_items
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
