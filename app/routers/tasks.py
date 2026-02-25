from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.role import require_roles
from app.models.user import User, UserRole
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskAssign, TaskResponse
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    """Admin/Manager: Create a new task."""
    return task_service.create_task(db, data, current_user)


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin/Manager → all company tasks.
    Employee → only tasks assigned to them.
    Supports pagination and title search.
    """
    return task_service.get_tasks(db, current_user, skip=skip, limit=limit, search=search)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin/Manager → update any company task.
    Employee → only their assigned tasks.
    """
    return task_service.update_task(db, task_id, data, current_user)


@router.patch("/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    task_id: int,
    data: TaskAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    """Admin/Manager: Assign a task to a user."""
    return task_service.assign_task(db, task_id, data, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    """Admin-only: Delete a task."""
    task_service.delete_task(db, task_id, current_user)
