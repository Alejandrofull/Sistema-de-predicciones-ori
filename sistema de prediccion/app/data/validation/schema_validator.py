import pandas as pd

class SchemaValidator:
    def validate_required_columns(self, df: pd.DataFrame, required: list[str]) -> None:
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
