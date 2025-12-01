import httpx
import os
import random  # <--- NEW
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from dotenv import load_dotenv

from database import get_session
from models import Project, Column, Task, User
from auth import get_current_user
import config

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Та же палитра, что и в боте
TASK_COLORS = ["yellow", "green", "blue", "purple", "pink", "orange", "teal", "indigo", "rose"]


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    projects = session.exec(select(Project).where(Project.owner_id == user.telegram_id)).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects, "user": user})


@router.post("/projects/new", response_class=HTMLResponse)
async def create_project(request: Request, name: str = Form(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    new_proj = Project(name=name, owner_id=user.telegram_id)
    session.add(new_proj)
    session.commit()
    session.refresh(new_proj)

    defaults = ["Идеи", "В работе", "Сгенерировано AI", "Архив"]
    for col_name in defaults:
        session.add(Column(name=col_name, project_id=new_proj.id))
    session.commit()

    return templates.TemplateResponse("partials/project_item.html", {"request": request, "project": new_proj})


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def read_project(request: Request, project_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)
    if not project or project.owner_id != user.telegram_id:
        return Response(status_code=404)

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/board_view.html", {"request": request, "project": project})

    return templates.TemplateResponse("project_page.html", {"request": request, "project": project, "user": user})


# --- CONTEXT / DESCRIPTION ---

@router.get("/projects/{project_id}/description", response_class=HTMLResponse)
async def get_project_description(request: Request, project_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)
    if not project or project.owner_id != user.telegram_id:
        return Response(status_code=404)

    return templates.TemplateResponse("partials/project_description_modal.html", {"request": request, "project": project})


@router.patch("/projects/{project_id}/description", response_class=HTMLResponse)
async def update_project_description(request: Request, project_id: int, description: str = Form(""), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)
    if not project or project.owner_id != user.telegram_id:
        return Response(status_code=404)

    project.description = description
    session.add(project)
    session.commit()
    return Response(content="", media_type="text/html")


# --- AI GENERATION ---
@router.post("/projects/{project_id}/ai_generate", response_class=HTMLResponse)
async def ai_generate(request: Request, project_id: int, prompt: str = Form(...), mode: str = Form(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)

    if not project or project.owner_id != user.telegram_id:
        return Response(status_code=404)

    ai_col = next((c for c in project.columns if "AI" in c.name), None)
    if not ai_col:
        ai_col = Column(name="Сгенерировано AI", project_id=project_id)
        session.add(ai_col)
        session.commit()
        session.refresh(ai_col)

    context_part = ""
    if project.description:
        context_part = f"КОНТЕКСТ ПРОЕКТА:\n{project.description}\n\n"

    if mode == "breakdown":
        ai_system_instruction = (
            f"{context_part}"
            f"Ты - опытный менеджер. Учитывая контекст проекта (если задан), разбей задачу '{prompt}' на пошаговый план. "
            "ТОЛЬКО список задач. Без нумерации. "
        )
    else:
        ai_system_instruction = (
            f"{context_part}"
            f"Ты - креативный помощник. Учитывая контекст проекта (если задан), придумай идеи для канбан-доски на тему: '{prompt}'. "
            "ТОЛЬКО список. Без нумерации."
        )

    url = os.getenv("GEMINI_API_URL")
    if url:
        url = url.rstrip("/") + "/generate"

    if not url:
        session.add(Task(content="⚠️ Ошибка конфигурации: нет GEMINI_API_URL", column_id=ai_col.id))
        session.commit()
        return templates.TemplateResponse("partials/column.html", {"request": request, "column": ai_col})

    payload = {
        "service_name": "fast_kanban_app_web",
        "model": "gemini-flash-latest",
        "prompt": ai_system_instruction
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60.0)
            if resp.status_code == 200:
                data = resp.json()
                tasks_content = [line.strip() for line in data.get("text", "").split('\n') if line.strip()]

                # Выбираем цвет для пачки
                batch_color = random.choice(TASK_COLORS)

                for content in tasks_content:
                    clean_content = content.lstrip("- ").lstrip("• ").lstrip("1234567890. ")
                    if clean_content:
                        session.add(Task(content=clean_content, column_id=ai_col.id, color=batch_color))
                session.commit()
            else:
                session.add(Task(content=f"⚠️ API Error: {resp.status_code}", column_id=ai_col.id))
                session.commit()

    except Exception as e:
        session.add(Task(content=f"⚠️ Ошибка: {str(e)}", column_id=ai_col.id))
        session.commit()

    session.refresh(ai_col)
    return templates.TemplateResponse("partials/column.html", {"request": request, "column": ai_col})


# --- PROJECT EDITING ---

@router.get("/projects/{project_id}/edit_title", response_class=HTMLResponse)
async def get_project_title_edit(request: Request, project_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)
    if not project or project.owner_id != user.telegram_id:
        return Response(status_code=404)

    return templates.TemplateResponse("partials/project_title_edit.html", {"request": request, "project": project})


@router.patch("/projects/{project_id}", response_class=HTMLResponse)
async def patch_project_title(request: Request, project_id: int, name: str = Form(...), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    project = session.get(Project, project_id)
    if project and project.owner_id == user.telegram_id:
        project.name = name
        session.add(project)
        session.commit()
        session.refresh(project)
        return templates.TemplateResponse("partials/project_title.html", {"request": request, "project": project})

    return Response(status_code=404)