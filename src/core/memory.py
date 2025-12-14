from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage

from src.settings import settings
from src.llm.client import get_llm


class ConversationMemory:
    """Управление памятью диалогов по conversation_id."""

    def __init__(self) -> None:
        """
        Инициализирует хранилище памяти диалогов.
        """
        self.memories: dict[str, ConversationSummaryBufferMemory] = {}
        self.llm = get_llm()

    def get_memory(self, conversation_id: str) -> ConversationSummaryBufferMemory:
        """
        Получает или создает память для conversation_id.

        Args:
            conversation_id: Идентификатор диалога

        Returns:
            ConversationSummaryBufferMemory: Объект памяти для диалога
        """
        if conversation_id not in self.memories:
            self.memories[conversation_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=settings.max_history_messages * 50,
                return_messages=True,
            )
        return self.memories[conversation_id]

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """
        Добавляет сообщение в память диалога.

        Args:
            conversation_id: Идентификатор диалога
            role: Роль отправителя ('user' или 'assistant')
            content: Текст сообщения
        """
        memory = self.get_memory(conversation_id)
        if role == "user":
            memory.chat_memory.add_user_message(content)
        else:
            memory.chat_memory.add_ai_message(content)

    def get_history(self, conversation_id: str) -> list[BaseMessage]:
        """
        Получает историю сообщений диалога.

        Args:
            conversation_id: Идентификатор диалога

        Returns:
            list[BaseMessage]: Список сообщений диалога
        """
        memory = self.get_memory(conversation_id)
        return memory.chat_memory.messages

    def get_summary(self, conversation_id: str) -> str:
        """
        Получает summary диалога.

        Args:
            conversation_id: Идентификатор диалога

        Returns:
            str: Резюме диалога
        """
        memory = self.get_memory(conversation_id)
        return memory.moving_summary_buffer or ""

    def format_history(self, conversation_id: str) -> str:
        """
        Форматирует историю диалога в строку для промпта.

        Args:
            conversation_id: Идентификатор диалога

        Returns:
            str: Отформатированная история диалога
        """
        messages = self.get_history(conversation_id)
        if not messages:
            return "Истории диалога нет."

        history_parts = []
        for msg in messages[-settings.max_history_messages :]:
            role = "Пользователь" if msg.type == "human" else "Агент"
            history_parts.append(f"{role}: {msg.content}")

        return "\n".join(history_parts)

    def is_first_message(self, conversation_id: str) -> bool:
        """
        Проверяет, является ли это первым сообщением в диалоге.

        Args:
            conversation_id: Идентификатор диалога

        Returns:
            bool: True если это первое сообщение
        """
        return conversation_id not in self.memories or len(self.get_history(conversation_id)) == 0


conversation_memory = ConversationMemory()

