from sqlalchemy import create_engine, text

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
    pool_pre_ping=True
)


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user, NOW();")
        )

        row = result.fetchone()

        return {
            "database": row[0],
            "user": row[1],
            "server_time": str(row[2])
        }
