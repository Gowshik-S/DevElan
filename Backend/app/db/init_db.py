from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.usecase import UseCase
from app.models.user import User, UserRole


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_initial_data() -> None:
    with SessionLocal() as db:
        changed = False

        admin = db.scalar(select(User).where(User.register_no == "ADMIN001"))
        if admin is None:
            admin = db.scalar(select(User).where(User.email == "admin@devela.local"))
        if admin is None:
            admin = db.scalar(
                select(User).where(User.role == UserRole.ADMIN).order_by(User.id.asc())
            )
        if admin is None:
            admin = User(
                full_name="Platform Admin",
                register_no="ADMIN001",
                email="admin@devela.local",
                class_name="Admin",
                year_semester="N/A",
                password_hash=get_password_hash("Admin@123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            changed = True

        student = db.scalar(select(User).where(User.register_no == "STU001"))
        if student is None:
            student = db.scalar(select(User).where(User.email == "student001@devela.local"))
        if student is None:
            student = User(
                full_name="Demo Student",
                register_no="STU001",
                email="student001@devela.local",
                class_name="A",
                year_semester="Year 1 / Semester 1",
                password_hash=get_password_hash("Student@123"),
                role=UserRole.STUDENT,
                is_active=True,
            )
            db.add(student)
            changed = True

        use_case = db.scalar(select(UseCase).where(UseCase.code == "EL-01"))
        if use_case is None:
            use_case = UseCase(
                code="EL-01",
                title="PDF QA System",
                description=(
                    "Build a retrieval-augmented generation workflow that answers natural "
                    "language questions from PDF content."
                ),
                key_concepts=[
                    "PDF Loading",
                    "Chunking",
                    "Embeddings",
                    "Vector DB",
                    "Top-K Retrieval",
                    "RAG",
                ],
                workflow_steps=[
                    "Load the PDF documents from the provided dataset.",
                    "Split long content into semantically meaningful chunks.",
                    "Generate embeddings for each chunk.",
                    "Store chunk vectors in a searchable vector database.",
                    "Retrieve top matching chunks for each question.",
                    "Compose a grounded answer from retrieved context.",
                    "Return answer, confidence, and supporting chunk references.",
                ],
                output_description="Question answer with cited source snippets.",
            )
            db.add(use_case)
            changed = True

        if changed:
            db.flush()

        if changed:
            db.commit()


def initialize_database() -> None:
    create_tables()
    seed_initial_data()
