from pydantic import BaseModel, Field

from app.models.submission import SubmissionStatus


class UseCaseSummary(BaseModel):
    id: int
    code: str
    title: str
    status: SubmissionStatus | None = None


class UseCaseListResponse(BaseModel):
    items: list[UseCaseSummary] = Field(default_factory=list)
    message: str | None = None


class UseCaseDetail(BaseModel):
    id: int
    code: str
    title: str
    description: str
    key_concepts: list[str]
    workflow_steps: list[str]
    output_description: str | None = None
    status: SubmissionStatus | None = None
