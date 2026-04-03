import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubmissionStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in-progress"
    PENDING = "pending"
    WAITING = "waiting"
    NO_VIDEO = "no-video"


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("user_id", "usecase_id", name="uq_submission_user_usecase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usecase_id: Mapped[int] = mapped_column(ForeignKey("use_cases.id", ondelete="CASCADE"), nullable=False)
    repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        SqlEnum(SubmissionStatus, name="submission_status_enum"),
        default=SubmissionStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="submissions")
    usecase = relationship("UseCase", back_populates="submissions")
    video_assets = relationship("VideoAsset", back_populates="submission", cascade="all, delete-orphan")


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(600), nullable=False, unique=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    submission = relationship("Submission", back_populates="video_assets")
