from __future__ import annotations

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property

import networkx as nx
from typing import List, Tuple, Any, Dict, Optional, Set, ClassVar

from tc_utils import TcFile, expand_objects, flatten_objects
from validation.shortest_paths import get_shortest_path, without_trivial_nodes, has_direct_path


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
    full_path: bool = field(default=False)
    auto_service: bool = field(default=False)
    distance: bool = field(default=False)
    max_speed: int = field(default=5000)

    @property
    def train(self) -> Dict[str, Any]:
        if self.distance:
            return {"speed": 1}
        else:
            return {"speed": self.max_speed}

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
        parser.add_argument("--distance", action="store_true",
                            help="Sucht den kürzesten Pfad anhand der Strecke, nicht der Geschwindigkeit")
        parser.add_argument("--max-speed", type=int, default=5000,
                            help="Die angenommene Höchstgeschwindigkeit eines Zuges.")
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
                auto_service=args.auto_service if 'auto_service' in args else False,
                distance=args.distance,
                max_speed=args.max_speed
            )
        else:
            # Use the default suggestion config for the given service level
            # TODO: Allow to override stuff
            base_suggestion = path_suggestion_configs.get(args.path_suggestion_service, PathSuggestionConfigs.SPECIAL)
            return base_suggestion


class PathSuggestionConfigs(Enum):
    HGV = PathSuggestionConfig(
        use_sfs=True,
        non_electrified=False
    )
    IC = PathSuggestionConfig(
        use_sfs=True,
        max_speed=200
    )
    REGIO = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"},
        max_speed=190
    )
    REGIO_SHORT = PathSuggestionConfig(
        use_sfs=False,
        avoid_equipments={"ETCS", "KRM", "TVM"},
        max_speed=160
    )
    SPECIAL = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"}
    )
    FREIGHT_IMPORTANT = PathSuggestionConfig(
        avoid_equipments={"KRM", "TVM"},
        max_speed=200
    )
    FREIGHT = FREIGHT_IMPORTANT


path_suggestion_configs: Dict[int, PathSuggestionConfig] = {
    0: PathSuggestionConfigs.HGV.value,
    1: PathSuggestionConfigs.IC.value,
    2: PathSuggestionConfigs.REGIO.value,
    3: PathSuggestionConfigs.REGIO_SHORT.value,
    4: PathSuggestionConfigs.SPECIAL.value,
    5: PathSuggestionConfigs.REGIO.value,
    10: PathSuggestionConfigs.FREIGHT_IMPORTANT.value,
    11: PathSuggestionConfigs.FREIGHT.value
}


def get_path_suggestion(graph: nx.Graph, stations: List[str],
                        config: PathSuggestionConfig = PathSuggestionConfig(),
                        station_to_group: Optional[Dict[str, int]] = None,
                        existing_path_suggestion: List[str] | None = None) -> List[str] | None:
    path_complete = get_shortest_path(graph,
                                      stations=existing_path_suggestion if existing_path_suggestion else stations,
                                      config=config)
    if not path_complete:
        # For single stations, we can't compute a pathSuggestion
        return None
    assert nx.is_simple_path(graph, path_complete), path_complete
    if not config.full_path:
        path_without_trivial_nodes = without_trivial_nodes(graph, stations, path_complete, station_to_group)
        return path_without_trivial_nodes
    else:
        return path_complete


def fixed_path_suggestion(graph: nx.Graph, stations: List[str],
                          existing_path_suggestion: List[str],
                          config: PathSuggestionConfig = PathSuggestionConfig(),
                          station_to_group: Optional[Dict[str, int]] = None) -> List[str] | None:
    new_path_complete = []
    updated = False
    existing_path_suggestion_set = set(existing_path_suggestion)
    for segment_start, segment_end in nx.utils.pairwise(existing_path_suggestion):
        new_path_complete.append(segment_start)
        if not has_direct_path(graph, segment_start, segment_end, existing_path_suggestion_set):
            updated = True
            expanded_segment = get_shortest_path(graph, [segment_start, segment_end], config=config)
            if expanded_segment:
                # Only add the stations _between_ the start and end of the segment
                expanded_segment = expanded_segment[1:-1]
                new_path_complete.extend(expanded_segment)
    new_path_complete.append(existing_path_suggestion[-1])

    if not config.full_path and updated:
        new_path = without_trivial_nodes(graph, stations, new_path_complete, station_to_group)
        return new_path
    else:
        return new_path_complete
