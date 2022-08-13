from __future__ import annotations

import argparse
import logging
from os import PathLike

from cli_utils import add_default_cli_args
from structures.task import *
from tc_utils import TcFile
from validation.graph import graph_from_files, path_suggestion_configs


def update_path_suggestions(tc_directory: PathLike | str,
                            force: bool = False,
                            config: PathSuggestionConfig | None = None,
                            graph: nx.Graph | None = None) -> TcFile:
    if not config:
        config = PathSuggestionConfig()

    station_json = TcFile('Station', tc_directory)

    if not graph:
        path_json = TcFile('Path', tc_directory)
        graph = graph_from_files(station_json, path_json, case_sensitive=True)

    task_model_json = TcFile('TaskModel', tc_directory)

    station_groups = {station['ril100']: station.get('group') for station in station_json.data}

    for task in task_model_json.data:
        update_path_suggestion(task, graph.copy(as_view=True), force=force, config=config,
                               station_to_group=station_groups)

    return task_model_json


def update_path_suggestion(task: Dict[str, Any],
                           graph: nx.Graph,
                           config: PathSuggestionConfig,
                           station_to_group: Dict[str, int],
                           force: bool = False):
    if 'stations' in task:
        stations = task['stations']
        if force or 'pathSuggestion' not in task:
            try:
                if config.auto_service:
                    logging.debug("Using automatic pathSuggestion config")
                    if 'service' in task:
                        config_ = path_suggestion_configs[task['service']]
                    else:
                        logging.warning("Task enthält kein \"service\": {}".format(task))
                        config_ = config
                else:
                    config_ = config
                path_suggestion = get_path_suggestion(graph, stations, config=config_,
                                                      station_to_group=station_to_group)
                if path_suggestion:
                    task['pathSuggestion'] = path_suggestion
            except nx.exception.NetworkXNoPath as e:
                logging.exception("Konnte keine pathSuggestion finden", exc_info=e)
        if 'pathSuggestion' in task and (task['pathSuggestion'] == task['stations'] or not task['pathSuggestion']):
            task.pop('pathSuggestion')
    if 'objects' in task:
        for sub_task in task['objects']:
            update_path_suggestion(sub_task, graph, config, station_to_group, force)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Füge pathSuggestions hinzu')
    add_default_cli_args(parser, data_directory=False)
    parser.add_argument('--force', action='store_true',
                        help="Aktualisiert alle pathSuggestions, auch existierende")
    PathSuggestionConfig.add_cli_args(parser, allow_auto_service=True)
    args = parser.parse_args()
    config = PathSuggestionConfig.from_cli_args(args)

    tasks_json = update_path_suggestions(tc_directory=args.tc_directory, force=args.force, config=config)

    tasks_json.save_formatted()
