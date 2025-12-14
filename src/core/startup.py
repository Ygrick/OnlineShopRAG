from pathlib import Path

from qdrant_client import QdrantClient

from src.core.logging_config import get_logger
from src.settings import settings
from src.rag.retriever import RAGRetriever

logger = get_logger(__name__)


def check_and_index_qdrant(retriever: RAGRetriever) -> None:
    """
    Проверяет наличие данных в Qdrant и индексирует при необходимости.
    """
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    try:
        collection_info = client.get_collection(settings.qdrant_collection_name)
        points_count = collection_info.points_count
        if points_count > 0:
            logger.info(f"Qdrant коллекция уже содержит {points_count} векторов, пропускаем индексацию")
            return
    except Exception:
        pass

    project_root = Path(__file__).parent.parent.parent
    html_path = project_root / settings.context_html_file

    if not html_path.exists():
        logger.warning(f"Файл {html_path} не найден, пропускаем индексацию")
        return

    logger.info("Начинаем индексацию документа в Qdrant...")
    try:
        retriever.index_document(str(html_path))
        logger.info("Индексация завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка при индексации: {e}", exc_info=True)

