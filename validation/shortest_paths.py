from typing import Dict, Any, List, Optional

import networkx as nx


def get_shortest_path(graph: nx.Graph,
                      stations: List[str],
                      train: Optional[Dict[str, Any]] = None) -> Optional[List[str]]:
    if len(stations) >= 2:
        # Only use the track's maxSpeed if there is no train
        train_max_speed = train['speed'] if train and 'maxSpeed' in train else 5000
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
    return [node for node, degree in graph.degree(path) if degree > 2 or node in stations]
