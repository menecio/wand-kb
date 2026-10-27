from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Ollama configuration
    ollama_base_url: str = "http://ollama:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_generation_model: str = "qwen2.5:3b"

    # Qdrant configuration
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "knowledge_base"

    # Embedding model
    embedding_dimensions: int = 768

    # Chunking configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Upload storage
    upload_dir: str = "data/uploads"

    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
