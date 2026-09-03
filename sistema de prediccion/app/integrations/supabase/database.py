from sqlalchemy import create_engine, text

from app.config.settings import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
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