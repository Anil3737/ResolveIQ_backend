# app/config.py

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv


load_dotenv()


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")  # Default MySQL port
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "resolveiq")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "resolveiq_secret")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    @property
    def DATABASE_URL(self) -> str:
        # MySQL connection string for SQLAlchemy with port support
        # Requires: pip install pymysql
        # URL-encode password to handle special characters like @, #, etc.
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{self.DB_USER}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
