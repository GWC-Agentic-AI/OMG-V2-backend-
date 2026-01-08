from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    APP_DB: str = "omg-appcontrol-db"
    TEMPLE_DB: str = "omg-temple-db"
    AI_DB : str = "omg-ai-db"
    
    token_limit: int = 3500
    max_history_messages: int = 50
    pagination_default_limit: int = 30
    pagination_max_limit: int = 100
    
    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_temperature: float = 0.2
    openai_max_tokens: int = 800
    

settings = Settings()
