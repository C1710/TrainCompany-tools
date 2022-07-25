from __future__ import annotations

import argparse
import logging
import os
import re
from os import PathLike
from typing import List, Tuple

from cli_utils import check_files, process_station_input
from geo.location_data import add_location_data_to_list
from structures import DataSet
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
                            gpx: bool = False
                            ) -> TcFile:
    data_set = DataSet.load_data(data_directory)
    station_codes = process_station_input(station_codes, data_set)
    code_to_station = {code: station for code, station in iter_stations_by_codes_reverse(data_set.station_data)}
    stations = [code_to_station[code] for code in station_codes]

    add_location_data_to_list(stations)

    for station in stations:
        if not station.platform_count or not station.platform_length and station.group != 4:
            logging.warning("{}       : No platform data available".format(station.codes[0]))
            logging.warning("{} on OSM: https://openstreetmap.org/#map=17/{}/{}&layers=T"
                         .format(station.codes[0],
                                 station.location.latitude,
                                 station.location.longitude))
            logging.warning("{} on G/M: https://maps.google.com/maps/@{},{},17z"
                         .format(station.codes[0],
                                 station.location.latitude,
                                 station.location.longitude))

    station_json = TcFile('Station', tc_directory)
    add_stations_to_file(stations, station_json, override_stations, update_stations, append=append)

    if trassenfinder:
        create_trassenfinder([(code, code_to_station[code.upper()].name) for code in station_codes], tc_directory)
    if gpx:
        create_gpx(stations, tc_directory)

    return station_json


def create_trassenfinder(stations: List[Tuple[str, str]], tc_directory: PathLike | str = '..'):
    lines = ['utf-8;"Lfd. km";;"Betriebsstelle (kurz)";"Nachfolgende Streckennr.";;;;;;;;;;;;;;;"Bemerkung"\n']
    for index, (code, station_name) in enumerate(stations):
        lines.append('"{}";;"{}";"0";;;;;;;;;;;;;;"{}; Kundenhalt"\n'.format("0,0" if index == 0 else "", code, station_name))
    assert len(lines) == len(stations) + 1
    filename = "{}-{}.csv".format(stations[0][0], stations[-1][0])
    index = 1
    while os.path.exists(os.path.join(tc_directory, filename)):
        filename = "{}-{}-{}.csv".format(index,stations[0][0], stations[-1][0])
        index += 1
    with open(os.path.join(tc_directory, filename), 'w', encoding='utf-8', newline='\n') as outfile:
        outfile.writelines(lines)


def create_gpx(stations: List[Station], tc_directory: PathLike | str = '..'):
    pass


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Importiere neue Betriebsstellen in TrainCompany')
    parser.add_argument('--stations', metavar='RIL100', type=str, nargs='+', required=True,
                        help='Die RIL100-Codes, die hinzugefügt werden sollen')
    parser.add_argument('--tc-dir', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data-dir', dest='data_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    update_or_override = parser.add_mutually_exclusive_group()
    update_or_override.add_argument('--override-stations', action='store_true',
                                    help="Überschreibt Haltestellen, bzw. fügt spezifischere hinzu")
    update_or_override.add_argument('--update-stations', action='store_true',
                                    help="Aktualisiert existierende Haltestellen, fügt aber keine hinzu")
    parser.add_argument('--append', action='store_true',
                        help="Fügt alles am Ende ein")
    parser.add_argument('--trassenfinder', action='store_true',
                        help="Legt eine Trassenfinder-ähnliche Datei mit den Haltestellen an.")
    parser.add_argument('--gpx', action='store_true',
                        help="Legt eine GPX-Datei mit Wegpunkten an, die bspw. auf brouter.de importiert werden kann.")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)
    station_json = import_stations_into_tc(
        args.stations,
        args.tc_directory,
        args.data_directory,
        args.override_stations,
        args.update_stations,
        append=args.append,
        trassenfinder=args.trassenfinder,
        gpx=args.gpx
    )
    station_json.save()
