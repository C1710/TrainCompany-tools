from __future__ import annotations

import argparse
import logging
from os import PathLike

from cli_utils import add_default_cli_args, use_default_cli_args
from structures.task import *
from tc_utils import TcFile
from validation.graph import graph_from_files, path_suggestion_configs, fixed_path_suggestion


def update_path_suggestions(tc_directory: PathLike | str,
                            force: bool = False,
                            fix: bool = False,
                            preserve_existing_path_suggestions: bool = True,
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
        update_path_suggestion(task, graph.copy(as_view=True),
                               force=force, fix=fix, preserve=preserve_existing_path_suggestions,
                               config=config,
                               station_to_group=station_groups)

    return task_model_json


def update_path_suggestion(task: Dict[str, Any],
                           graph: nx.Graph,
                           config: PathSuggestionConfig,
                           station_to_group: Dict[str, int],
                           force: bool = False,
                           fix: bool = False,
                           preserve: bool = False,
                           service: int | None = None,
                           stops_everywhere: bool | None = None):
    if 'service' in task:
        service = task['service']
    if 'stopsEverwhere' in task:
        stops_everywhere = task['stopsEverwhere']
    if 'stopsEverywhere' in task:
        stops_everywhere = task['stopsEverywhere']
    if 'stations' in task and not stops_everywhere:
        stations = task['stations']
        if 'pathSuggestion' in task:
            preserve_ = preserve
        else:
            # We don't want to preserve the newly added pathSuggestions, only existing ones (even if they are the same as stations)
            preserve_ = False
        if fix or force or 'pathSuggestion' not in task:
            try:
                if config.auto_service:
                    logging.debug("Using automatic pathSuggestion config")
                    if service is not None:
                        config_ = path_suggestion_configs[service]
                    else:
                        logging.warning("Task enthält kein \"service\": {}".format(task))
                        config_ = config
                else:
                    config_ = config
                if force or 'pathSuggestion' not in task:
                    path_suggestion = get_path_suggestion(graph, stations, config=config_,
                                                          station_to_group=station_to_group)
                elif fix:
                    # We want to change as little as possible and be as close to the game's strategy as possible.
                    config_.distance = True
                    path_suggestion = fixed_path_suggestion(graph, stations, config=config_,
                                                            existing_path_suggestion=task['pathSuggestion'],
                                                            station_to_group=station_to_group)
                if path_suggestion:
                    task['pathSuggestion'] = path_suggestion
            except nx.exception.NetworkXNoPath as e:
                logging.exception("Konnte keine pathSuggestion finden", exc_info=e)
        if 'pathSuggestion' in task and (
                task['pathSuggestion'] == task['stations']
                or not task['pathSuggestion']) \
                and not preserve_:
            task.pop('pathSuggestion')
    if stops_everywhere:
        if 'pathSuggestion' in task:
            task.pop('pathSuggestion')
    if 'objects' in task:
        for sub_task in task['objects']:
            update_path_suggestion(sub_task, graph, config=config, station_to_group=station_to_group,
                                   force=force, fix=fix, preserve=preserve, service=service,
                                   stops_everywhere=stops_everywhere)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Füge pathSuggestions hinzu')
    add_default_cli_args(parser, data_directory=False)
    fix_or_force = parser.add_mutually_exclusive_group(required=False)
    fix_or_force.add_argument('--force', action='store_true',
                              help="Aktualisiert alle pathSuggestions, überschreibt auch existierende")
    fix_or_force.add_argument('--fix', action='store_true',
                              help="Schließt auch Lücken in bestehenden pathSuggestions")
    parser.add_argument("--no-preserve", action='store_true',
                        help="Löscht bestehende pathSuggestions, wenn sie redundant sind")
    PathSuggestionConfig.add_cli_args(parser, allow_auto_service=True)
    args = parser.parse_args()
    use_default_cli_args(args)
    config = PathSuggestionConfig.from_cli_args(args)

    tasks_json = update_path_suggestions(tc_directory=args.tc_directory, force=args.force, fix=args.fix, config=config)

    tasks_json.save_formatted()
