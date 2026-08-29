from typing import Any
import pandas as pd
from app.data.ingestion.loader_factory import LoaderFactory
from app.data.transformers.prediction_transformer import PredictionTransformer
from app.data.validation.data_quality import DataQualityAnalyzer

class ImportService:
    def load(self, source_type: str, source: Any, **kwargs) -> pd.DataFrame:
        return LoaderFactory.create(source_type).load(source, **kwargs)

    def prepare_for_prediction(self, df: pd.DataFrame, date_column: str, target_column: str) -> pd.DataFrame:
        return PredictionTransformer().prepare(df, date_column, target_column)

    def quality_report(self, df: pd.DataFrame) -> dict:
        return DataQualityAnalyzer().report(df)
