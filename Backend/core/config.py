import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    # Database connection params for supabase
    db_user: str = os.getenv("user", "")
    db_password: str = os.getenv("password", "")
    db_host: str = os.getenv("host", "")
    db_port: int = int(os.getenv("port", ""))
    db_name: str = os.getenv("dbname", "")
    
    def __post_init__(self):
        if not all([self.db_user, self.db_password, self.db_host]):
            raise ValueError(
                "Database environment variables required: user, password, host"
            )


settings = Settings()


__all__ = ["settings"]

