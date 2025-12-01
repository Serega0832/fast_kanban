import os
from sqlmodel import SQLModel, Session, create_engine

# Считываем данные из .env (или переменных окружения сервера)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "kanban_db")

# Формируем строку подключения для MySQL (используем драйвер pymysql)
# Формат: mysql+pymysql://user:password@host:port/dbname
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем движок
# Важно: аргумент connect_args={"check_same_thread": False} нужен ТОЛЬКО для SQLite.
# Для MySQL мы его убираем.
# pool_pre_ping=True помогает восстанавливать соединение, если MySQL его разорвал (MySQL has gone away)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def create_db_and_tables():
    # Эта функция создаст таблицы в MySQL при запуске, если их нет
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session