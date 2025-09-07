from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Model names for embeddings and generation via Ollama
    ollama_embed_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.1:8b-instruct"

    # Retrieval configuration
    top_k: int = 12
    top_m: int = 6

    # Paths to knowledge base artifacts
    kb_index_path: str = "admin/index.faiss"
    kb_chunks_path: str = "admin/chunks.jsonl"

    # WhatsApp credentials
    whatsapp_verify_token: str = ""
    whatsapp_token: str = ""

    # Shared secret for admin endpoints
    admin_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
