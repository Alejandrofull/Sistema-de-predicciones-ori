import pandas as pd
from app.data.preprocessing.cleaner import DataCleaner
from app.data.preprocessing.date_parser import DateParser
from app.data.validation.column_validator import ColumnValidator
from app.data.validation.schema_validator import SchemaValidator

class PredictionTransformer:
    """Converts raw input into the canonical dataframe expected by feature engineering/models."""

    def prepare(self, df: pd.DataFrame, date_column: str, target_column: str) -> pd.DataFrame:
        df = DataCleaner().clean(df)
        date_column = date_column.strip().lower().replace(" ", "_")
        target_column = target_column.strip().lower().replace(" ", "_")
        ColumnValidator().ensure_unique_columns(df)
        SchemaValidator().validate_required_columns(df, [date_column, target_column])
        df = DateParser().parse(df, date_column)
        df[target_column] = pd.to_numeric(df[target_column], errors="raise")
        return df
