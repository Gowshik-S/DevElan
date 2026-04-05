from pydantic import BaseModel, Field, HttpUrl

from app.models.submission import SubmissionStatus


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
