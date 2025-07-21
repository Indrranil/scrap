from app.models.pipeline_session_output import PipelineSessionOutput as PipelineSessionOutputModel
from app.schemas.pipeline_session_output import PipelineSessionOutputCreate, PipelineSessionOutput
from app.services.base import CRUDBase


class PipelineSessionOutputService(CRUDBase[PipelineSessionOutputModel, PipelineSessionOutputCreate, PipelineSessionOutputCreate]):
    """
    Pipeline Session Output-specific CRUD service.
    """
    
    def __init__(self):
        super().__init__(PipelineSessionOutputModel)


# Create a singleton instance
pipeline_session_output_service = PipelineSessionOutputService()
