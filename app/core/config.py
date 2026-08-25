from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hf_token: str = ""
    default_hf_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    sec_edgar_user_agent: str = "FinancialNewsResearcher/1.0 (admin@example.com)"
    sec_edgar_rate_limit_pause: float = 0.1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
