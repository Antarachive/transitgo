"""Single-source and all-pairs shortest paths."""
from __future__ import annotations

import heapq

from graph import Graph

INF = float("inf")


class NegativeCycleError(ValueError):
    pass


def dijkstra(g: Graph, s: int):
    """O(E log V) with a binary heap. Greedy choice is only valid when all
    weights are non-negative (a finalised vertex is never improved later)."""
    dist, prev, done = [INF] * g.n, [-1] * g.n, [False] * g.n
    dist[s] = 0
    pq = [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if done[u]:
            continue
        done[u] = True
        for v, w in g.adj[u]:
            if not done[v] and d + w < dist[v]:
                dist[v], prev[v] = d + w, u
                heapq.heappush(pq, (dist[v], v))
    return dist, prev


def bellman_ford(g: Graph, s: int):
    """O(V*E). Handles negative weights and detects negative cycles."""
    dist, prev = [INF] * g.n, [-1] * g.n
    dist[s] = 0
    arcs = g.arcs()
    for _ in range(g.n - 1):
        changed = False
        for u, v, w in arcs:
            if dist[u] + w < dist[v]:
                dist[v], prev[v] = dist[u] + w, u
                changed = True
        if not changed:
            break
    for u, v, w in arcs:
        if dist[u] + w < dist[v]:
            raise NegativeCycleError("negative cycle reachable from source")
    return dist, prev


def floyd_warshall(g: Graph):
    """O(V^3) dynamic programming over intermediate vertices.
    Returns (dist, nxt) where nxt[i][j] is the first hop on a best i->j path."""
    n = g.n
    dist = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    nxt = [[-1] * n for _ in range(n)]
    for u, v, w in g.arcs():
        if w < dist[u][v]:
            dist[u][v], nxt[u][v] = w, v
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == INF:
                continue
            di = dist[i]
            for j in range(n):
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
                    nxt[i][j] = nxt[i][k]
    return dist, nxt


def path_from_prev(prev, s, t):
    path, v = [], t
    while v != -1:
        path.append(v)
        if v == s:
            break
        v = prev[v]
    path.reverse()
    return path if path and path[0] == s else []


def path_from_next(nxt, s, t):
    if s == t:
        return [s]
    if nxt[s][t] < 0:
        return []
    path = [s]
    while s != t:
        s = nxt[s][t]
        path.append(s)
    return path
