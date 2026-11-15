"""Application settings loaded from environment variables and a local .env file."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration for IGNIS AI."""

    data_dir: Path = Path("data")
    retrieval_mode: Literal["bm25", "vector", "auto"] = "bm25"
    llm_provider: str = "openai_compatible"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_api_key: SecretStr = SecretStr("")
    llm_base_url: str | None = "https://api.groq.com/openai/v1"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    min_retrieval_score: float = Field(default=0.35, ge=0.0, le=1.0)
    demo_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    def require_live_config(self) -> None:
        """Raise a clear error if live (non-demo) mode is missing required settings."""
        if self.demo_mode:
            return
        missing = [
            name
            for name, value in {
                "LLM_PROVIDER": self.llm_provider,
                "LLM_MODEL": self.llm_model,
                "LLM_API_KEY": self.llm_api_key.get_secret_value(),
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")


settings = Settings()