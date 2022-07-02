from typing import Dict, Any, List, Optional

import networkx as nx


def get_shortest_path(graph: nx.Graph,
                      train: Dict[str, Any],
                      task: Dict[str, Any]) -> Optional[List[str]]:
    if 'stations' in task and len(task['stations']) >= 2:
        train_max_speed = train['speed']
        shortest_paths = (
            nx.dijkstra_path(graph, station_from, station_to,
                             weight=lambda start, end, edge: min(edge['maxSpeed'], train_max_speed) / edge['length'])
            for station_from, station_to in zip(task['stations'], task['stations'][1:])
        )
        shortest_path = list(shortest_paths.__next__())
        for sub_path in shortest_paths:
            shortest_path.extend(sub_path[1:])
            return shortest_path
    else:
        return None


def without_trivial_nodes(graph: nx.Graph, path: List[str]) -> List[str]:
    return [node for node, degree in graph.degree(path) if degree > 2]
