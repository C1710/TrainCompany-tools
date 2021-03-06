import re
from typing import List, Tuple, Optional

from importer import CsvImporter
from structures.route import Track, TrackKind
from structures.station import StreckenKilometer


class DbStreckenImporter(CsvImporter[Track]):
    def __init__(self):
        super().__init__(
            delimiter=',',
            encoding='cp1252',
            skip_first_line=False
        )

    def deserialize(self, entry: List[str]) -> Optional[Track]:
        v_max = convert_min_max_speed(entry[10])[1]
        track = Track(
            route_number=int(entry[1]),
            length=float(entry[3]),
            electrified=entry[8] != 'nicht elektrifiziert',
            kind=TrackKind.from_speed_category(v_max, entry[13]),
            # Make we can sort the tracks later on
            from_km=min(StreckenKilometer.from_str(entry[6]), StreckenKilometer.from_str(entry[7])),
            to_km=max(StreckenKilometer.from_str(entry[7]), StreckenKilometer.from_str(entry[7]))
        )
        # Don't add Gegengleis
        return track if int(entry[2]) != 2 else None


speed_re = re.compile(r"(ab (\d+) )?bis (\d+) km/h")


def convert_min_max_speed(speed_str: str) -> Tuple[int, int]:
    match = speed_re.search(speed_str)
    if match is not None:
        v_from = match.group(2)
        v_to = int(match.group(3))
        if v_from is None:
            v_from = 0
        else:
            v_from = int(v_from)
        return v_from, v_to
    return 0, 0
