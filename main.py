import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from contextlib import asynccontextmanager
from database import create_db_and_tables

# Импортируем роутеры
from routers import projects, columns, tasks, auth

# Логика запуска/остановки
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Глобальный обработчик 401 ошибки (если не залогинен -> на /login)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login")
    return await request.app.default_exception_handler(request, exc)

# Подключаем роутеры
app.include_router(auth.router) # Сначала Auth
app.include_router(projects.router)
app.include_router(columns.router)
app.include_router(tasks.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)