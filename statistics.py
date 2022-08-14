from __future__ import annotations
import argparse
from os import PathLike

from cli_utils import add_default_cli_args, use_default_cli_args
from tc_utils import TcFile, flatten_objects


def print_statistics(tc_directory: PathLike | str = '..',
                     data_directory: PathLike | str = 'data',
                     length: bool = True,
                     num_stations: bool = True,
                     **kwargs):
    station_json = TcFile('Station', tc_directory)
    path_json = TcFile('Path', tc_directory)

    if length:
        paths = flatten_objects(path_json.data)
        total_length = sum((path['length'] for path in paths))
        print(f"Gesamtlänge des Netzes: {total_length} km")
    if num_stations:
        stations = flatten_objects(station_json.data)
        station_count = 0
        for _ in stations:
            station_count += 1
        print(f"Anzahl Haltestellen:    {station_count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gibt Statistiken aus")
    add_default_cli_args(parser)
    args = parser.parse_args()
    use_default_cli_args(args)
    print_statistics(**args.__dict__)
