from app.models.pipeline_session_output_unit import PipelineSessionOutputUnit as PipelineSessionOutputUnitModel
from app.schemas.pipeline_session_output_unit import PipelineSessionOutputUnitCreate, PipelineSessionOutputUnit
from app.services.base import CRUDBase


class PipelineSessionOutputUnitService(CRUDBase[PipelineSessionOutputUnitModel, PipelineSessionOutputUnitCreate, PipelineSessionOutputUnitCreate]):
    """
    Pipeline Session Output Unit-specific CRUD service.
    """
    
    def __init__(self):
        super().__init__(PipelineSessionOutputUnitModel)


# Create a singleton instance
pipeline_session_output_unit_service = PipelineSessionOutputUnitService()
