import pandas as pd
from sklearn.preprocessing import StandardScaler

class NumericNormalizer:
    def fit_transform(self, df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
        result = df.copy()
        scaler = StandardScaler()
        result[columns] = scaler.fit_transform(result[columns])
        return result, scaler
