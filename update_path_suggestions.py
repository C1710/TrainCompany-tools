from __future__ import annotations

import argparse
import os
from os import PathLike

from structures.task import *
from tc_utils import TcFile
from validation import build_tc_graph


def update_path_suggestions(tc_directory: PathLike | str) -> TcFile:
    path_json = TcFile('Path', tc_directory)
    station_json = TcFile('Station', tc_directory)
    task_model_json = TcFile('TaskModel', tc_directory)

    selected_codes = [station['ril100'] for station in station_json.data]

    # Expand sub-paths
    paths = []
    for path in path_json.data:
        if 'objects' not in path:
            paths.append(path)
        else:
            for sub_path in path.pop('objects'):
                new_path = path.copy()
                new_path.update(sub_path)
                paths.append(new_path)

    path_edges = [(path['start'], path['end'], path) for path in paths
                  if path['start'] in selected_codes and path['end'] in selected_codes]

    graph = build_tc_graph(selected_codes, path_edges)
    for task in task_model_json.data:
        update_path_suggestion(task, graph)
    return task_model_json


def update_path_suggestion(task: Dict[str, Any],
                           graph: nx.Graph):
    if 'stations' in task:
        stations = task['stations']
        task['pathSuggestion'] = without_trivial_nodes(graph, stations, get_shortest_path(graph, stations))
        if task['pathSuggestion'] == task['stations']:
            task.pop('pathSuggestion')
    elif 'objects' in task:
        for sub_task in task['objects']:
            update_path_suggestion(sub_task, graph)
    if 'group' in task and task['group'] == 0 and 'pathSuggestion' in task:
        task.pop('pathSuggestion')


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    parser = argparse.ArgumentParser(description='Füge pathSuggestions hinzu')
    parser.add_argument('--tc-dir', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    args = parser.parse_args()

    tasks_json = update_path_suggestions(tc_directory=args.tc_directory)

    tasks_json.save_formatted()
