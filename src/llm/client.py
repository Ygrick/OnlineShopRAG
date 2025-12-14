from langchain_openai import ChatOpenAI

from src.settings import settings


def get_llm() -> ChatOpenAI:
    """
    Создает и возвращает экземпляр ChatOpenAI.

    Returns:
        ChatOpenAI: Экземпляр LLM для генерации ответов
    """
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
        temperature=0.7,
    )

