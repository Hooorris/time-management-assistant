from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


def test_task_http_api_flow(db_session, unique_title: str) -> None:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    try:
        create_response = client.post(
            "/tasks/create",
            json={
                "title": unique_title,
                "user_command": "pytest api create",
                "start_time": (now + timedelta(hours=1)).isoformat(),
                "reminder_time": (now + timedelta(hours=1)).isoformat(),
            },
        )
        assert create_response.status_code == 200
        task_id = create_response.json()["task_id"]

        query_response = client.get("/tasks/query", params={"date": now.date().isoformat(), "query": unique_title})
        assert query_response.status_code == 200
        assert len(query_response.json()["tasks"]) == 1

        update_response = client.post(
            "/tasks/update",
            json={
                "task_id": task_id,
                "user_command": "pytest api update",
                "changes": {"priority": "high"},
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["task"]["priority"] == "high"

        complete_response = client.post(
            "/tasks/complete",
            json={"task_id": task_id, "user_command": "pytest api complete"},
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["task"]["status"] == "done"

        summary_response = client.post(
            "/summary/daily",
            json={"date": now.date().isoformat(), "timezone": "Asia/Shanghai"},
        )
        assert summary_response.status_code == 200

        delete_response = client.post(
            "/tasks/delete",
            json={"task_id": task_id, "user_command": "pytest api delete"},
        )
        assert delete_response.status_code == 200
    finally:
        app.dependency_overrides.clear()
