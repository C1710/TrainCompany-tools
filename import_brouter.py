#!/usr/bin/env python

from __future__ import annotations

import argparse
import os.path
from os import PathLike
from typing import Tuple

from cli_utils import check_files, add_default_cli_args
from geo.location_data import add_location_data_to_list
from importers.brouter import BrouterImporter
from importers.db_trassenfinder import DbTrassenfinderImporter, convert_waypoints_to_route
from structures import DataSet
from structures.route import TcRoute
from tc_utils import TcFile
from tc_utils.paths import add_route_to_files


def import_gpx_into_tc(gpx: PathLike | str,
                       tc_directory: PathLike | str = '..',
                       data_directory: PathLike | str = 'data',
                       override_stations: bool = False,
                       add_annotation: bool = False
                       ) -> Tuple[TcFile, TcFile]:
    data_set = DataSet.load_data(data_directory)
    waypoints = BrouterImporter().import_data(gpx)

    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)

    route = convert_waypoints_to_route(waypoints, data_set.station_data, data_set.path_data)
    tc_route = TcRoute.from_route(route, data_set.station_data, add_annotations=add_annotation)

    # Add location data from Google, if necessary
    add_location_data_to_list(tc_route.stations)

    add_route_to_files(tc_route, station_json, path_json,
                       override_stations=override_stations)

    return station_json, path_json


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Importiere neue Routen von brouter.de in TrainCompany')
    parser.add_argument('brouter', metavar='GPX', type=str,
                        help="Die aus brouter MIT WAYPOINTS exportierte GPX-Datei")
    add_default_cli_args(parser)
    parser.add_argument('--stations_only', action='store_true', help="Fügt nur Stationen ein")
    parser.add_argument('--override_stations', action='store_true',
                        help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    parser.add_argument('--annotate', action='store_true',
                        help="Fügt die vollen Stationsnamen hinzu. Die müssen später wieder gelöscht werden!")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    path_json, station_json = import_gpx_into_tc(
        args.brouter,
        args.tc_directory,
        args.data_directory,
        args.override_stations,
        add_annotation=args.annotate
    )

    station_json.save()
    if not args.stations_only:
        path_json.save()
