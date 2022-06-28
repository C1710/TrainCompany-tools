from __future__ import annotations

import argparse
import os
import re
import sys
from os import PathLike
from typing import List

from structures import DataSet
from tc_utils import TcFile
from tc_utils.stations import add_stations_to_file
from . import check_files


def import_stations_into_tc(stations: List[str],
                            tc_directory: PathLike | str = '..',
                            data_directory: PathLike | str = 'data',
                            override_stations: bool = False,
                            update_stations: bool = False
                            ) -> TcFile:
    data_set = DataSet.load_data(data_directory)
    code_to_station = {code: station for station in data_set.station_data for code in station.codes}
    stations = [code_to_station[code.upper()] for code in stations]

    station_json = TcFile('Station', tc_directory)
    add_stations_to_file(stations, station_json, override_stations, update_stations)
    return station_json


def import_regex_stations_into_tc(stations_regex: str,
                                  tc_directory: PathLike | str = '..',
                                  data_directory: PathLike | str = 'data',
                                  override_stations: bool = False,
                                  update_stations: bool = False
                                  ) -> TcFile:
    regex = re.compile(stations_regex, re.RegexFlag.IGNORECASE)
    data_set = DataSet.load_data(data_directory)
    stations = [station for station in data_set.station_data if any((regex.match(code) for code in station.codes))]

    station_json = TcFile('Station', tc_directory)
    add_stations_to_file(stations, station_json, override_stations, update_stations)
    return station_json


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Importiere neue Betriebsstellen in TrainCompany')
    regex_or_ril100_list = parser.add_mutually_exclusive_group()
    regex_or_ril100_list.add_argument('stations', metavar='RIL100', type=str, nargs='+',
                                      required='--regex' not in sys.argv,
                                      help='Die RIL100-Codes, die hinzugefügt werden sollen')
    regex_or_ril100_list.add_argument('--regex', type=str, metavar='REGEX',
                                      help="Ein regulärer Ausdruck, "
                                           "nach dem die Betriebsstellen hinzugefügt werden sollen.")
    parser.add_argument('--tc_directory', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data_directory', dest='data_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    update_or_override = parser.add_mutually_exclusive_group()
    update_or_override.add_argument('--override_stations', action='store_true',
                                    help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    update_or_override.add_argument('--update-stations', action='store_true',
                                    help="Aktualisiert existierende Haltestellen, fügt aber keine hinzu")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)
    if args.stations is not None:
        station_json = import_stations_into_tc(
            args.stations,
            args.tc_directory,
            args.data_directory,
            args.override_stations,
            args.update_stations
        )
    else:
        # We (should?) have a regex
        station_json = import_regex_stations_into_tc(
            args.regex,
            args.tc_directory,
            args.data_directory,
            args.override_stations,
            args.update_stations
        )
    station_json.save()
