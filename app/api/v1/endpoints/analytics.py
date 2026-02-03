from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Literal

from app.api.deps import get_db
from app.db.models.url import URL
from app.db.models.click import Click
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummary, ClicksByDay

router = APIRouter()

# Valid periods as literal type
PeriodType = Literal["1d", "7d", "30d", "all"]

# Period to timedelta mapping
PERIOD_MAP = {
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@router.get(
    "/analytics/{short_code}",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK
)
async def get_analytics(
    short_code: str,
    period: PeriodType = Query(default="7d"),  # Query parameter with default
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for a shortened URL.
    
    - **short_code**: The short code of the URL
    - **period**: Time period (1d, 7d, 30d, all)
    """
    
    # 1. Find the URL
    result = await db.execute(
        select(URL).where(URL.short_code == short_code)
    )
    url = result.scalar_one_or_none()
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with code '{short_code}' not found"
        )
    
    # 2. Calculate start_date based on period
    start_date = None
    if period != "all":
        start_date = datetime.utcnow() - PERIOD_MAP[period]
    
    # 3. Base query condition
    base_condition = [Click.url_id == url.id]
    if start_date:
        base_condition.append(Click.created_at >= start_date)
    
    # 4. Query summary stats
    summary_result = await db.execute(
        select(
            func.count(Click.id).label("total_clicks"),
            func.count(Click.ip_address.distinct()).label("unique_visitors"),
            func.min(Click.created_at).label("first_click"),
            func.max(Click.created_at).label("last_click"),
        ).where(*base_condition)
    )
    summary_row = summary_result.one()
    
    summary = AnalyticsSummary(
        total_clicks=summary_row.total_clicks,
        unique_visitors=summary_row.unique_visitors,
        first_click=summary_row.first_click,
        last_click=summary_row.last_click,
    )
    
    # 5. Query clicks by day
    clicks_by_day_result = await db.execute(
        select(
            func.date(Click.created_at).label("click_date"),
            func.count(Click.id).label("clicks"),
        )
        .where(*base_condition)
        .group_by(func.date(Click.created_at))
        .order_by(func.date(Click.created_at).asc())
    )
    
    clicks_by_day = [
        ClicksByDay(date=row.click_date, clicks=row.clicks)
        for row in clicks_by_day_result.all()
    ]
    
    # 6. Build response
    return AnalyticsResponse(
        short_code=url.short_code,
        target_url=url.target_url,
        created_at=url.created_at,
        summary=summary,
        clicks_by_day=clicks_by_day,
    )
