from __future__ import annotations

import logging
from abc import ABCMeta
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import List, Optional, Dict, Any, Tuple, Set

from structures.country import germany, country_for_code
from structures.station import Station, iter_stations_by_codes_reverse, CodeTuple, StreckenKilometer
from geo import Location


@dataclass(frozen=True)
class Route:
    waypoints: List[CodeWaypoint]
    tracks: List[Tuple[Track, ...]]


@dataclass(frozen=True)
class Path:
    route_numer: int
    tracks: Tuple[Track]


def merge_tracks(tracks: List[Track]) -> List[Path]:
    route_number_to_tracks: Dict[int, Set[Track]] = {}
    for track in tracks:
        if track.route_number not in route_number_to_tracks:
            route_number_to_tracks[track.route_number] = set()
        route_number_to_tracks[track.route_number].add(track)
    # Sorting the segments makes it easier later on
    for tracks in route_number_to_tracks.values():
        tracks = list(tracks)
        tracks.sort(key=lambda track: track.from_km)
        # Check for duplicates
        for (track, next_track) in zip(tracks, tracks[1:]):
            assert track.from_km != next_track.from_km, (track, next_track)
    return [
        Path(
            route_numer=route_number,
            tracks=tuple(tracks)
        ) for route_number, tracks in route_number_to_tracks.items()
    ]


def invalid_station(code: str) -> Station:
    logging.warning("Unbekannter Haltepunkt: {}. Kann keine automatischen Daten hinzufügen.".format(code))
    station = Station(
        codes=CodeTuple(code)
    )
    return station


@dataclass
class TcRoute:
    stations: List[Station]
    path: TcPath

    @staticmethod
    def from_route(route: Route, station_data: List[Station],
                   add_annotations: bool = False) -> TcRoute:
        # Because we add the last (i.e. least precise) codes first, the "better" ones will override them at the end
        code_to_station = {code: station for code, station in iter_stations_by_codes_reverse(station_data)}
        stations = [code_to_station[waypoint.code] if waypoint.code in code_to_station else invalid_station(waypoint.code)
                    for waypoint in route.waypoints if waypoint.is_stop]
        paths = TcPath.merge(TcPath.from_route(route, add_annotations=add_annotations, code_to_station=code_to_station))
        return TcRoute(stations, paths)


@dataclass
class TcPath:
    start: Optional[str] = field(default=None)
    start_long: Optional[str] = field(default=None)
    end: Optional[str] = field(default=None)
    end_long: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    electrified: Optional[bool] = field(default=None)
    group: Optional[int] = field(default=None)
    length: Optional[int] = field(default=None)
    maxSpeed: Optional[int] = field(default=None)
    twistingFactor: Optional[float] = field(default=None)
    neededEquipments: Optional[List[str]] = field(default=None)
    objects: Optional[List[TcPath] | List[Dict[str, Any]]] = field(default=None)

    @staticmethod
    def from_route(route: Route,
                   add_annotations: bool = False,
                   code_to_station: Optional[Dict[str, Station]] = None) -> List[TcPath]:
        paths = []
        if add_annotations:
            assert code_to_station is not None
        visited_waypoints: List[CodeWaypoint] = []
        visited_tracks: List[Track] = []
        for (waypoint_start, tracks, waypoint_end) in zip(route.waypoints, route.tracks, route.waypoints[1:]):
            waypoint_start: CodeWaypoint
            tracks: Tuple[Track]
            waypoint_end: CodeWaypoint

            visited_tracks.extend(tracks)
            visited_waypoints.append(waypoint_start)

            if waypoint_end.is_stop:
                length = waypoint_end.distance_from_start - visited_waypoints[0].distance_from_start
                visited_countries: Set = set()
                visited_countries.update({country_for_code(waypoint.code)[0] for waypoint in visited_waypoints})
                visited_countries.add(country_for_code(waypoint_end.code)[0])
                needed_countries = [country.iso_3166 for country in visited_countries]
                if not add_annotations:
                    # Add a new path
                    path = TcPath(
                        name=None,
                        start=visited_waypoints[0].code,
                        end=waypoint_end.code,
                        electrified=all((track.electrified for track in visited_tracks)),
                        group=max(visited_tracks, key=lambda track: track.kind.rank).kind.value,
                        length=int(length),
                        maxSpeed=None,
                        twistingFactor=None,
                        neededEquipments=needed_countries if needed_countries else None,
                        objects=None
                    )
                else:
                    start_code = visited_waypoints[0].code
                    end_code = waypoint_end.code
                    path = TcPath(
                        name=None,
                        start=start_code,
                        start_long=code_to_station[start_code].name if start_code in code_to_station else '',
                        end=end_code,
                        end_long=code_to_station[end_code].name if end_code in code_to_station else '',
                        electrified=all((track.electrified for track in visited_tracks)),
                        group=max(visited_tracks, key=lambda track: track.kind.rank).kind.value,
                        length=int(length),
                        maxSpeed=None,
                        twistingFactor=None,
                        neededEquipments=needed_countries if needed_countries else None,
                        objects=None
                    )
                paths.append(path)
                # We will add this one the next time anyway
                visited_waypoints = []
                visited_tracks = []
        return paths

    @staticmethod
    def merge(paths: List[TcPath]) -> TcPath:
        main_path = TcPath(
            maxSpeed=0,
            twistingFactor=0
        )
        for attr in paths[0].__dict__.keys():
            base = paths[0].__getattribute__(attr)
            if all((path.__getattribute__(attr) == base for path in paths)):
                # Add to the main path if not None
                if base is not None:
                    main_path.__setattr__(attr, base)
                # Remove from the subpaths
                for path in paths:
                    path.__setattr__(attr, None)
        main_path.objects = paths
        return main_path

    def to_dict(self) -> Dict[str, Any]:
        data = {key: value for key, value in self.__dict__.items() if value is not None}
        try:
            data['objects'] = [path.to_dict() for path in data['objects']]
        except KeyError:
            pass
        return data


@dataclass(frozen=True)
class Track:
    route_number: int
    electrified: bool
    kind: TrackKind
    length: float
    from_km: Optional[StreckenKilometer] = field(default=None)
    to_km: Optional[StreckenKilometer] = field(default=None)


class TrackKind(Enum):
    HAUPTBAHN = 0
    NEBENBAHN = 1
    SFS = 2
    UNKNOWN = -1

    @property
    def rank(self):
        if self == TrackKind.HAUPTBAHN:
            return 1
        if self == TrackKind.NEBENBAHN:
            return 0
        if self == TrackKind.SFS:
            return 2
        if self == TrackKind.UNKNOWN:
            return -1

    def __lt__(self, other):
        return self.rank < other.rank

    @staticmethod
    def from_speed_category(v_max: float, category: str) -> TrackKind:
        if category == "Nebenbahn":
            return TrackKind.NEBENBAHN
        elif category == "Hauptbahn":
            if v_max >= 250:
                return TrackKind.SFS
            else:
                return TrackKind.HAUPTBAHN
        else:
            return TrackKind.UNKNOWN


@dataclass(frozen=True)
class Waypoint(metaclass=ABCMeta):
    distance_from_start: float
    is_stop: bool
    next_route_number: Optional[int]


@dataclass(frozen=True)
class CodeWaypoint(Waypoint):
    code: str
