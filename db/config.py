from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    APP_DB: str = "omg-appcontrol-db"
    TEMPLE_DB: str = "omg-temple-db"

settings = Settings()
