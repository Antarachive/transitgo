# TransitGo — Campus Shuttle Routing & Capacity Scheduling

A DAA (Design & Analysis of Algorithms) project. TransitGo models a campus as a weighted graph
(stops = vertices, roads = edges weighted by travel time) and uses classic graph, greedy and
dynamic-programming algorithms to plan shuttle routes, schedules and fleet size so that
passenger waiting time stays low within seat-capacity and shift-time limits.

Python/Flask backend, plain HTML/CSS/JS frontend, SQLite for accounts. No build step.

## Features

| Screen | What it does | Algorithms |
|---|---|---|
| **Routes** | Fastest path between two stops, drawn on the campus graph. A "priority lane" toggle adds a −2 min edge to show why Dijkstra needs non-negative weights. | Dijkstra, Bellman-Ford, Floyd-Warshall |
| **Backbone** | Cheapest set of roads connecting every stop | Kruskal (union-find), Prim (heap) |
| **Schedule** | Assigns trip requests to 1–4 shuttles inside time windows, then picks which waiting groups board within seat capacity | Greedy earliest-finish, 0-1 knapsack DP, fractional knapsack (upper bound) |
| **Benchmark** | Times the algorithms on random sparse/dense graphs of growing size | all of the above |
| **Policy** | Compares fleet sizes (served trips, average wait, served per shuttle), recommends a fleet, loading rule and loop route | Floyd-Warshall + greedy + DP + nearest-neighbour |

Also: account registration and sign-in (hashed passwords, session cookie), guest mode, light/dark theme, responsive layout.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python backend/app.py                                  # http://127.0.0.1:5000
```

Options (environment variables): `PORT` (default 5000), `SECRET_KEY` (**set this** outside local demos),
`TRANSITGO_DB` (SQLite path, default `transitgo.db`), `DEBUG=1`.

Run the tests (algorithm correctness + API/auth):

```bash
python -m pytest backend -q
```

Run the benchmark from the terminal: `python backend/benchmark.py [--dense]`.

## Project structure

```
transitgo/
├── README.md
├── requirements.txt
├── backend/
│   ├── app.py              Flask app: pages, auth, JSON API
│   ├── graph.py            Graph (adjacency lists), dataset loader, priority-lane variant
│   ├── shortest_paths.py   Dijkstra, Bellman-Ford, Floyd-Warshall, path reconstruction
│   ├── mst.py              Kruskal + DSU, Prim
│   ├── scheduling.py       Greedy scheduler, 0-1 knapsack, fractional knapsack
│   ├── policy.py           Fleet recommendation, loop route
│   ├── benchmark.py        Random graphs + timing harness (also a CLI)
│   ├── data/campus.json    Sample dataset: 9 stops, 15 roads, 8 waiting groups
│   └── tests/              pytest suite
└── frontend/
    ├── login.html          Sign in / create account / guest
    ├── app.html            Dashboard
    └── static/             style.css, login.js, app.js
```

## API

All `/api/*` routes except auth need a signed-in session (guest counts). JSON in, JSON out.

| Method & path | Body | Returns |
|---|---|---|
| `POST /api/register` | `name, email, password (8+)` | `name` |
| `POST /api/login` | `email, password` | `name` |
| `POST /api/guest`, `POST /api/logout` | – | – |
| `GET /api/me` | – | `name, guest` |
| `GET /api/graph` | – | stops, edges, groups, requests |
| `POST /api/route` | `algo` (`dijkstra`/`bellman-ford`/`floyd-warshall`), `src`, `dst`, `lane` | path, cost, edges, complexity, warning |
| `POST /api/mst` | `algo` (`kruskal`/`prim`) | edges, total, full, saved |
| `POST /api/schedule` | `k` (1–8), `cap` (5–200) | served trips, avg wait, knapsack result |
| `POST /api/benchmark` | `dense` | rows of timings (ms) |
| `POST /api/policy` | `cap` | table, `best_k`, knapsack, loop route |

## Modelling decisions

- **Graph:** undirected roads stored as two directed arcs each, so one direction can change independently
  (the priority lane is Academic → Library only).
- **Waiting time:** for a trip request with earliest start `e`, waiting = actual start − `e`. A trip may start
  up to 20 minutes late; otherwise it is rejected.
- **Trip duration:** all-pairs shortest time (Floyd-Warshall) + 3 min dwell.
- **Boarding value:** a waiting group's value = size × minutes already waited (passenger-minutes relieved).
- **Data:** the campus map and the 14 trip requests are synthetic and reproducible (`random.Random(7)`).

## Algorithm choices, complexity and correctness

| Subproblem | Algorithm | Time | Why / correctness sketch |
|---|---|---|---|
| SSSP, non-negative weights | Dijkstra (binary heap) | O(E log V) | Greedy: the closest unfinalised vertex cannot be improved later, because any other route to it passes through a vertex at least as far. Breaks with negative edges. |
| SSSP, negative edges | Bellman-Ford | O(V·E) | A shortest path has ≤ V−1 edges, so V−1 relaxation rounds suffice; one more round detects negative cycles. |
| APSP | Floyd-Warshall | O(V³) | DP over "paths using only the first k vertices as intermediates"; recurrence `d[i][j] = min(d[i][j], d[i][k] + d[k][j])`. Johnson's O(V² log V + VE) is preferable on large sparse graphs. |
| Backbone | Kruskal / Prim | O(E log V) | Cut property: the lightest edge crossing any cut belongs to some MST. |
| Trip scheduling | Greedy earliest finish, best-fit shuttle | O(n log n + nk) | Optimal for one shuttle without windows (exchange argument); a strong heuristic with windows and k > 1. |
| Boarding choice | 0-1 knapsack DP | O(n · cap) | Optimal substructure + overlapping subproblems. Ratio-greedy can be suboptimal (the app shows the gap); fractional knapsack is solved optimally by greedy and gives an upper bound. |

Measured runtimes (Python, sparse graphs, ms): n=120 → Dijkstra ≈ 0.1, Bellman-Ford ≈ 0.2, Kruskal ≈ 0.1,
Floyd-Warshall ≈ 46. Use the Benchmark screen or `benchmark.py` for your own machine.

## Limitations and ideas

- Google/Facebook/Apple sign-in from the design mockup is not implemented; "Continue as guest" replaces it.
- Auth is meant for a course demo: no email verification, password reset or rate limiting. Use HTTPS, set
  `SECRET_KEY`, and run behind a production WSGI server (e.g. gunicorn) before any real deployment.
- Scheduling is a heuristic for k > 1 with windows (the exact problem is NP-hard in general).
- Possible extensions: Johnson's algorithm, real transit data (GTFS), live demand, time-dependent edge weights.
