from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.models.submission import SubmissionEvaluationDecision, SubmissionStatus


class RepoLinkSubmissionRequest(BaseModel):
    use_case_id: str = Field(min_length=1, max_length=50)
    repo_url: HttpUrl


class RepoLinkSubmissionResponse(BaseModel):
    success: bool
    repo_id: int
    status: SubmissionStatus
    message: str


class VideoUploadResponse(BaseModel):
    success: bool
    video_id: int
    video_type: str | None = None
    status: SubmissionStatus
    message: str


class ResumableUploadStartRequest(BaseModel):
    use_case_id: str = Field(min_length=1, max_length=50)
    upload_key: str = Field(min_length=8, max_length=600)
    file_name: str = Field(min_length=1, max_length=255)
    file_size_bytes: int = Field(gt=0)
    upload_kind: Literal["meeting", "demo"] = "meeting"
    content_type: str | None = Field(default=None, max_length=120)
    preferred_chunk_size_bytes: int | None = Field(default=None, ge=262144, le=8388608)


class ResumableUploadSessionResponse(BaseModel):
    upload_id: str
    upload_kind: Literal["meeting", "demo"]
    file_name: str
    file_size_bytes: int
    chunk_size_bytes: int
    received_bytes: int
    complete: bool
    expires_at: datetime
    message: str


class ResumableUploadChunkResponse(BaseModel):
    upload_id: str
    received_bytes: int
    file_size_bytes: int
    complete: bool


class ResumableUploadCancelResponse(BaseModel):
    success: bool
    message: str


class SubmissionDetail(BaseModel):
    submission_id: int
    use_case_id: int
    use_case_code: str
    project_title: str
    repo_url: str | None = None
    video_id: int | None = None
    meeting_video_id: int | None = None
    demo_video_id: int | None = None
    status: SubmissionStatus
    evaluation_decision: SubmissionEvaluationDecision | None = None
    admin_feedback: str | None = None


class SubmissionListItem(BaseModel):
    submission_id: int
    user_name: str
    register_no: str
    project_title: str
    repo_link: str | None = None
    video_id: int | None = None
    meeting_video_id: int | None = None
    demo_video_id: int | None = None
    status: SubmissionStatus
    evaluation_decision: SubmissionEvaluationDecision | None = None
    admin_feedback: str | None = None


class SubmissionListResponse(BaseModel):
    page: int
    limit: int
    total: int
    submissions: list[SubmissionListItem]


class StatusUpdateRequest(BaseModel):
    submission_id: int
    status: SubmissionStatus


class StatusUpdateResponse(BaseModel):
    success: bool
    submission_id: int
    updated_status: SubmissionStatus


class SubmissionEvaluationUpdateRequest(BaseModel):
    submission_id: int
    evaluation_decision: SubmissionEvaluationDecision
    admin_feedback: str | None = Field(default=None, max_length=2000)


class SubmissionEvaluationUpdateResponse(BaseModel):
    success: bool
    submission_id: int
    evaluation_decision: SubmissionEvaluationDecision
    admin_feedback: str | None = None
    message: str
