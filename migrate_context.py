from sqlmodel import Session, text
from database import engine


def migrate_context():
    """
    Миграция для добавления поля description в таблицу Project.
    """
    print("🔄 Обновление структуры БД (добавление контекста)...")

    with Session(engine) as session:
        try:
            # Проверяем, есть ли колонка
            session.exec(text("SELECT description FROM project LIMIT 1"))
            print("✅ Колонка 'description' уже существует.")
        except Exception:
            print("⚠️ Колонка 'description' не найдена. Добавляем...")
            try:
                # Добавляем колонку TEXT
                session.exec(text("ALTER TABLE project ADD COLUMN description TEXT"))
                session.commit()
                print("✅ Успешно! Поле 'description' добавлено.")
            except Exception as e:
                print(f"❌ Ошибка миграции: {e}")


if __name__ == "__main__":
    migrate_context()