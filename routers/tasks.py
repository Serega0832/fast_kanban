from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from database import get_session
from models import Task, Column

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/columns/{column_id}/tasks", response_class=HTMLResponse)
async def create_task(request: Request, column_id: int, content: str = Form(...), session: Session = Depends(get_session)):
    new_task = Task(content=content, column_id=column_id)
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return templates.TemplateResponse("partials/task.html", {"request": request, "task": new_task})



@router.post("/tasks/{task_id}/archive", response_class=HTMLResponse)
async def archive_task(request: Request, task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        return ""

    # Запоминаем текущую и будущую колонки для обновления UI
    source_col = task.column
    project = source_col.project

    # --- ЛОГИКА ПЕРЕМЕЩЕНИЯ ---

    if not task.is_done:
        # 1. ОТПРАВЛЯЕМ В АРХИВ
        archive_col = next((c for c in project.columns if "Архив" in c.name), None)
        if not archive_col:
            archive_col = Column(name="Архив", project_id=project.id)
            session.add(archive_col)
            session.commit()
            session.refresh(archive_col)

        target_col = archive_col
        task.is_done = True
        task.original_column_id = source_col.id  # Запоминаем, откуда пришла

    else:
        # 2. ВОЗВРАЩАЕМ ИЗ АРХИВА
        target_col_id = task.original_column_id

        # Если память потеряна (старая задача), вернем в первую колонку проекта (которая не архив)
        if not target_col_id:
            first_col = next((c for c in project.columns if "Архив" not in c.name), None)
            target_col_id = first_col.id if first_col else source_col.id

        target_col = session.get(Column, target_col_id)
        # Если вдруг той колонки уже нет, оставляем где была или кидаем в первую попавшуюся
        if not target_col:
            target_col = source_col

        task.is_done = False
        task.original_column_id = None  # Стираем память

    # Применяем изменения
    task.column_id = target_col.id
    session.add(task)
    session.commit()

    # Обновляем данные для рендеринга
    session.refresh(source_col)
    session.refresh(target_col)
    session.refresh(task)

    # --- ГЕНЕРАЦИЯ ОТВЕТА (HTMX OOB) ---

    # 1. Рендерим заголовки обеих колонок (чтобы обновить цифры счетчиков)
    source_header = templates.TemplateResponse("partials/column_header.html", {"request": request, "column": source_col}).body.decode("utf-8")
    target_header = templates.TemplateResponse("partials/column_header.html", {"request": request, "column": target_col}).body.decode("utf-8")

    # 2. Рендерим СПИСОК задач для ЦЕЛЕВОЙ колонки (чтобы задача там появилась)
    # Мы берем весь контейнер задач целиком, чтобы не мучаться с insertAdjacentHTML
    # Важно: в partials/column.html у нас есть цикл задач. Нам нужно отрендерить только содержимое контейнера задач.
    # Но проще всего через OOB обновить весь блок <div id="col-X-tasks">

    target_tasks_html = ""
    for t in target_col.tasks:
        target_tasks_html += templates.TemplateResponse("partials/task.html", {"request": request, "task": t}).body.decode("utf-8")

    response_content = f"""
    <!-- 1. Удаляем задачу из старого места (возвращаем пустоту в ответ на клик) -->

    <!-- 2. Обновляем заголовок СТАРОЙ колонки (OOB) -->
    <div id="col-header-{source_col.id}" hx-swap-oob="true">
        {source_header}
    </div>

    <!-- 3. Обновляем заголовок НОВОЙ колонки (OOB) -->
    <div id="col-header-{target_col.id}" hx-swap-oob="true">
        {target_header}
    </div>

    <!-- 4. Обновляем список задач НОВОЙ колонки (OOB) -->
    <div id="col-{target_col.id}-tasks" hx-swap-oob="true" class="flex-1 overflow-y-auto min-h-[20px] pr-1 custom-scrollbar pb-2">
        {target_tasks_html}
    </div>
    """

    return HTMLResponse(content=response_content)




@router.delete("/tasks/{task_id}", response_class=HTMLResponse)
async def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task:
        session.delete(task)
        session.commit()
    return ""


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def get_edit_task(request: Request, task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    return templates.TemplateResponse("partials/task_edit.html", {"request": request, "task": task})


@router.patch("/tasks/{task_id}", response_class=HTMLResponse)
async def patch_task(request: Request, task_id: int, content: str = Form(...), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task:
        task.content = content
        session.add(task)
        session.commit()
        session.refresh(task)
    return templates.TemplateResponse("partials/task.html", {"request": request, "task": task})

