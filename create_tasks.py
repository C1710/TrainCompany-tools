from __future__ import annotations

import argparse
import os
import sys
from os import PathLike
from typing import Type, Generator

from cli_utils import check_files
from structures.task import *
from tc_utils import TcFile
from validation import build_tc_graph


def create_tasks(Gattung: Type,
                 line_number: Optional[int],
                 stations: List[List[str]],
                 name: Optional[str] = None,
                 tc_directory: PathLike | str = '..',
                 pronouns: Optional[Pronouns] = None,
                 add_path_suggestion: bool = False
                 ) -> TcFile:
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
            for sub_task in path.pop('objects'):
                new_task = path.copy()
                new_task.update(sub_task)
                paths.append(new_task)

    path_edges = [(path['start'], path['end'], path) for path in paths
                  if path['start'] in selected_codes and path['end'] in selected_codes]

    graph = build_tc_graph(selected_codes, path_edges)

    tasks: List[GattungTask] = [Gattung(
        line=line_number,
        stations=stations_task,
        line_name=name,
        name_pronouns=pronouns
    ) for stations_task in stations]
    for task in tasks:
        task.add_sfs_description(graph=graph)
    tasks_dicts = [task.to_dict(graph, add_suggestion=add_path_suggestion) for task in tasks]
    tasks_merged = merge_task_dicts(tasks_dicts)
    for merged_task in tasks_merged:
        extract_remaining_subtask_from_task(merged_task)
        cleanup_task(merged_task)
    task_groups = [task['group'] if 'group' in task else -1 for task in task_model_json.data]
    assert -1 not in task_groups
    # Insert before the first 0 group entry
    first_0_index = task_groups.index(0)
    for task in tasks_merged:
        if task['group'] == 1:
            task_model_json.data.insert(first_0_index, task)
            first_0_index += 1
        else:
            task_model_json.data.append(task)

    return task_model_json


if __name__ == '__main__':
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    gattungen = {task.gattung: task for task in (SbahnTask, RbTask, ReTask, IreTask,
                                                 IcTask, EcTask,
                                                 IceTask, IceSprinterTask, EceTask)}

    parser = argparse.ArgumentParser(description='Erstelle neue Strecken')
    parser.add_argument('task_type', choices=list(gattungen), type=str, help="Die Zuggattung")
    parser.add_argument('--number', type=str, help="Die Liniennummer")
    parser.add_argument('--name', type=str, help="Linienname")
    parser.add_argument('--article', type=str, help='Artikel des Liniennames', choices=['der', 'die'],
                        required='--name' in sys.argv)
    parser.add_argument('--stations', metavar='RIL100', type=str, nargs='+', action='append', required=True,
                        help='Die RIL100-Codes der angefahrenen bahnhöfe, die hinzugefügt werden sollen')
    parser.add_argument('--no_add_suggestion', action='store_true',
                        help="Fügt der Task einen Hinweis auf den kürzesten Pfad hinzu.")
    parser.add_argument('--tc-dir', dest='tc_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.dirname(script_dir),
                        help="Das Verzeichnis, in dem sich die TrainCompany-Daten befinden")
    parser.add_argument('--data-dir', dest='data_directory', metavar='VERZEICHNIS', type=str,
                        default=os.path.join(script_dir, 'data'),
                        help="Das Verzeichnis, in dem sich die DB OpenData-Datensätze befinden")
    args = parser.parse_args()

    check_files(args.tc_directory, args.data_directory)

    article_to_pronoun = {
        'der': ErIhmPronouns(),
        'die': SieIhrPronouns(),
        None: None
    }

    tasks_json = create_tasks(
                     gattungen[args.task_type],
                     line_number=args.number,
                     stations=args.stations,
                     tc_directory=args.tc_directory,
                     name=args.name,
                     pronouns=article_to_pronoun[args.article],
                     add_path_suggestion=not args.no_add_suggestion
                 )

    tasks_json.save_formatted()
