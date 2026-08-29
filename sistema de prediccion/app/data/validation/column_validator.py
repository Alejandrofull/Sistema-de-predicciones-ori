import pandas as pd

class ColumnValidator:
    def ensure_unique_columns(self, df: pd.DataFrame) -> None:
        duplicates = df.columns[df.columns.duplicated()].tolist()
        if duplicates:
            raise ValueError(f"Duplicate columns: {duplicates}")
