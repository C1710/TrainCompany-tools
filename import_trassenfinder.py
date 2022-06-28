from __future__ import annotations

import argparse
import os.path
from os import PathLike
from os.path import isfile
from typing import Tuple

from importers.db_trassenfinder import DbTrassenfinderImporter, convert_waypoints_tracks_to_route
from structures import DataSet
from structures.route import TcRoute
from tc_utils import TcFile
from tc_utils.paths import add_route_to_files



def import_trasse_into_tc(trasse: PathLike | str,
                          tc_directory: PathLike | str = '..',
                          data_directory: PathLike | str = 'data',
                          override_stations: bool = False
                          ) -> Tuple[TcFile, TcFile]:
    data_set = DataSet.load_data(data_directory)
    waypoints = DbTrassenfinderImporter().import_data(trasse)

    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)

    route = convert_waypoints_tracks_to_route(waypoints, data_set.track_data)
    tc_route = TcRoute.from_route(route, data_set.station_data)

    add_route_to_files(tc_route, station_json, path_json, override_stations=override_stations)

    return station_json, path_json


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    
    parser = argparse.ArgumentParser(description='Importiere neue Routen vom Trassenfinder in TrainCompany')
    parser.add_argument('trasse', metavar='TRASSENFINDER_DATEI', type=str,
                        help="Die CSV-Datei, die aus Trassenfinder exportiert wurde")
    parser.add_argument('--tc_directory', dest='tc_directory', metavar='VERZEICHNIS', type=str, default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data_directory', dest='data_directory', metavar='VERZEICHNIS', type=str, default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    parser.add_argument('--stations_only', action='store_true', help="Fügt nur Stationen ein")
    parser.add_argument('--override_stations', action='store_true',
                        help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    args = parser.parse_args()

    for tc_file in ['Station', 'Path']:
        if not isfile(os.path.join(args.tc_directory, tc_file) + '.json'):
            print('Konnte Datei nicht finden: {} (in {})'.format(tc_file, args.tc_directory))
    for data_file in ['bahnhoefe', 'bahnsteige', 'betriebsstellen', 'strecken']:
        if not isfile(os.path.join(args.data_directory, data_file) + '.csv'):
            print('Konnte Datei nicht finden: {} (in {})'.format(data_file, args.data_directory))

    path_json, station_json = import_trasse_into_tc(
        args.trasse,
        args.tc_directory,
        args.data_directory,
        args.override_stations
    )

    station_json.save()
    if not args.stations_only:
        path_json.save()
