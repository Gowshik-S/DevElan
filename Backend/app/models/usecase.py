from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UseCase(Base):
    __tablename__ = "use_cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    key_concepts: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    workflow_steps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    output_description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    assignments = relationship("UseCaseAssignment", back_populates="usecase", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="usecase", cascade="all, delete-orphan")


class UseCaseAssignment(Base):
    __tablename__ = "use_case_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "usecase_id", name="uq_user_usecase_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usecase_id: Mapped[int] = mapped_column(ForeignKey("use_cases.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="assignments")
    usecase = relationship("UseCase", back_populates="assignments")
