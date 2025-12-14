from src.core.logging_config import get_logger
from src.models import ChatResponse
from src.core.memory import conversation_memory
from src.llm.client import get_llm
from src.llm.prompts import RAG_ANSWER_PROMPT
from src.rag.retriever import RAGRetriever
from src.scenario.runner import ScenarioRunner

logger = get_logger(__name__)


class SupportAgent:
    """Агент технической поддержки с RAG и сценариями."""

    def __init__(self, retriever: RAGRetriever) -> None:
        """
        Инициализирует агента поддержки.
        """
        self.retriever = retriever
        self.scenario_runner = ScenarioRunner()
        self.llm = get_llm()

    async def handle_message(self, conversation_id: str, message: str) -> ChatResponse:
        """
        Обрабатывает сообщение пользователя.

        Args:
            conversation_id: Идентификатор диалога
            message: Сообщение пользователя

        Returns:
            ChatResponse: Ответ агента
        """
        scenario_context = ""
        last_step_scenario = ""

        if conversation_memory.is_first_message(conversation_id):
            logger.info(f"Первый запрос для conversation_id={conversation_id}, запуск сценария")
            logger.info(f"Сообщение пользователя: {message}")
            try:
                scenario_context, last_step_scenario = self.scenario_runner.run(message)
                logger.info(f"Сценарий выполнен, last_step={last_step_scenario}")
            except Exception as e:
                logger.warning(f"Ошибка при выполнении сценария: {e}", exc_info=True)
                scenario_context = ""
                last_step_scenario = ""

        conversation_memory.add_message(conversation_id, "user", message)

        context, chunks = self.retriever.retrieve(message)
        history = conversation_memory.format_history(conversation_id)

        chain = RAG_ANSWER_PROMPT | self.llm
        response = chain.invoke(
            {
                "context": f"{scenario_context}\n\nКонтекст из базы знаний:\n{context}",
                "history": history,
                "question": message,
            }
        )
        answer = response.content

        conversation_memory.add_message(conversation_id, "assistant", answer)

        chunks_data = [
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "source": chunk["source"],
                "score": chunk["score"],
            }
            for chunk in chunks
        ]

        return ChatResponse(
            conversation_id=conversation_id,
            answer=answer,
            chunks=chunks_data,
            last_step_scenario=last_step_scenario,
        )

