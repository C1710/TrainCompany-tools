from __future__ import annotations
from abc import ABCMeta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from tools.structures.station import PathLocation, Station


@dataclass
class Route:
    waypoints: List[CodeWaypoint]
    tracks: List[Track]


@dataclass
class TcRoute:
    stations: List[Station]
    path: TcPath

    @staticmethod
    def from_route(route: Route, station_data: List[Station]) -> TcRoute:
        code_to_station = {code: station for station in station_data for code in station.codes}
        station_data = [code_to_station[waypoint.code] for waypoint in route.waypoints if waypoint.is_stop]
        paths = TcPath.merge(TcPath.from_route(route))
        return TcRoute(station_data, paths)


@dataclass
class TcPath:
    start: Optional[str] = field(default=None)
    end: Optional[str] = field(default=None)
    name: Optional[str] = field(default=None)
    electrified: Optional[bool] = field(default=None)
    group: Optional[int] = field(default=None)
    length: Optional[int] = field(default=None)
    maxSpeed: Optional[int] = field(default=None)
    twistingFactor: Optional[float] = field(default=None)
    objects: Optional[List[TcPath]] = field(default=None)

    @staticmethod
    def from_route(route: Route) -> List[TcPath]:
        paths = []
        visited_waypoints: List[CodeWaypoint] = []
        visited_tracks: List[Track] = []
        for (waypoint_start, track, waypoint_end) in zip(route.waypoints, route.tracks, route.waypoints[1:]):
            waypoint_start: CodeWaypoint
            track: Track
            waypoint_end: CodeWaypoint

            visited_tracks.append(track)
            visited_waypoints.append(waypoint_start)

            if waypoint_end.is_stop:
                length = waypoint_end.distance_from_start - visited_waypoints[0].distance_from_start
                # Add a new path
                path = TcPath(
                    name=None,
                    start=visited_waypoints[0].code,
                    end=waypoint_end.code,
                    electrified=all((track.electrified for track in visited_tracks)),
                    group=max((track.kind.rank for track in visited_tracks)),
                    length=int(length),
                    maxSpeed=None,
                    twistingFactor=None,
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
        for attr in ['electrified', 'group', 'name']:
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


@dataclass
class Track:
    route_number: int
    electrified: bool
    kind: TrackKind
    length: float


class TrackKind(Enum):
    HAUPTBAHN = 0
    NEBENBAHN = 1
    SFS = 2

    @property
    def rank(self):
        if self == TrackKind.HAUPTBAHN:
            return 1
        if self == TrackKind.NEBENBAHN:
            return 0
        if self == TrackKind.SFS:
            return 2

    @staticmethod
    def from_speed_category(v_max: float, category: str) -> TrackKind:
        if category == "Nebenbahn":
            return TrackKind.NEBENBAHN
        elif category == "Hauptbahn":
            if v_max >= 250:
                return TrackKind.HAUPTBAHN
            else:
                return TrackKind.SFS
        else:
            raise NotImplementedError("Unsupported track category: {}".format(category))


@dataclass
class Waypoint(metaclass=ABCMeta):
    distance_from_start: float
    is_stop: bool
    next_route_number: Optional[int]


@dataclass
class CodeWaypoint(Waypoint):
    code: str


@dataclass
class PathLocationWaypoint(Waypoint):
    location: PathLocation

    def __init__(self, lfd_km: float, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.location = PathLocation(
            route_number=self.next_route_number,
            lfd_km=lfd_km
        )


