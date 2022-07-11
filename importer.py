import csv
import logging
from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')


class Importer(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def import_data(self, file_name: str) -> List[T]:
        pass


class CsvImporter(Importer[T], metaclass=ABCMeta):
    delimiter: str
    encoding: str
    skip_first_line: bool = True

    @abstractmethod
    def __init__(self,
                 delimiter: str = ';',
                 encoding: str = 'utf-8',
                 skip_first_line: bool = True):
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_first_line = skip_first_line

    def import_data(self, file_name: str) -> List[T]:
        with open(file_name, encoding=self.encoding) as csv_file:
            reader = csv.reader(csv_file, delimiter=self.delimiter)
            if self.skip_first_line:
                first_line = reader.__next__()
                if first_line[0] == "utf-8" and self.encoding != 'utf-8':
                    self.encoding = 'utf-8'
                    logging.info("Reopening with UTF-8 encoding")
                    return self.import_data(file_name)
            data = (self.deserialize(entry) for entry in reader)
            data = [entry for entry in data if entry is not None]
        return data

    @abstractmethod
    def deserialize(self, entry: List[str]) -> Optional[T]:
        pass
