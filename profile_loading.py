from __future__ import annotations

import argparse
import cProfile
import os
import pstats
import random
from os import PathLike
from typing import Dict, Any, Optional
from matplotlib import pyplot as plt

from cli_utils import check_files
from geo.location_data import with_location_data
from structures import DataSet
from structures.station import iter_stations_by_codes_reverse, Station
from tc_utils import TcFile


def profile_loading(tc_directory: PathLike | str = '..',
                    data_directory: PathLike | str = 'data'
                    ):
    data_set = DataSet.load_data(data_directory)
    stations: Dict[str, Station] = {code: station
                                    for code, station in iter_stations_by_codes_reverse(data_set.station_data)}
    path_json = TcFile('Path', tc_directory)
    station_json = TcFile('Station', tc_directory)


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Test')
    parser.add_argument('--tc_directory', dest='tc_directory', metavar='VERZEICHNIS', type=str, default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data_directory', dest='data_directory', metavar='VERZEICHNIS', type=str, default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    profiler = cProfile.Profile()
    profiler.enable()
    profile_loading(args.tc_directory, args.data_directory)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats("cumtime")
    stats.print_stats()


