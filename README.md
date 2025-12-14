# OnlineShopRAG

AI-агент технической поддержки с RAG-системой на базе Qdrant, памятью диалогов и обработкой сценариев.

## Требования

- Python 3.12+
- Docker и Docker Compose
- uv (пакетный менеджер)

## Установка

1. Клонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и заполните переменные окружения:
   ```bash
   cp .env.example .env
   ```
   Обязательно укажите `ONLINESHOPRAG__LLM_API_KEY`

## Запуск через Docker Compose

1. Запустите сервисы:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. Дождитесь запуска всех сервисов:
   - **Qdrant** - векторная БД для хранения векторов (порт 6333)
   - **MLflow** - трекинг экспериментов и метрик (порт 5000)
   - **FastAPI** - REST API приложения (порт 8000)
   - **Streamlit** - веб-интерфейс чата (порт 8501)
   - **Dozzle** - просмотр логов всех контейнеров (порт 8080)

3. Откройте веб-интерфейсы сервисов:
   - **Streamlit** (чат с агентом): http://localhost:8501/
   - **FastAPI** (API документация): http://localhost:8000/docs
   - **Qdrant** (панель управления БД): http://localhost:6333/dashboard#/collections
   - **MLflow** (эксперименты и трассировка): http://localhost:5000/#/experiments/1/traces
   - **Dozzle** (логи контейнеров): http://localhost:8080/

## Сервисы

### Streamlit
Веб-интерфейс для общения с AI-агентом технической поддержки. Позволяет отправлять сообщения, просматривать историю диалога и создавать новые чаты.

### FastAPI
REST API приложения с автоматической документацией Swagger UI. Предоставляет эндпоинты для чата, проверки здоровья и интеграции с внешними системами.

### Qdrant
Векторная база данных для хранения и поиска эмбеддингов документов. Панель управления позволяет просматривать коллекции, точки данных и выполнять запросы.

### MLflow
Система трекинга экспериментов и метрик. Хранит логи вызовов LLM, время выполнения запросов и другую телеметрию для анализа работы агента.

### Dozzle
Веб-интерфейс для просмотра логов всех Docker контейнеров в реальном времени. Удобен для отладки и мониторинга работы сервисов.

**Примечание:** Приложение работает исключительно на CPU. Индексация документов может занять продолжительное время при первом запуске.

При первом запуске приложение автоматически проверит наличие данных в Qdrant и при необходимости проиндексирует документ, указанный в настройках `context_html_file`.

## Индексация документа

Индексация происходит автоматически при старте приложения через `lifespan`. Файл для индексации указывается в настройках `context_html_file` (по умолчанию `Context.html`).

Если нужно переиндексировать документ вручную:

```bash
docker-compose -f docker/docker-compose.yml exec app uv run python -c "from src.settings import settings; from src.rag.retriever import RAGRetriever; RAGRetriever().index_document(settings.context_html_file)"
```

Или локально (если установлены зависимости):

```bash
uv run python -c "from src.settings import settings; from src.rag.retriever import RAGRetriever; RAGRetriever().index_document(settings.context_html_file)"
```

## Использование

### Веб-интерфейс (Streamlit)

После запуска docker-compose откройте в браузере:
```
http://localhost:8501
```

В интерфейсе вы можете:
- Отправлять сообщения агенту поддержки
- Просматривать историю диалога
- Видеть найденные релевантные чанки из базы знаний
- Создавать новые диалоги

### REST API

#### POST /chat

Отправка сообщения в чат:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_1",
    "message": "Привет! Как снять деньги с карты?"
  }'
```

Пример ответа:

```json
{
  "conversation_id": "conv_1",
  "answer": "Антон, Чтобы снять деньги с карты, обратитесь в ближайшее отделение банка.",
  "chunks": [
    {
      "chunk_id": "1_0",
      "text": "...",
      "source": "...",
      "score": 0.85
    }
  ],
  "last_step_scenario": "6"
}
```

#### Проверка здоровья

```bash
curl http://localhost:8000/health
```

#### MLflow UI

Откройте в браузере для просмотра экспериментов и метрик:
```
http://localhost:5000
```

## Примеры использования

### Диалог 1: Обычный запрос

```bash
# Первое сообщение
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_1",
    "message": "Привет! Как снять деньги с карты?"
  }'

# Продолжение диалога
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_1",
    "message": "Спасибо!"
  }'
```

### Диалог 2: С днем рождения

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_2",
    "message": "Привет! Как снять деньги с карты? У меня кстати сегодня день рождения."
  }'
```

### Диалог 3: Разные conversation_id (изоляция контекста)

```bash
# Диалог A
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_a",
    "message": "Как проверить аннулированные чеки?"
  }'

# Диалог B (независимый от conv_a)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_b",
    "message": "Как добавить аватарку?"
  }'
```

## Структура проекта

```
OnlineShopRAG/
├── src/
│   ├── main.py              # Точка входа, FastAPI app
│   ├── streamlit_app.py     # Streamlit веб-интерфейс
│   ├── models.py            # Pydantic модели для API
│   ├── settings.py          # Конфигурация через Pydantic BaseSettings
│   ├── core/                # Ядро приложения (agent, memory, startup)
│   ├── rag/                 # RAG система (retriever с индексацией, chunking)
│   ├── scenario/            # Движок выполнения сценариев
│   └── llm/                 # LLM интеграция и промпты
├── docker/                  # Docker файлы
├── Context.html             # База знаний для индексации (настраивается в settings.py)
├── Scenario.json            # Сценарий "День рождения" (настраивается в settings.py)
└── README.md
```

## Особенности

- **RAG система**: Векторный поиск в Qdrant с гибридным поиском (BM25 + векторный) и фильтрацией по релевантности
- **Память диалога**: Langchain ConversationSummaryBufferMemory для хранения истории и контекста разговоров
- **Сценарии**: Выполнение JSON-сценариев с нодами text/tool/if/end и подстановкой переменных
- **Fallback**: Автоматическая эскалация при отсутствии релевантных результатов в базе знаний
- **CPU-first**: Приложение оптимизировано для работы на CPU без GPU зависимостей
