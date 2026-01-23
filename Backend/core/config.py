import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

load_dotenv()


# Model provider types
ModelProvider = Literal["openai", "ace"]


@dataclass(slots=True)
class Settings:
    # Database connection params for supabase
    db_user: str = os.getenv("user", "")
    db_password: str = os.getenv("password", "")
    db_host: str = os.getenv("host", "")
    db_port: int = int(os.getenv("port", ""))
    db_name: str = os.getenv("dbname", "")
    
    # Supabase REST API (for RLS testing via PostgREST)
    supabase_url: str = os.getenv("SUPABASE_URL", "")  # e.g. https://xxxxx.supabase.co
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")  # anon key (NOT service role)
    
    # Chatbot / RAG settings (OpenAI-compatible API)
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    llm_endpoint: str = os.getenv("LLM_ENDPOINT", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    
    # Fine-tuned Ace model settings (HuggingFace)
    ace_model_name: str = os.getenv("ACE_MODEL_NAME", "khaled324/ace")
    ace_enabled: bool = os.getenv("ACE_ENABLED", "true").lower() == "true"
    
    # Default model for generation tasks
    default_generation_model: str = os.getenv("DEFAULT_GENERATION_MODEL", "openai")
    
    # ChromaDB settings
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "")
    
    # Embedding model (sentence-transformers)
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # File storage settings
    file_storage_dir: str = os.getenv("FILE_STORAGE_DIR", "./user_files")
    
    def __post_init__(self):
        if not all([self.db_user, self.db_password, self.db_host]):
            raise ValueError(
                "Database environment variables required: user, password, host"
            )


settings = Settings()


__all__ = ["settings"]

