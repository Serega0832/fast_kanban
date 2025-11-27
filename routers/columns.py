from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session
from database import get_session
from models import Column

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/projects/{project_id}/columns", response_class=HTMLResponse)
async def create_column(request: Request, project_id: int, name: str = Form(...), session: Session = Depends(get_session)):
    new_col = Column(name=name, project_id=project_id)
    session.add(new_col)
    session.commit()
    session.refresh(new_col)
    return templates.TemplateResponse("partials/column.html", {"request": request, "column": new_col})

@router.delete("/columns/{column_id}", response_class=HTMLResponse)
async def delete_column(column_id: int, session: Session = Depends(get_session)):
    col = session.get(Column, column_id)
    if col:
        session.delete(col)
        session.commit()
    return ""

@router.get("/columns/{column_id}/edit", response_class=HTMLResponse)
async def get_edit_column(request: Request, column_id: int, session: Session = Depends(get_session)):
    column = session.get(Column, column_id)
    return templates.TemplateResponse("partials/column_edit.html", {"request": request, "column": column})

@router.patch("/columns/{column_id}", response_class=HTMLResponse)
async def patch_column(request: Request, column_id: int, name: str = Form(...), session: Session = Depends(get_session)):
    column = session.get(Column, column_id)
    if column:
        column.name = name
        session.add(column)
        session.commit()
        session.refresh(column)
    return templates.TemplateResponse("partials/column_header.html", {"request": request, "column": column})