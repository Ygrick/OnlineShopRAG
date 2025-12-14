from pathlib import Path
from typing import Any

from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from src.core.logging_config import get_logger
from src.settings import settings
from src.rag.chunking import parse_html, split_chunks

logger = get_logger(__name__)


class RAGRetriever:
    """Ретривер для поиска релевантных чанков с использованием Qdrant + BM25."""

    def __init__(self, documents: list[Document] | None = None) -> None:
        """
        Инициализирует ретривер с подключением к Qdrant и BM25.

        Args:
            documents: Список документов для BM25 ретривера. Если None, загружает из Qdrant.
        """
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection_name = settings.qdrant_collection_name

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_name,
            model_kwargs={"device": "cpu"},
        )

        # Проверяем существование коллекции и создаем если нет
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Коллекция {self.collection_name} существует")
        except Exception:
            logger.info(f"Коллекция {self.collection_name} не найдена, создаем пустую...")
            vector_size = len(self.embedding_model.embed_query("dimension probe"))
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Создана пустая коллекция {self.collection_name}")

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_model,
        )

        qdrant_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.top_k, "score_threshold": settings.min_score},
        )

        if documents is None:
            try:
                documents = self._load_documents_from_qdrant(self.vector_store)
            except Exception:
                documents = []

        if documents:
            bm25_retriever = BM25Retriever.from_documents(documents)
            bm25_retriever.k = settings.top_k

            self.retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, qdrant_retriever],
                weights=[0.4, 0.6],
            )
        else:
            self.retriever = qdrant_retriever

    def _load_documents_from_qdrant(self, vector_store: QdrantVectorStore) -> list[Document]:
        """
        Загружает документы из Qdrant для BM25 ретривера.

        Args:
            vector_store: QdrantVectorStore для загрузки документов

        Returns:
            list[Document]: Список документов из Qdrant
        """
        all_docs = vector_store.similarity_search("", k=10000)
        return all_docs

    def index_document(self, html_path: str) -> None:
        """
        Индексирует HTML документ в Qdrant.

        Args:
            html_path: Путь к HTML файлу для индексации
        """
        logger.info(f"Парсинг HTML файла: {html_path}")
        chunks = parse_html(html_path)
        logger.info(f"Извлечено {len(chunks)} статей")

        logger.info("Разбивка на чанки...")
        split_chunks_list = split_chunks(chunks)
        logger.info(f"Создано {len(split_chunks_list)} чанков")

        collection_name = self.collection_name

        try:
            collection_info = self.client.get_collection(collection_name)
            points_count = collection_info.points_count
            if points_count > 0:
                logger.info(f"Коллекция {collection_name} уже содержит {points_count} векторов, удаляем для переиндексации...")
            self.client.delete_collection(collection_name)
        except Exception:
            pass

        vector_size = len(self.embedding_model.embed_query("dimension probe"))
        logger.info(f"Создание коллекции {collection_name} с размером вектора {vector_size}...")
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

        logger.info("Преобразование в Langchain Document...")
        documents = []
        for chunk in split_chunks_list:
            doc = Document(
                page_content=chunk["text"],
                metadata={
                    "chunk_id": chunk["chunk_id"],
                    "source": chunk["source"],
                    "date": chunk["date"],
                },
            )
            documents.append(doc)

        logger.info("Загрузка документов в Qdrant через Langchain...")
        self.vector_store.add_documents(documents)
        logger.info(f"Успешно загружено {len(documents)} документов в Qdrant")

    def retrieve(self, query: str) -> tuple[str, list[dict[str, Any]]]:
        """
        Ищет релевантные чанки для запроса и форматирует их в контекст.

        Args:
            query: Текст запроса пользователя

        Returns:
            tuple: (отформатированный контекст, список чанков с метаданными)
        """
        docs = self.retriever.invoke(query)

        scores_map = {}
        try:
            results_with_scores = self.vector_store.similarity_search_with_score(query, k=settings.top_k * 2)
            for doc, score in results_with_scores:
                chunk_id = doc.metadata.get("chunk_id", "")
                if chunk_id:
                    scores_map[chunk_id] = float(score)
        except Exception:
            pass

        chunks = []
        for doc in docs:
            metadata = doc.metadata
            chunk_id = metadata.get("chunk_id", "")
            score = scores_map.get(chunk_id, metadata.get("score", 0.0))

            # Фильтрация по min_score
            if score >= settings.min_score:
                chunks.append(
                    {
                        "text": doc.page_content,
                        "chunk_id": chunk_id,
                        "source": metadata.get("source", ""),
                        "date": metadata.get("date", ""),
                        "score": score,
                    }
                )

        # Ограничиваем количество чанков до top_k
        chunks = chunks[:settings.top_k]

        if not chunks:
            context = ""
        else:
            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                context_parts.append(f"[{i}] {chunk['text']}")
            context = "\n\n".join(context_parts)

        return context, chunks
