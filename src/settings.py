from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    # OpenAI
    llm_api_key: str
    llm_model: str = "openai/gpt-oss-20b:free"
    llm_api_base: str = "https://openrouter.ai/api/v1"

    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "kb_chunks"

    # RAG параметры
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    min_score: float = 0.5

    # Память диалога
    max_history_messages: int = 20

    # API URL для Streamlit
    api_url: str = "http://app:8000"

    # MLflow
    mlflow_tracking_uri: str = "http://mlflow:5000"
    mlflow_experiment_name: str = "onlineshoprag"

    # Embedding модель
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # Файлы данных
    context_html_file: str = "Context.html"
    scenario_json_file: str = "Scenario.json"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_prefix="ONLINESHOPRAG__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()

