# Используем легкий образ Python
FROM python:3.11-slim

# Отключаем создание .pyc файлов и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Устанавливаем системные зависимости (curl нужен для healthcheck, если понадобится)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# Даем права на выполнение скрипта запуска
RUN chmod +x start.sh

# Открываем порт
EXPOSE 8000

# Указываем, где будет лежать база данных (для переопределения в database.py)
ENV DB_PATH="/app/data/kanban.db"

# Запускаем скрипт
CMD ["./start.sh"]