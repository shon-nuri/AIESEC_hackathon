from fastapi import FastAPI
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    USER_NAME: str
    PASSWORD: str
    HOST: str
    PORT: str
    NAME: str
    model_config = SettingsConfigDict(env_file=".env")

    @computed_field
    def DATABASE_URL(self) -> str:
        return (f'postgresql+asyncpg://{self.USER_NAME}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}')


settings = Settings()
    
