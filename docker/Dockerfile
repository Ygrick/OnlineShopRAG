FROM python:3.12-slim

# Создание символических ссылок для python и pip
RUN ln -s /usr/bin/python3.12 /usr/bin/python

WORKDIR /app

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Копирование файлов зависимостей
COPY pyproject.toml uv.lock README.md ./

# Копирование кода приложения
COPY src/ ./src/

# Установка зависимостей
ENV UV_LINK_MODE=copy
RUN uv sync --frozen

# Запуск приложения
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

