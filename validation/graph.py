from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from enum import Enum

import networkx as nx
from typing import List, Tuple, Any, Dict, Optional, Set, ClassVar

from tc_utils import TcFile, expand_objects, flatten_objects
from validation.shortest_paths import get_shortest_path, without_trivial_nodes


def build_tc_graph(stations: List[str], paths: List[Tuple[str, str] | Tuple[str, str, Dict[str, Any]]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(stations)
    graph.add_edges_from(paths)
    return graph


def graph_from_files(station_json: TcFile, path_json: TcFile, case_sensitive: bool = False) -> nx.Graph:
    maybe_upper = str.upper if not case_sensitive else lambda s: s

    station_codes = [maybe_upper(station['ril100']) for station in flatten_objects(station_json.data)]
    path_edges = [(maybe_upper(path['start']), maybe_upper(path['end']), path) for path in
                  flatten_objects(path_json.data)
                  if maybe_upper(path['start']) in station_codes and maybe_upper(path['end']) in station_codes]

    return build_tc_graph(station_codes, path_edges)


@dataclass
class PathSuggestionConfig:
    use_sfs: bool = field(default=True)
    non_electrified: bool = field(default=True)
    avoid_equipments: Set[str] = field(default_factory=set)
    full_path: bool = field(default=False),
    auto_service: bool = field(default=False)

    @classmethod
    def add_cli_args(cls, parser: ArgumentParser, allow_auto_service: bool = False):
        parser.add_argument("--avoid-sfs", action='store_true',
                            help="Versucht, SFS zu meiden.")
        parser.add_argument("--electrified", action='store_true',
                            help="Versucht, nicht-elektrifizierte Strecken zu meiden.")
        parser.add_argument("--full-path", action='store_true',
                            help="Vereinfacht den Pfad nicht.")
        parser.add_argument("--avoid-equipments", type=str, nargs='+', metavar="EQUIPMENT",
                            help="Equipments, die gemieden werden sollen.")
        if allow_auto_service:
            parser.add_argument("--auto-service", action="store_true",
                                help="pathSuggestion-Konfiguration automatisch festlegen.")
        parser.add_argument("--path-suggestion-service", type=int,
                            help="Nutzt die Standard-PathSuggestion-Konfiguration für die angegebene Aufgabenkategorie.")

    @classmethod
    def from_cli_args(cls, args: Namespace) -> PathSuggestionConfig:
        if args.path_suggestion_service is None:
            return cls(
                use_sfs=not args.avoid_sfs,
                non_electrified=not args.electrified,
                avoid_equipments=args.avoid_equipments,
                full_path=args.full_path,
                auto_service=args.auto_service,
            )
        else:
            # Use the default suggestion config for the given service level
            # TODO: Allow to override stuff
            base_suggestion = path_suggestion_configs[args.path_suggestion_service]
            return base_suggestion


class PathSuggestionConfigs(PathSuggestionConfig, Enum):
    HGV = PathSuggestionConfig(
        use_sfs=True,
        non_electrified=False
    )
    IC = PathSuggestionConfig(
        use_sfs=True
    )
    REGIO = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"}
    )
    REGIO_SHORT = PathSuggestionConfig(
        use_sfs=False,
        avoid_equipments={"ETCS", "KRM", "TVM"}
    )
    SPECIAL = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"}
    )
    FREIGHT_IMPORTANT = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"}
    )
    FREIGHT = FREIGHT_IMPORTANT


path_suggestion_configs: Dict[int, PathSuggestionConfig] = {
    0: PathSuggestionConfigs.HGV,
    1: PathSuggestionConfigs.IC,
    2: PathSuggestionConfigs.REGIO,
    3: PathSuggestionConfigs.REGIO_SHORT,
    4: PathSuggestionConfigs.SPECIAL,
    10: PathSuggestionConfigs.FREIGHT_IMPORTANT,
    11: PathSuggestionConfigs.FREIGHT
}


def get_path_suggestion(graph: nx.Graph, stations: List[str],
                        config: PathSuggestionConfig = PathSuggestionConfig(),
                        station_to_group: Optional[Dict[str, int]] = None) -> List[str] | None:
    path_complete = get_shortest_path(graph, stations,
                                      use_sfs=config.use_sfs,
                                      accept_non_electrified=config.non_electrified,
                                      avoid_equipments=config.avoid_equipments)
    if not path_complete:
        # For single stations, we can't compute a pathSuggestion
        return None
    assert nx.is_simple_path(graph, path_complete)
    if not config.full_path:
        path_without_trivial_nodes = without_trivial_nodes(graph, stations, path_complete, station_to_group)
        return path_without_trivial_nodes
    else:
        return path_complete
