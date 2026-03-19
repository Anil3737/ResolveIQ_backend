import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env file
# python-dotenv automatically searches from the current working directory
# upward — works on any machine: local, AWS, Render, Railway, etc.
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
    
    # Build database URI from environment variables
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306") # Default XAMPP MySQL port
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "resolveiq")
    
    # URL encode password for SQLAlchemy to handle special characters like '@'
    # Fixed to use mysql+pymysql to match requirements.txt
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pooling and stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 10,
        "max_overflow": 20,
        "connect_args": {
            "connect_timeout": 10
        }
    }
    
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET", "jwt_secret_key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get("JWT_EXPIRE_MINUTES", "60")))
