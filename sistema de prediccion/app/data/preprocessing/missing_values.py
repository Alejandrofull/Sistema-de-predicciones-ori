import pandas as pd

class MissingValueHandler:
    def apply(self, df: pd.DataFrame, strategy: str = "drop") -> pd.DataFrame:
        if strategy == "drop":
            return df.dropna().reset_index(drop=True)
        if strategy == "ffill":
            return df.ffill()
        if strategy == "bfill":
            return df.bfill()
        if strategy == "interpolate":
            return df.interpolate(numeric_only=True).ffill().bfill()
        raise ValueError(f"Unsupported missing-value strategy: {strategy}")
