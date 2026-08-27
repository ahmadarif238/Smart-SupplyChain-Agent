"""Database engine setup.

Hardened (2026-08):

  * `create_engine(DATABASE_URL)` ran at import time with no guard. If the env
    var was unset it raised `TypeError` on `None`; the committed value pointed
    at `localhost:5432`, which does not exist on Vercel/Hugging Face, so the
    deployed app could never start.
  * `connect_args={"sslmode": "require"}` is psycopg2-only and raises on SQLite,
    so it is now applied only to Postgres URLs.
  * The URL is probed once and falls back to a local SQLite file when Postgres
    is unset or unreachable, so the service always boots and always serves.

Set DATABASE_URL to a live Postgres instance to get shared persistence back.
"""

import os
import re
import tempfile
import urllib.parse
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # Crucial for Supabase transaction pooling

load_dotenv()


def _normalise(url: str) -> str:
    """Make a hand-pasted Postgres URL safe to parse."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # `user:[YOUR-PASSWORD]@host` and raw #/&/@ in a password both make the URL
    # unparseable. Strip the placeholder brackets and percent-encode.
    m = re.match(r"^(?P<scheme>[a-z+]+://)(?P<user>[^:/@]+):(?P<pw>.*)@(?P<rest>[^@]+)$", url)
    if m:
        pw = m.group("pw")
        if pw.startswith("[") and pw.endswith("]"):
            pw = pw[1:-1]
        pw = urllib.parse.quote(urllib.parse.unquote(pw), safe="")
        url = f"{m.group('scheme')}{m.group('user')}:{pw}@{m.group('rest')}"
    return url


def _sqlite_fallback() -> str:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    local = os.path.join(root, "supplychain.db")
    try:
        with open(local, "a"):
            pass
        return f"sqlite:///{local}"
    except OSError:
        # Serverless hosts only allow writes under /tmp.
        return f"sqlite:///{os.path.join(tempfile.gettempdir(), 'supplychain.db')}"


def _make_engine(url: str):
    if url.startswith("sqlite"):
        # NullPool/sslmode are Postgres concerns; check_same_thread is SQLite-only.
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(
        url,
        poolclass=NullPool,
        connect_args={"sslmode": "require", "connect_timeout": 10},
    )


_configured = (os.getenv("DATABASE_URL") or "").strip().strip('"')
USING_FALLBACK = False

if not _configured:
    print("WARNING: DATABASE_URL not set - using local SQLite.")
    DATABASE_URL, USING_FALLBACK = _sqlite_fallback(), True
else:
    DATABASE_URL = _normalise(_configured)
    try:
        with _make_engine(DATABASE_URL).connect():
            pass
    except Exception as exc:  # noqa: BLE001 - any failure means "fall back"
        print(f"WARNING: DATABASE_URL unreachable ({type(exc).__name__}: {exc}). "
              f"Falling back to local SQLite so the app can still start.")
        DATABASE_URL, USING_FALLBACK = _sqlite_fallback(), True

engine = _make_engine(DATABASE_URL)

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
