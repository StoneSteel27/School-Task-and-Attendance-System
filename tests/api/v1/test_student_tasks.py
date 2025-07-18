from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User as UserModel
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskWithSubmissionStatus
from datetime import date


def test_list_student_tasks_with_submission_status(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    test_normal_user: UserModel,
):
    # Create a task for the student's class
    task = Task(
        title="Test Task",
        description="Test Description",
        due_date=date.today(),
        school_class_id=test_normal_user.school_class_id,
        subject="Math",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Get tasks and check initial status
    response = client.get(
        f"{settings.API_V1_STR}/students/me/tasks",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    task_data = tasks[0]
    TaskWithSubmissionStatus.model_validate(task_data)
    assert task_data["submission_status"] is None

    # Submit the task
    submission_data = {"file": ("test.txt", b"test content")}
    response = client.post(
        f"{settings.API_V1_STR}/students/me/tasks/{task.id}/submit",
        headers=normal_user_token_headers,
        files=submission_data,
    )
    assert response.status_code == 200

    # Get tasks again and check status
    response = client.get(
        f"{settings.API_V1_STR}/students/me/tasks",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    tasks = response.json()
    task_data = tasks[0]
    TaskWithSubmissionStatus.model_validate(task_data)
    assert task_data["submission_status"] == TaskStatus.SUBMITTED
