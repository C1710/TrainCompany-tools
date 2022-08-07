import logging
from typing import Dict, Any, List, Optional, Generator, Set

import networkx as nx

from cli_utils import format_list_double_quotes


def get_shortest_path(graph: nx.Graph,
                      stations: List[str],
                      train: Optional[Dict[str, Any]] = None,
                      use_sfs: bool = True,
                      accept_non_electrified: bool = True,
                      avoid_equipments: Optional[Set[str]] = None,
                      log: bool = True) -> Optional[List[str]]:
    if len(stations) >= 2:
        if avoid_equipments is None:
            avoid_equipments = set()
        # Only use the track's maxSpeed if there is no train
        train_max_speed = train['speed'] if train and 'speed' in train else 5000

        visited_stations = set()

        def edge_weight(start: str, end: str, edge: Dict[str, Any]) -> Optional[float]:
            assert edge['maxSpeed'] >= 1 and train_max_speed >= 1
            weight = edge['length'] / min(edge['maxSpeed'], train_max_speed)
            assert weight > 0
            if not accept_non_electrified and not edge.get('electrified'):
                # We simply set the weight to something larger
                weight *= 20
            if not use_sfs and edge.get('group') == 2:
                weight *= 5
            needed_equipments = set(edge.get('neededEquipments')) if 'neededEquipments' in edge else set()
            if not needed_equipments.isdisjoint(avoid_equipments):
                weight *= 20
            if end in stations:
                # Don't try to visit a stop in a subpath.
                # If it is a path to the stop, we will have no other choice but to visit it.
                weight = 10000
            if end in visited_stations:
                # Don't visit anything twice
                return None
            return weight

        shortest_paths = []
        for station_from, station_to in zip(stations, stations[1:]):
            try:
                if station_from not in graph.nodes:
                    station_from = station_from.upper()
                if station_to not in graph.nodes:
                    station_to = station_to.upper()
                if graph.has_edge(station_from, station_to):
                    path = [station_from, station_to]
                else:
                    path = nx.dijkstra_path(graph, station_from, station_to,
                                            weight=edge_weight)
            except nx.exception.NetworkXNoPath as e:
                # We will need to try to find an alternative path
                if log:
                    logging.error("Konnte keinen Pfad finden für {}".format(format_list_double_quotes(stations)))
                    logging.debug("Pfad bisher: {}".format(format_list_double_quotes(merge_shortest_paths(shortest_paths))))
                raise e
            shortest_paths.append(path)
            visited_stations.update(path)

        # Assemble the total shortest path
        return merge_shortest_paths(shortest_paths)
    else:
        return None


def merge_shortest_paths(shortest_paths: List[List[str]]) -> List[str]:
    shortest_path = shortest_paths.pop(0)
    for sub_path in shortest_paths:
        shortest_path.extend(sub_path[1:])
    return shortest_path


# TODO: Add weight parameter
def get_shortest_path_distance(graph: nx.Graph,
                               stations: List[str]) -> Optional[List[str]]:
    return get_shortest_path(graph, stations, train={'speed': 1})


def without_trivial_nodes(graph: nx.Graph, stations: List[str], path: List[str],
                          station_groups: Optional[Dict[str, int]] = None) -> List[str]:
    return list(_without_trivial_nodes(graph, stations, path, station_groups))


def _without_trivial_nodes(graph: nx.Graph, stations: List[str], path: List[str],
                           station_groups: Optional[Dict[str, int]] = None,
                           add_adjacent_2_degree: bool = False) -> Generator[str, None, None]:
    yield path[0]
    for last_node, this_node, next_node in zip(path, path[1:], path[2:]):
        if this_node in stations:
            yield this_node
            continue
        # We want to yield all nodes that have degree != 2 themselves or an adjacent one.
        # However, we do not care if one of the other nodes has degree 1, because it would still be trivial
        if graph.degree[this_node] != 2 \
                or (add_adjacent_2_degree and (graph.degree[last_node] > 2 or graph.degree[next_node] > 2)):
            if not station_groups or station_groups.get(this_node) not in (5, 6):
                yield this_node
    yield path[-1]
