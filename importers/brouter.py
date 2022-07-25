import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Set

import geopy.distance
import gpxpy

from geo import Location
from importer import Importer
from structures.route import CodeWaypoint
from structures.station import Station


class BrouterImporter(Importer[CodeWaypoint]):
    stations: List[Station]

    def __init__(self, station_data: List[Station]):
        self.stations = station_data

    def import_data(self, file_name: str) -> List[CodeWaypoint]:
        with open(file_name, encoding='utf-8') as input_file:
            gpx = gpxpy.parse(input_file)
        waypoint_locations = [(waypoint, Location(
            longitude=waypoint.longitude,
            latitude=waypoint.latitude)) for waypoint in gpx.waypoints]
        stops: List[Station] = [None for _ in range(len(waypoint_locations))]
        # First, we need to figure out the codes for the waypoints
        for station in self.stations:
            for index, waypoint, location in enumerate(waypoint_locations):
                if station.location.distance(location) < 0.08:
                    if stops[index]:
                        logging.warning("Multiple stations in the same location: {}, {}".format(
                            stops[index].codes[0],
                            station.codes[0]
                        ))
                    else:
                        stops[index] = station

        # Now we go through the file, accumulate distances and create the new waypoints
        distance_total = 0
        code_waypoints = []
        last_location: Optional[Location] = None
        for trackpoint in gpx.tracks[0].segments[0].points:
            location = Location(
                latitude=trackpoint.latitude,
                longitude=trackpoint.longitude
            )
            if last_location:
                distance_total += location.distance(last_location)
            # Check if we have a stop here
            for stop in stops:
                if stop.location.distance(location) < 0.08:
                    # We have a stop here - add the CodeWaypoint
                    code_waypoints.append(CodeWaypoint(
                        code=stop.codes[0],
                        distance_from_start=distance_total,
                        is_stop=True,
                        next_route_number=0
                    ))
        return code_waypoints
