"""TransitGo API server (Flask). Run:  python backend/app.py"""
from __future__ import annotations

import math
import os
import re
import sqlite3
import time
from functools import wraps
from pathlib import Path

from flask import Flask, g as flask_g, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from benchmark import run_benchmark
from graph import build_graph, load_campus
from mst import kruskal, prim
from policy import recommend
from scheduling import average_wait, greedy_schedule, knapsack, make_requests
from shortest_paths import (NegativeCycleError, bellman_ford, dijkstra,
                            floyd_warshall, path_from_next, path_from_prev)

ROOT = Path(__file__).resolve().parent.parent
FRONT = ROOT / "frontend"
DB_PATH = os.environ.get("TRANSITGO_DB", str(ROOT / "transitgo.db"))
CAMPUS = load_campus()
BASE_DIST, BASE_NXT = floyd_warshall(build_graph(CAMPUS))
REQUESTS = make_requests(BASE_DIST)
COMPLEXITY = {"dijkstra": "O(E log V)", "bellman-ford": "O(V·E)", "floyd-warshall": "O(V³)",
              "kruskal": "O(E log V)", "prim": "O(E log V)"}


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(FRONT / "static"), static_url_path="/static")
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      DB=db_path or DB_PATH)

    # ---------- database ----------
    def db():
        if "db" not in flask_g:
            flask_g.db = sqlite3.connect(app.config["DB"])
            flask_g.db.row_factory = sqlite3.Row
        return flask_g.db

    @app.teardown_appcontext
    def close_db(_):
        c = flask_g.pop("db", None)
        if c:
            c.close()

    with sqlite3.connect(app.config["DB"]) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL, created REAL NOT NULL)""")

    def need_login(fn):
        @wraps(fn)
        def wrap(*a, **k):
            if "uid" not in session and not session.get("guest"):
                return jsonify(error="Please sign in."), 401
            return fn(*a, **k)
        return wrap

    def body():
        return request.get_json(silent=True) or {}

    # ---------- pages ----------
    @app.get("/")
    def index():
        if "uid" in session or session.get("guest"):
            return redirect("/app")
        return send_from_directory(FRONT, "login.html")

    @app.get("/app")
    def dashboard():
        if "uid" not in session and not session.get("guest"):
            return redirect("/")
        return send_from_directory(FRONT, "app.html")

    # ---------- auth ----------
    EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    @app.post("/api/register")
    def register():
        b = body()
        name, email, pw = (b.get("name") or "").strip(), (b.get("email") or "").strip().lower(), b.get("password") or ""
        if not name or not EMAIL.match(email):
            return jsonify(error="Enter your name and a valid email."), 400
        if len(pw) < 8:
            return jsonify(error="Password must be at least 8 characters."), 400
        try:
            cur = db().execute("INSERT INTO users(name,email,pw_hash,created) VALUES(?,?,?,?)",
                               (name, email, generate_password_hash(pw), time.time()))
            db().commit()
        except sqlite3.IntegrityError:
            return jsonify(error="That email is already registered."), 409
        session.clear()
        session["uid"], session["name"] = cur.lastrowid, name
        return jsonify(name=name)

    @app.post("/api/login")
    def login():
        b = body()
        row = db().execute("SELECT * FROM users WHERE email=?", ((b.get("email") or "").strip().lower(),)).fetchone()
        if not row or not check_password_hash(row["pw_hash"], b.get("password") or ""):
            return jsonify(error="Wrong email or password."), 401
        session.clear()
        session["uid"], session["name"] = row["id"], row["name"]
        return jsonify(name=row["name"])

    @app.post("/api/guest")
    def guest():
        session.clear()
        session["guest"], session["name"] = True, "Guest"
        return jsonify(name="Guest")

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.get("/api/me")
    @need_login
    def me():
        return jsonify(name=session.get("name"), guest=bool(session.get("guest")))

    # ---------- optimisation API ----------
    @app.get("/api/graph")
    @need_login
    def graph_info():
        return jsonify(stops=CAMPUS["stops"], edges=CAMPUS["edges"], groups=CAMPUS["groups"],
                       requests=[r.__dict__ for r in REQUESTS])

    @app.post("/api/route")
    @need_login
    def route():
        b = body()
        n = len(CAMPUS["stops"])
        try:
            algo, s, t, lane = str(b.get("algo", "dijkstra")).lower(), int(b["src"]), int(b["dst"]), bool(b.get("lane"))
        except (KeyError, TypeError, ValueError):
            return jsonify(error="src and dst are required."), 400
        if algo not in ("dijkstra", "bellman-ford", "floyd-warshall") or not (0 <= s < n and 0 <= t < n):
            return jsonify(error="Unknown algorithm or stop."), 400
        g = build_graph(CAMPUS, lane)
        t0, warning, avg = time.perf_counter(), None, None
        try:
            if algo == "dijkstra":
                dist, prev = dijkstra(g, s)
                path, cost = path_from_prev(prev, s, t), dist[t]
                if g.has_negative():
                    truth = bellman_ford(g, s)[0][t]
                    if truth != cost:
                        warning = (f"Negative edge present: Dijkstra's greedy choice is no longer valid. "
                                   f"Correct time (Bellman-Ford) is {truth} min.")
            elif algo == "bellman-ford":
                dist, prev = bellman_ford(g, s)
                path, cost = path_from_prev(prev, s, t), dist[t]
            else:
                D, X = floyd_warshall(g)
                path, cost = path_from_next(X, s, t), D[s][t]
                pairs = [D[i][j] for i in range(n) for j in range(n) if i != j]
                avg = round(sum(pairs) / len(pairs), 1)
        except NegativeCycleError as e:
            return jsonify(error=str(e)), 422
        ms = (time.perf_counter() - t0) * 1000
        return jsonify(path=path, cost=None if math.isinf(cost) else cost, ms=round(ms, 3),
                       complexity=COMPLEXITY[algo], warning=warning, avg_trip=avg,
                       edges=[[a, c] for a, c in zip(path, path[1:])])

    @app.post("/api/mst")
    @need_login
    def mst():
        algo = str(body().get("algo", "kruskal")).lower()
        if algo not in ("kruskal", "prim"):
            return jsonify(error="Unknown algorithm."), 400
        E = CAMPUS["edges"]
        tree = (kruskal if algo == "kruskal" else prim)(len(CAMPUS["stops"]), E)
        total, full = sum(e[2] for e in tree), sum(e[2] for e in E)
        return jsonify(algo=algo, edges=tree, total=total, full=full, saved=full - total,
                       complexity=COMPLEXITY[algo])

    @app.post("/api/schedule")
    @need_login
    def schedule():
        b = body()
        try:
            k, cap = int(b.get("k", 2)), int(b.get("cap", 20))
        except (TypeError, ValueError):
            return jsonify(error="k and cap must be integers."), 400
        if not (1 <= k <= 8 and 5 <= cap <= 200):
            return jsonify(error="k must be 1-8 and cap 5-200."), 400
        sv = greedy_schedule(REQUESTS, k)
        nodes, edges = set(), []
        for t in sv:
            p = path_from_next(BASE_NXT, t["o"], t["d"])
            nodes.update(p)
            edges += [[x, y] for x, y in zip(p, p[1:])]
        return jsonify(served=sv, total=len(REQUESTS), avg_wait=round(average_wait(sv), 1),
                       knapsack=knapsack(CAMPUS["groups"], cap), nodes=sorted(nodes), edges=edges)

    @app.post("/api/benchmark")
    @need_login
    def bench():
        return jsonify(dense=bool(body().get("dense")), rows=run_benchmark(bool(body().get("dense"))))

    @app.post("/api/policy")
    @need_login
    def pol():
        try:
            cap = int(body().get("cap", 20))
        except (TypeError, ValueError):
            return jsonify(error="cap must be an integer."), 400
        if not 5 <= cap <= 200:
            return jsonify(error="cap must be 5-200."), 400
        return jsonify(recommend(CAMPUS, cap))

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"TransitGo running at http://127.0.0.1:{port}")
    create_app().run(host="127.0.0.1", port=port, debug=os.environ.get("DEBUG") == "1")
