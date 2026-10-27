from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_port: int = 8000
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    # Configurable decision cutoff (UTC) - documented assumption, not a hard rule
    decision_cutoff_hour_utc: int = 11

    class Config:
        env_file = ".env"


settings = Settings()
