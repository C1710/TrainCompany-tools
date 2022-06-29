from __future__ import annotations

import argparse
import os
from os import PathLike
from typing import Dict, Any, Optional
from matplotlib import pyplot as plt

from cli_utils import check_files
from structures import DataSet
from structures.station import iter_stations_by_codes_reverse, Station
from tc_utils import TcFile


def test_twisting(tc_directory: PathLike | str = '..',
                  data_directory: PathLike | str = 'data'
                  ):
    data_set = DataSet.load_data(data_directory)
    stations: Dict[str, Station] = {code: station
                                    for code, station in iter_stations_by_codes_reverse(data_set.station_data)}
    path_json = TcFile('Path', tc_directory)

    comparisons = []
    for path in path_json.data:
        if 'objects' not in path:
            twisting_comparison = compare_twisting(path, stations)
            if twisting_comparison is not None:
                comparisons.append(twisting_comparison)
        else:
            for sub_path in path['objects']:
                if 'twistingFactor' not in sub_path:
                    sub_path.update({'twistingFactor': path['twistingFactor'] if 'twistingFactor' in path else 0.2})
                twisting_comparison = compare_twisting(sub_path, stations)
                if twisting_comparison is not None:
                    comparisons.append(twisting_comparison)
    twisting_computed, twisting_target = zip(*comparisons)
    plt.plot([0.0, 0.7], [0.0, 0.7])
    plt.scatter(x=twisting_target, y=twisting_computed)
    plt.yscale('log')
    plt.xscale('log')
    plt.show()


def compute_twisting_factor(distance_real: float, distance_direct: float) -> float:
    twisting_factor = 1 - (distance_direct / distance_real)
    # Cap twistingFactor between 0.05 and 0.5
    twisting_factor = max(0.005, twisting_factor)
    twisting_factor = min(twisting_factor, 1.0)
    return twisting_factor


def compare_twisting(path: Dict[str, Any], stations: Dict[str, Station]) -> Optional[float, float]:
    twisting_target = path['twistingFactor']
    start = path['start']
    end = path['end']
    distance_real = path['length']
    station_start = stations[start]
    station_end = stations[end]
    if station_start.location and station_end.location:
        distance_direct = station_start.location.distance(station_end.location)
        twisting_computed = compute_twisting_factor(distance_real, distance_direct)
        return twisting_computed, twisting_target
    else:
        print(station_start, station_end, "", sep='\n')


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

    test_twisting(args.tc_directory, args.data_directory)


