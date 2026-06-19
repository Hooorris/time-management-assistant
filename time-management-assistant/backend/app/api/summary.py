from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_task_service
from app.database import get_db
from app.schemas import DailySummaryRequest, DailySummaryResponse

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("/daily", operation_id="daily_summary", response_model=DailySummaryResponse)
def daily_summary(payload: DailySummaryRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db, timezone_name=payload.timezone)
    return service.daily_summary(date_value=payload.date)
