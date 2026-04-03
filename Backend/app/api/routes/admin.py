import re
from hashlib import sha1

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.dependencies import require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.usecase import UseCase, UseCaseAssignment
from app.models.user import User, UserRole
from app.schemas.admin import (
    AssignmentSyncResponse,
    BulkImportResponse,
    RowFailure,
    UseCaseImportResponse,
)
from app.schemas.user import AdminUserCreateRequest, AdminUserCreateResponse
from app.services.tabular_parser import parse_uploaded_table

router = APIRouter(prefix="/admin", tags=["Admin"])


def _pick_value(row: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
        else:
            normalized = str(value).strip()
            if normalized:
                return normalized
    return None


def _split_list_field(raw_value: str | None) -> list[str]:
    if raw_value is None:
        return []

    cleaned = raw_value.strip()
    if not cleaned:
        return []

    parts = [
        item.strip()
        for item in cleaned.replace("\n", ";").split(";")
    ]
    if len(parts) == 1:
        parts = [item.strip() for item in cleaned.split(",")]
    return [item for item in parts if item]


def _normalize_register_no(raw_value: str) -> str:
    return "".join(raw_value.upper().split())


def _build_user_identifier(full_name: str | None, register_no: str | None, email: str | None) -> str | None:
    parts: list[str] = []
    if full_name:
        parts.append(" ".join(full_name.split()))
    if register_no:
        parts.append(_normalize_register_no(register_no))
    if email:
        parts.append(email.strip().lower())

    if not parts:
        return None
    return " | ".join(parts)


def _build_assignment_identifier(register_no: str | None, use_case_code: str | None) -> str | None:
    parts: list[str] = []
    if register_no:
        parts.append(_normalize_register_no(register_no))
    if use_case_code:
        parts.append(use_case_code.strip().upper())

    if not parts:
        return None
    return " | ".join(parts)


def _normalize_topic(raw_value: str) -> str:
    return " ".join(raw_value.split())


def _normalize_use_case_code(raw_value: str) -> str:
    normalized = raw_value.strip().upper().replace("_", "-")

    numeric_match = re.fullmatch(r"(\d+)(?:\.0+)?", normalized)
    if numeric_match:
        return f"EL-{numeric_match.group(1)}"

    prefixed_match = re.fullmatch(r"EL-?(\d+)", normalized)
    if prefixed_match:
        return f"EL-{prefixed_match.group(1)}"

    return normalized


def _build_use_case_code(topic: str) -> str:
    slug = re.sub(r"[^A-Z0-9]+", "-", topic.strip().upper()).strip("-")
    if not slug:
        slug = "UNTITLED"

    base_code = f"UC-{slug}"
    if len(base_code) <= 50:
        return base_code

    digest = sha1(topic.strip().encode("utf-8")).hexdigest()[:8].upper()
    truncated = slug[: 50 - len("UC--") - len(digest)]
    return f"UC-{truncated}-{digest}"


def _resolve_unique_use_case_code(db: Session, base_code: str) -> str:
    candidate = base_code
    counter = 2
    while db.scalar(select(UseCase.id).where(UseCase.code == candidate)) is not None:
        suffix = f"-{counter}"
        candidate = f"{base_code[:50 - len(suffix)]}{suffix}"
        counter += 1
    return candidate


def _upsert_use_case_from_row(db: Session, row: dict[str, object], use_case_code: str) -> tuple[UseCase, bool]:
    normalized_code = use_case_code.strip().upper()
    use_case = db.scalar(select(UseCase).where(UseCase.code.ilike(normalized_code)))

    title_raw = _pick_value(
        row,
        "title",
        "topic",
        "problem_title",
        "problem_statement_title",
        "problem",
        "use_case_title",
    )
    description_raw = _pick_value(
        row,
        "description",
        "the_objective",
        "objective_text",
        "problem_statement",
        "problem_description",
        "objective",
    )
    output_description_raw = _pick_value(
        row,
        "output",
        "expected_output",
        "output_description",
    )
    key_concepts = _split_list_field(_pick_value(row, "key_concepts", "key_concept"))
    workflow_steps = _split_list_field(_pick_value(row, "workflow_steps", "workflow", "steps"))

    title = " ".join(title_raw.split()) if title_raw else None
    description = " ".join(description_raw.split()) if description_raw else None
    output_description = " ".join(output_description_raw.split()) if output_description_raw else None

    if use_case is None:
        if not title or not description:
            raise ValueError(
                "Use case code not found in catalog. Upload use case CSV with matching ID/Code "
                "or include title and objective in assignment file."
            )

        use_case = UseCase(
            code=normalized_code,
            title=title,
            description=description,
            key_concepts=key_concepts,
            workflow_steps=workflow_steps,
            output_description=output_description,
        )
        db.add(use_case)
        db.flush()
        return use_case, True

    changed = False
    if title and use_case.title != title:
        use_case.title = title
        changed = True
    if description and use_case.description != description:
        use_case.description = description
        changed = True
    if key_concepts and use_case.key_concepts != key_concepts:
        use_case.key_concepts = key_concepts
        changed = True
    if workflow_steps and use_case.workflow_steps != workflow_steps:
        use_case.workflow_steps = workflow_steps
        changed = True
    if output_description and use_case.output_description != output_description:
        use_case.output_description = output_description
        changed = True

    if changed:
        db.add(use_case)
        db.flush()

    return use_case, changed


@router.post("/users/create", response_model=AdminUserCreateResponse)
def create_user(
    payload: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminUserCreateResponse:
    existing = db.scalar(
        select(User).where(
            or_(
                User.register_no == payload.register_no,
                User.email == payload.email.lower(),
            )
        )
    )
    if existing is not None:
        return AdminUserCreateResponse(
            user_id=existing.id,
            success=False,
            message="User with same register number or email already exists.",
            temp_password="",
        )

    temp_password = payload.register_no
    user = User(
        full_name=payload.full_name,
        register_no=payload.register_no,
        email=payload.email.lower(),
        class_name=payload.class_assign,
        password_hash=get_password_hash(temp_password),
        role=UserRole.STUDENT,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return AdminUserCreateResponse(
        user_id=user.id,
        success=True,
        message="User created successfully.",
        temp_password=temp_password,
    )


@router.post("/users/bulk-import", response_model=BulkImportResponse)
def bulk_import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> BulkImportResponse:
    rows = parse_uploaded_table(file)
    imported_count = 0
    failures: list[RowFailure] = []

    for fallback_row_number, row in enumerate(rows, start=1):
        row_number = int(row.get("__row_number__", fallback_row_number))
        full_name = _pick_value(row, "full_name", "name", "student_name", "column_1")
        register_no = _pick_value(
            row,
            "register_no",
            "register_number",
            "reg_no",
            "register",
            "regno",
            "column_2",
        )
        email = _pick_value(row, "email", "email_id", "mail", "column_3")
        class_assign = _pick_value(row, "class", "class_name", "assign_class", "column_4") or "Unassigned"
        year_semester = _pick_value(
            row,
            "year_semester",
            "year_sem",
            "year_semester_value",
            "year",
            "semester",
            "column_5",
        )

        if not full_name or not register_no or not email:
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Missing required columns (full_name/name, register_no, email).",
                    identifier=_build_user_identifier(full_name, register_no, email),
                )
            )
            continue

        register_no = _normalize_register_no(register_no)
        email = email.lower().strip()

        exists = db.scalar(
            select(User.id).where(
                or_(
                    User.register_no == register_no,
                    User.email == email,
                )
            )
        )
        if exists is not None:
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="User already exists for register number or email.",
                    identifier=_build_user_identifier(full_name, register_no, email),
                )
            )
            continue

        user = User(
            full_name=full_name.strip(),
            register_no=register_no,
            email=email,
            class_name=class_assign,
            year_semester=" ".join(year_semester.split()) if year_semester else None,
            password_hash=get_password_hash(register_no),
            role=UserRole.STUDENT,
            is_active=True,
        )

        try:
            db.add(user)
            db.commit()
            imported_count += 1
        except IntegrityError:
            db.rollback()
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Constraint violation while creating user.",
                    identifier=_build_user_identifier(full_name, register_no, email),
                )
            )

    return BulkImportResponse(
        success=len(failures) == 0,
        imported_count=imported_count,
        failures=failures,
    )


@router.post("/usecase/import", response_model=UseCaseImportResponse)
def import_use_cases(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> UseCaseImportResponse:
    rows = parse_uploaded_table(file)
    created_count = 0
    updated_count = 0
    failures: list[RowFailure] = []

    for fallback_row_number, row in enumerate(rows, start=1):
        row_number = int(row.get("__row_number__", fallback_row_number))
        topic = _pick_value(
            row,
            "topic",
            "title",
            "problem_title",
            "problem_statement_title",
            "problem",
            "use_case_title",
            "column_1",
        )
        objective = _pick_value(
            row,
            "objective",
            "the_objective",
            "objective_text",
            "description",
            "problem_statement",
            "problem_description",
            "column_2",
        )
        key_concepts_raw = _pick_value(row, "key_concepts", "key_concept", "column_3")
        output_description = _pick_value(
            row,
            "output",
            "expected_output",
            "output_description",
            "column_4",
        )
        use_case_code_raw = _pick_value(
            row,
            "use_case_code",
            "usecase_code",
            "problem_code",
            "problem_id",
            "problem_no",
            "problem_number",
            "problem_statement_id",
            "problem_statement_number",
            "problem_statement_no",
            "code",
            "use_case_id",
            "id",
        )

        if not topic or not objective:
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Missing required fields (Topic and Objective).",
                )
            )
            continue

        normalized_topic = _normalize_topic(topic)
        normalized_objective = " ".join(objective.split())
        key_concepts = _split_list_field(key_concepts_raw)
        normalized_output = " ".join(output_description.split()) if output_description else None
        normalized_code = _normalize_use_case_code(use_case_code_raw) if use_case_code_raw else None

        try:
            use_case = None
            if normalized_code:
                use_case = db.scalar(select(UseCase).where(UseCase.code.ilike(normalized_code)))

            if use_case is None:
                use_case = db.scalar(
                    select(UseCase).where(func.lower(UseCase.title) == normalized_topic.lower())
                )

            if use_case is None:
                code = normalized_code or _resolve_unique_use_case_code(
                    db,
                    _build_use_case_code(normalized_topic),
                )
                db.add(
                    UseCase(
                        code=code,
                        title=normalized_topic,
                        description=normalized_objective,
                        key_concepts=key_concepts,
                        workflow_steps=[],
                        output_description=normalized_output,
                    )
                )
                db.commit()
                created_count += 1
                continue

            if normalized_code and use_case.code != normalized_code:
                existing_code = db.scalar(
                    select(UseCase.id).where(
                        UseCase.id != use_case.id,
                        UseCase.code.ilike(normalized_code),
                    )
                )
                if existing_code is not None:
                    failures.append(
                        RowFailure(
                            row=row_number,
                            reason=(
                                f"Use case code '{normalized_code}' already belongs to another record."
                            ),
                        )
                    )
                    continue
                use_case.code = normalized_code

            use_case.title = normalized_topic
            use_case.description = normalized_objective
            use_case.key_concepts = key_concepts
            use_case.output_description = normalized_output
            db.add(use_case)
            db.commit()
            updated_count += 1
        except IntegrityError:
            db.rollback()
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Constraint violation while importing use case.",
                )
            )

    return UseCaseImportResponse(
        success=len(failures) == 0,
        created_count=created_count,
        updated_count=updated_count,
        failures=failures,
    )


@router.post("/usecase/assign", response_model=AssignmentSyncResponse)
def assign_use_cases(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> AssignmentSyncResponse:
    rows = parse_uploaded_table(file)
    mapped_count = 0
    mapped_identifiers: list[str] = []
    failures: list[RowFailure] = []

    for fallback_row_number, row in enumerate(rows, start=1):
        row_number = int(row.get("__row_number__", fallback_row_number))
        register_no = _pick_value(
            row,
            "register_no",
            "register_number",
            "reg_no",
            "register",
            "regno",
            "column_1",
        )
        use_case_code = _pick_value(
            row,
            "use_case_code",
            "usecase_code",
            "problem_code",
            "problem_id",
            "problem_no",
            "problem_number",
            "problem_statement_id",
            "problem_statement_number",
            "problem_statement_no",
            "code",
            "use_case_id",
            "id",
            "column_2",
        )

        if not register_no or not use_case_code:
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Missing register number or use case code.",
                    identifier=_build_assignment_identifier(register_no, use_case_code),
                )
            )
            continue

        register_no = _normalize_register_no(register_no)
        use_case_code = _normalize_use_case_code(use_case_code)

        user = db.scalar(select(User).where(User.register_no == register_no))
        if user is None:
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="User not found for register number.",
                    identifier=_build_assignment_identifier(register_no, use_case_code),
                )
            )
            continue

        try:
            use_case, use_case_updated = _upsert_use_case_from_row(db, row, use_case_code)

            existing_assignment = db.scalar(
                select(UseCaseAssignment).where(
                    UseCaseAssignment.user_id == user.id,
                    UseCaseAssignment.usecase_id == use_case.id,
                )
            )

            assignment_added = False
            if existing_assignment is None:
                db.add(UseCaseAssignment(user_id=user.id, usecase_id=use_case.id))
                assignment_added = True
                mapped_count += 1
                mapped_identifiers.append(
                    _build_assignment_identifier(register_no, use_case_code)
                )

            if use_case_updated or assignment_added:
                db.commit()
        except ValueError as exc:
            db.rollback()
            failures.append(
                RowFailure(
                    row=row_number,
                    reason=str(exc),
                    identifier=_build_assignment_identifier(register_no, use_case_code),
                )
            )
        except IntegrityError:
            db.rollback()
            failures.append(
                RowFailure(
                    row=row_number,
                    reason="Constraint violation while assigning use case.",
                    identifier=_build_assignment_identifier(register_no, use_case_code),
                )
            )

    return AssignmentSyncResponse(
        success=len(failures) == 0,
        mapped_count=mapped_count,
        mapped_identifiers=mapped_identifiers,
        failures=failures,
    )
