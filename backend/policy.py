"""Fleet-size recommendation, loop route and cost/benefit table."""
from __future__ import annotations

from graph import build_graph
from scheduling import average_wait, greedy_schedule, knapsack, make_requests
from shortest_paths import floyd_warshall, path_from_next


def tour_edges(nxt, tour):
    nodes, edges = set(), []
    for a, b in zip(tour, tour[1:]):
        p = path_from_next(nxt, a, b)
        nodes.update(p)
        edges += [[x, y] for x, y in zip(p, p[1:])]
    return sorted(nodes), edges


def recommend(campus, cap):
    g = build_graph(campus)
    dist, nxt = floyd_warshall(g)
    reqs = make_requests(dist)
    rows = []
    for k in range(1, 5):
        sv = greedy_schedule(reqs, k)
        rows.append({"k": k, "served": len(sv), "total": len(reqs),
                     "avg_wait": round(average_wait(sv), 1),
                     "per_shuttle": round(len(sv) / k, 1)})
    best = rows[-1]["k"]            # smallest fleet whose next vehicle adds <= 1 trip
    for a, b in zip(rows, rows[1:]):
        if a["served"] == a["total"] or b["served"] - a["served"] <= 1:
            best = a["k"]
            break
    # nearest-neighbour loop over all stops, using all-pairs times
    cur, tour, seen = 0, [0], {0}
    while len(seen) < g.n:
        nxt_stop = min((j for j in range(g.n) if j not in seen), key=lambda j: dist[cur][j])
        seen.add(nxt_stop)
        tour.append(nxt_stop)
        cur = nxt_stop
    tour.append(0)
    nodes, edges = tour_edges(nxt, tour)
    return {
        "rows": rows, "best_k": best,
        "knapsack": knapsack(campus["groups"], cap),
        "tour": tour, "tour_time": sum(dist[a][b] for a, b in zip(tour, tour[1:])),
        "nodes": nodes, "edges": edges,
    }
