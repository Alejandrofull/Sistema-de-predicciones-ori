import pandas as pd

class DataCleaner:
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result.columns = [str(c).strip().lower().replace(" ", "_") for c in result.columns]
        return result.drop_duplicates().reset_index(drop=True)
