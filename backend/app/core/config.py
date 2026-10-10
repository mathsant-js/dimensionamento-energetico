from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    def require_secret_key(self) -> str:
        secret = self.SECRET_KEY or ""
        if len(secret) < 32:
            raise RuntimeError(
                "SECRET_KEY deve ser configurada com pelo menos 32 caracteres"
            )
        return secret

settings = Settings()
