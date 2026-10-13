"""Runtime experiments on random graphs (varying size and density)."""
from __future__ import annotations

import random
import time

from graph import Graph
from mst import kruskal
from shortest_paths import bellman_ford, dijkstra, floyd_warshall


def random_graph(n, dense, seed):
    """Ring (guarantees connectivity) + random chords. Sparse: ~2n extra edges,
    dense: ~n(n-1)/4 extra edges."""
    r = random.Random(seed)
    edges = [(i, (i + 1) % n, r.randint(1, 9)) for i in range(n)]
    for _ in range(n * (n - 1) // 4 if dense else 2 * n):
        a, b = r.randrange(n), r.randrange(n)
        if a != b:
            edges.append((a, b, r.randint(1, 9)))
    g = Graph(n)
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, edges


def _time(fn, reps):
    t = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t) / reps * 1000


def run_benchmark(dense=False, sizes=(20, 40, 80, 120)):
    rows = []
    for n in sizes:
        g, edges = random_graph(n, dense, n)
        rows.append({
            "n": n, "edges": len(edges),
            "dijkstra": _time(lambda: dijkstra(g, 0), 3),
            "bellman_ford": _time(lambda: bellman_ford(g, 0), 3),
            "floyd_warshall": _time(lambda: floyd_warshall(g), 1),
            "kruskal": _time(lambda: kruskal(n, edges), 3),
        })
    return rows


if __name__ == "__main__":
    import sys
    dense = "--dense" in sys.argv
    print(f"{'n':>5} {'E':>6} {'dijkstra':>10} {'bellman':>10} {'floyd':>10} {'kruskal':>10}  (ms)")
    for r in run_benchmark(dense):
        print(f"{r['n']:>5} {r['edges']:>6} {r['dijkstra']:>10.2f} {r['bellman_ford']:>10.2f} "
              f"{r['floyd_warshall']:>10.2f} {r['kruskal']:>10.2f}")
