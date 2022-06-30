import networkx as nx
from typing import List, Tuple


def build_tc_graph(stations: List[str], paths: List[Tuple[str, str]]) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(stations)
    graph.add_edges_from(paths)
    return graph
