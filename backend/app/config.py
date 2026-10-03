from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_name: str = "NutriAI"

    database_url: str = "sqlite+aiosqlite:///./nutriai.db"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Stored as a CSV string so .env parsing stays straightforward across all
    # pydantic-settings versions. Use the `cors_origins` property to read it.
    cors_origins_raw: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_client_secret: str = ""

    azure_storage_connection_string: str = ""
    azure_storage_container: str = "meal-images"

    # AI provider — mock | github | qwen25vl | yolov8 | florence2 | smolvlm
    ai_provider: str = "mock"

    # GitHub Models (real vision). Token is a GitHub PAT with models:read scope.
    github_token: str = ""
    ai_vision_model: str = "gpt-4o"
    ai_vision_endpoint: str = "https://models.github.ai/inference"

    # USDA FoodData Central — real nutrition fallback. Free key:
    # https://fdc.nal.usda.gov/api-key-signup
    usda_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
