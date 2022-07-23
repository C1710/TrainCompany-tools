from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional, List, Iterable, Generator, Tuple, Set, Any, Dict, FrozenSet

# It will add all of them in that order if one is added
from geo import Location
from structures.country import Country, country_for_station, country_for_code, split_country

special_codes: Tuple[Tuple[str, ...], ...] = (
    ("EMSTP", "EMST"),
    ("BL", "BLS"),
    ("EBILP", "EBIL")
)

more_whitespace_re = re.compile(r'  +')


class _CodeList(List[str]):
    def append(self, __object: str):
        for code in expand_codes(__object):
            if code not in self:
                super().append(code)

    def extend(self, __iterable: Iterable[str]):
        for code in __iterable:
            self.append(code)


def expand_codes(base_code: str) -> Generator[str, None, None]:
    yield base_code
    if more_whitespace_re.search(base_code):
        base_code = more_whitespace_re.sub(' ', base_code)
        yield base_code
    if ' ' in base_code:
        base_code = base_code.split(' ')[0]
        yield base_code
    if base_code.isnumeric():
        # Replace UIC code prefix by country flag, if applicable
        country, code_without_country, _ = split_country(base_code)
        flag_code = country.flag + code_without_country
        yield flag_code
    for special in special_codes:
        if base_code in special:
            for other in special:
                if other != base_code:
                    yield other


def _without_duplicates(data: Iterable) -> List:
    result = []
    seen: Set = set()
    for item in data:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


class CodeTuple(Tuple[str]):
    def __add__(self, other):
        return CodeTuple(*self, *other)

    def __new__(cls, *args):
        if not len(args):
            return tuple.__new__(cls)
        return tuple.__new__(cls, _without_duplicates(
            (expanded_code for code in args for expanded_code in expand_codes(code))
        ))


def iter_stations_by_codes(stations: List[Station]) -> Generator[Tuple[str, Station], None, None]:
    max_index = max((len(station.codes) for station in stations)) - 1
    for index in range(0, max_index + 1):
        for station in stations:
            if len(station.codes) > index:
                yield station.codes[index], station


def iter_stations_by_codes_reverse(stations: List[Station]) -> Generator[Tuple[str, Station], None, None]:
    # We don't want to use -1 here, because we want to account for the length of the codes
    max_index = max((len(station.codes) for station in stations)) - 1
    for index in range(max_index, -1, -1):
        for station in stations:
            try:
                yield station.codes[index], station
            except IndexError:
                pass


@dataclass(frozen=True)
class Station:
    name: Optional[str] = field(default=None)
    # A station might have multiple codes like "UE P" and "UE"
    # or stations outside of Germany might use a different scheme
    codes: CodeTuple[str] = field(default_factory=CodeTuple)
    number: Optional[int] = field(default=None)
    location: Optional[Location] = field(default=None)
    locations_path: FrozenSet[PathLocation] = field(default_factory=frozenset)
    kind: Optional[str] = field(default=None)
    platforms: Tuple[Platform] = field(default_factory=tuple)
    station_category: Optional[int] = field(default=None)
    _group: Optional[int] = field(default=None)

    @property
    def group(self) -> int:
        if not self._group:
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
                    # Haltepunkt (unsichtbar)
                    return 5
            if self.kind and self.kind.lower() == 'abzw':
                # Abzweig
                return 4
            else:
                return 3
        else:
            return self._group

    @cached_property
    def platform_count(self) -> int:
        return len(self.platforms) if self.platforms is not None else 0

    @cached_property
    def platform_length(self) -> int:
        return max((platform.length for platform in self.platforms)) if self.platforms else 0

    @cached_property
    def country(self) -> Country:
        return country_for_station(self)


def merge_stations_on_first_code(stations: List[Station]) -> List[Station]:
    merged_stations: Dict[str, Station] = {}
    for station in stations:
        code = station.codes[0]
        if code in merged_stations:
            existing_station = merged_stations.pop(code)
            merged_stations.update({
                code: _merge_station(existing_station, station, 'codes')
            })
        else:
            merged_stations.update({code: station})
    return list(merged_stations.values())


def merge_stations(onto: List[Station],
                   new_data: List[Station],
                   on: str,
                   ignore_data_loss: bool = False) -> List[Station]:
    remaining_stations = set(onto)
    if not ignore_data_loss:
        assert_unique_first_code(onto)
        assert_unique_first_code(new_data)
    merged_stations = []
    if on != "codes":
        id_to_station = {station.__getattribute__(on): station for station in onto}
        id_to_wip: Dict[Any, Dict[str, Any]] = {}
        for new_station in new_data:
            key = new_station.__getattribute__(on)
            if key in id_to_station:
                # It's a match!
                # Move the station into the WIP state
                station = id_to_station.pop(key)
                remaining_stations.remove(station)
                id_to_wip[key] = station.__dict__.copy()
            if key in id_to_wip:
                # ...but only the next time.
                _merge_station_dicts_inplace(id_to_wip[key], new_station.__dict__.copy(), on)
            else:
                # New station
                merged_stations.append(new_station)
    else:
        id_to_station = {code: station for code, station in iter_stations_by_codes_reverse(onto)}
        id_to_wip: Dict[str, Dict[str, Any]] = {}
        for new_station in new_data:
            code_in_stations = False
            for code in new_station.codes:
                if code in id_to_station:
                    # Move the station into the WIP state
                    station = id_to_station.pop(code)
                    if station in remaining_stations:
                        remaining_stations.remove(station)
                        id_to_wip[code] = station.__dict__.copy()
                if code in id_to_wip:
                    # We won't have an else-branch here, because we only want the first code to be added in case
                    # the station is not existing at all
                    code_in_stations = True
                    _merge_station_dicts_inplace(id_to_wip[code], new_station.__dict__.copy(), on)
            if not code_in_stations:
                # It's completely new, add it to the list
                merged_stations.append(new_station)
    # Add old, unchanged values
    merged_stations.extend(remaining_stations)
    # And then the modified/new ones
    merged_stations.extend(set((Station(**new_station_data) for new_station_data in id_to_wip.values())))

    if not ignore_data_loss:
        assert len(merged_stations) >= len(onto), (len(merged_stations), len(onto))

    return merged_stations


def assert_unique_first_code(stations: List[Station]):
    first_codes = sorted([station.codes[0] for station in stations])
    for last_code, code in zip(first_codes, first_codes[1:]):
        assert last_code != code, code


def _merge_station(station: Station, new_station: Station, on: str) -> Station:
    result: Dict[str, Any] = station.__dict__.copy()
    _merge_station_dicts_inplace(result, new_station.__dict__.copy(), on)
    return Station(**result)


def _merge_station_dicts_inplace(station: Dict[str, Any], new_station: Dict[str, Any], on: str):
    """Merges one station onto another, in place (with Dicts as a temporary structure)"""
    for key, value in station.items():
        if key not in ['codes', 'location_path', 'platforms', on] and value is None:
            if value is None:
                station[key] = new_station[key]
        elif key == 'codes':
            station['codes'] += new_station['codes']
        elif key == 'platforms' and not station['platforms']:
            station['platforms'] = new_station['platforms']
        elif key == 'locations_path':
            station['locations_path'] = station['locations_path'].union(new_station['locations_path'])


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
    proj: Optional[bool | int] = None

    @staticmethod
    def from_station(station: Station, projection: int = 1) -> TcStation:
        x, y = station.location.to_projection(projection) if station.location else (0, 0)
        return TcStation(
            name=station.name,
            ril100=station.codes[0],
            group=station.group if station.group is not None else 2,
            x=x,
            y=y,
            platformLength=int(station.platform_length) if station.platform_length != 0 or station.platform_count != 0
                                                           or station.group in (0, 1, 2, 5) else None,
            platforms=station.platform_count if station.platform_count != 0 else None,
            forRandomTasks=None,
            proj=projection
        )


@dataclass(frozen=True)
class PathLocation:
    __slots__ = 'route_number', 'lfd_km'
    route_number: int
    lfd_km: StreckenKilometer


@dataclass(frozen=True)
class Platform:
    __slots__ = 'length', 'station'
    length: float
    # The station could be a station code, or a station number
    station: str | int


@dataclass(frozen=True)
class StreckenKilometer:
    lfd_km: float
    correction: float

    def __lt__(self, other: StreckenKilometer) -> bool:
        if self.lfd_km != other.lfd_km:
            return self.lfd_km < other.lfd_km
        else:
            return self.correction < other.correction

    def __eq__(self, other: StreckenKilometer) -> bool:
        return self.lfd_km == other.lfd_km and self.correction == other.correction

    def __le__(self, other: StreckenKilometer) -> bool:
        return self < other or self == other

    @staticmethod
    def from_str(km_str: str):
        if '+' in km_str:
            lfd_km, correction = km_str.split(' + ')
            return StreckenKilometer(
                lfd_km=float(lfd_km.replace(',', '.')),
                correction=float(correction.replace(',', '.'))
            )
        else:
            return StreckenKilometer(
                lfd_km=float(km_str.replace(',', '.')),
                correction=0
            )
