from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from sqlalchemy.exc import OperationalError
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database configuration from environment variables
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "protected-db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "protected_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "protected_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "protected_resource")

# Construct database URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"

# Create SQLAlchemy engine with retry logic
def create_engine_with_retry(max_retries=5, retry_interval=5):
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Successfully connected to the database")
            return engine
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to connect to database (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise

# Create engine with retry logic
engine = create_engine_with_retry()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 