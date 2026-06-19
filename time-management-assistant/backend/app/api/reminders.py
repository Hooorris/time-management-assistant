from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_task_service
from app.database import get_db
from app.schemas import CheckRemindersRequest, ReminderCheckResponse

router = APIRouter(prefix="/reminder", tags=["reminder"])


@router.post("/check", operation_id="check_reminders", response_model=ReminderCheckResponse)
def check_reminders(payload: CheckRemindersRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db)
    return service.check_reminders(
        now=payload.now,
        channels=payload.channels,
        user_command=payload.user_command,
    )
