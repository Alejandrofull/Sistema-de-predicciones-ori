import pandas as pd

class DataTypeValidator:
    def validate_numeric(self, df: pd.DataFrame, columns: list[str]) -> None:
        invalid = [c for c in columns if c in df.columns and not pd.api.types.is_numeric_dtype(df[c])]
        if invalid:
            raise ValueError(f"Columns must be numeric: {invalid}")
