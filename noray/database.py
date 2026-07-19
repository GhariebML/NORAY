import os
import psycopg2
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from noray.config import settings

def update_env_file(key: str, value: str):
    """Updates or adds a key-value pair in the .env file to persist configurations."""
    env_path = Path(".env")
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
            
    if not found:
        lines.append(f"{key}={value}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def is_port_open(host: str, port: str | int) -> bool:
    import socket
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except OSError:
        return False

def test_postgres_connection(port: str) -> bool:
    """Attempts to connect to Postgres on the specified port with configured credentials."""
    try:
        conn = psycopg2.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=port,
            dbname=settings.POSTGRES_DB,
            connect_timeout=3
        )
        conn.close()
        return True
    except psycopg2.Error:
        return False

def resolve_database_url() -> str:
    """
    Implements resilient database detection:
    1. Checks explicit DATABASE_URL.
    2. Tests native PostgreSQL on standard port (5432).
    3. Tests alternative Docker fallback port (5433) if 5432 is occupied by another Postgres.
    4. Falls back to SQLite if no Postgres is available.
    """
    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    # Priority 1: Configured Port
    if test_postgres_connection(settings.POSTGRES_PORT):
        print(f"[OK] Validated PostgreSQL connection on {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    
    # Priority 2: Fallback Docker Port (e.g. native Windows DB occupies 5432, we map Docker to 5433)
    fallback_port = "5433" if settings.POSTGRES_PORT == "5432" else "5432"
    if test_postgres_connection(fallback_port):
        print(f"[WARN] Port {settings.POSTGRES_PORT} occupied. Resolved to PostgreSQL on port {fallback_port}. Persisting...")
        update_env_file("POSTGRES_PORT", fallback_port)
        settings.POSTGRES_PORT = fallback_port # Update runtime settings
        return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{fallback_port}/{settings.POSTGRES_DB}"

    # Priority 3: SQLite fallback for dev
    from noray.config import PROJECT_ROOT
    sqlite_path = PROJECT_ROOT / "data" / "noray_fallback.db"
    print(f"[WARN] No PostgreSQL instances available. Falling back to SQLite at {sqlite_path}.")
    return f"sqlite:///{sqlite_path}"

# Resolve the URL and initialize engine
DATABASE_URL = resolve_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency to yield local database session and close after request completion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
