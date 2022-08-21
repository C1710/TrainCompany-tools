from __future__ import annotations

import logging
import re
from collections import Counter
from functools import lru_cache

import statistics
from typing import List, Tuple, Dict, Any

import geopy.distance
import gpxpy
import unidecode
from geopy.extra.rate_limiter import RateLimiter
from gpxpy.gpx import GPXTrackPoint
from networkx.utils import pairwise

import geo
from geo import Location, overpass
from geo.overpass import query_rail_around_gpx, request_overpass, douglas_peucker, create_query
from geo.photon_advanced_reverse import PhotonAdvancedReverse
from structures.country import countries
from structures.route import TcPath, TrackKind, sinousity_to_twisting_factor
from structures.station import Station, CodeTuple


class BrouterImporterNew:
    stations: List[Station]
    name_to_station: Dict[str, Station]
    language: str | bool
    fallback_town: bool
    fail_on_unknown: bool
    path_tolerance: float

    def __init__(self, station_data: List[Station],
                 language: str | bool = False,
                 fallback_town: bool = False,
                 fail_on_unknown: bool = False,
                 path_tolerance: float = 0.4):
        self.stations = station_data
        self.name_to_station = {normalize_name(station.name): station
                                for station in station_data}
        self.language = language
        self.fallback_town = fallback_town
        self.fail_on_unknown = fail_on_unknown
        self.path_tolerance = path_tolerance

    def import_data(self, file_name: str) -> Tuple[List[Station], List[TcPath]]:
        with open(file_name, encoding='utf-8') as input_file:
            gpx = gpxpy.parse(input_file)

        # Step 1: Find the OSM railway stations for all waypoints
        geolocator = PhotonAdvancedReverse()
        reverse = RateLimiter(geolocator.reverse, min_delay_seconds=0.5, max_retries=3)

        # It may be possible that the waypoint has a different location to its station
        waypoint_location_to_station_location = {}

        for waypoint in gpx.waypoints:
            # Find stations close to the given waypoint location
            possible_stations: List[geopy.location.Location] | None = reverse(
                geopy.Point(latitude=waypoint.latitude, longitude=waypoint.longitude),
                exactly_one=False,
                limit=6,
                query_string_filter='+'.join(["osm_value:stop", "osm_value:station", "osm_value:halt"]),
                language=self.language,
                timeout=10
            )
            if possible_stations is None:
                if self.fallback_town:
                    logging_fn = logging.info
                else:
                    logging_fn = logging.error

                logging_fn(f"No station found for location (lat={waypoint.latitude}, lon={waypoint.longitude})")
                logging.debug("On G/M: https://maps.google.com/maps/@{},{},17z/data=!3m1!1e3".format(
                    waypoint.latitude,
                    waypoint.longitude
                ))
                logging.debug("On OSM: https://openstreetmap.org/#map=17/{}/{}&layers=T".format(
                    waypoint.latitude,
                    waypoint.longitude
                ))

                if self.fallback_town:
                    # Now we will try to look for a nearby town/city/village instead
                    possible_stations = reverse(
                        geopy.Point(latitude=waypoint.latitude, longitude=waypoint.longitude),
                        exactly_one=False,
                        limit=6,
                        query_string_filter='+'.join(["osm_value:city", "osm_value:town", "osm_value:borough",
                                                      "osm_value:hamlet", "osm_value:village",
                                                      "osm_value:municipality"]),
                        language=self.language,
                        timeout=10
                    )
                    if possible_stations is None:
                        logging.error(
                            f"No station or town found for location (lat={waypoint.latitude}, lon={waypoint.longitude})")
                        logging.info("On G/M: https://maps.google.com/maps/@{},{},17z/data=!3m1!1e3".format(
                            waypoint.latitude,
                            waypoint.longitude
                        ))
                        logging.info("On OSM: https://openstreetmap.org/#map=17/{}/{}&layers=T".format(
                            waypoint.latitude,
                            waypoint.longitude
                        ))
                        if self.fail_on_unknown:
                            raise ValueError("Unknown station")
                        else:
                            logging.error("Ignoring station")
                        continue
                else:
                    if self.fail_on_unknown:
                        raise ValueError("Unknown station")
                    else:
                        logging.error("Ignoring station")
                    continue

            for possible_station in possible_stations:
                if 'name' not in possible_station.raw['properties']:
                    logging.info("Station ohne Namen: {}".format(possible_station.raw))

            possible_station_names = (normalize_name(station.raw['properties']['name'])
                                      for station in possible_stations if 'name' in station.raw['properties'])
            possible_station_groups = [group_from_photon_response(station.raw['properties']) for station in
                                       possible_stations]
            # Is one of these names in our data set?
            for name in possible_station_names:
                if name in self.name_to_station:
                    # Remove it from the lookup table to prevent having the same station twice
                    station = self.name_to_station.pop(name)
                    # Add this location if necessary
                    if station.location is None or station.group == -1:
                        station_dict = station.__dict__
                        if station.location is None:
                            station_dict["location"] = Location(
                                latitude=waypoint.latitude,
                                longitude=waypoint.longitude
                            )
                        if station.group == -1:
                            station_dict["_group"] = largest_group(possible_station_groups)
                        station = Station(**station_dict)
                        self.stations.append(station)
                    break
            else:
                logging.info("Couldn't find any of these stations: {}. Creating new one.".format(
                    [station.raw['properties']['name'] for station in possible_stations if
                     'name' in station.raw['properties']]
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

                logging.debug(f"New station: {station}")

                # Add to the data set (it should propagate to the original data set as well)
                self.stations.append(station)
                # We do not want to add it to the lookup table to ensure that we only have unique stations
            waypoint_location_to_station_location[Location(longitude=waypoint.longitude,
                                                           latitude=waypoint.latitude)] = station

        # Now we go through the trackpoints and add stations and segments
        path_segments: List[Tuple[Station, List[GPXTrackPoint], Station]] = []
        # Collect the visited stations here
        stops: List[Station] = []
        # The index in the track segment where the last stop was located
        last_stop_index: int = 0
        last_stop: Station | None = None
        points = gpx.tracks[0].segments[0].points
        for index, trackpoint in enumerate(gpx.tracks[0].segments[0].points):
            location = Location(
                latitude=trackpoint.latitude,
                longitude=trackpoint.longitude
            )
            # Check if this trackpoint is a stop
            for waypoint_location, stop in waypoint_location_to_station_location.items():
                if waypoint_location.distance_float(location) < 0.08:
                    # We have a stop here, add it to the list
                    path_segments.append((last_stop, points[last_stop_index:index], stop))
                    last_stop_index = index
                    last_stop = stop
                    stops.append(stop)
                    # We don't want to match the stop multiple times
                    waypoint_location_to_station_location.pop(waypoint_location)
                    break
        # The first entry is garbage
        path_segments.pop(0)
        assert path_segments

        overpass_queries = [query_rail_around_gpx(min(0.001, self.path_tolerance - 0.02), segment)
                            for _, segment, _ in path_segments]
        overpass_responses = overpass.query_multiple(overpass_queries)

        return stops, [tc_path_from_gpx(start, segment, end, self.path_tolerance, overpass_response=overpass_response)
                       for (start, segment, end), overpass_response in zip(path_segments, overpass_responses)]


def overpass_to_path(overpass_tags: Dict[str, Any]) -> TcPath:
    return TcPath(
        start="",
        end="",
        name=overpass_tags.get("name", None),
        electrified=overpass_tags.get("electrified", "no") != "no",
        group=get_group_from_overpass(overpass_tags),
        length=0,
        maxSpeed=int(overpass_tags.get("maxspeed", "0")),
        twistingFactor=None,
        sinuosity=None,
        neededEquipments=get_equipments_from_overpass(overpass_tags)
    )


def get_equipments_from_overpass(overpass_tags: Dict[str, Any]) -> List[str]:
    needed_equipments = []
    if overpass_tags.get("gauge", "1435") != "1435":
        needed_equipments.append(f"{overpass_tags.get('gauge')}mm")
    return needed_equipments


def get_group_from_overpass(overpass_tags: Dict[str, Any]) -> int | None:
    usage = overpass_tags.get("usage", "main")
    if usage in ("branch", "industrial", "military", "test", "tourism"):
        return 1
    if int(overpass_tags.get("maxspeed", "0")) >= 230:
        return 2
    else:
        return 0


def tc_path_from_gpx(start: Station, segment: List[GPXTrackPoint], end: Station,
                     tolerance: float = 0.4,
                     overpass_response: List[Dict[str, Any]] | None = None) -> TcPath:
    length = sum((geopy.distance.geodesic(
        (last_trackpoint.latitude, last_trackpoint.longitude),
        (trackpoint.latitude, trackpoint.longitude)).km for last_trackpoint, trackpoint in pairwise(segment)))

    if not overpass_response:
        overpass_query = create_query(query_rail_around_gpx(min(0.001, tolerance - 0.02), segment))
        print(len(overpass_query))
        assert len(overpass_query) <= 30000

        overpass_response = overpass.request_overpass(overpass_query)
    sub_paths = [overpass_to_path(sub_path['tags']) for sub_path in overpass_response]
    if not sub_paths:
        sub_paths = [
            TcPath()
        ]

    names = Counter((sub_path.name for sub_path in sub_paths)).most_common(2)
    # We now have (at most) the two most common names, which could be None
    # [(None, _), ...]
    if names[0][0] is None:
        # Using the last value ensures that we always get some value, even if the names are _only_ None
        name = names[-1][0]
    else:
        # If the most common name is something, take that!
        name = names[0][0]

    group = max((sub_path.group for sub_path in sub_paths if sub_path.group is not None),
                key=lambda group: TrackKind(group))

    # TODO: Check if this makes sense?
    max_speeds = [sub_path.maxSpeed for sub_path in sub_paths if sub_path.maxSpeed]
    logging.debug(max_speeds)
    max_max_speed = max(max_speeds)
    avg_max_speed = statistics.mean(max_speeds)
    # We mostly use the maximum speed, but also add a bit of the average one in.
    # It would be better if we could weigh it according to the segment lengths, but that would get more complicated
    max_speed = max_max_speed
    needed_equipments = set((equipment for sub_path in sub_paths for equipment in sub_path.neededEquipments))

    start_country = start.country.flag
    end_country = end.country.flag
    if start.country.iso_3166 != "DE" or end.country.iso_3166 != "DE":
        needed_equipments.add(start_country)
        needed_equipments.add(end_country)

    direct_distance = start.location.distance(end.location)
    sinuosity = round(length / direct_distance, ndigits=3)
    twisting_factor = round(sinousity_to_twisting_factor(sinuosity), ndigits=2)

    return TcPath(
        start=start.codes[0],
        start_long=start.name,
        end=end.codes[0],
        end_long=end.name,
        name=name,
        electrified=statistics.median_low((sub_path.electrified for sub_path in sub_paths)),
        group=group,
        length=int(length),
        maxSpeed=int(max_speed),
        twistingFactor=twisting_factor,
        sinuosity=sinuosity,
        neededEquipments=list(needed_equipments)
    )


def simplify_path_with_stops(path: List[Tuple[Station, List[GPXTrackPoint], Station]], max_radius: float):
    for index, (start, segment, end) in enumerate(path):
        path[index] = (start, list(douglas_peucker(segment, max_radius)), end)


delimiters = re.compile(r"[- _]", flags=re.IGNORECASE)
omitted_tokens = re.compile(r"[.']", flags=re.IGNORECASE)
more_than_one_space = re.compile(r"\s\s+")


@lru_cache
def normalize_name(name: str) -> str:
    name = name.lower()
    name = unidecode.unidecode(name)
    name = delimiters.sub(" ", name)
    name = omitted_tokens.sub("", name)
    name = more_than_one_space.sub(" ", name)
    name = name.replace("saint", "st")
    return name


def group_from_photon_response(response: Dict[str, Any]) -> int | None:
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
        group = None
    return group


def largest_group(groups: List[int]) -> int | None:
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
        return None
