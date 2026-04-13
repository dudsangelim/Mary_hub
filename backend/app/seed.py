from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models.curriculum import CurriculumItem, Subject
from app.models.family import Family, Guardian, Student
from app.models.material import SchoolTask
from app.models.profile import InterestProfile, StudentProfile
from app.security import hash_password


SUBJECTS = [
    {"slug": "portugues-1fund", "name": "Língua Portuguesa", "grade": "1_fund", "category": "core"},
    {"slug": "matematica-1fund", "name": "Matemática", "grade": "1_fund", "category": "core"},
    {"slug": "ciencias-1fund", "name": "Ciências", "grade": "1_fund", "category": "core"},
    {"slug": "geografia-1fund", "name": "Geografia", "grade": "1_fund", "category": "core"},
    {"slug": "historia-1fund", "name": "História", "grade": "1_fund", "category": "core"},
    {"slug": "ciencias-humanas-1fund", "name": "Ciências Humanas", "grade": "1_fund", "category": "core"},
    {"slug": "portugues-7fund", "name": "Português", "grade": "7_fund", "category": "core"},
    {"slug": "matematica-7fund", "name": "Matemática", "grade": "7_fund", "category": "core"},
    {"slug": "ingles-7fund", "name": "Inglês", "grade": "7_fund", "category": "core"},
]

CURRICULUM = {
    "portugues-1fund": [
        "Alfabeto: reconhecimento de letras maiúsculas e minúsculas",
        "Formação de sílabas simples",
        "Leitura de palavras com sílabas canônicas (CV)",
    ],
    "matematica-1fund": [
        "Números de 0 a 20: contagem e escrita",
        "Adição com resultados até 10",
        "Figuras geométricas planas: reconhecimento",
    ],
    "ciencias-1fund": [
        "Seres vivos e elementos da natureza",
        "Partes do corpo humano e cuidados básicos",
        "Observação do ambiente e do tempo",
    ],
    "geografia-1fund": [
        "Espaços da casa, da escola e do bairro",
        "Noções de localização e trajetos simples",
        "Paisagens naturais e modificadas",
    ],
    "historia-1fund": [
        "História pessoal e da família",
        "Rotina e passagem do tempo",
        "Datas e acontecimentos importantes",
    ],
    "ciencias-humanas-1fund": [
        "Revisão integrada de História e Geografia",
        "Leitura de imagens, mapas simples e linhas do tempo",
        "Projetos interdisciplinares de mundo social",
    ],
    "portugues-7fund": [
        "Interpretação de textos narrativos e dissertativos",
        "Concordância verbal e nominal",
        "Produção de texto argumentativo",
    ],
    "matematica-7fund": [
        "Números inteiros: operações e propriedades",
        "Equações do 1º grau",
        "Razão e proporção",
    ],
    "ingles-7fund": [
        "Present Perfect: formation and usage",
        "Reading comprehension: short articles",
        "Vocabulary: daily routines and travel",
    ],
}


async def seed() -> None:
    async with SessionLocal() as session:
        family = await session.scalar(select(Family).where(Family.name == "Família Eduardo"))
        if family is None:
            family = Family(name="Família Eduardo", timezone="America/Sao_Paulo", settings={})
            session.add(family)
            await session.flush()

        guardian = await session.scalar(select(Guardian).where(Guardian.email == "eduardo@mary.local"))
        if guardian is None:
            guardian = Guardian(
                family_id=family.id,
                name="Eduardo",
                email="eduardo@mary.local",
                password_hash=hash_password("mary2026"),
                role="parent",
                is_primary=True,
            )
            session.add(guardian)
            await session.flush()

        students_by_name: dict[str, Student] = {}
        for payload in [
            {
                "name": "Lucas Henrique Sousa Angelim",
                "grade": "1_fund",
                "grade_label": "1º ano do Ensino Fundamental",
                "avatar_color": "#3b82f6",
            },
            {
                "name": "Malu",
                "grade": "7_fund",
                "grade_label": "7º ano do Ensino Fundamental",
                "avatar_color": "#ec4899",
            },
        ]:
            student = await session.scalar(select(Student).where(Student.family_id == family.id, Student.name == payload["name"]))
            if student is None and payload["name"].startswith("Lucas"):
                student = await session.scalar(
                    select(Student).where(Student.family_id == family.id, Student.name.ilike("Lucas%"))
                )
            if student is None:
                student = Student(family_id=family.id, **payload)
                session.add(student)
                await session.flush()
            else:
                student.name = payload["name"]
                student.grade = payload["grade"]
                student.grade_label = payload["grade_label"]
                student.avatar_color = payload["avatar_color"]
            students_by_name[payload["name"]] = student

        profiles = {
            "Lucas Henrique Sousa Angelim": {
                "attention_span_minutes": 20,
                "best_study_time": "afternoon",
                "notes": "Em fase de alfabetização e acompanhamento diário de agenda escolar",
            },
            "Malu": {
                "attention_span_minutes": 40,
                "best_study_time": "morning",
                "notes": "Aluna do 7º ano com foco em rotina, matemática e acompanhamento multidisciplinar",
            },
        }
        for name, payload in profiles.items():
            student = students_by_name[name]
            profile = await session.scalar(select(StudentProfile).where(StudentProfile.student_id == student.id))
            if profile is None:
                session.add(StudentProfile(student_id=student.id, difficulty_areas=[], strength_areas=[], **payload))
            interests = await session.scalar(select(InterestProfile).where(InterestProfile.student_id == student.id))
            if interests is None:
                session.add(InterestProfile(student_id=student.id, interests=[], favorite_subjects=[], hobbies=[], motivators=[], aversions=[]))

        subject_map: dict[str, Subject] = {}
        allowed_first_fund_slugs = {
            "portugues-1fund",
            "matematica-1fund",
            "ciencias-1fund",
            "geografia-1fund",
            "historia-1fund",
            "ciencias-humanas-1fund",
        }
        for payload in SUBJECTS:
            subject = await session.scalar(select(Subject).where(Subject.slug == payload["slug"]))
            if subject is None:
                subject = Subject(**payload)
                session.add(subject)
                await session.flush()
            else:
                subject.name = payload["name"]
                subject.grade = payload["grade"]
                subject.category = payload["category"]
                subject.is_active = True
            subject_map[payload["slug"]] = subject

        first_fund_subjects = list((await session.scalars(select(Subject).where(Subject.grade == "1_fund"))).all())
        for subject in first_fund_subjects:
            if subject.slug not in allowed_first_fund_slugs:
                subject.is_active = False

        for slug, items in CURRICULUM.items():
            subject = subject_map[slug]
            for index, title in enumerate(items):
                exists = await session.scalar(select(CurriculumItem).where(CurriculumItem.subject_id == subject.id, CurriculumItem.title == title))
                if exists is None:
                    session.add(
                        CurriculumItem(
                            subject_id=subject.id,
                            title=title,
                            order_index=index,
                            source_type="seed_demo",
                        )
                    )

        today = date.today()
        demo_tasks = [
            (
                "Lucas Henrique Sousa Angelim",
                "Lição de casa: letras do alfabeto",
                "portugues-1fund",
                today + timedelta(days=1),
                "pending",
                "normal",
            ),
            (
                "Lucas Henrique Sousa Angelim",
                "Contar objetos até 20",
                "matematica-1fund",
                today + timedelta(days=2),
                "pending",
                "normal",
            ),
            ("Malu", "Redação: texto dissertativo sobre meio ambiente", "portugues-7fund", today + timedelta(days=3), "pending", "high"),
            ("Malu", "Lista de exercícios: equações do 1º grau", "matematica-7fund", today + timedelta(days=2), "pending", "normal"),
        ]
        for student_name, title, subject_slug, due_date, status, priority in demo_tasks:
            student = students_by_name[student_name]
            exists = await session.scalar(select(SchoolTask).where(SchoolTask.student_id == student.id, SchoolTask.title == title, SchoolTask.deleted_at.is_(None)))
            if exists is None:
                session.add(
                    SchoolTask(
                        student_id=student.id,
                        created_by=guardian.id,
                        title=title,
                        subject_id=subject_map[subject_slug].id,
                        task_type="homework",
                        due_date=due_date,
                        status=status,
                        priority=priority,
                        source="manual",
                    )
                )

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
