from pydantic import BaseModel
class HealthResponse(BaseModel):
    status: str
    version: str
class TaskRequest(BaseModel):
    task: str