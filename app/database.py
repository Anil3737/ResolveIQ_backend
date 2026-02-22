# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from app.config import Config
from urllib.parse import quote_plus

# Build database URI if needed, but preferably use Config.SQLALCHEMY_DATABASE_URI
# However, this file seems to be used independently in some cases.
# Let's ensure it can access the database correctly.

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
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
