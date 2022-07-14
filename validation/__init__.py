from __future__ import annotations

import logging
import random
import re
import time
import timeit
from os import PathLike
from typing import Dict, Any

import networkx as nx
from networkx import is_connected

from geo.location_data import with_location_data
from structures import DataSet, Station
from structures.station import iter_stations_by_codes_reverse
from geo import Location
from tc_utils import TcFile
from validation.graph import build_tc_graph
from transform_to_laea import transform_coordinate_for_station


def print_path(path: Dict[str, Any]) -> str:
    output = ""
    if 'name' in path:
        output += path['name'] + " "
    output += '{} -> {}'.format(path['start'], path['end'])
    return output


def validate(tc_directory: PathLike | str = '..',
             data_directory: PathLike | str = 'data'
             ) -> int:
    data_set = DataSet.load_data(data_directory)
    stations: Dict[str, Station] = {code: station
                                    for code, station in iter_stations_by_codes_reverse(data_set.station_data)}
    path_json = TcFile('Path', tc_directory)
    station_json = TcFile('Station', tc_directory)
    train_json = TcFile('Train', tc_directory)
    train_equipment_json = TcFile('TrainEquipment', tc_directory)
    task_model_json = TcFile('TaskModel', tc_directory)

    issues = 0

    # Step 1: Validate stations
    logging.info(" --- Station.json --- ")
    selected_codes = [station['ril100'] for station in station_json.data]
    selected_stations = [(station, stations[station['ril100']] if station['ril100'] in stations else None)
                         for station in station_json.data]

    flag_re = re.compile(r"[🇦-🇿]{2}")
    known_flags = ["🇨🇭"]

    for station, station_obj in selected_stations:
        transform_coordinate_for_station(station)
        if station_obj is None:
            if flag_re.search(station['ril100']):
                for known_flag in known_flags:
                    if known_flag in station['ril100']:
                        logging.warning("Unbekannte Haltestelle: {}".format(station['ril100']))
                        issues += 50
                        break
                else:
                    logging.info("Betriebsstelle in unbekanntem Land: {}".format(station['ril100']))
            else:
                logging.warning("Unbekannte Haltestelle: {}".format(station['ril100']))
                issues += 50
            continue
        # 1.1. location check
        # Currently not done because the new coordinates are not yet supported
        real_location = station_obj.location
        if real_location and False:
            data_location = Location.from_tc(station['x'], station['y'])
            delta = real_location.distance(data_location)
            if delta > 20:
                logging.warning("Haltepunkt {} ist über 20 km vom echten Punkt entfernt.".format(station['ril100']))
                issues += 5
            if delta > 60:
                logging.warning("Haltepunkt {} ist über 60 km vom echten Punkt entfernt.".format(station['ril100']))
                issues += 10
            if delta > 300:
                logging.warning("Haltepunkt {} ist über 300 km vom echten Punkt entfernt.".format(station['ril100']))
                issues += 20

        # 1.2. Platforms
        real_platforms = station_obj.platforms
        if real_platforms and 'platformLength' in station:
            # Length checking is disabled for now because it might not work correctly
            if False:
                data_platform_length = station['platformLength']
                delta = abs(station_obj.platform_length - data_platform_length)
                if delta > 20:
                    logging.warning("Haltepunkt {} hat eine um > 20 m abweichende Bahnsteiglänge."
                                    .format(station['ril100']))
                    issues += 10
                if delta > 100:
                    logging.warning("Haltepunkt {} hat eine um > 100 m abweichende Bahnsteiglänge."
                                    .format(station['ril100']))
                    issues += 100

            data_platforms = station['platforms']
            delta = abs(station_obj.platform_count - data_platforms)
            if delta > 2:
                # Platform count is not used anyway
                issues += 10

        # 1.3. group - Not used at the moment
        pass

    # Step 2: Paths
    logging.info(" --- Path.json --- ")
    # Expand sub-paths
    paths = []
    for path in path_json.data:
        if 'objects' not in path:
            paths.append(path)
        else:
            for sub_task in path.pop('objects'):
                new_task = path.copy()
                new_task.update(sub_task)
                paths.append(new_task)

    for path in paths:
        # Add default values if necessary
        if 'group' not in path:
            path['group'] = 0
        if 'electrified' not in path:
            path['electrified'] = True

        # 2.0. has speed and length
        if 'maxSpeed' not in path:
            logging.warning("Pfad hat keine vMax: {}".format(print_path(path)))
            issues += 10000
        if 'length' not in path:
            logging.warning("Pfad hat keine Länge: {}".format(print_path(path)))
            issues += 10000

        # 2.1. Speed - group
        if 'maxSpeed' in path and path['maxSpeed'] >= 250 and path['group'] != 2:
            logging.warning("Nicht-SFS mit >= 250 km/h: {}".format(print_path(path)))
            issues += 50

        # 2.2. SFS - electrified
        if path['group'] == 2 and not path['electrified']:
            logging.warning("Nicht elektrifizierte SFS: {}".format(print_path(path)))
            issues += 1000

        # 2.3. Path length for Non-SFS
        if path['group'] != 2 and path['length'] > 40:
            logging.warning(">40 km langer Streckenabschnitt auf Nicht-SFS: {}".format(print_path(path)))
            issues += 5
        if path['group'] != 2 and path['length'] > 80:
            logging.warning(">80 km langer Streckenabschnitt auf Nicht-SFS: {}".format(print_path(path)))
            issues += 40

        # 2.4. realistic twistingFactor
        if path['twistingFactor'] > 0.5:
            logging.info("twistingFactor > 0.5: {}".format(
                print_path(path)
            ))
            issues += 5

        # 2.5. Only cover existing stations
        if path['start'] not in selected_codes:
            logging.error("Nicht existierender Start-Bahnhof: {}".format(path['start']))
            issues += 10000
        if path['end'] not in selected_codes:
            logging.error("Nicht existierender End-Bahnhof: {}".format(path['start']))
            issues += 10000

        # 2.6. SFS-name for non-SFS
        if 'name' in path:
            if 'SFS' in path['name'] and not path['group'] == 2:
                logging.warning("Strecke hat SFS im Namen, ist aber keine: {}".format(print_path(path)))
                issues += 20
            if 'SFS' in path['name']:
                logging.warning("Strecke hat SFS im Namen, obwohl es als Kategorie bereits angezeigt wird: {}"
                                .format(print_path(path)))
                issues += 5

    # Step 3: graph-based validation
    logging.info(" --- Routing --- ")
    path_edges = [(path['start'], path['end'], path) for path in paths
                  if path['start'] in selected_codes and path['end'] in selected_codes]

    graph = build_tc_graph(selected_codes, path_edges)
    if not is_connected(graph):
        logging.error("Das Netz ist nicht zusammenhängend.")
        for node, degree in graph.degree():
            if degree == 0:
                logging.error("Haltepunkt ohne Route: {}".format(node))
        issues += 1000

    # Step 4: trains
    logging.info(" --- Train.json --- ")
    # 4.1. unique train IDs
    train_ids = [train['id'] for train in train_json.data]
    train_ids.sort()
    for train_id, next_id in zip(train_ids, train_ids[1:]):
        if train_id == next_id:
            logging.error("Doppelte Train-ID: {}".format(train_id))
            issues += 10000

    # 4.2. realistic acceleration
    # TODO: -
    pass

    # 4.3. only existing train equipments
    train_equipments = [equipment['idString'] for equipment in train_equipment_json.data]
    for train in train_json.data:
        if 'equipments' in train:
            for used_equipment in train['equipments']:
                if used_equipment not in train_equipments:
                    logging.error("Zug {} hat nicht existierendes Equipment: {}".format(train['id'], used_equipment))
                    issues += 10000

    # 4.4. operationCosts
    # TODO: Better validation (e.g., high force = high costs)
    for train in train_json.data:
        if 'operationCosts' not in train:
            train['operationCosts'] = 0
        if train['force'] > 0 and train['operationCosts'] < 5:
            logging.error("Zug {} (ID {}) hat keine/zu geringe operationCosts: {}"
                          .format(train['name'] if 'name' in train else 'Unbenannt', train['id'], train['operationCosts']))
            issues += 1000

    # Step 5: task model
    logging.info(" --- TaskModel.json --- ")
    # Expand sub-tasks
    tasks = []
    for task in task_model_json.data:
        if 'objects' not in task:
            tasks.append(task)
        else:
            for sub_task in task.pop('objects'):
                new_task = task.copy()
                new_task.update(sub_task)
                tasks.append(new_task)

    for task in tasks:
        # 5.1. All stations exist
        if 'stations' in task:
            for station in task['stations']:
                if station not in selected_codes:
                    logging.error("Nicht existierender Haltepunkt: {}".format(station))
                    issues += 10000

    return issues

