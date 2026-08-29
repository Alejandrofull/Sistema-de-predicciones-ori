from pathlib import Path
from .api_loader import APILoader
from .csv_loader import CSVLoader
from .database_loader import DatabaseLoader
from .excel_loader import ExcelLoader
from .json_loader import JSONLoader
from .parquet_loader import ParquetLoader

class LoaderFactory:
    _by_format = {
        "csv": CSVLoader,
        "xlsx": ExcelLoader,
        "xls": ExcelLoader,
        "json": JSONLoader,
        "parquet": ParquetLoader,
        "database": DatabaseLoader,
        "api": APILoader,
    }

    @classmethod
    def create(cls, source_type: str):
        key = source_type.lower().lstrip(".")
        if key not in cls._by_format:
            raise ValueError(f"Unsupported source type: {source_type}")
        return cls._by_format[key]()

    @classmethod
    def from_filename(cls, filename: str):
        suffix = Path(filename).suffix.lower().lstrip(".")
        return cls.create(suffix)
