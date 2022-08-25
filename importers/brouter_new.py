from __future__ import annotations

import itertools
import logging
import random
import re
from collections import Counter
from functools import lru_cache

import statistics
from typing import List, Tuple, Dict, Any, Callable

import geopy.distance
import gpxpy
import unidecode
from geopy.extra.rate_limiter import RateLimiter
from gpxpy.gpx import GPXTrackPoint, GPXWaypoint
from networkx.utils import pairwise

import geo
from geo import Location, overpass
from geo.overpass import query_rail_around_gpx, request_overpass, douglas_peucker, create_query
from geo.photon_advanced_reverse import PhotonAdvancedReverse
from structures.country import countries
from structures.route import TcPath, TrackKind, sinousity_to_twisting_factor
from structures.station import Station, CodeTuple, Platform


class BrouterImporterNew:
    stations: List[Station]
    name_to_station: Dict[str, Station]
    language: str | bool
    fallback_town: bool
    fail_on_unknown: bool
    path_tolerance: float
    use_overpass: bool
    get_platform_data: bool
    use_waypoint_locations: bool
    raw: bool
    prefix_raw: str
    check_country: bool = True

    def __init__(self, station_data: List[Station],
                 language: str | bool = False,
                 fallback_town: bool = False,
                 fail_on_unknown: bool = False,
                 path_tolerance: float = 0.4,
                 use_overpass: bool = True,
                 get_platform_data: bool = True,
                 use_waypoint_locations: bool = True,
                 raw: bool = False,
                 prefix_raw: str = "STATION",
                 check_country: bool = True):
        self.stations = station_data
        self.name_to_station = {normalize_name(station.name): station
                                for station in station_data}
        self.language = language
        self.fallback_town = fallback_town
        self.fail_on_unknown = fail_on_unknown
        self.path_tolerance = path_tolerance
        self.use_overpass = use_overpass
        self.get_platform_data = get_platform_data
        self.use_waypoint_locations = use_waypoint_locations
        self.raw = raw
        self.prefix_raw = prefix_raw
        self.check_country = check_country

    def import_data(self, file_name: str) -> Tuple[List[Station], List[TcPath]]:
        with open(file_name, encoding='utf-8') as input_file:
            gpx = gpxpy.parse(input_file)

        # Step 1: Find the OSM railway stations for all waypoints
        geolocator = PhotonAdvancedReverse()
        reverse = RateLimiter(geolocator.reverse, min_delay_seconds=0.5, max_retries=3)

        waypoint_location_to_station_location = self.collect_waypoint_stations(gpx.waypoints, reverse)

        path_segments, stops = self.collect_path_segments(gpx.tracks[0].segments[0].points,
                                                          waypoint_location_to_station_location)

        if self.use_overpass:
            overpass_queries = [query_rail_around_gpx(min(0.001, self.path_tolerance - 0.02), segment)
                                for _, segment, _ in path_segments]
            overpass_responses = overpass.query_multiple(overpass_queries)
        else:
            overpass_responses = itertools.repeat(None)

        return stops, [tc_path_from_gpx(start, segment, end, overpass_response=overpass_response)
                       for (start, segment, end), overpass_response in zip(path_segments, overpass_responses)]

    @staticmethod
    def collect_path_segments(points: List[GPXTrackPoint],
                              waypoint_location_to_station_location: Dict[Location, Station]) \
            -> Tuple[List[Tuple[Station, List[GPXTrackPoint], Station]], List[Station]]:
        # Now we go through the trackpoints and add stations and segments
        path_segments: List[Tuple[Station, List[GPXTrackPoint], Station]] = []
        # Collect the visited stations here
        stops: List[Station] = []
        # The index in the track segment where the last stop was located
        last_stop_index: int = 0
        last_stop: Station | None = None
        for index, trackpoint in enumerate(points):
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

        return path_segments, stops

    def collect_waypoint_stations(self, waypoints: List[GPXWaypoint],
                                  geocode_reverse) -> Dict[Location, Station]:
        # It may be possible that the waypoint has a different location to its station
        waypoint_location_to_station_location = {}

        raw_stations = 1
        for waypoint in waypoints:
            # Find stations close to the given waypoint location
            possible_stations: List[geopy.location.Location] | None = geocode_reverse(
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
                    possible_stations = geocode_reverse(
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
                    if self.raw:
                        possible_stations = [
                            geopy.Location(
                                address="",
                                point=geopy.Point(
                                    latitude=waypoint.latitude,
                                    longitude=waypoint.longitude
                                ),
                                raw={
                                    "properties": {
                                        "name": "Unbekannte Haltestelle",
                                        "osm_value": "NOTHING",
                                        "countrycode": "UN",
                                        "osm_id": random.randint(0, 1_000_000_000)
                                    }
                                }
                            )
                        ]
                    else:
                        if self.fail_on_unknown:
                            raise ValueError("Unknown station")
                        else:
                            logging.error("Ignoring station")
                        continue

            for possible_station in possible_stations:
                if 'name' not in possible_station.raw['properties']:
                    logging.info("Station ohne Namen: {}".format(possible_station.raw))

            possible_station_names = ((normalize_name(station.raw['properties']['name']),
                                       station)
                                      for station in possible_stations if 'name' in station.raw['properties'])
            possible_station_groups = [group_from_photon_response(station.raw['properties']) for station in
                                       possible_stations]
            # Is one of these names in our data set?
            for name, possible_station in possible_station_names:
                if name in self.name_to_station:
                    station = self.name_to_station[name]
                    countrycode = possible_station.raw["properties"].get("countrycode", None)
                    # We might want to assert that the station we are associating here actually is in the right country
                    if countrycode is not None and self.check_country:
                        country = station.country
                        if countrycode.upper() != country.iso_3166:
                            # Wrong country
                            continue
                    # Check that the station is not too far from the waypoint
                    if station.location is not None:
                        if geopy.distance.geodesic(station.point, possible_station.point).km > 2.0:
                            continue
                    # Remove it from the lookup table to prevent having the same station twice
                    self.name_to_station.pop(name)
                    # Add this location if necessary
                    if station.location is None or station.group == -1 or self.use_waypoint_locations:
                        station_dict = station.__dict__
                        if station.location is None or self.use_waypoint_locations:
                            station_dict["location"] = Location(
                                latitude=waypoint.latitude,
                                longitude=waypoint.longitude
                            )
                        if station.group == -1:
                            station_dict["_group"] = largest_group(possible_station_groups)
                        station = Station(**station_dict)
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
                # We (ab)use the United Nations as a placeholder for completely made up stations
                if country.iso_3166 != "UN":
                    code = f"{country.flag}O{new_station_properties['osm_id']}"
                else:
                    code = f"{country.flag}{self.prefix_raw}{raw_stations}"
                    raw_stations += 1
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

            if station.platform_length == 0 and self.get_platform_data and not station.country.iso_3166 == "UN":
                station = with_osm_platform_data(station)

            # Add to the data set (it should propagate to the original data set as well)
            self.stations.append(station)
            # We do not want to add it to the lookup table to ensure that we only have unique stations

            waypoint_location_to_station_location[Location(longitude=waypoint.longitude,
                                                           latitude=waypoint.latitude)] = station
        return waypoint_location_to_station_location


def with_osm_platform_data(station: Station) -> Station:
    geolocator = geopy.Photon(timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.5, max_retries=3)
    station_location = geopy.Point(latitude=station.location.latitude,
                                   longitude=station.location.longitude)
    platforms: List[geopy.Location] | None = geocode(station.name, location_bias=station_location,
                                                     osm_tag="railway:platform",
                                                     exactly_one=False, limit=20)
    station_platforms = []
    if platforms:
        for platform in platforms:
            if geopy.distance.geodesic(platform.point, station_location).kilometers > 0.8:
                continue
            platform = platform.raw["properties"]
            if "extent" in platform and len(platform["extent"]) in (4, 8):
                if len(platform["extent"]) == 4:
                    # We have a platform with a line shape
                    longitude_a, latitude_a, longitude_b, latitude_b = platform["extent"]
                    point_a = geopy.Point(
                        latitude=latitude_a,
                        longitude=longitude_a
                    )
                    point_b = geopy.Point(
                        latitude=latitude_b,
                        longitude=longitude_b
                    )
                    length = geopy.distance.geodesic(point_a, point_b).meters
                elif len(platform["extent"]) == 8:
                    # It's a rectangle (or similar)
                    lon_a, lat_a, lon_b, lat_b, lon_c, lat_c, lon_d, lat_d = platform["extent"]
                    point_a = geopy.Point(
                        latitude=lat_a,
                        longitude=lon_a
                    )
                    point_b = geopy.Point(
                        latitude=lat_b,
                        longitude=lon_b
                    )
                    point_c = geopy.Point(
                        latitude=lat_c,
                        longitude=lon_c
                    )
                    point_d = geopy.Point(
                        latitude=lat_d,
                        longitude=lon_d
                    )
                    length = max(geopy.distance.geodesic(point_start, point_end) for point_start, point_end in (
                        (point_a, point_b),
                        (point_b, point_c),
                        (point_c, point_d),
                        (point_d, point_a)
                    )).meters
                else:
                    raise ValueError("But that is unpossible!")
                if station_platforms:
                    # We assume that there is one Hausbahnsteig and otherwise Mittelbahnsteige
                    station_platforms.append(Platform(
                        length=length,
                        station=station.number
                    ))
                station_platforms.append(Platform(
                    length=length,
                    station=station.number
                ))
            else:
                logging.debug("Bahnsteig ohne Größe gefunden bei {}".format(station))
        if station_platforms:
            station_dict = station.__dict__
            station_dict.pop("platform_length", 0)
            station_dict.pop("platform_count", 0)
            station_dict.pop("group", 0)
            station_dict.pop("country", None)
            if not station_dict["platforms"]:
                station_dict["platforms"] = station_platforms
            else:
                station_dict["_platform_length"] = max((platform.length for platform in station_platforms))
            return Station(**station_dict)
    logging.debug("Keine Bahnsteige gefunden für {}".format(station))
    return station


def bbox(location: Location, radius: float = 0.004) -> (geopy.Point, geopy.Point):
    a = geopy.Point(
        latitude=round(location.latitude - radius, 3),
        longitude=round(location.longitude - radius, 3)
    )
    b = geopy.Point(
        latitude=round(location.latitude + radius, 3),
        longitude=round(location.longitude - radius, 3)
    )
    return a, b


def overpass_to_path(overpass_tags: Dict[str, Any]) -> TcPath:
    if "maxspeed" in overpass_tags:
        max_speed: str = overpass_tags["maxspeed"]
        max_speed = max_speed.replace("+", "")
        max_speed = max_speed.split(";")[0].strip()
        if "mph" in max_speed:
            max_speed = max_speed.replace(" mph", "")
            max_speed = str(int(int(max_speed) * 1.609344))
            overpass_tags["maxspeed"] = max_speed
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
                     overpass_response: List[Dict[str, Any]] | None = None) -> TcPath:
    length = sum((geopy.distance.geodesic(
        (last_trackpoint.latitude, last_trackpoint.longitude),
        (trackpoint.latitude, trackpoint.longitude)).km for last_trackpoint, trackpoint in pairwise(segment)))

    if overpass_response is None:
        overpass_response = []
    sub_paths = [overpass_to_path(sub_path['tags']) for sub_path in overpass_response]
    if not sub_paths:
        sub_paths = [TcPath(group=-1, neededEquipments=[])]

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
    if not max_speeds:
        max_speeds = [-1]
    max_max_speed = max(max_speeds)
    avg_max_speed = statistics.mean(max_speeds)
    # We mostly use the maximum speed, but also add a bit of the average one in.
    # It would be better if we could weigh it according to the segment lengths, but that would get more complicated
    max_speed = max_max_speed
    needed_equipments = set((equipment for sub_path in sub_paths for equipment in sub_path.neededEquipments))

    start_country = start.country.iso_3166
    end_country = end.country.iso_3166
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
