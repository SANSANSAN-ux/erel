from threading import Lock

from fastapi import APIRouter, HTTPException, Header

from models import TaskCreate, Task
from database import users_db, tasks_db, get_user_by_token


router = APIRouter(
    prefix="/tasks",
    tags=["Поручения"]
)

tasks_lock = Lock()


def require_user(token): #по токену находим пользователя
    user = get_user_by_token(token) if token else None

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Войдите в аккаунт. Если сервер перезапускался — войдите заново."
        )

    return user


@router.get("/", response_model=list[Task])
def get_tasks():
    return list(tasks_db.values())


@router.post("/", response_model=Task)
def create_task(
    task_data: TaskCreate,
    token: str | None = Header(default=None)
):
    staff = require_user(token) #проверяем роль , создавать поручения могут только сотрудники стафф

    if staff.role != "staff":
        raise HTTPException(
            status_code=403,
            detail="Создавать поручения могут только сотрудники."
        )

    title = task_data.title.strip()
    description = task_data.description.strip()

    if not title or not description:
        raise HTTPException(
            status_code=400,
            detail="Заполните название и описание."
        )

    if task_data.reward <= 0:
        raise HTTPException(
            status_code=400,
            detail="Награда должна быть больше нуля."
        )

    with tasks_lock:
        task_id = max(tasks_db.keys(), default=0) + 1

        task = Task(
            id=task_id,
            title=title,
            description=description,
            reward=task_data.reward,
            creator_id=staff.id
        )

        tasks_db[task_id] = task

    return task


@router.post("/{task_id}/take", response_model=Task)
def take_task(
    task_id: int,
    token: str | None = Header(default=None)
):
    student = require_user(token)

    if student.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Брать поручения могут только ученики."
        )

    with tasks_lock:
        task = tasks_db.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Поручение не найдено."
            )

        if task.status != "open":
            raise HTTPException(
                status_code=400,
                detail="Поручение уже занято или выполнено."
            )

        task.assignee_id = student.id
        task.status = "in_progress"

    return task


@router.post("/{task_id}/complete", response_model=Task)
def complete_task(
    task_id: int,
    token: str | None = Header(default=None)
):
    staff = require_user(token)

    if staff.role != "staff":
        raise HTTPException(
            status_code=403,
            detail="Подтверждать выполнение могут только сотрудники."
        )

    with tasks_lock:
        task = tasks_db.get(task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Поручение не найдено."
            )

        if task.creator_id != staff.id:
            raise HTTPException(
                status_code=403,
                detail="Подтвердить выполнение может только автор поручения."
            )

        if task.status != "in_progress":
            raise HTTPException(
                status_code=400,
                detail="Поручение не находится в работе или уже завершено."
            )

        student = users_db.get(task.assignee_id)

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Исполнитель не найден."
            )

        student.balance += task.reward #подтверждаем, и начисляеем коины на баланс ученика, отмечаем выполненным
        student.completed_tasks += 1
        task.status = "completed"

    return task