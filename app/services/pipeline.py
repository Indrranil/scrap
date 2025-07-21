from app.models.pipeline import Pipeline as PipelineModel
from app.schemas.pipeline import PipelineCreate, Pipeline
from app.services.base import CRUDBase


class PipelineService(CRUDBase[PipelineModel, PipelineCreate, PipelineCreate]):
    """
    Pipeline-specific CRUD service.
    """
    
    def __init__(self):
        super().__init__(PipelineModel)


# Create a singleton instance
pipeline_service = PipelineService()
