from datetime import timedelta, datetime
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlmodel import Session, select
from database import get_session
from models import User
import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Страница входа (просто кнопка)
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Ссылка на бота с параметром start=login
    # Замени FastKanbanBot на имя своего бота!
    bot_link = f"https://t.me/{config.bot_name}?start=login"
    return templates.TemplateResponse("login.html", {"request": request, "bot_link": bot_link})


# Обработка Magic Link
@router.get("/auth/callback")
async def auth_callback(token: str, session: Session = Depends(get_session)):
    try:
        # 1. Декодируем токен (проверяем подпись SECRET_KEY)
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        telegram_id = payload.get("sub")
        username = payload.get("name")
        token_type = payload.get("type")

        if not telegram_id or token_type != "magic_link":
            raise HTTPException(status_code=400, detail="Invalid token")

        # 2. Ищем пользователя или создаем нового (Авторегистрация)
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            session.commit()

        # 3. Создаем долгоживущий Session Token (на 7 дней)
        access_token_expires = timedelta(days=7)
        expire = datetime.utcnow() + access_token_expires

        # В токен сессии кладем тоже telegram_id
        session_token = jwt.encode(
            {"sub": telegram_id, "exp": expire, "type": "access"},
            config.SECRET_KEY,
            algorithm=config.ALGORITHM
        )

        # 4. Редиректим на главную с кукой
        response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=f"Bearer {session_token}", httponly=True)
        return response

    except JWTError:
        raise HTTPException(status_code=400, detail="Token expired or invalid")