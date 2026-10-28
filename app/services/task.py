from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import TaskORM
from app.repositories.task import TaskRepository
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repository = TaskRepository(db)

    def list_task(self) -> list[TaskRead]:
        return [
            TaskRead.model_validate(item)
            for item in self.task_repository.get_all()
        ]

    def _get_or_404(self, task_id: str) -> TaskORM:
        item = self.task_repository.get_by_id(task_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        return item

    def create_task(self, payload: TaskCreate) -> TaskRead:
        item = self.task_repository.create(title=payload.title)
        self.db.commit()
        self.db.refresh(item)
        return TaskRead.model_validate(item)

    def update_task(self, task_id: str, payload: TaskUpdate) -> TaskRead:
        item = self._get_or_404(task_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return TaskRead.model_validate(item)

    def delete_task(self, task_id: str) -> None:
        item = self._get_or_404(task_id)
        self.task_repository.delete(item)
        self.db.commit()
