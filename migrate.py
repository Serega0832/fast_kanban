from sqlmodel import Session, text
from database import engine


def migrate_db():
    """
    Простая миграция для SQLite.
    Добавляет колонку owner_id в таблицу project.
    """
    print("🔄 Начинаем обновление базы данных...")

    with Session(engine) as session:
        try:
            # 1. Проверяем, есть ли уже такая колонка
            # Если этот запрос упадет, значит колонки нет
            session.exec(text("SELECT owner_id FROM project LIMIT 1"))
            print("✅ Колонка 'owner_id' уже существует. Миграция не требуется.")
        except Exception:
            print("⚠️ Колонка 'owner_id' не найдена. Добавляем...")
            try:
                # 2. Добавляем колонку средствами SQLite
                session.exec(text("ALTER TABLE project ADD COLUMN owner_id VARCHAR"))
                session.commit()
                print("✅ Успешно! Поле 'owner_id' добавлено в таблицу Project.")
            except Exception as e:
                print(f"❌ Ошибка при изменении таблицы: {e}")


if __name__ == "__main__":
    migrate_db()