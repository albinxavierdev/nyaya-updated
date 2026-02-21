from typing import List, ClassVar

from decouple import config
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", default="dev-secret-change-in-production")
    JWT_REFRESH_SECRET_KEY: str = config("JWT_REFRESH_SECRET_KEY", default="dev-refresh-secret-change-in-production")
    ALGORITHM: ClassVar[str] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    PROJECT_NAME: str = "NYAYANTAR"
    COOKIE_SECURE: bool = False

    MONGO_CONNECTION_STRING: str = config("MONGODB_URI", default="mongodb://localhost:27017")
    GOOGLE_CLIENT_ID: str = config("GOOGLE_CLIENT_ID", default="")
    GOOGLE_CLIENT_SECRET: str = config("GOOGLE_CLIENT_SECRET", default="")

    model_config = {"extra": "ignore"}


settings = Settings()
