from datetime import datetime, timedelta
from sqlmodel import Session, select
from jose import jwt
import config
from database import engine
from models import Project, Column


def get_db_session():
    """Создает и возвращает сессию базы данных."""
    return Session(engine)


def create_login_token(telegram_id: int, username: str) -> str:
    """Генерирует короткоживущий токен (5 минут) для Magic Link."""
    expire = datetime.utcnow() + timedelta(minutes=5)
    to_encode = {
        "sub": str(telegram_id),
        "name": username,
        "type": "magic_link",
        "exp": expire
    }
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def get_user_projects(telegram_id: int):
    """Возвращает проекты пользователя + общие проекты (если админ)."""
    with get_db_session() as session:
        # Личные проекты
        stmt = select(Project).where(Project.owner_id == str(telegram_id))
        user_projects = session.exec(stmt).all()

        # Если админ, добавляем проекты без владельца (старые/общие)
        if str(telegram_id) == str(config.ADMIN_TG_ID):
            stmt_admin = select(Project).where(Project.owner_id == None)
            admin_projects = session.exec(stmt_admin).all()
            return user_projects + admin_projects

        return user_projects