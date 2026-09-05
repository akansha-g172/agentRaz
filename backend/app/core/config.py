from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgentRaz"
    environment: str = "development"

    database_url: str

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    max_transaction_amount: float = 70000
    max_retry_attempts: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()