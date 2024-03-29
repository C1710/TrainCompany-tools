from __future__ import annotations

import csv
import json
import logging
from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any, TextIO, Generator, Iterator

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
        try:
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
        except UnicodeDecodeError as e:
            if self.encoding != "utf-8":
                self.encoding = "utf-8"
                logging.info("Reopening with UTF-8 encoding")
                return self.import_data(file_name)
            else:
                raise e
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


class WikipediaImporter(Importer[T], metaclass=ABCMeta):
    skip_first_entry: bool

    @abstractmethod
    def __init__(self,
                 skip_first_entry: bool = True):
        self.skip_first_entry = skip_first_entry

    @abstractmethod
    def deserialize(self, entry: List[str]) -> T | None:
        pass

    def import_data(self, file_name: str) -> List[T]:
        with open(file_name, encoding="utf-8") as input_file:
            entries = self.iter_table_entries(input_file)
            # We might want to discard a table header
            if self.skip_first_entry:
                next(entries)
            data = (self.deserialize(entry) for entry in entries)
            data = [entry for entry in data if entry is not None]
            return data

    def iter_table_entries(self, input_file: TextIO) -> Generator[List[str], None, None]:
        lines: Iterator[str] = iter(input_file)
        # We will ignore the first |- line
        next(lines)
        entry = []
        for line in lines:
            if line.strip() != "|-" and line.strip() != "|}":
                line = line.strip().lstrip("|").lstrip()
                entry.append(line)
            else:
                yield entry
                entry = []
