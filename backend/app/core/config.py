from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USER_NAME: str
    PASSWORD: str
    HOST: str
    PORT: str
    NAME: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()