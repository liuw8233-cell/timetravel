from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key-please-change"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天

    # 邮件
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "时空胶囊"

    # 默认AI
    DEFAULT_AI_PROVIDER: str = "openai"
    DEFAULT_AI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_AI_API_KEY: str = ""
    DEFAULT_AI_MODEL: str = "gpt-4o-mini"

    # 内容审核
    CONTENT_REVIEW_ENABLED: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
