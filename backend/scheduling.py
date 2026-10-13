"""Greedy trip scheduler and knapsack-style passenger loading."""
from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass

SHIFT = 240   # minutes in the scheduling window (07:00-11:00)
SLACK = 20    # a trip may start at most this many minutes after its request time


@dataclass
class Request:
    o: int      # origin stop
    d: int      # destination stop
    e: int      # earliest start (minutes from shift start)
    dur: int    # trip duration, from the all-pairs time matrix + dwell


def make_requests(dist, count=14, seed=7) -> list[Request]:
    """Synthetic but reproducible trip requests."""
    r, n, out = random.Random(seed), len(dist), []
    for i in range(count):
        o = r.randrange(n)
        d = r.randrange(n)
        if d == o:
            d = (d + 3) % n
        out.append(Request(o, d, int(i * 7 + r.random() * 8), math.ceil(dist[o][d]) + 3))
    return out


def greedy_schedule(requests, k, shift=SHIFT, slack=SLACK):
    """Earliest-finish-time greedy on k shuttles with start-time windows.

    Requests are sorted by finish time; each goes to the *busiest* shuttle that
    can still take it (best fit), which keeps other shuttles free for later.
    O(n log n + n*k). Optimal for k=1 without windows (classic activity
    selection); a strong heuristic once windows and k > 1 are added."""
    free = [0] * k
    served = []
    for r in sorted(requests, key=lambda r: r.e + r.dur):
        best = -1
        for j in range(k):
            s = max(r.e, free[j])
            if s <= r.e + slack and s + r.dur <= shift and (best < 0 or free[j] > free[best]):
                best = j
        if best >= 0:
            s = max(r.e, free[best])
            free[best] = s + r.dur
            served.append({**asdict(r), "s": s, "j": best})
    return sorted(served, key=lambda t: t["s"])


def average_wait(served):
    return sum(t["s"] - t["e"] for t in served) / len(served) if served else 0.0


def knapsack(groups, cap):
    """0-1 knapsack by DP, O(n*cap). groups = [(stop, size, waited_min)].
    value = size * waited (passenger-minutes of waiting relieved)."""
    n = len(groups)
    w = [g[1] for g in groups]
    v = [g[1] * g[2] for g in groups]
    dp = [[0] * (cap + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for c in range(cap + 1):
            dp[i][c] = dp[i - 1][c]
            if w[i - 1] <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - w[i - 1]] + v[i - 1])
    picked, c = [], cap
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            picked.append(i - 1)
            c -= w[i - 1]
    picked.reverse()
    # Whole-group greedy by value/weight, for comparison: not always optimal.
    left, ratio_val = cap, 0
    for i in sorted(range(n), key=lambda i: v[i] / w[i], reverse=True):
        if w[i] <= left:
            left -= w[i]
            ratio_val += v[i]
    return {
        "picked": picked,
        "value": dp[n][cap],
        "seats_used": sum(w[i] for i in picked),
        "ratio_greedy_value": ratio_val,
        "fractional_bound": round(fractional_knapsack(groups, cap), 1),
    }


def fractional_knapsack(groups, cap):
    """Greedy by value/weight is *optimal* when groups may be split: O(n log n).
    Gives an upper bound for the 0-1 problem."""
    left, total = cap, 0.0
    for _, size, waited in sorted(groups, key=lambda g: g[2], reverse=True):
        take = min(size, left)
        total += take * waited
        left -= take
        if left == 0:
            break
    return total
