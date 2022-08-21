import random
from typing import Dict, Any

from cleanup import remove_annotations_from_path
from structures.route import TcPath, TcRoute
from tc_utils import TcFile
from tc_utils.stations import add_stations_to_file


def add_path_to_file(path: TcPath, file: TcFile, append: bool = False, clean: bool = False):
    # TODO: Prevent duplicate path
    path_dict: Dict[str, Any] = path.to_dict()
    if clean:
        remove_annotations_from_path(path_dict)
    file.data.insert(random.randint(0, len(file.data)) if not append else len(file.data), path_dict)


def add_route_to_files(
        route: TcRoute,
        station_file: TcFile,
        path_file: TcFile,
        override_stations: bool = False,
        append: bool = False
):
    add_stations_to_file(route.stations, station_file, override_stations, append=append)
    add_path_to_file(route.path, path_file, append=append)
