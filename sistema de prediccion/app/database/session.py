from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import DATABASE_URL


def _normalize_db_url(url: str) -> str:
    """Fuerza el driver psycopg 3 (el que está en requirements.txt)."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(
    _normalize_db_url(DATABASE_URL),
    pool_pre_ping=True,
    # Descomenta la siguiente línea solo si usas el pooler de Supabase
    # (puerto 6543) y te sale el error "prepared statement already exists":
    # connect_args={"prepare_threshold": None},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
