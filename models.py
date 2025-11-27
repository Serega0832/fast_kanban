from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

# ... (Project и Column оставляем без изменений) ...

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    columns: List["Column"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})

class Column(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    project_id: int = Field(foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="columns")
    tasks: List["Task"] = Relationship(back_populates="column", sa_relationship_kwargs={"cascade": "all, delete"})

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    is_done: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # --- НОВОЕ ПОЛЕ: запоминаем, откуда задача пришла ---
    original_column_id: Optional[int] = Field(default=None)

    column_id: int = Field(foreign_key="column.id")
    column: Optional[Column] = Relationship(back_populates="tasks")