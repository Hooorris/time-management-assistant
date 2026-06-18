import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy.inspection import inspect


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def model_to_dict(model: Any) -> dict[str, Any]:
    mapper = inspect(model).mapper
    return {
        column.key: to_jsonable(getattr(model, column.key))
        for column in mapper.column_attrs
    }
