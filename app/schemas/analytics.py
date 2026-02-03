from pydantic import BaseModel
from datetime import datetime, date


class ClicksByDay(BaseModel):
    date: date
    clicks: int


class AnalyticsSummary(BaseModel):
    total_clicks: int
    unique_visitors: int
    first_click: datetime | None = None
    last_click: datetime | None = None


class AnalyticsResponse(BaseModel):
    short_code: str
    target_url: str
    created_at: datetime
    summary: AnalyticsSummary
    clicks_by_day: list[ClicksByDay]
