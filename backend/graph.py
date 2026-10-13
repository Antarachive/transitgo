"""Graph model (adjacency lists) and campus dataset loader.

Stops are vertices, roads are edges weighted by travel time in minutes.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "campus.json"
LANE_EDGE = (2, 5)     # Library <-> Academic road
LANE_WEIGHT = -2       # priority-lane discount, applied Academic -> Library only


class Graph:
    """Directed weighted graph stored as adjacency lists: O(V + E) space."""

    def __init__(self, n: int):
        self.n = n
        self.adj: list[list[tuple[int, float]]] = [[] for _ in range(n)]

    def add_arc(self, u: int, v: int, w: float) -> None:
        self.adj[u].append((v, w))

    def add_edge(self, u: int, v: int, w: float) -> None:
        self.add_arc(u, v, w)
        self.add_arc(v, u, w)

    def arcs(self) -> list[tuple[int, int, float]]:
        return [(u, v, w) for u in range(self.n) for v, w in self.adj[u]]

    def has_negative(self) -> bool:
        return any(w < 0 for _, _, w in self.arcs())


def load_campus() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def build_graph(campus: dict, lane: bool = False) -> Graph:
    """Undirected road network; with lane=True one direction becomes negative."""
    g = Graph(len(campus["stops"]))
    for u, v, w in campus["edges"]:
        g.add_arc(u, v, w)
        back = LANE_WEIGHT if (lane and (u, v) == LANE_EDGE) else w
        g.add_arc(v, u, back)
    return g
