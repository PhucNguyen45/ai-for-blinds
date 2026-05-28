from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-3.0-pro"
    max_image_mb: int = 10
    request_timeout_s: int = 60
    allowed_origins: str = "*"


settings = Settings()
