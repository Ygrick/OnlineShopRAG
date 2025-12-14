from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Модель запроса для POST /chat."""

    conversation_id: str = Field(..., description="Идентификатор диалога")
    message: str = Field(..., description="Сообщение пользователя")


class ChatResponse(BaseModel):
    """Модель ответа для POST /chat."""

    conversation_id: str = Field(..., description="Идентификатор диалога")
    answer: str = Field(..., description="Ответ агента")
    chunks: list[dict] = Field(default_factory=list, description="Найденные релевантные чанки")
    last_step_scenario: str = Field(default="", description="Последняя выполненная нода сценария")

