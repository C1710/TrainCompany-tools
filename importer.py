from __future__ import annotations

import csv
import json
import logging
from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any

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


class JsonImporter(Importer[T], metaclass=ABCMeta):
    encoding: str
    top_level_entry: List[str]

    @abstractmethod
    def __init__(self,
                 top_level_entry: List[str] | str,
                 encoding: str = 'utf-8'):
        self.encoding = encoding
        if isinstance(top_level_entry, str):
            self.top_level_entry = [top_level_entry]
        else:
            self.top_level_entry = top_level_entry

    @abstractmethod
    def deserialize(self, entry: Any) -> Optional[T]:
        pass

    def import_data(self, file_name: str) -> List[T]:
        with open(file_name, encoding=self.encoding) as json_file:
            content = json.load(json_file)
            for entry in self.top_level_entry:
                content = content[entry]
            data = (self.deserialize(entry) for entry in content)
            data = [entry for entry in data if entry is not None]
        return data

