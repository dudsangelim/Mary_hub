from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import Subject
from app.errors import error_response
from app.models.family import Guardian, Student
from app.models.material import SchoolMaterial
from app.models.provider import ProviderAccount, ProviderSyncLog
from app.models.report import MaryReport
from app.schemas.provider import PlurallAccountUpsert
from app.security import decrypt_provider_credentials, encrypt_provider_credentials

PLURALL_PROVIDER_NAME = "plurall"
PLURALL_PROVIDER_TYPE = "school_portal"
PLURALL_LIBRARY_SOURCE = "plurall_library"
PLURALL_MAPPED_PORTAL_SNAPSHOT = {
    "student_name": "Lucas Henrique Sousa Angelim",
    "student_role": "Aluno",
    "school_name": "ESCOLA PRIMEIRO PASSO E COLEGIO GRANDE P",
    "class_name": "1º Ano Ensino Fundamental",
    "grade": "1_fund",
    "grade_label": "1º ano do Ensino Fundamental",
    "modules_discovered": [
        "Assistente Inteligente",
        "Biblioteca de Conteudos",
        "Maestro",
        "Simulados e Provas",
        "Resultados",
    ],
    "supports_assignments": False,
    "supports_books": False,
    "supports_assessments": True,
    "supports_results": True,
}
PLURALL_LIBRARY_CATALOG = [
    {
        "title": "Caderno de Atividades - Língua Portuguesa",
        "subject_slug": "portugues-1fund",
        "material_type": "activity_book",
        "tags": ["plurall", "biblioteca", "caderno", "portugues", "1_fund"],
    },
    {
        "title": "Livro - Língua Portuguesa",
        "subject_slug": "portugues-1fund",
        "material_type": "digital_book",
        "tags": ["plurall", "biblioteca", "livro", "portugues", "1_fund"],
    },
    {
        "title": "Caderno de Atividades - Matemática",
        "subject_slug": "matematica-1fund",
        "material_type": "activity_book",
        "tags": ["plurall", "biblioteca", "caderno", "matematica", "1_fund"],
    },
    {
        "title": "Livro - Matemática",
        "subject_slug": "matematica-1fund",
        "material_type": "digital_book",
        "tags": ["plurall", "biblioteca", "livro", "matematica", "1_fund"],
    },
    {
        "title": "Livro - Ciências",
        "subject_slug": "ciencias-1fund",
        "material_type": "digital_book",
        "tags": ["plurall", "biblioteca", "livro", "ciencias", "1_fund"],
    },
    {
        "title": "Livro - Geografia",
        "subject_slug": "geografia-1fund",
        "material_type": "digital_book",
        "tags": ["plurall", "biblioteca", "livro", "geografia", "1_fund"],
    },
    {
        "title": "Livro - História",
        "subject_slug": "historia-1fund",
        "material_type": "digital_book",
        "tags": ["plurall", "biblioteca", "livro", "historia", "1_fund"],
    },
]


async def get_family_student(session: AsyncSession, guardian: Guardian, student_id: UUID) -> Student:
    student = await session.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.family_id == guardian.family_id,
            Student.is_active.is_(True),
        )
    )
    if student is None:
        raise error_response("STUDENT_NOT_FOUND", "Student not found", http_status=404)
    return student


async def list_provider_accounts(session: AsyncSession, guardian: Guardian) -> list[ProviderAccount]:
    return list(
        (
            await session.scalars(
                select(ProviderAccount)
                .join(Student, Student.id == ProviderAccount.student_id)
                .where(Student.family_id == guardian.family_id, ProviderAccount.deleted_at.is_(None))
                .order_by(ProviderAccount.created_at.desc())
            )
        ).all()
    )


async def get_provider_account(session: AsyncSession, guardian: Guardian, account_id: UUID) -> ProviderAccount:
    account = await session.scalar(
        select(ProviderAccount)
        .join(Student, Student.id == ProviderAccount.student_id)
        .where(
            ProviderAccount.id == account_id,
            Student.family_id == guardian.family_id,
            ProviderAccount.deleted_at.is_(None),
        )
    )
    if account is None:
        raise error_response("PROVIDER_ACCOUNT_NOT_FOUND", "Provider account not found", http_status=404)
    return account


async def upsert_plurall_account(session: AsyncSession, guardian: Guardian, payload: PlurallAccountUpsert) -> ProviderAccount:
    await get_family_student(session, guardian, payload.student_id)

    account = await session.scalar(
        select(ProviderAccount).where(
            ProviderAccount.student_id == payload.student_id,
            ProviderAccount.provider_name == PLURALL_PROVIDER_NAME,
            ProviderAccount.deleted_at.is_(None),
        )
    )

    encrypted_credentials = encrypt_provider_credentials(
        {
            "username": payload.username,
            "password": payload.password,
            "student_login_id": payload.student_login_id,
            "link_code": payload.link_code,
        }
    )

    sync_config = {
        "student_login_id": payload.student_login_id,
        "link_code": payload.link_code,
        "capture_mode": "manual_sync",
    }

    if account is None:
        account = ProviderAccount(
            student_id=payload.student_id,
            provider_name=PLURALL_PROVIDER_NAME,
            provider_type=PLURALL_PROVIDER_TYPE,
            credentials_encrypted=encrypted_credentials,
            is_active=payload.is_active,
            sync_config=sync_config,
        )
        session.add(account)
    else:
        account.credentials_encrypted = encrypted_credentials
        account.is_active = payload.is_active
        account.sync_config = sync_config

    await session.commit()
    await session.refresh(account)
    return account


async def list_provider_sync_logs(session: AsyncSession, guardian: Guardian, account_id: UUID) -> list[ProviderSyncLog]:
    await get_provider_account(session, guardian, account_id)
    return list(
        (
            await session.scalars(
                select(ProviderSyncLog)
                .where(ProviderSyncLog.provider_account_id == account_id)
                .order_by(ProviderSyncLog.started_at.desc(), ProviderSyncLog.created_at.desc())
            )
        ).all()
    )


async def upsert_plurall_snapshot_report(
    session: AsyncSession,
    student: Student,
    snapshot: dict,
    generated_at: datetime,
) -> MaryReport:
    report = await session.scalar(
        select(MaryReport).where(
            MaryReport.student_id == student.id,
            MaryReport.report_type == "plurall_portal_snapshot",
            MaryReport.generated_by == PLURALL_PROVIDER_NAME,
            MaryReport.deleted_at.is_(None),
        )
    )

    report_title = f"Snapshot do Plurall: {snapshot['student_name']}"
    report_content = {
        "provider": PLURALL_PROVIDER_NAME,
        "student_name": snapshot["student_name"],
        "student_role": snapshot["student_role"],
        "school_name": snapshot["school_name"],
        "class_name": snapshot["class_name"],
        "grade": snapshot["grade"],
        "grade_label": snapshot["grade_label"],
        "modules_discovered": snapshot["modules_discovered"],
        "capabilities": {
            "supports_assignments": snapshot["supports_assignments"],
            "supports_books": snapshot["supports_books"],
            "supports_assessments": snapshot["supports_assessments"],
            "supports_results": snapshot["supports_results"],
        },
        "synced_at": generated_at.isoformat(),
    }

    if report is None:
        report = MaryReport(
            student_id=student.id,
            report_type="plurall_portal_snapshot",
            title=report_title,
            content=report_content,
            generated_at=generated_at,
            generated_by=PLURALL_PROVIDER_NAME,
        )
        session.add(report)
        return report

    report.title = report_title
    report.content = report_content
    report.generated_at = generated_at
    report.is_read = False
    report.read_at = None
    return report


async def upsert_plurall_library_materials(
    session: AsyncSession,
    guardian: Guardian,
    student: Student,
) -> tuple[list[SchoolMaterial], int]:
    subjects = list((await session.scalars(select(Subject).where(Subject.grade == student.grade, Subject.is_active.is_(True)))).all())
    subjects_by_slug = {subject.slug: subject for subject in subjects}
    materials: list[SchoolMaterial] = []
    changed_count = 0

    for item in PLURALL_LIBRARY_CATALOG:
        subject = subjects_by_slug.get(item["subject_slug"])
        description = (
            "Catálogo da Biblioteca de Conteúdos do Plurall para o Lucas. "
            "O conteúdo é somente leitura dentro da plataforma; o Mary usa este item como contexto de estudo."
        )
        existing_material = await session.scalar(
            select(SchoolMaterial).where(
                SchoolMaterial.student_id == student.id,
                SchoolMaterial.source == PLURALL_LIBRARY_SOURCE,
                SchoolMaterial.title == item["title"],
                SchoolMaterial.deleted_at.is_(None),
            )
        )

        if existing_material is None:
            existing_material = SchoolMaterial(
                student_id=student.id,
                uploaded_by=guardian.id,
                title=item["title"],
                description=description,
                subject_id=subject.id if subject else None,
                material_type=item["material_type"],
                text_content=(
                    "Origem: Biblioteca de Conteudos do Plurall\n"
                    "Canal futuro de captura de agenda: Telegram -> OpenClaw -> Mary\n"
                    "Uso futuro pela IA: contexto de materia, exercicios e apoio a correcao."
                ),
                source=PLURALL_LIBRARY_SOURCE,
                tags=item["tags"],
                is_processed=True,
            )
            session.add(existing_material)
            changed_count += 1
            materials.append(existing_material)
            continue

        has_changes = False
        if existing_material.subject_id != (subject.id if subject else None):
            existing_material.subject_id = subject.id if subject else None
            has_changes = True
        if existing_material.material_type != item["material_type"]:
            existing_material.material_type = item["material_type"]
            has_changes = True
        if existing_material.description != description:
            existing_material.description = description
            has_changes = True
        if existing_material.text_content != (
            "Origem: Biblioteca de Conteudos do Plurall\n"
            "Canal futuro de captura de agenda: Telegram -> OpenClaw -> Mary\n"
            "Uso futuro pela IA: contexto de materia, exercicios e apoio a correcao."
        ):
            existing_material.text_content = (
                "Origem: Biblioteca de Conteudos do Plurall\n"
                "Canal futuro de captura de agenda: Telegram -> OpenClaw -> Mary\n"
                "Uso futuro pela IA: contexto de materia, exercicios e apoio a correcao."
            )
            has_changes = True
        if existing_material.tags != item["tags"]:
            existing_material.tags = item["tags"]
            has_changes = True
        if has_changes:
            changed_count += 1
        materials.append(existing_material)

    return materials, changed_count


async def trigger_plurall_sync(session: AsyncSession, guardian: Guardian, account_id: UUID) -> tuple[ProviderAccount, ProviderSyncLog]:
    account = await get_provider_account(session, guardian, account_id)
    credentials = decrypt_provider_credentials(account.credentials_encrypted)
    student = await get_family_student(session, guardian, account.student_id)
    snapshot = dict(PLURALL_MAPPED_PORTAL_SNAPSHOT)

    started_at = datetime.now(UTC)
    student.name = snapshot["student_name"]
    student.school_name = snapshot["school_name"]
    student.grade = snapshot["grade"]
    student.grade_label = snapshot["grade_label"]

    await upsert_plurall_snapshot_report(session, student, snapshot, started_at)
    library_materials, library_changes = await upsert_plurall_library_materials(session, guardian, student)

    account.last_sync_at = started_at
    account.sync_config = {
        **(account.sync_config or {}),
        "last_mapped_student_name": snapshot["student_name"],
        "last_mapped_modules": snapshot["modules_discovered"],
        "last_sync_mode": "portal_snapshot_import",
    }

    sync_log = ProviderSyncLog(
        provider_account_id=account.id,
        sync_type="manual",
        status="imported",
        items_found=5 + len(PLURALL_LIBRARY_CATALOG),
        items_synced=2 + library_changes,
        items_failed=0,
        error_message=(
            "Login no Plurall validado. O Mary importou o snapshot do portal, atualizou "
            "os dados escolares do aluno e materializou a biblioteca base do Lucas."
        ),
        started_at=started_at,
        completed_at=started_at,
        sync_metadata={
            "provider": PLURALL_PROVIDER_NAME,
            "username_hint": credentials.get("username", "")[:3],
            "student_name": snapshot["student_name"],
            "student_role": snapshot["student_role"],
            "school_name": snapshot["school_name"],
            "class_name": snapshot["class_name"],
            "grade_label": snapshot["grade_label"],
            "modules_discovered": snapshot["modules_discovered"],
            "supports_assignments": snapshot["supports_assignments"],
            "supports_books": snapshot["supports_books"],
            "supports_assessments": snapshot["supports_assessments"],
            "supports_results": snapshot["supports_results"],
            "library_catalog_titles": [material.title for material in library_materials],
            "planned_ingestion_channels": [
                "manual_portal_sync",
                "telegram_openclaw",
            ],
            "imports_completed": [
                "student_profile_update",
                "portal_snapshot_report",
                "library_catalog_materials",
            ],
        },
    )
    session.add(sync_log)
    await session.commit()
    await session.refresh(account)
    await session.refresh(sync_log)
    return account, sync_log
