from sqlmodel import Session, text
from database import engine


def migrate_color():
    """
    Миграция для добавления поля color в таблицу Task.
    """
    print("🔄 Обновление структуры БД (добавление цветов)...")

    with Session(engine) as session:
        try:
            session.exec(text("SELECT color FROM task LIMIT 1"))
            print("✅ Колонка 'color' уже существует.")
        except Exception:
            print("⚠️ Колонка 'color' не найдена. Добавляем...")
            try:
                session.exec(text("ALTER TABLE task ADD COLUMN color VARCHAR"))
                session.commit()
                print("✅ Успешно! Поле 'color' добавлено.")
            except Exception as e:
                print(f"❌ Ошибка миграции: {e}")


if __name__ == "__main__":
    migrate_color()