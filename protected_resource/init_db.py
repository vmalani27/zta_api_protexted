import logging
from app.db.session import engine
from app.db.base import Base
from app.models.models import User, Student, Teacher, Hostel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    logger.info("Creating initial database tables")
    init_db()
    logger.info("Initial database tables created") 