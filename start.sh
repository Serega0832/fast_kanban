#!/bin/bash

# Создаем папку для базы данных, если её нет (важно для Volumes)
mkdir -p /app/data

# Применяем миграции (если нужно)
# python migrate.py
# python migrate_color.py
# python migrate_context.py
# python migrate_users.py

# Запускаем бота в фоновом режиме (& в конце)
python bot_run.py &

# Запускаем FastAPI через uvicorn на 8000 порту
# host 0.0.0.0 обязателен для Docker
uvicorn main:app --host 0.0.0.0 --port 8000