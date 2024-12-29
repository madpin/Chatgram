from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data.models import Base
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

# Database configuration (replace with your database details)
DATABASE_URL = "sqlite:///db/chatbot_v2.db"

try:
    import logfire

    logfire.configure()
    has_logfire = True
    logger.info("Logfire successfully configured")
except ImportError:
    has_logfire = False
    logger.warning("Logfire not available, continuing without it")

# Create a database engine
engine = create_engine(DATABASE_URL)
if has_logfire:
    logfire.instrument_sqlalchemy(engine=engine)
    logger.info("SQLAlchemy instrumented with Logfire")


def recreate_database():
    """Drops all tables and creates them again."""
    logger.warning("Recreating database - all data will be lost")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    logger.info("Database recreated successfully")


# Create all tables in the database if they do not exist
Base.metadata.create_all(engine)
logger.info("Database tables created/verified")

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.debug("Session factory created")


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    logger.debug("New database session created")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")


# Performance considerations:
# - The database engine is created once and reused for all database operations.
# - The `get_db` function provides a way to manage database sessions efficiently
#   using a context manager.
