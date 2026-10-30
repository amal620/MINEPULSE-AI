from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "MINEPULSE AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite+aiosqlite:///./minepulse.db"

    MODEL_PROVIDER: str = "openrouter"
    OPENROUTER_API_KEY: str = ""
    MODEL_NAME: str = "openai/gpt-4o-mini"

    MAX_AGENT_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()