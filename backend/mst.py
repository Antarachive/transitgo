"""Minimum spanning trees over an undirected edge list [(u, v, w), ...]."""
from __future__ import annotations

import heapq


class DSU:
    """Union-find with path compression and union by rank: ~O(alpha(n))."""

    def __init__(self, n):
        self.p, self.r = list(range(n)), [0] * n

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.r[a] < self.r[b]:
            a, b = b, a
        self.p[b] = a
        self.r[a] += self.r[a] == self.r[b]
        return True


def kruskal(n, edges):
    """O(E log E) = O(E log V): sort edges, add if no cycle (cut property)."""
    d, out = DSU(n), []
    for u, v, w in sorted(edges, key=lambda e: e[2]):
        if d.union(u, v):
            out.append((u, v, w))
    return out


def prim(n, edges, root=0):
    """O(E log V) with a binary heap: grow one tree by the cheapest crossing edge."""
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    seen, out, pq = [False] * n, [], [(0, root, -1)]
    while pq:
        w, u, par = heapq.heappop(pq)
        if seen[u]:
            continue
        seen[u] = True
        if par >= 0:
            out.append((par, u, w))
        for v, wv in adj[u]:
            if not seen[v]:
                heapq.heappush(pq, (wv, v, u))
    return out
