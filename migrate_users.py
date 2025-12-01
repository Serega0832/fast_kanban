from sqlmodel import Session, SQLModel
from database import engine
from models import User # Убедись, что User импортирован, чтобы SQLModel о нем узнал

def create_users_table():
    print("Создаем таблицу пользователей...")
    SQLModel.metadata.create_all(engine)
    print("Готово!")

if __name__ == "__main__":
    create_users_table()