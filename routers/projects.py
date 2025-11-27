import httpx
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from database import get_session
from models import Project, Column, Task
import os
from dotenv import load_dotenv


load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@router.post("/projects/new", response_class=HTMLResponse)
async def create_project(request: Request, name: str = Form(...), session: Session = Depends(get_session)):
    new_proj = Project(name=name)
    session.add(new_proj)
    session.commit()
    session.refresh(new_proj)
    # Создаем дефолтные колонки + Архив
    defaults = ["Идеи", "В работе", "Сгенерировано AI", "Архив"]
    for col_name in defaults:
        session.add(Column(name=col_name, project_id=new_proj.id))
    session.commit()
    return templates.TemplateResponse("partials/project_item.html", {"request": request, "project": new_proj})

@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def read_project(request: Request, project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if not project: return Response(status_code=404)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/board_view.html", {"request": request, "project": project})
    return templates.TemplateResponse("project_page.html", {"request": request, "project": project})

# --- AI GENERATION ---
@router.post("/projects/{project_id}/ai_generate", response_class=HTMLResponse)
async def ai_generate(request: Request, project_id: int, prompt: str = Form(...), mode: str = Form(...), session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    ai_col = next((c for c in project.columns if "AI" in c.name), None)
    if not ai_col:
        ai_col = Column(name="Сгенерировано AI", project_id=project_id)
        session.add(ai_col)
        session.commit()
        session.refresh(ai_col)

    if mode == "breakdown":
        ai_system_instruction = f"Ты - опытный менеджер. Разбей задачу '{prompt}' на пошаговый план. ТОЛЬКО список. Без нумерации. Максимум 5 пунктов."
    else:
        ai_system_instruction = f"Придумай 3-5 коротких идей для канбан-доски: '{prompt}'. ТОЛЬКО список. Без нумерации."

    url = os.getenv("GEMINI_API_URL")

    if not url:
        # Обработка ошибки, если URL не задан
        session.add(Task(content="⚠️ Ошибка конфигурации: нет GEMINI_API_URL", column_id=ai_col.id))
        session.commit()
        return templates.TemplateResponse("partials/column.html", {"request": request, "column": ai_col})
    payload = {"service_name": "fast_kanban_app", "model": "gemini-flash-latest", "prompt": ai_system_instruction}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=45.0)
            data = resp.json()
            tasks_content = [line.strip() for line in data.get("text", "").split('\n') if line.strip()]

            for content in tasks_content:
                clean_content = content.lstrip("- ").lstrip("• ").lstrip("1234567890. ")
                if clean_content:
                    session.add(Task(content=clean_content, column_id=ai_col.id))
            session.commit()
    except Exception as e:
        session.add(Task(content=f"⚠️ Ошибка: {str(e)}", column_id=ai_col.id))
        session.commit()

    session.refresh(ai_col)
    return templates.TemplateResponse("partials/column.html", {"request": request, "column": ai_col})

# --- PROJECT EDITING ---

@router.get("/projects/{project_id}/edit_title", response_class=HTMLResponse)
async def get_project_title_edit(request: Request, project_id: int, session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    # Убедись, что файл templates/partials/project_title_edit.html существует!
    return templates.TemplateResponse("partials/project_title_edit.html", {"request": request, "project": project})

@router.patch("/projects/{project_id}", response_class=HTMLResponse)
async def patch_project_title(request: Request, project_id: int, name: str = Form(...), session: Session = Depends(get_session)):
    project = session.get(Project, project_id)
    if project:
        project.name = name
        session.add(project)
        session.commit()
        session.refresh(project)
    # Убедись, что файл templates/partials/project_title.html существует!
    return templates.TemplateResponse("partials/project_title.html", {"request": request, "project": project})