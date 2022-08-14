from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Set, Any

import geopy.distance
import gpxpy
import unidecode

import geo
from geo import Location
from geo.photon_advanced_reverse import PhotonAdvancedReverse
from importer import Importer
from structures.country import countries
from structures.route import CodeWaypoint
from structures.station import Station, CodeTuple


class BrouterImporterNew(Importer[CodeWaypoint]):
    stations: List[Station]
    name_to_station: Dict[str, Station]

    def __init__(self, station_data: List[Station]):
        self.stations = station_data
        self.name_to_station = {unidecode.unidecode(station.name.lower()): station for station in station_data}

    def import_data(self, file_name: str) -> List[CodeWaypoint]:
        with open(file_name, encoding='utf-8') as input_file:
            gpx = gpxpy.parse(input_file)

        stops = []
        # Step 1: Find the OSM railway stations for all waypoints
        geolocator = PhotonAdvancedReverse()
        for waypoint in gpx.waypoints:
            # Find stations close to the given waypoint location
            possible_stations: List[geopy.location.Location] | None = geolocator.reverse(
                geopy.Point(latitude=waypoint.latitude, longitude=waypoint.longitude),
                exactly_one=False,
                limit=6,
                query_string_filter='+'.join(["osm_value:stop", "osm_value:station", "osm_value:halt"])
            )
            if possible_stations is None:
                logging.error(f"No station found for location (lat={waypoint.latitude}, lon={waypoint.longitude})")
                logging.debug("On G/M: https://maps.google.com/maps/@{},{},17z/data=!3m1!1e3".format(
                    waypoint.latitude,
                    waypoint.longitude
                ))
                logging.debug("On OSM: https://openstreetmap.org/#map=17/{}/{}&layers=T".format(
                    waypoint.latitude,
                    waypoint.longitude
                ))
                logging.error("Ignoring station")
                continue

            # FIXME: Apply other normalizations as well
            possible_station_names = (unidecode.unidecode(station.raw['properties']['name'].lower())
                                      for station in possible_stations)
            possible_station_groups = [group_from_photon_response(station.raw['properties']) for station in
                                       possible_stations]
            # Is one of these names in our data set?
            for name in possible_station_names:
                if name in self.name_to_station:
                    # Remove it from the lookup table to prevent having the same station twice
                    station = self.name_to_station.pop(name)
                    # Add this location if necessary
                    if station.location is None:
                        station_dict = station.__dict__
                        station_dict.pop('location')
                        station = Station(
                            **station_dict,
                            location=Location(
                                latitude=waypoint.latitude,
                                longitude=waypoint.longitude
                            )
                        )
                        self.stations.append(station)
                    break
            else:
                logging.info("Couldn't find any of these stations: {}. Creating new one.".format(
                    [station.raw['properties']['name'] for station in possible_stations]
                ))
                # We create a new station because we can't find an existing one
                new_station = possible_stations[0]
                new_station_properties = possible_stations[0].raw['properties']

                country = countries[new_station_properties['countrycode']]
                # The new codes use the osm_id - Flag + O (for OpenStreetMaps) + osm_id
                code = f"{country.flag}O{new_station_properties['osm_id']}"
                # It might be longer than the limit...
                assert len(bytes(code, "utf-8")) <= 20

                # Assemble the station with all data we have
                station = Station(
                    name=new_station_properties['name'],
                    codes=CodeTuple(code),
                    # 69 is not a UIC country code
                    number=int("69" + str(new_station_properties['osm_id'])),
                    location=geo.Location(
                        latitude=new_station.latitude,
                        longitude=new_station.longitude
                    ),
                    _group=largest_group(possible_station_groups)

                )

                # Add to the data set (it should propagate to the original data set as well)
                self.stations.append(station)
                # We do not want to add it to the lookup table to ensure that we only have unique stations
            stops.append(station)

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
                    # We don't want to match the stop multiple times
                    stops.remove(stop)
                    break
        return code_waypoints


def group_from_photon_response(response: Dict[str, Any]) -> int:
    value = response['osm_value']
    if value == 'station':
        group = 2
    elif value == 'stop':
        group = 5
    elif value == 'halt':
        group = 5
    elif value == 'junction':
        group = 4
    else:
        group = -1
    return group


def largest_group(groups: List[int]) -> int:
    if 0 in groups:
        return 0
    if 1 in groups:
        return 1
    if 2 in groups:
        return 2
    if 5 in groups:
        return 5
    if 3 in groups:
        return 3
    if 6 in groups:
        return 6
    if 4 in groups:
        return 4
    else:
        return -1
