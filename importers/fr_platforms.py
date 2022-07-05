from typing import Optional, List

from importer import CsvImporter
from structures.station import Platform


class FrPlatformsImporter (CsvImporter[Platform]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Platform]:
        platform = Platform(
            length=float(entry[7]),
            station=0
        )
        return platform
