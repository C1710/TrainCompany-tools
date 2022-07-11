from dataclasses import dataclass
from typing import List, Optional, Tuple

from importer import CsvImporter
from structures.station import Location, Station


@dataclass(frozen=True)
class GeoWaypoint:
    distance_from_last_waypoint: int
    location: Location


class BrouterImporter (CsvImporter[GeoWaypoint]):
    def __init__(self):
        super().__init__(
            delimiter='\t',
            encoding='utf-8',
            skip_first_line=True
        )

    def deserialize(self, entry: List[str]) -> Optional[GeoWaypoint]:
        longitude = float(entry[0][:-6]) + float(entry[0][-6:]) * 0.000001
        latitude = float(entry[1][:-6]) + float(entry[1][-6:]) * 0.000001

        waypoint = GeoWaypoint(
            distance_from_last_waypoint=int(entry[3]),
            location=Location(
                longitude=longitude,
                latitude=latitude
            )
        )

        return waypoint


def which_stations(waypoints: List[GeoWaypoint], stations: List[Station]) -> List[Tuple[int, Station]]:
    """Returns the indices of the waypoints that are stations and the respective stations"""
    station_waypoints = []
    for station in stations:
        location = station.location
        for index, waypoint in enumerate(waypoints):
            if location.distance(waypoint.location) < 1.0:
                station_waypoints.append((index, station))
    assert len(dict(station_waypoints)) == len(station_waypoints), "Found multiple stations for one waypoint"
    return station_waypoints
