import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from the Backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


DEFAULT_PORT = 8000


@dataclass(slots=True)
class Settings:
    # Database connection params (Supabase style)
    db_user: str = os.getenv("user", "")
    db_password: str = os.getenv("password", "")
    db_host: str = os.getenv("host", "")
    db_port: int = int(os.getenv("port", "5432"))
    db_name: str = os.getenv("dbname", "postgres")
    
    # App settings
    port: int = int(os.getenv("PORT", DEFAULT_PORT))
    
    def __post_init__(self):
        if not all([self.db_user, self.db_password, self.db_host]):
            raise ValueError(
                "Database environment variables required: user, password, host"
            )


settings = Settings()


__all__ = ["settings"]

