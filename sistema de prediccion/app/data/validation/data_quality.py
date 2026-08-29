import pandas as pd

class DataQualityAnalyzer:
    def report(self, df: pd.DataFrame) -> dict:
        return {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_values": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_by_column": {k: int(v) for k, v in df.isna().sum().to_dict().items()},
        }
