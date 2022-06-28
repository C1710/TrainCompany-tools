from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Iterable


# It will add all of them in that order if one is added
special_codes: List[List[str]] = [
    ["EMSTP", "EMST"]
]


class CodeList (List[str]):
    def append(self, __object: str):
        if __object not in self:
            super().append(__object)
            if '  ' in __object:
                __object = __object.replace('  ', ' ')
                if __object not in self:
                    super().append(__object)
            if ' ' in __object:
                __object = __object.split(' ')[0]
                if __object not in self:
                    super().append(__object)
        for special in special_codes:
            if __object in special:
                for other in special:
                    if other != __object:
                        super().append(other)

    def extend(self, __iterable: Iterable[str]):
        for code in __iterable:
            self.append(code)


@dataclass
class Station:
    name: Optional[str] = field(default=None)
    # A station might have multiple codes like "UE P" and "UE"
    # or stations outside of Germany might use a diffferent scheme
    _codes: CodeList[str] = field(default_factory=CodeList)
    number: Optional[int] = field(default=None)
    location: Optional[Location] = field(default=None)
    location_path: Optional[PathLocation] = field(default=None)
    kind: Optional[str] = field(default=None)
    platforms: List[Platform] = field(default_factory=list)
    station_category: Optional[int] = field(default=None)

    @property
    def group(self) -> int:
        if self.station_category is not None:
            if 1 <= self.station_category <= 2:
                # Knotenbahnhof
                return 0
            if self.station_category == 3:
                # Hauptbahnhof
                return 1
            if 4 <= self.station_category < 7:
                # Nebenbahnhof
                return 2
            if self.station_category == 7:
                # Haltepunkt (unsichtbar
                return 5
        if self.kind and self.kind.lower() == 'abzw':
            # Abzweig
            return 4
        else:
            return 3

    @property
    def platform_count(self) -> int:
        return len(self.platforms) if self.platforms is not None else 0

    @property
    def platform_length(self) -> int:
        return max((platform.length for platform in self.platforms)) if self.platforms else 0

    @property
    def codes(self):
        return self._codes


def merge_stations(onto: List[Station],
                   new_data: List[Station],
                   on: str):
    id_to_station = {station.__getattribute__(on): station for station in onto}
    for new_station in new_data:
        try:
            station = id_to_station[new_station.__getattribute__(on)]
            if on != 'name' and station.name is None:
                station.name = new_station.name
            if on != 'number' and station.number is None:
                station.number = new_station.number
            if on != 'station_category' and station.station_category is None:
                station.station_category = new_station.station_category
            if on != 'location' and station.location is None:
                station.location = new_station.location
            if on != 'location_path' and station.location_path is None:
                station.location_path = new_station.location_path
            if on != 'platforms' and station.platforms is None:
                station.platforms = new_station.platforms
            if on != 'kind' and station.kind is None:
                station.kind = new_station.kind
            station.codes.extend(new_station.codes)
        except KeyError:
            # Not in the list (yet)
            onto.append(new_station)


@dataclass
class TcStation:
    name: str
    ril100: str
    group: int
    x: int
    y: int
    platformLength: Optional[int]
    platforms: Optional[int]
    forRandomTasks: Optional[bool]

    @staticmethod
    def from_station(station: Station) -> TcStation:
        x, y = station.location.convert_to_tc() if station.location else (0, 0)
        return TcStation(
            name=station.name,
            ril100=station.codes[0],
            group=station.group if station.group is not None else 2,
            x=x,
            y=y,
            platformLength=int(station.platform_length),
            platforms=station.platform_count,
            forRandomTasks=None
        )


origin_x: float = 6.482451
origin_y: float = 51.766433
scale_x: float = 625.0 / (11.082989 - origin_x)
scale_y: float = 385.0 / (49.445616 - origin_y)


@dataclass
class Location:
    __slots__ = 'latitude', 'longitude'
    latitude: float
    longitude: float

    def convert_to_tc(self) -> (int, int):
        x = int((self.longitude - origin_x) * scale_x)
        y = int((self.latitude - origin_y) * scale_y)
        return x, y


@dataclass
class PathLocation:
    __slots__ = 'route_number', 'lfd_km'
    route_number: int
    lfd_km: float


@dataclass
class Platform:
    __slots__ = 'length', 'station'
    length: float
    # The station could be a station code, a station number, or simply a station object
    station: str | int | Station
