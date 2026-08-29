import pandas as pd
from sqlalchemy import create_engine


class DatabaseExporter:
    def export(self, data: pd.DataFrame, connection_url: str, table: str, if_exists: str = "append") -> int:
        engine = create_engine(connection_url)
        data.to_sql(table, engine, if_exists=if_exists, index=False)
        return len(data)
