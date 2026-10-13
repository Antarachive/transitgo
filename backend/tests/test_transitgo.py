import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app import create_app
from benchmark import random_graph
from graph import build_graph, load_campus
from mst import kruskal, prim
from scheduling import greedy_schedule, knapsack, make_requests
from shortest_paths import (INF, NegativeCycleError, bellman_ford, dijkstra,
                            floyd_warshall, path_from_next, path_from_prev)
from graph import Graph

C = load_campus()


def test_shortest_paths_agree_without_negatives():
    g = build_graph(C)
    D, _ = floyd_warshall(g)
    for s in range(g.n):
        assert dijkstra(g, s)[0] == bellman_ford(g, s)[0] == D[s]


def test_priority_lane_breaks_dijkstra_not_bellman_ford():
    g = build_graph(C, lane=True)
    assert dijkstra(g, 0)[0][2] == 6          # wrong: greedy finalised too early
    assert bellman_ford(g, 0)[0][2] == 5      # correct: 0 -> Academic -> Library
    assert floyd_warshall(g)[0][0][2] == 5


def test_paths_reconstruct_to_reported_cost():
    g = build_graph(C)
    D, X = floyd_warshall(g)
    _, prev = dijkstra(g, 0)
    p = path_from_next(X, 0, 7)
    assert p == path_from_prev(prev, 0, 7) or len(p) > 1
    w = {(u, v): c for u, v, c in g.arcs()}
    assert sum(w[a, b] for a, b in zip(p, p[1:])) == D[0][7]


def test_negative_cycle_detected():
    g = Graph(3)
    g.add_arc(0, 1, 1); g.add_arc(1, 2, -3); g.add_arc(2, 1, 1)
    with pytest.raises(NegativeCycleError):
        bellman_ford(g, 0)


def test_kruskal_equals_prim_and_spans():
    for seed in range(5):
        _, E = random_graph(30, False, seed)
        a, b = kruskal(30, E), prim(30, E)
        assert len(a) == len(b) == 29
        assert sum(e[2] for e in a) == sum(e[2] for e in b)


def test_knapsack_optimal_vs_bruteforce():
    groups = C["groups"]
    for cap in (12, 20, 33, 47):
        best = max(sum(groups[i][1] * groups[i][2] for i in sub)
                   for r in range(len(groups) + 1) for sub in itertools.combinations(range(len(groups)), r)
                   if sum(groups[i][1] for i in sub) <= cap)
        k = knapsack(groups, cap)
        assert k["value"] == best >= k["ratio_greedy_value"]
        assert k["seats_used"] <= cap and k["value"] <= k["fractional_bound"]


def test_greedy_schedule_is_feasible():
    D, _ = floyd_warshall(build_graph(C))
    reqs = make_requests(D)
    for k in (1, 2, 3):
        by = {}
        for t in greedy_schedule(reqs, k):
            assert t["e"] <= t["s"] <= t["e"] + 20 and t["s"] + t["dur"] <= 240
            by.setdefault(t["j"], []).append((t["s"], t["s"] + t["dur"]))
        for iv in by.values():
            iv.sort()
            assert all(a[1] <= b[0] for a, b in zip(iv, iv[1:]))
    assert len(greedy_schedule(reqs, 2)) >= len(greedy_schedule(reqs, 1))


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "t.db"))
    return app.test_client()


def test_auth_flow_and_protection(client):
    assert client.post("/api/route", json={"src": 0, "dst": 3}).status_code == 401
    assert client.post("/api/register", json={"name": "Ana", "email": "a@x.io", "password": "short"}).status_code == 400
    assert client.post("/api/register", json={"name": "Ana", "email": "a@x.io", "password": "longenough1"}).status_code == 200
    client.post("/api/logout")
    assert client.post("/api/register", json={"name": "Ana", "email": "a@x.io", "password": "longenough1"}).status_code == 409
    assert client.post("/api/login", json={"email": "a@x.io", "password": "bad"}).status_code == 401
    assert client.post("/api/login", json={"email": "a@x.io", "password": "longenough1"}).status_code == 200
    assert client.get("/api/me").json["name"] == "Ana"


def test_api_endpoints(client):
    client.post("/api/guest")
    r = client.post("/api/route", json={"algo": "dijkstra", "src": 0, "dst": 3, "lane": True}).json
    assert r["warning"] and r["path"][0] == 0 and r["path"][-1] == 3
    assert client.post("/api/mst", json={"algo": "prim"}).json["total"] == client.post("/api/mst", json={"algo": "kruskal"}).json["total"]
    assert client.post("/api/schedule", json={"k": 2, "cap": 20}).json["knapsack"]["value"] > 0
    assert client.post("/api/policy", json={"cap": 20}).json["best_k"] in (1, 2, 3, 4)
    assert client.post("/api/route", json={"algo": "x", "src": 0, "dst": 1}).status_code == 400
    assert client.post("/api/schedule", json={"k": 99, "cap": 20}).status_code == 400
