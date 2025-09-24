from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import oracledb

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

engine = create_engine(
    f"oracle+oracledb://{ORACLE_CONNECTION_STRING}",
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
