from typing import List, Optional

from importer import CsvImporter
from structures.station import Platform


class ChPlatformsImporter (CsvImporter[Platform]):

    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[Platform]:
        platform = Platform(
            length=float(entry[6]),
            station=int(entry[13])
        ) if entry[6] and entry[13] else None
        return platform

# We can reuse the add_platforms_to_stations function
