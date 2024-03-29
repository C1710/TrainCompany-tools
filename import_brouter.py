#!/usr/bin/env python

from __future__ import annotations

import argparse
from os import PathLike
from typing import Tuple

from cli_utils import check_files, add_default_cli_args, use_default_cli_args
from geo.location_data import add_location_data_to_list
from importers.brouter_new import BrouterImporterNew
from structures import DataSet
from structures.route import TcPath
from tc_utils import TcFile
from tc_utils.paths import add_path_to_file
from tc_utils.stations import add_stations_to_file


def import_gpx_into_tc(gpx: PathLike | str,
                       tc_directory: PathLike | str = '..',
                       data_directory: PathLike | str = 'data',
                       override_stations: bool = False,
                       language: str | bool = False,
                       fallback_town: bool = False,
                       tolerance: float = 0.4,
                       use_overpass: bool = True,
                       use_waypoint_location: bool = False,
                       raw_waypoint_prefix: str | None = None,
                       check_country: bool = True
                       ) -> Tuple[TcFile, TcFile]:
    data_set = DataSet.load_data(data_directory)
    importer = BrouterImporterNew(data_set.station_data, language=language, fallback_town=fallback_town,
                                  path_tolerance=tolerance, use_overpass=use_overpass,
                                  use_waypoint_locations=use_waypoint_location, prefix_raw=raw_waypoint_prefix,
                                  raw=raw_waypoint_prefix is not None,
                                  check_country=check_country)
    stations, paths = importer.import_data(gpx)

    path = TcPath.merge(paths)

    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)

    # Add location data, if necessary
    add_location_data_to_list(stations)

    add_stations_to_file(stations, station_json, override_stations=override_stations)

    # The top-level path might have a 0 twistingFactor which we don't want to keep
    if path.twistingFactor == 0:
        path.twistingFactor = None

    add_path_to_file(path, path_json, clean=True)

    return station_json, path_json


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Importiere neue Routen von brouter.de in TrainCompany')
    parser.add_argument('brouter', metavar='GPX', type=str,
                        help="Die aus brouter MIT WAYPOINTS exportierte GPX-Datei")
    add_default_cli_args(parser)
    parser.add_argument('--stations_only', action='store_true', help="Fügt nur Stationen ein")
    parser.add_argument('--override_stations', action='store_true',
                        help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    parser.add_argument("--language", choices=['de', 'en', 'fr'],
                        help="Sprache für die Bahnhofsnamen")
    parser.add_argument("--towns", action="store_true",
                        help="Falls kein Bahnhof gefunden wird, wird der Ort genommen")
    parser.add_argument("--tolerance", default=0.05, type=float,
                        help="Gibt an, wie stark die Strecke für Online-Abfragen vereinfacht werden soll in km.\n"
                             "Ein kleinerer Wert funktioniert genauer, ist aber aufwändiger")
    parser.add_argument("--no-overpass", action="store_true",
                        help="Nutzt nicht die Overpass-API, um Daten zu vervollständigen.")
    parser.add_argument("--waypoint-location", action="store_true",
                        help="Verwendet immer den in brouter angegebenen Standort für eine Haltestelle")
    parser.add_argument("--raw-waypoints",
                        help="Fügt nicht existierende Stationen mit dem Präfix hinzu (nur für Fähren empfohlen)")
    parser.add_argument("--no-check-country", action="store_true",
                        help="Prüft beim Abgleich mit den Datensätzen nicht, ob das Land übereinstimmt")
    args = parser.parse_args()
    use_default_cli_args(args)

    check_files(args.tc_directory, args.data_directory)

    path_json, station_json = import_gpx_into_tc(
        args.brouter,
        args.tc_directory,
        args.data_directory,
        args.override_stations,
        language=args.language if args.language else False,
        fallback_town=args.towns,
        tolerance=args.tolerance,
        use_overpass=not args.no_overpass,
        use_waypoint_location=args.waypoint_location,
        raw_waypoint_prefix=args.raw_waypoints,
        check_country=not args.no_check_country
    )

    station_json.save()
    if not args.stations_only:
        path_json.save()
