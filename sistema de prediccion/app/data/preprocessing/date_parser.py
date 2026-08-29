import pandas as pd

class DateParser:
    def parse(self, df: pd.DataFrame, date_column: str) -> pd.DataFrame:
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column], errors="raise")
        return result.sort_values(date_column).reset_index(drop=True)
