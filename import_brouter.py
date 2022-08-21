#!/usr/bin/env python

from __future__ import annotations

import argparse
import os.path
from os import PathLike
from typing import Tuple

from cleanup import remove_annotations_from_path
from cli_utils import check_files, add_default_cli_args, use_default_cli_args
from geo.location_data import add_location_data_to_list
from importers.brouter import BrouterImporter
from importers.brouter_new import BrouterImporterNew
from importers.db_trassenfinder import DbTrassenfinderImporter, convert_waypoints_to_route
from structures import DataSet
from structures.route import TcRoute, TcPath
from tc_utils import TcFile
from tc_utils.paths import add_route_to_files, add_path_to_file
from tc_utils.stations import add_stations_to_file


def import_gpx_into_tc(gpx: PathLike | str,
                       tc_directory: PathLike | str = '..',
                       data_directory: PathLike | str = 'data',
                       override_stations: bool = False,
                       use_google: bool = False,
                       language: str | bool = False,
                       fallback_town: bool = False,
                       tolerance: float = 0.4
                       ) -> Tuple[TcFile, TcFile]:
    data_set = DataSet.load_data(data_directory)
    importer = BrouterImporterNew(data_set.station_data, language=language, fallback_town=fallback_town,
                                  path_tolerance=tolerance)
    stations, paths = importer.import_data(gpx)

    path = TcPath.merge(paths)

    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)

    # Add location data, if necessary
    add_location_data_to_list(stations, use_google=use_google)

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
    parser.add_argument("--use-google", action='store_true',
                        help="Nutzt die Google Maps-API für fehlende Standort-Daten (API-Key erforderlich)")
    parser.add_argument("--language", choices=['de', 'en', 'fr'],
                        help="Sprache für die Bahnhofsnamen")
    parser.add_argument("--towns", action="store_true",
                        help="Falls kein Bahnhof gefunden wird, wird der Ort genommen")
    parser.add_argument("--tolerance", default=0.05, type=float,
                        help="Gibt an, wie stark die Strecke für Online-Abfragen vereinfacht werden soll in km.\n"
                             "Ein kleinerer Wert funktioniert genauer, ist aber aufwändiger")
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
        tolerance=args.tolerance
    )

    station_json.save()
    if not args.stations_only:
        path_json.save()
