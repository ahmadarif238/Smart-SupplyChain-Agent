from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # <--- Crucial for Transaction Pooling
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# For Supabase Transaction Pooler (Port 6543):
# 1. Use NullPool to let Supavisor handle the pooling.
# 2. Add connect_args to ensure SSL is used.
engine = create_engine(
    DATABASE_URL, 
    poolclass=NullPool,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions to ensure they are closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
