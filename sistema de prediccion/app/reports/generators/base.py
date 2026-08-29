from abc import ABC, abstractmethod
from pathlib import Path


class BaseReportGenerator(ABC):
    @abstractmethod
    def generate(self, context: dict, destination: Path) -> Path:
        raise NotImplementedError
