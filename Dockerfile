FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Устанавливаем необходимые зависимости
RUN apk update && apk add --no-cache \
    libpq \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    bash  # Для поддержки bash

# Обновление pip python
RUN pip install --upgrade pip

# Установка зависимостей проекта
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app

# Копирование проекта
COPY . .

# Настройка прав доступа
RUN chmod -R 777 ./

# Команда для запуска сервера Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "starkstore.wsgi:application"]