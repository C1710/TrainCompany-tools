from __future__ import annotations

import networkx as nx
from typing import List, Tuple, Any, Dict, Optional, Set

from tc_utils import TcFile, expand_objects, flatten_objects
from validation.shortest_paths import get_shortest_path, without_trivial_nodes


def build_tc_graph(stations: List[str], paths: List[Tuple[str, str] | Tuple[str, str, Dict[str, Any]]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(stations)
    graph.add_edges_from(paths)
    return graph


def graph_from_files(station_json: TcFile, path_json: TcFile) -> nx.Graph:
    station_codes = [station['ril100'] for station in flatten_objects(station_json.data)]
    path_edges = [(path['start'], path['end'], path) for path in flatten_objects(path_json.data)
                  if path['start'] in station_codes and path['end'] in station_codes]

    return build_tc_graph(station_codes, path_edges)


def get_path_suggestion(graph: nx.Graph, stations: List[str],
                        use_sfs: bool = True,
                        non_electrified: bool = True,
                        avoid_equipments: Optional[Set[str]] = None) -> List[str]:
    path_complete = get_shortest_path(graph, stations,
                                      use_sfs=use_sfs,
                                      non_electrified=non_electrified,
                                      avoid_equipments=avoid_equipments)
    assert nx.is_path(graph, path_complete)
    path_without_trivial_nodes = without_trivial_nodes(graph, stations, path_complete)
    return path_without_trivial_nodes
