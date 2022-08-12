#!/usr/bin/env python

from __future__ import annotations

import argparse
import logging
import os
import re
from os import PathLike
from typing import List, Tuple, Optional

import gpxpy.gpx

from cli_utils import check_files, process_station_input, add_default_cli_args, add_station_cli_args, parse_station_args
from geo.location_data import add_location_data_to_list, with_location_data
from structures import DataSet
from structures.country import split_country, CountryRepresentation, iso_3166_to_country, tld_to_country
from structures.station import iter_stations_by_codes_reverse, Station
from tc_utils import TcFile
from tc_utils.stations import add_stations_to_file


def import_stations_into_tc(station_codes: List[str],
                            tc_directory: PathLike | str = '..',
                            data_directory: PathLike | str = 'data',
                            override_stations: bool = False,
                            update_stations: bool = False,
                            append: bool = False,
                            trassenfinder: bool = False,
                            gpx: bool = False,
                            annotate: bool = False,
                            data_set: Optional[DataSet] = None,
                            station_json: TcFile | None = None,
                            case_sensitive: bool = False,
                            **kwargs) -> TcFile:
    if not data_set:
        data_set = DataSet.load_data(data_directory)
    code_to_station = {code: station for code, station in iter_stations_by_codes_reverse(data_set.station_data)}
    stations = [with_location_data(code_to_station[code.upper() if not case_sensitive else code]) for code in
                station_codes]

    add_location_data_to_list(stations)

    for station in stations:
        if not station.platform_count or not station.platform_length and station.group != 4:
            logging.warning("{}        : Keine Bahnsteigdaten bekannt".format(station.codes[0]))
            if station.location:
                logging.warning("{} auf OSM: https://openstreetmap.org/#map=17/{}/{}&layers=T"
                                .format(station.codes[0],
                                        station.location.latitude,
                                        station.location.longitude))
                logging.warning("{} auf G/M: https://maps.google.com/maps/@{},{},17z/data=!3m1!1e3"
                                .format(station.codes[0],
                                        station.location.latitude,
                                        station.location.longitude))
                if annotate:
                    station['google_maps'] = "https://maps.google.com/maps/@{},{},17z/data=!3m1!1e3".format(
                        station.location.latitude, station.location.longitude)
                    station['osm'] = "https://openstreetmap.org/#map=17/{}/{}&layers=T".format(
                        station.location.latitude, station.location.longitude)
            else:
                "{} ohne bekannten Standort".format(station.codes[0])
    if not station_json:
        station_json = TcFile('Station', tc_directory)
    add_stations_to_file(stations.copy(), station_json, override_stations, update_stations, append=append)

    if trassenfinder:
        create_trassenfinder(
            [(code, code_to_station[code.upper() if not case_sensitive else code].name) for code in station_codes],
            tc_directory)
    if gpx:
        create_gpx(stations, tc_directory)

    return station_json


def get_filename(code_start: str, code_end: str, extension: str, tc_directory: PathLike | str = '..'):
    country_start, code_start, representation = split_country(code_start)
    if country_start is not None and representation in (CountryRepresentation.FLAG,):
        code_start = country_start.iso_3166 + "_" + code_start
    country_end, code_end, _ = split_country(code_end)
    if country_end is not None and representation in (CountryRepresentation.FLAG,):
        code_end = country_end.iso_3166 + "_" + code_end
    filename = "{}-{}.{}".format(code_start, code_end, extension)
    index = 1
    while os.path.exists(os.path.join(tc_directory, filename)):
        filename = "{}-{}-{}.{}".format(code_start, code_end, index, extension)
        index += 1
    return os.path.join(tc_directory, filename)


def create_trassenfinder(stations: List[Tuple[str, str]], tc_directory: PathLike | str = '..'):
    lines = ['utf-8;"Lfd. km";;"Betriebsstelle (kurz)";"Nachfolgende Streckennr.";;;;;;;;;;;;;;;"Bemerkung"\n']
    for index, (code, station_name) in enumerate(stations):
        lines.append('"{}";;"{}";"0";;;;;;;;;;;;;;"{}; Kundenhalt"\n'.format("0,0" if index == 0 else "", code, station_name))
    assert len(lines) == len(stations) + 1
    filename = get_filename(stations[0][0], stations[-1][0], "csv", tc_directory)
    with open(filename, 'w', encoding='utf-8', newline='\n') as outfile:
        outfile.writelines(lines)


def create_gpx(stations: List[Station], tc_directory: PathLike | str = '..'):
    gpx = gpxpy.gpx.GPX()
    for station in stations:
        if not station.location:
            logging.warning("Haltestelle ohne Standortdaten: {}. Bitte manuell hinzufügen.".format(station.codes[0]))
    trackpoints = [gpxpy.gpx.GPXTrackPoint(latitude=station.location.latitude,
                                           longitude=station.location.longitude,
                                           name=station.name) for station in stations if station.location]
    track = gpxpy.gpx.GPXTrack()
    segment = gpxpy.gpx.GPXTrackSegment()
    segment.points.extend(trackpoints)
    track.segments.append(segment)
    gpx.tracks.append(track)
    filename = get_filename(stations[0].codes[0], stations[-1].codes[0], "gpx", tc_directory)
    with open(filename, 'w', encoding='utf-8', newline='\n') as outfile:
        outfile.write(gpx.to_xml(prettyprint=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Importiere neue Betriebsstellen in TrainCompany')
    add_default_cli_args(parser)
    add_station_cli_args(parser,
                         help="Die (RIL100-)Codes der Haltestellen, die hinzugefügt werden sollen",
                         help_countries="Die Länder, deren Haltestellen hinzugefügt werden sollen",
                         required=True,
                         # TODO: Allow this
                         allow_multiple_stations=True)

    update_or_override = parser.add_mutually_exclusive_group()
    update_or_override.add_argument('--override-stations', action='store_true',
                                    help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    update_or_override.add_argument('--update-stations', action='store_true',
                                    help="Aktualisiert existierende Haltestellen, fügt aber keine hinzu")
    parser.add_argument('--append', action='store_true',
                        help="Fügt alles am Ende ein")
    parser.add_argument('--annotate', action='store_true',
                        help="Fügt Links zu Google Maps/OSM hinzu, wenn Bahnsteigdaten fehlen")
    parser.add_argument('--trassenfinder', action='store_true',
                        help="Legt eine Trassenfinder-ähnliche Datei mit den Haltestellen an.")
    parser.add_argument('--gpx', action='store_true',
                        help="Legt eine GPX-Datei mit Wegpunkten an, die bspw. auf brouter.de importiert werden kann.")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)
    stations = parse_station_args(args, required=True, inplace=False)
    station_json = TcFile("Station", args.tc_directory)
    data_set = DataSet.load_data(args.data_directory)
    for station_codes in stations:
        station_json = import_stations_into_tc(**args.__dict__, data_set=data_set, station_json=station_json,
                                               station_codes=station_codes)
    station_json.save()
