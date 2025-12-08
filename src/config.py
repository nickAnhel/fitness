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


class Settings(BaseSettings):
    db: DBSettings = Field(default_factory=DBSettings)  # type: ignore
    logging: LoggingConfig = Field(default_factory=LoggingConfig)  # type: ignore
    project: ProjectSettings = Field(default_factory=ProjectSettings)  # type: ignore


settings = Settings()
