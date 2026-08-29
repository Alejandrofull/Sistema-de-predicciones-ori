import pandas as pd
from sqlalchemy import create_engine, text
from .base_loader import BaseLoader

class DatabaseLoader(BaseLoader):
    """Loads data from any SQLAlchemy-supported database."""

    def load(self, source: str, **kwargs) -> pd.DataFrame:
        query = kwargs.pop("query", None)
        table = kwargs.pop("table", None)
        if not query and not table:
            raise ValueError("Provide either 'query' or 'table'.")
        engine = create_engine(source)
        try:
            if query:
                with engine.connect() as connection:
                    return pd.read_sql(text(query), connection, **kwargs)
            return pd.read_sql_table(table, engine, **kwargs)
        finally:
            engine.dispose()
