from contextlib import asynccontextmanager

import mlflow
from fastapi import FastAPI, HTTPException

from src.core.logging_config import get_logger, setup_logging
from src.models import ChatRequest, ChatResponse
from src.core.agent import SupportAgent
from src.settings import settings
from src.core.startup import check_and_index_qdrant
from src.rag.retriever import RAGRetriever

setup_logging()
logger = get_logger(__name__)

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
mlflow.set_experiment(settings.mlflow_experiment_name)
mlflow.langchain.autolog()

logger.info("Инициализация приложения...")
retriever = RAGRetriever()
agent = SupportAgent(retriever)
logger.info("Приложение готово к работе")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    logger.info("Запуск приложения...")
    check_and_index_qdrant(retriever)
    yield
    logger.info("Остановка приложения...")


app = FastAPI(title="OnlineShopRAG API", version="0.1.0", lifespan=lifespan)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Проверка здоровья приложения."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Обрабатывает запрос пользователя в чат.

    Args:
        request: Запрос с conversation_id и message

    Returns:
        ChatResponse: Ответ агента с chunks и last_step_scenario
    """
    logger.info(f"Получен запрос от conversation_id={request.conversation_id}")
    try:
        response = await agent.handle_message(
            conversation_id=request.conversation_id,
            message=request.message,
        )
        logger.info(f"Ответ сформирован для conversation_id={request.conversation_id}, найдено {len(response.chunks)} чанков")
        return response
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

