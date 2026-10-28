from dataclasses import dataclass
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str]


def get_settings() -> Settings:
    cors_origins = json.loads(os.environ["CORS_ORIGINS"])
    if not isinstance(cors_origins, list) or not all(isinstance(origin, str) for origin in cors_origins):
        raise ValueError("CORS_ORIGINS must be a JSON array of strings")
    return Settings(
        database_url=os.environ["DATABASE_URL"],
        cors_origins=cors_origins,
    )
