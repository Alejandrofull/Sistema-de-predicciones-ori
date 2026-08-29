import pandas as pd

class OutlierHandler:
    def clip_iqr(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        result = df.copy()
        for column in columns:
            if column not in result.columns:
                continue
            q1, q3 = result[column].quantile([0.25, 0.75])
            iqr = q3 - q1
            result[column] = result[column].clip(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        return result
