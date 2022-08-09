from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field

import networkx as nx
from typing import List, Tuple, Any, Dict, Optional, Set, ClassVar

from tc_utils import TcFile, expand_objects, flatten_objects
from validation.shortest_paths import get_shortest_path, without_trivial_nodes


def build_tc_graph(stations: List[str], paths: List[Tuple[str, str] | Tuple[str, str, Dict[str, Any]]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(stations)
    graph.add_edges_from(paths)
    return graph


def graph_from_files(station_json: TcFile, path_json: TcFile) -> nx.Graph:
    station_codes = [station['ril100'].upper() for station in flatten_objects(station_json.data)]
    path_edges = [(path['start'].upper(), path['end'].upper(), path) for path in flatten_objects(path_json.data)
                  if path['start'].upper() in station_codes and path['end'].upper() in station_codes]

    return build_tc_graph(station_codes, path_edges)


@dataclass
class PathSuggestionConfig:
    use_sfs: bool = field(default=True)
    non_electrified: bool = field(default=True)
    avoid_equipments: Set[str] = field(default_factory=set)
    full_path: bool = False

    @classmethod
    def add_cli_args(cls, parser: ArgumentParser):
        parser.add_argument("--avoid-sfs", action='store_true',
                            help="Versucht, SFS zu meiden.")
        parser.add_argument("--electrified", action='store_true',
                            help="Versucht, nicht-elektrifizierte Strecken zu meiden.")
        parser.add_argument("--full-path", action='store_true',
                            help="Vereinfacht den Pfad nicht.")
        parser.add_argument("--avoid-equipments", type=str, nargs='+', metavar="EQUIPMENT",
                            help="Equipments, die gemieden werden sollen.")

    @classmethod
    def from_cli_args(cls, args: Namespace) -> PathSuggestionConfig:
        return cls(
            use_sfs=not args.avoid_sfs,
            non_electrified=not args.electrified,
            avoid_equipments=args.avoid_equipments,
            full_path=args.full_path
        )


def get_path_suggestion(graph: nx.Graph, stations: List[str],
                        config: PathSuggestionConfig = PathSuggestionConfig(),
                        station_to_group: Optional[Dict[str, int]] = None) -> List[str]:
    path_complete = get_shortest_path(graph, stations,
                                      use_sfs=config.use_sfs,
                                      accept_non_electrified=config.non_electrified,
                                      avoid_equipments=config.avoid_equipments)
    assert nx.is_simple_path(graph, path_complete)
    if not config.full_path:
        path_without_trivial_nodes = without_trivial_nodes(graph, stations, path_complete, station_to_group)
        return path_without_trivial_nodes
    else:
        return path_complete
