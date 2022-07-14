from __future__ import annotations

import argparse
import os
from os import PathLike
from typing import List

from cli_utils import check_files


def export_station_list(country: str,
                        data_directory: PathLike | str = '..') -> List[str]:
    from structures import DataSet

    if country == 'DE':
        station_data = DataSet.load_station_data_de(data_directory)
    else:
        station_data_de = DataSet.load_station_data_de(data_directory)
        if country == 'CH':
            station_data = DataSet.load_station_data_ch(data_directory)
            station_data_de = [station for station in station_data_de if any((code.startswith("XS") for code in station.codes))]
        if country == 'FR':
            station_data = DataSet.load_station_data_fr(data_directory)
            station_data_de = [station for station in station_data_de if any((code.startswith("XF") for code in station.codes))]
        if country == 'UK':
            station_data = DataSet.load_station_data_uk(data_directory)
            station_data_de = [station for station in station_data_de if any((code.startswith("XK") for code in station.codes))]
        station_data.extend(station_data_de)

    return ["{}\t{}\n".format(station.name, station.codes) for station in station_data]


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Importiere neue Routen vom Trassenfinder in TrainCompany')
    parser.add_argument('country', metavar="LAND", type=str, choices=('UK', 'FR', 'CH', 'DE'),
                        help="Das Land, für das die Stationsliste exportiert werden soll.")
    parser.add_argument('--out_file', metavar='DATEI', type=str,
                        help="Die Datei, in die gespeichert werden soll. Standard: stations_<Land>.tsv")
    parser.add_argument('--tc_directory', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data_directory', dest='data_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    stations = export_station_list(args.country, args.data_directory)
    if args.out_file is None:
        args.out_file = os.path.join(args.tc_directory, "stations_{}.tsv".format(args.country))
    with open(args.out_file, 'w', newline='\n', encoding='utf-8') as out_file:
        out_file.writelines(stations)
