from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app.deps import CurrentGuardian, DbSession
from app.schemas.task import DashboardSummaryResponse, DashboardTodayResponse
from app.services.task_service import dashboard_summary, dashboard_today

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today", response_model=DashboardTodayResponse)
async def get_today(session: DbSession, current_guardian: CurrentGuardian) -> DashboardTodayResponse:
    students = await dashboard_today(session, current_guardian)
    return DashboardTodayResponse(date=date.today(), students=students)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(session: DbSession, current_guardian: CurrentGuardian) -> DashboardSummaryResponse:
    return DashboardSummaryResponse(students=await dashboard_summary(session, current_guardian))
