from __future__ import annotations

import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models.curriculum import CurriculumItem, Subject
from app.models.family import Family, Guardian, Student
from app.models.material import SchoolTask
from app.models.profile import InterestProfile, StudentProfile
from app.security import hash_password


SUBJECTS = [
    # 1º ano EF — Lucas
    {"slug": "portugues-1fund", "name": "Língua Portuguesa", "grade": "1_fund", "category": "core"},
    {"slug": "matematica-1fund", "name": "Matemática", "grade": "1_fund", "category": "core"},
    {"slug": "ciencias-1fund", "name": "Ciências", "grade": "1_fund", "category": "core"},
    {"slug": "geografia-1fund", "name": "Geografia", "grade": "1_fund", "category": "core"},
    {"slug": "historia-1fund", "name": "História", "grade": "1_fund", "category": "core"},
    {"slug": "ciencias-humanas-1fund", "name": "Ciências Humanas", "grade": "1_fund", "category": "core"},
    {"slug": "artes-1fund", "name": "Artes", "grade": "1_fund", "category": "enrichment"},
    {"slug": "educacao-fisica-1fund", "name": "Educação Física", "grade": "1_fund", "category": "enrichment"},
    {"slug": "ensino-religioso-1fund", "name": "Ensino Religioso", "grade": "1_fund", "category": "enrichment"},
    {"slug": "musica-1fund", "name": "Música", "grade": "1_fund", "category": "enrichment"},
    {"slug": "ingles-1fund", "name": "Inglês", "grade": "1_fund", "category": "enrichment"},
    {"slug": "formacao-crista-1fund", "name": "Formação Cristã", "grade": "1_fund", "category": "enrichment"},
    {"slug": "projeto-vida-1fund", "name": "Projeto de Vida", "grade": "1_fund", "category": "enrichment"},
    # 7º ano EF — Malu
    {"slug": "portugues-7fund", "name": "Português", "grade": "7_fund", "category": "core"},
    {"slug": "matematica-7fund", "name": "Matemática", "grade": "7_fund", "category": "core"},
    {"slug": "ingles-7fund", "name": "Inglês", "grade": "7_fund", "category": "core"},
    {"slug": "ciencias-7fund", "name": "Ciências 1", "grade": "7_fund", "category": "core"},
    {"slug": "ciencias2-7fund", "name": "Ciências 2", "grade": "7_fund", "category": "core"},
    {"slug": "historia-7fund", "name": "História", "grade": "7_fund", "category": "core"},
    {"slug": "geografia-7fund", "name": "Geografia", "grade": "7_fund", "category": "core"},
    {"slug": "artes-7fund", "name": "Artes", "grade": "7_fund", "category": "enrichment"},
    {"slug": "educacao-fisica-7fund", "name": "Educação Física", "grade": "7_fund", "category": "enrichment"},
    {"slug": "ensino-religioso-7fund", "name": "Ensino Religioso", "grade": "7_fund", "category": "enrichment"},
    {"slug": "espanhol-7fund", "name": "Espanhol", "grade": "7_fund", "category": "enrichment"},
    # Correção 5 — matérias faltantes do 7º ano
    {"slug": "redacao-7fund", "name": "Redação", "grade": "7_fund", "category": "core"},
    {"slug": "geometria-7fund", "name": "Geometria", "grade": "7_fund", "category": "core"},
    {"slug": "ed-digital-7fund", "name": "Educação Digital/Atualidades", "grade": "7_fund", "category": "digital"},
    {"slug": "ed-financeira-7fund", "name": "Educação Financeira", "grade": "7_fund", "category": "financial"},
    {"slug": "laboratorio-7fund", "name": "Laboratório", "grade": "7_fund", "category": "lab"},
    {"slug": "oficina-7fund", "name": "Oficina", "grade": "7_fund", "category": "project"},
    {"slug": "socioemocional-7fund", "name": "Educação Socioemocional", "grade": "7_fund", "category": "socio"},
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
    "geometria-7fund": [
        "Ângulos: classificação e medidas",
        "Triângulos: classificação e propriedades",
        "Área e perímetro de polígonos",
    ],
}

# Lucas 1º ano FT — horário real do Colégio Grande Passo (TARDE, 13h15-17h45)
LUCAS_WEEKLY_SCHEDULE = {
    "monday": [
        {"subject": "Inglês", "start": "13:15", "end": "14:00"},
        {"subject": "Matemática", "start": "14:00", "end": "14:40"},
        {"subject": "Matemática", "start": "14:40", "end": "15:20"},
        {"subject": "Lanche", "start": "15:20", "end": "15:50", "is_break": True},
        {"subject": "Matemática", "start": "15:50", "end": "16:30"},
        {"subject": "Parque", "start": "16:30", "end": "17:00", "is_break": True},
        {"subject": "Matemática", "start": "17:00", "end": "17:40"},
    ],
    "tuesday": [
        {"subject": "Arte", "start": "13:15", "end": "14:00"},
        {"subject": "Inglês", "start": "14:00", "end": "14:40"},
        {"subject": "Português", "start": "14:40", "end": "15:20"},
        {"subject": "Lanche", "start": "15:20", "end": "15:50", "is_break": True},
        {"subject": "Português", "start": "15:50", "end": "16:30"},
        {"subject": "Parque", "start": "16:30", "end": "17:00", "is_break": True},
        {"subject": "Português", "start": "17:00", "end": "17:40"},
    ],
    "wednesday": [
        {"subject": "Matemática", "start": "13:15", "end": "14:00"},
        {"subject": "Inglês", "start": "14:00", "end": "14:40"},
        {"subject": "Maker", "start": "14:40", "end": "15:20"},
        {"subject": "Lanche", "start": "15:20", "end": "15:50", "is_break": True},
        {"subject": "Matemática", "start": "15:50", "end": "16:30"},
        {"subject": "Parque", "start": "16:30", "end": "17:00", "is_break": True},
        {"subject": "Matemática", "start": "17:00", "end": "17:40"},
    ],
    "thursday": [
        {"subject": "Inglês", "start": "13:15", "end": "14:00"},
        {"subject": "Português", "start": "14:00", "end": "14:40"},
        {"subject": "Português", "start": "14:40", "end": "15:20"},
        {"subject": "Lanche", "start": "15:20", "end": "15:50", "is_break": True},
        {"subject": "Português", "start": "15:50", "end": "16:30"},
        {"subject": "Parque", "start": "16:30", "end": "17:00", "is_break": True},
        {"subject": "Português", "start": "17:00", "end": "17:40"},
    ],
    "friday": [
        {"subject": "História/Geografia", "start": "13:15", "end": "14:40"},
        {"subject": "Ciências", "start": "14:40", "end": "15:20"},
        {"subject": "Educação Física", "start": "15:30", "end": "16:10"},
        {"subject": "Lanche", "start": "16:10", "end": "16:30", "is_break": True},
        {"subject": "Parque", "start": "16:30", "end": "17:00", "is_break": True},
        {"subject": "Educação Socioemocional", "start": "17:00", "end": "17:40"},
    ],
}

# Lucas — janelas de tutoria com a Mary (noturnas)
LUCAS_TUTOR_WINDOWS = {
    "monday":    [{"start": "20:15", "end": "21:30", "kind": "homework", "label": "Tarefa de casa"}],
    "tuesday":   [{"start": "20:15", "end": "21:30", "kind": "homework", "label": "Tarefa de casa"}],
    "wednesday": [{"start": "20:15", "end": "21:30", "kind": "homework", "label": "Tarefa de casa"}],
    "thursday":  [{"start": "20:15", "end": "21:30", "kind": "homework", "label": "Tarefa de casa"}],
    "friday":    [{"start": "20:15", "end": "21:30", "kind": "light", "label": "Revisão leve"}],
    "saturday":  [],
    "sunday":    [{"start": "20:00", "end": "20:45", "kind": "weekly_prep", "label": "Preparação semanal"}],
}

# Malu 7º ano D — horário real do Colégio Grande Passo
# Terça-feira é integral (manhã + tarde). Os demais dias são só tarde.
MALU_WEEKLY_SCHEDULE = {
    "monday": [
        {"subject": "Oficina", "start": "13:15", "end": "14:00"},
        {"subject": "Oficina", "start": "14:00", "end": "14:45"},
        {"subject": "Artes", "start": "14:45", "end": "15:30", "teacher": "Suzanny"},
        {"subject": "História", "start": "15:30", "end": "16:15", "teacher": "Suzy"},
        {"subject": "Intervalo", "start": "16:15", "end": "16:45", "is_break": True},
        {"subject": "Espanhol", "start": "16:45", "end": "17:30", "teacher": "Cinthia Souza"},
        {"subject": "Laboratório", "start": "17:30", "end": "18:15", "teacher": "Lili"},
    ],
    "tuesday": [
        {"subject": "Educação Digital/Atualidades", "start": "07:15", "end": "08:00", "teacher": "Suzy"},
        {"subject": "Geometria", "start": "08:00", "end": "08:45", "teacher": "Caio"},
        {"subject": "Educação Física", "start": "08:45", "end": "09:30", "teacher": "João Carlos"},
        {"subject": "Intervalo", "start": "09:30", "end": "10:00", "is_break": True},
        {"subject": "Redação", "start": "10:00", "end": "10:45", "teacher": "Aline"},
        {"subject": "Redação", "start": "10:45", "end": "11:30", "teacher": "Aline"},
        {"subject": "História", "start": "13:15", "end": "14:00", "teacher": "Suzy"},
        {"subject": "História", "start": "14:00", "end": "14:45", "teacher": "Suzy"},
        {"subject": "Ciências 1", "start": "14:45", "end": "15:30", "teacher": "Lili"},
        {"subject": "Ciências 1", "start": "15:30", "end": "16:15", "teacher": "Lili"},
        {"subject": "Intervalo", "start": "16:15", "end": "16:45", "is_break": True},
        {"subject": "Português", "start": "16:45", "end": "17:30", "teacher": "Pollyanna"},
        {"subject": "Português", "start": "17:30", "end": "18:15", "teacher": "Pollyanna"},
    ],
    "wednesday": [
        {"subject": "Ciências 2", "start": "13:15", "end": "14:00", "teacher": "Jessika"},
        {"subject": "Matemática", "start": "14:00", "end": "14:45", "teacher": "Valéria Vieira"},
        {"subject": "Matemática", "start": "14:45", "end": "15:30", "teacher": "Valéria Vieira"},
        {"subject": "Inglês", "start": "15:30", "end": "16:15", "teacher": "Tales"},
        {"subject": "Intervalo", "start": "16:15", "end": "16:45", "is_break": True},
        {"subject": "Geografia", "start": "16:45", "end": "17:30", "teacher": "Carol"},
        {"subject": "Ativ. Português", "start": "17:30", "end": "18:15", "teacher": "Pollyanna"},
    ],
    "thursday": [
        {"subject": "Português", "start": "13:15", "end": "14:00", "teacher": "Pollyanna"},
        {"subject": "Geometria", "start": "14:00", "end": "14:45", "teacher": "Caio"},
        {"subject": "Inglês", "start": "14:45", "end": "15:30", "teacher": "Tales"},
        {"subject": "Matemática", "start": "15:30", "end": "16:15", "teacher": "Valéria Vieira"},
        {"subject": "Intervalo", "start": "16:15", "end": "16:45", "is_break": True},
        {"subject": "Matemática", "start": "16:45", "end": "17:30", "teacher": "Valéria Vieira"},
        {"subject": "Educação Física", "start": "17:30", "end": "18:15", "teacher": "João Carlos"},
    ],
    "friday": [
        {"subject": "Educação Financeira", "start": "13:15", "end": "14:00", "teacher": "Luma"},
        {"subject": "Inglês", "start": "14:00", "end": "14:45", "teacher": "Tales"},
        {"subject": "Inglês", "start": "14:45", "end": "15:30", "teacher": "Tales"},
        {"subject": "Educação Socioemocional", "start": "15:30", "end": "16:15"},
        {"subject": "Intervalo", "start": "16:15", "end": "16:45", "is_break": True},
        {"subject": "Geografia", "start": "16:45", "end": "17:30", "teacher": "Carol"},
        {"subject": "Geografia", "start": "17:30", "end": "18:15", "teacher": "Carol"},
    ],
}

# Malu — janelas de tutoria reais (terça bloqueada: integral + vôlei)
MALU_TUTOR_WINDOWS = {
    "monday":    [{"start": "20:00", "end": "22:00", "kind": "homework", "label": "Tarefa de casa"}],
    "tuesday":   [],  # BLOQUEADO — integral + vôlei, chega destruída
    "wednesday": [
        {"start": "09:00", "end": "11:00", "kind": "self_study", "label": "Estudo próprio"},
        {"start": "20:00", "end": "22:00", "kind": "homework", "label": "Tarefa de casa"},
    ],
    "thursday":  [{"start": "21:15", "end": "22:00", "kind": "light", "label": "Revisão pós-vôlei"}],
    "friday": [
        {"start": "09:00", "end": "11:00", "kind": "self_study", "label": "Estudo próprio"},
        {"start": "20:00", "end": "22:00", "kind": "homework", "label": "Tarefa de casa"},
    ],
    "saturday":  [],
    "sunday":    [{"start": "20:00", "end": "21:00", "kind": "weekly_prep", "label": "Preparação semanal"}],
}

# Malu — atividades fixas fora da escola
MALU_FIXED_ACTIVITIES = [
    {
        "name": "Vôlei",
        "weekdays": ["tuesday", "thursday"],
        "start": "19:30",
        "end": "20:30",
        "blocks_tutor": False,
    },
]


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

        profile_data = {
            "Lucas Henrique Sousa Angelim": {
                "attention_span_minutes": 20,
                "best_study_time": "afternoon",
                "notes": "Em fase de alfabetização e acompanhamento diário de agenda escolar",
                "weekly_schedule": LUCAS_WEEKLY_SCHEDULE,
                "fixed_activities": [],
                "tutor_windows": LUCAS_TUTOR_WINDOWS,
            },
            "Malu": {
                "attention_span_minutes": 40,
                "best_study_time": "morning",
                "notes": "Aluna do 7º ano com foco em rotina, matemática e acompanhamento multidisciplinar",
                "weekly_schedule": MALU_WEEKLY_SCHEDULE,
                "fixed_activities": MALU_FIXED_ACTIVITIES,
                "tutor_windows": MALU_TUTOR_WINDOWS,
            },
        }
        for name, payload in profile_data.items():
            student = students_by_name[name]
            profile = await session.scalar(select(StudentProfile).where(StudentProfile.student_id == student.id))
            if profile is None:
                session.add(StudentProfile(student_id=student.id, difficulty_areas=[], strength_areas=[], **payload))
            else:
                profile.weekly_schedule = payload["weekly_schedule"]
                profile.fixed_activities = payload["fixed_activities"]
                profile.tutor_windows = payload["tutor_windows"]
            interests = await session.scalar(select(InterestProfile).where(InterestProfile.student_id == student.id))
            if interests is None:
                session.add(InterestProfile(student_id=student.id, interests=[], favorite_subjects=[], hobbies=[], motivators=[], aversions=[]))

        subject_map: dict[str, Subject] = {}
        allowed_first_fund_slugs = {s["slug"] for s in SUBJECTS if s["grade"] == "1_fund"}
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
