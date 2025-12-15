from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DBSettings(ConfigBase):
    host: str
    port: str
    name: str
    user: str
    password: str

    echo: bool = False

    model_config = SettingsConfigDict(env_prefix="db_")

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ProjectSettings(ConfigBase):
    title: str
    description: str
    version: str
    debug: bool
    session_secret: str = Field(default="change-me")

    model_config = SettingsConfigDict(env_prefix="project_")


class LoggingConfig(ConfigBase):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    model_config = SettingsConfigDict(env_prefix="logging_")


class MailSettings(ConfigBase):
    host: str = "localhost"
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_email: str = "no-reply@example.com"
    from_name: str = "Fitness Club"
    use_tls: bool = True
    use_ssl: bool = False
    enabled: bool = True

    model_config = SettingsConfigDict(env_prefix="mail_")


class CelerySettings(ConfigBase):
    broker_url: str = "redis://redis:6379/0"
    result_backend: str | None = None
    default_queue: str = "default"
    timezone: str = "UTC"

    model_config = SettingsConfigDict(env_prefix="celery_")


class Settings(BaseSettings):
    db: DBSettings = Field(default_factory=DBSettings)  # type: ignore
    logging: LoggingConfig = Field(default_factory=LoggingConfig)  # type: ignore
    project: ProjectSettings = Field(default_factory=ProjectSettings)  # type: ignore
    mail: MailSettings = Field(default_factory=MailSettings)  # type: ignore
    celery: CelerySettings = Field(default_factory=CelerySettings)  # type: ignore


settings = Settings()
