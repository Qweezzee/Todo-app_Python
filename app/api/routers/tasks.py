from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_task_service
from app.schemas.task import TaskRead, TaskCreate, TaskUpdate
from app.services.task import TaskService

router = APIRouter(prefix="/tasks")


@router.get("")
def read_tasks(service: TaskService = Depends(get_task_service)) -> list[TaskRead]:
    return service.list_task()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, service: TaskService = Depends(get_task_service)) -> TaskRead:
    return service.create_task(payload)


@router.patch("/{task_id}")
def update_task(
    task_id: str, payload: TaskUpdate, service: TaskService = Depends(get_task_service)
) -> TaskRead:
    return service.update_task(task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, service: TaskService = Depends(get_task_service)) -> None:
    service.delete_task(task_id)
