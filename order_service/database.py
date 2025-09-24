from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
import oracledb
import time
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


# Oracle Database connection
ORACLE_USER = os.getenv("ORACLE_USER", "your_username")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "your_password")
ORACLE_HOST = os.getenv("ORACLE_HOST", "localhost")
ORACLE_PORT = os.getenv("ORACLE_PORT", "1521")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "ORCL")

# Oracle connection string
ORACLE_CONNECTION_STRING = (
    f"{ORACLE_USER}/{ORACLE_PASSWORD}@{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"
)

# Connection retry settings
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds


def create_engine_with_retry():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            engine = create_engine(
                f"oracle+oracledb://{ORACLE_CONNECTION_STRING}",
                pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
                pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", 30)),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", 1800)),
                pool_pre_ping=True,  # Enable connection health checks
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1 FROM DUAL")
            logger.info("Successfully connected to Oracle database")
            return engine
        except SQLAlchemyError as e:
            retries += 1
            logger.warning(
                f"Failed to connect to Oracle database (attempt {retries}/{MAX_RETRIES}): {e}"
            )
            if retries >= MAX_RETRIES:
                logger.error(
                    "Max retries exceeded. Could not connect to Oracle database."
                )
                raise
            time.sleep(RETRY_DELAY * retries)  # Exponential backoff


engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()
