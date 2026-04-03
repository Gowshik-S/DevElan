from pydantic import BaseModel, Field


class RowFailure(BaseModel):
    row: int
    reason: str
    identifier: str | None = None


class BulkImportResponse(BaseModel):
    success: bool
    imported_count: int
    failures: list[RowFailure] = Field(default_factory=list)


class AssignmentSyncResponse(BaseModel):
    success: bool
    mapped_count: int
    mapped_identifiers: list[str] = Field(default_factory=list)
    failures: list[RowFailure] = Field(default_factory=list)


class UseCaseImportResponse(BaseModel):
    success: bool
    created_count: int
    updated_count: int
    failures: list[RowFailure] = Field(default_factory=list)
