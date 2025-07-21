from app.models.pipeline_input import PipelineInput as PipelineInputModel
from app.schemas.pipeline_input import PipelineInputBase, PipelineInputResponse
from app.services.base import CRUDBase


class PipelineInputService(CRUDBase[PipelineInputModel, PipelineInputBase, PipelineInputBase]):
    """
    Pipeline Input-specific CRUD service.
    """
    
    def __init__(self):
        super().__init__(PipelineInputModel)


# Create a singleton instance
pipeline_input_service = PipelineInputService()
