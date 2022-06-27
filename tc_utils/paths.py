from typing import Dict, Any

from tools.structures.route import TcPath, TcRoute
from tools.tc_utils import TcFile
from tools.tc_utils.stations import add_stations_to_file


def add_path_to_file(path: TcPath, file: TcFile):
    # TODO: Prevent duplicate path
    path_dict: Dict[str, Any] = {key: value for key, value in path.__dict__.items() if value is not None}
    file.data.append(path_dict)


def add_route_to_files(
        route: TcRoute,
        station_file: TcFile,
        path_file: TcFile
):
    add_stations_to_file(route.stations, station_file)
    add_path_to_file(route.path, path_file)
