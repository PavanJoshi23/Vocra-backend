from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus
from app.models.extracted_skill import ExtractedSkill
from app.schemas.dashboard import (
    DashboardRates,
    DashboardSummary,
    DashboardTotals,
    MonthlyTrend,
    SkillDemand,
    StatusDistribution,
)

_INTERVIEWING_STATUSES = (ApplicationStatus.SCREENING, ApplicationStatus.INTERVIEW)
_CLOSED_STATUSES = (ApplicationStatus.OFFER, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN)


def _last_six_months() -> list[str]:
    now = datetime.now()
    year, month = now.year, now.month
    months: list[str] = []
    for _ in range(6):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


def get_summary(db: Session) -> DashboardSummary:
    base_filter = Application.is_deleted.is_(False)

    # Status distribution via a single group-by query
    status_rows = db.execute(
        select(Application.status, func.count(Application.id).label("cnt"))
        .where(base_filter)
        .group_by(Application.status)
    ).all()

    status_counts: dict[str, int] = {row.status: row.cnt for row in status_rows}
    total = sum(status_counts.values())

    interviewing = sum(
        status_counts.get(s.value, 0) for s in _INTERVIEWING_STATUSES
    )
    offers = status_counts.get(ApplicationStatus.OFFER.value, 0)
    rejected = status_counts.get(ApplicationStatus.REJECTED.value, 0)
    wishlist = status_counts.get(ApplicationStatus.WISHLIST.value, 0)
    applied_submitted = total - wishlist  # non-wishlist applications

    # Pending follow-ups: follow_up_date set, in the past/today, not closed
    today_str = datetime.now().date().isoformat()
    pending_followups_count = db.scalar(
        select(func.count(Application.id)).where(
            base_filter,
            Application.follow_up_date.is_not(None),
            Application.follow_up_date <= today_str,
            Application.status.notin_([s.value for s in _CLOSED_STATUSES]),
        )
    ) or 0

    totals = DashboardTotals(
        total=total,
        applied=applied_submitted,
        interviewing=interviewing,
        offers=offers,
        rejected=rejected,
        pending_followups=pending_followups_count,
    )

    denom = applied_submitted or 1  # avoid division by zero
    rates = DashboardRates(
        interview_rate=round(interviewing / denom, 4) if applied_submitted else 0.0,
        offer_rate=round(offers / denom, 4) if applied_submitted else 0.0,
        rejection_rate=round(rejected / denom, 4) if applied_submitted else 0.0,
    )

    # Monthly trend — last 6 months, fill missing months with 0
    month_expr = func.strftime("%Y-%m", Application.created_at)
    six_months_ago = _last_six_months()[0]  # earliest of the 6
    trend_rows = db.execute(
        select(month_expr.label("month"), func.count(Application.id).label("cnt"))
        .where(base_filter, month_expr >= six_months_ago)
        .group_by(month_expr)
        .order_by(month_expr)
    ).all()

    trend_map: dict[str, int] = {row.month: row.cnt for row in trend_rows}
    monthly_trend = [
        MonthlyTrend(month=m, count=trend_map.get(m, 0))
        for m in _last_six_months()
    ]

    # Status distribution
    status_distribution = [
        StatusDistribution(status=status, count=count)
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1])
    ]

    # Skill demand — aggregate JD-sourced skills, top 10
    skill_rows = db.execute(
        select(
            ExtractedSkill.skill_name.label("skill"),
            func.count(ExtractedSkill.id).label("cnt"),
        )
        .where(ExtractedSkill.source_type == "jd")
        .group_by(ExtractedSkill.skill_name)
        .order_by(func.count(ExtractedSkill.id).desc())
        .limit(10)
    ).all()

    skill_demand = [SkillDemand(skill=row.skill, count=row.cnt) for row in skill_rows]

    return DashboardSummary(
        totals=totals,
        rates=rates,
        monthly_trend=monthly_trend,
        status_distribution=status_distribution,
        skill_demand=skill_demand,
    )
