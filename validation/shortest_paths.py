from typing import Dict, Any, List, Optional, Generator

import networkx as nx


def get_shortest_path(graph: nx.Graph,
                      stations: List[str],
                      train: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
    if len(stations) >= 2:
        # Only use the track's maxSpeed if there is no train
        train_max_speed = train['speed'] if train and 'speed' in train else 5000
        shortest_paths = (
            nx.dijkstra_path(graph, station_from, station_to,
                             weight=lambda start, end, edge: edge['length'] / min(edge['maxSpeed'], train_max_speed))
            for station_from, station_to in zip(stations, stations[1:])
        )
        shortest_path = list(shortest_paths.__next__())
        for sub_path in shortest_paths:
            shortest_path.extend(sub_path[1:])
        return shortest_path
    else:
        return None


# TODO: Add weight parameter
def get_shortest_path_distance(graph: nx.Graph,
                               stations: List[str]) -> Optional[List[str]]:
    if len(stations) >= 2:
        shortest_paths = (
            nx.dijkstra_path(graph, station_from, station_to,
                             weight=lambda start, end, edge: edge['length'])
            for station_from, station_to in zip(stations, stations[1:])
        )
        shortest_path = list(shortest_paths.__next__())
        for sub_path in shortest_paths:
            shortest_path.extend(sub_path[1:])
        return shortest_path
    else:
        return None


def without_trivial_nodes(graph: nx.Graph, stations: List[str], path: List[str]) -> List[str]:
    return list(_without_trivial_nodes(graph, stations, path))


def _without_trivial_nodes(graph: nx.Graph, stations: List[str], path: List[str]) -> Generator[str, None, None]:
    yield path[0]
    for last_node, this_node, next_node in zip(path, path[1:], path[2:]):
        if this_node in stations:
            yield this_node
            continue
        # We want to yield all nodes that have degree != 2 themselves or an adjacent one.
        # However, we do not care if one of the other nodes has degree 1, because it would still be trivial
        if graph.degree[last_node] > 2 or graph.degree[this_node] != 2 or graph.degree[next_node] > 2:
            yield this_node
    yield path[-1]

