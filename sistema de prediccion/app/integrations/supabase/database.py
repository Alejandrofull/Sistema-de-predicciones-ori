from sqlalchemy import create_engine, text

from app.config.settings import DATABASE_URL


db_url = DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql+psycopg2://"):
    db_url = db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

engine = create_engine(
    db_url,
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
