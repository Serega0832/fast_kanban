import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_db_and_tables

# Импортируем роутеры
from routers import projects, columns, tasks

# Логика запуска/остановки
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Подключаем роутеры
app.include_router(projects.router)
app.include_router(columns.router)
app.include_router(tasks.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)