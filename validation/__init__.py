from __future__ import annotations

import logging
import re
from os import PathLike
from typing import Dict, Any

from networkx import is_connected

from geo import Location
from project_coordinates import project_coordinate_for_station
import tc_utils
from structures import DataSet, Station
from structures.station import iter_stations_by_codes_reverse
from tc_utils import TcFile
from validation.graph import build_tc_graph
from structures.country import country_for_code, countries, germany


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

    known_countries = (countries['CH'], germany)

    for station, station_obj in selected_stations:
        project_coordinate_for_station(station)
        if station_obj is None:
            country = country_for_code(station['ril100'])
            if country in known_countries:
                issues_score = 50
                logging.warning("+{: <6} Unbekannte Haltestelle: {}".format(issues_score, station['ril100']))
                issues += issues_score
            else:
                logging.info("+{: <6} Betriebsstelle in unbekanntem Land: {}".format(0, station['ril100']))
            continue
        # 1.1. location check
        # Currently not done because the new coordinates are not yet supported
        real_location = station_obj.location
        if real_location and False:
            data_location = Location.from_tc(station['x'], station['y'])
            delta = real_location.distance(data_location)
            issues_score = 0
            if delta > 300:
                issues_score = 35
                logging.warning("+{: <6} Haltepunkt {} ist ??ber 300 km vom echten Punkt entfernt.".format(issues_score, station['ril100']))
            elif delta > 60:
                issues_score = 15
                logging.warning("+{: <6} Haltepunkt {} ist ??ber 60 km vom echten Punkt entfernt.".format(issues_score, station['ril100']))
            elif delta > 20:
                issues_score = 5
                logging.warning("+{: <6} Haltepunkt {} ist ??ber 20 km vom echten Punkt entfernt.".format(issues_score, station['ril100']))
            issues += issues_score

        # 1.2. Platforms
        real_platforms = station_obj.platforms
        if real_platforms and 'platformLength' in station:
            # Length checking is disabled for now because it might not work correctly
            if False:
                data_platform_length = station['platformLength']
                delta = abs(station_obj.platform_length - data_platform_length)
                issues_score = 0
                if delta > 100:
                    issues_score = 100
                    logging.warning("+{: <6} Haltepunkt {} hat eine um > 100 m abweichende Bahnsteigl??nge."
                                    .format(issues_scorestation['ril100']))
                elif delta > 20:
                    issues_score = 10
                    logging.warning("+{: <6} Haltepunkt {} hat eine um > 20 m abweichende Bahnsteigl??nge."
                                    .format(issues_score, station['ril100']))
                issues += issues_score

                data_platforms = station['platforms']
                delta = abs(station_obj.platform_count - data_platforms)
                if delta > 2:
                    # Platform count is not used anyway
                    issues_score = 10
                    logging.warning("+{: <6} Haltepunkt {} hat eine falsche Bahnsteiganzahl. Soll: {} - Ist: {}"
                                    .format(issues_score, station['ril100']))
                    issues += issues_score

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

    train_equipments = [sub_equipment['idString'] for train_equipment in train_equipment_json.data for sub_equipment in
                        tc_utils.expand_objects(train_equipment)]

    for path in paths:
        # Add default values if necessary
        if 'group' not in path:
            path['group'] = 0
        if 'electrified' not in path:
            path['electrified'] = True

        # 2.0. has speed and length
        if 'maxSpeed' not in path:
            issues_score = 10000
            logging.warning("+{: <6} Pfad hat keine vMax: {}".format(issues_score, print_path(path)))
            issues += issues_score
        if 'length' not in path:
            issues_score = 10000
            logging.warning("+{: <6} Pfad hat keine L??nge: {}".format(issues_score, print_path(path)))
            issues += issues_score

        # 2.1. Speed - group
        if 'maxSpeed' in path and path['maxSpeed'] >= 250 and path['group'] != 2:
            issues_score = 50
            logging.warning("+{: <6} Nicht-SFS mit >= 250 km/h: {}".format(issues_score, print_path(path)))
            issues += issues_score

        # 2.2. SFS - electrified
        if path['group'] == 2 and not path['electrified']:
            issues_score = 10000
            logging.warning("Nicht elektrifizierte SFS: {}".format(print_path(path)))
            issues += issues_score

        issues_score = 0
        # 2.3. Path length for Non-SFS
        if path['group'] != 2 and path['length'] > 80:
            issues_score = 45
            logging.warning("+{: <6} >80 km langer Streckenabschnitt auf Nicht-SFS: {}".format(issues_score, print_path(path)))
        elif path['group'] != 2 and path['length'] > 40:
            issues_score = 5
            logging.warning("+{: <6} >40 km langer Streckenabschnitt auf Nicht-SFS: {}".format(issues_score, print_path(path)))
        issues += issues_score

        # 2.4. realistic twistingFactor
        if path['twistingFactor'] > 0.5:
            issues_score = 5
            logging.info("+{: <6} twistingFactor > 0.5: {}".format(
                issues_score,
                print_path(path)
            ))
            issues += issues_score

        # 2.5. Only cover existing stations
        if path['start'] not in selected_codes:
            issues_score = 10000
            logging.error("+{: <6} Nicht existierender Start-Bahnhof: {}".format(issues_score, path['start']))
            issues += issues_score
        if path['end'] not in selected_codes:
            issues_score = 10000
            logging.error("+{: <6} Nicht existierender End-Bahnhof: {}".format(issues_score, path['start']))
            issues += issues_score

        # 2.6. SFS-name for non-SFS
        if 'name' in path:
            if 'SFS' in path['name'] and not path['group'] == 2:
                issues_score = 20
                logging.warning("+{: <6} Strecke hat SFS im Namen, ist aber keine: {}".format(issues_score, print_path(path)))
                issues += issues_score
            if 'SFS' in path['name']:
                issues_score = 5
                logging.warning("+{: <6} Strecke hat SFS im Namen, obwohl es als Kategorie bereits angezeigt wird: {}"
                                .format(issues_score, print_path(path)))
                issues += issues_score

        # 2.7. Don't allow annotations
        if 'start_long' in path or 'end_long' in path:
            issues_score = 800
            logging.warning("+{: <6} Langer Haltestellenname immer noch vorhanden: {}"
                            .format(issues_score, print_path(path)))
            issues += issues_score

        # 2.8. Check for unknown equipments
        if 'neededEquipments' in path:
            for used_equipment in path['neededEquipments']:
                if used_equipment not in train_equipments:
                    issues_score = 10000
                    logging.error("+{: <6} Strecke {} hat nicht existierendes Equipment: {}"
                                  .format(issues_score, print_path(path), used_equipment))
                    issues += issues_score

    # Step 3: graph-based validation
    logging.info(" --- Routing --- ")
    path_edges = [(path['start'], path['end'], path) for path in paths
                  if path['start'] in selected_codes and path['end'] in selected_codes]

    graph = build_tc_graph(selected_codes, path_edges)
    if not is_connected(graph):
        issues_score = 10000
        logging.error("+{: <6} Das Netz ist nicht zusammenh??ngend.".format(issues_score))
        for node, degree in graph.degree():
            if degree == 0:
                logging.error(" {: <6} Haltepunkt ohne Route: {}".format('', node))
        issues += issues_score

    # Step 4: trains
    logging.info(" --- Train.json --- ")
    # 4.1. unique train IDs
    train_ids = [train['id'] for train in train_json.data]
    train_ids.sort()
    for train_id, next_id in zip(train_ids, train_ids[1:]):
        if train_id == next_id:
            issues_score = 10000
            logging.error("+{: <6} Doppelte Train-ID: {}".format(issues_score, train_id))
            issues += issues_score

    # 4.2. realistic acceleration
    # TODO: -
    pass

    # 4.3. only existing train equipments
    for train in train_json.data:
        if 'equipments' in train:
            for used_equipment in train['equipments']:
                if used_equipment not in train_equipments:
                    issues_score = 10000
                    logging.error("+{: <6} Zug {} hat nicht existierendes Equipment: {}"
                                  .format(issues_score, train['id'], used_equipment))
                    issues += issues_score

    # 4.4. operationCosts
    # TODO: Better validation (e.g., high force = high costs)
    for train in train_json.data:
        if 'operationCosts' not in train:
            train['operationCosts'] = 0
        if train['force'] > 0 and train['operationCosts'] < 5:
            issues_score = 10000
            logging.error("+{: <6} Zug {} (ID {}) hat keine/zu geringe operationCosts: {}"
                          .format(issues_score, train['name'] if 'name' in train else 'Unbenannt', train['id'], train['operationCosts']))
            issues += issues_score

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
                    issues_score = 10000
                    logging.error("+{: <6} Nicht existierender Haltepunkt: {}".format(issues_score, station))
                    issues += issues_score

    return issues

