# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # change to True if you want SQL logs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Use scoped_session for thread safety in Flask
db_session = scoped_session(SessionLocal)

Base = declarative_base()


# For use in models and routes
def get_db():
    return db_session()
