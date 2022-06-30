import logging
from typing import List

from importer import CsvImporter
from structures.route import CodeWaypoint, Route, Track, TrackKind


class DbTrassenfinderImporter(CsvImporter[CodeWaypoint]):
    def __init__(self):
        super().__init__(
            delimiter=';',
            encoding='cp1252',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> CodeWaypoint:
        waypoint = CodeWaypoint(
            distance_from_start=float(entry[0].replace(',', '.')),
            code=entry[2].replace('  ', ' '),
            is_stop='Kundenhalt' in entry[17],
            next_route_number=int(entry[3]) if entry[3] else None
        )
        return waypoint


def invalid_track(route_number: int) -> Track:
    logging.warning("Unbekannte Streckennr.: {}. Kann Elektrifizierung, Streckenart nicht identifizieren.".format(route_number))
    return Track(
        electrified=False,
        kind=TrackKind.UNKNOWN,
        length=0,
        route_number=route_number,
    )


def convert_waypoints_tracks_to_route(waypoints: List[CodeWaypoint], track_data: List[Track]) -> Route:
    route_number_to_track = {track.route_number: track for track in track_data}
    tracks_used = [route_number_to_track[waypoint.next_route_number]
                   if waypoint.next_route_number in route_number_to_track else invalid_track(waypoint.next_route_number)
                   for waypoint in waypoints if waypoint.next_route_number]
    return Route(
        waypoints,
        tracks_used
    )
