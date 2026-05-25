from pydantic import BaseModel


class DashboardTotals(BaseModel):
    total: int
    applied: int
    interviewing: int
    offers: int
    rejected: int
    pending_followups: int


class DashboardRates(BaseModel):
    interview_rate: float
    offer_rate: float
    rejection_rate: float


class MonthlyTrend(BaseModel):
    month: str
    count: int


class StatusDistribution(BaseModel):
    status: str
    count: int


class SkillDemand(BaseModel):
    skill: str
    count: int


class DashboardSummary(BaseModel):
    totals: DashboardTotals
    rates: DashboardRates
    monthly_trend: list[MonthlyTrend]
    status_distribution: list[StatusDistribution]
    skill_demand: list[SkillDemand]
