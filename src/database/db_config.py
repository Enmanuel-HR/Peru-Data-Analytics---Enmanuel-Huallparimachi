from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from loguru import logger

# Default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///peru_analytics.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully at: {DATABASE_URL}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def get_db():
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
