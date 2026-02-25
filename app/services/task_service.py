from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.user import User, UserRole
from app.schemas.task import TaskAssign, TaskCreate, TaskUpdate


def create_task(db: Session, data: TaskCreate, current_user: User) -> Task:
    task = Task(
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        company_id=current_user.company_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> List[Task]:
    query = db.query(Task).filter(Task.company_id == current_user.company_id)

    # Employees only see their assigned tasks
    if current_user.role == UserRole.employee:
        query = query.filter(Task.assigned_to == current_user.id)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()


def update_task(db: Session, task_id: int, data: TaskUpdate, current_user: User) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.company_id == current_user.company_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Employees can only update their own assigned tasks
    if current_user.role == UserRole.employee and task.assigned_to != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update tasks assigned to you",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def assign_task(db: Session, task_id: int, data: TaskAssign, current_user: User) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.company_id == current_user.company_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Ensure assignee is in the same company
    assignee = (
        db.query(User)
        .filter(User.id == data.assigned_to, User.company_id == current_user.company_id)
        .first()
    )
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found in your company")

    task.assigned_to = data.assigned_to
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, current_user: User) -> None:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.company_id == current_user.company_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()
