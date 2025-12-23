from typing import Dict, Any, List, Tuple
import numpy as np
from .model import run_single_sim


def _mean_ci(xs: List[float], alpha: float = 0.05) -> Tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    arr = np.asarray(xs, dtype=float)
    m = float(arr.mean())
    sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
    hw = 1.96 * sd / np.sqrt(arr.size) if arr.size > 1 else 0.0
    return m, hw


def run_replications(params: Dict[str, Any]) -> Dict[str, Any]:
    n = int(params.get("replications", 10))
    base_seed = int(params.get("seed", 42))

    rep_metrics = []
    all_wait: List[float] = []
    all_service: List[float] = []

    util_cashier: List[float] = []
    util_barista: List[float] = []
    util_kitchen: List[float] = []

    avg_q_cashier: List[float] = []
    avg_q_barista: List[float] = []
    avg_q_kitchen: List[float] = []

    max_q_cashier: List[float] = []
    max_q_barista: List[float] = []
    max_q_kitchen: List[float] = []

    last_q_series = None

    for i in range(n):
        out = run_single_sim(params, seed=base_seed + i)

        wait = out["wait_total"]
        service = out["service_total"]
        served = int(out["served"]) if out.get("served") is not None else len(wait)

        mean_wait = float(np.mean(wait)) if wait else 0.0
        median_wait = float(np.median(wait)) if wait else 0.0

        q = out["queues"]
        q_c = q["cashier_q"]
        q_b = q["barista_q"]
        q_k = q["kitchen_q"]

        avg_q_cashier.append(float(np.mean(q_c)) if q_c else 0.0)
        avg_q_barista.append(float(np.mean(q_b)) if q_b else 0.0)
        avg_q_kitchen.append(float(np.mean(q_k)) if q_k else 0.0)

        max_q_cashier.append(float(np.max(q_c)) if q_c else 0.0)
        max_q_barista.append(float(np.max(q_b)) if q_b else 0.0)
        max_q_kitchen.append(float(np.max(q_k)) if q_k else 0.0)

        util = out["utilization"]
        util_cashier.append(float(util["cashier"]))
        util_barista.append(float(util["barista"]))
        util_kitchen.append(float(util["kitchen"]))

        all_wait.extend(wait)
        all_service.extend(service)

        rep_metrics.append({
            "served": served,
            "mean_wait": mean_wait,
            "median_wait": median_wait,
        })

        last_q_series = q

    agg = {
        "served_mean_ci": _mean_ci([m["served"] for m in rep_metrics]),
        "mean_wait_ci": _mean_ci([m["mean_wait"] for m in rep_metrics]),
        "median_wait_ci": _mean_ci([m["median_wait"] for m in rep_metrics]),
        "avg_q_cashier_ci": _mean_ci(avg_q_cashier),
        "avg_q_barista_ci": _mean_ci(avg_q_barista),
        "avg_q_kitchen_ci": _mean_ci(avg_q_kitchen),
        "max_q_cashier_ci": _mean_ci(max_q_cashier),
        "max_q_barista_ci": _mean_ci(max_q_barista),
        "max_q_kitchen_ci": _mean_ci(max_q_kitchen),
        "util_cashier_ci": _mean_ci(util_cashier),
        "util_barista_ci": _mean_ci(util_barista),
        "util_kitchen_ci": _mean_ci(util_kitchen),
        "distributions": {
            "wait": all_wait,
            "service": all_service,
        },
        "last_q_series": last_q_series,
        "n": n,
    }
    return agg


def compare_scenarios(base_params: Dict[str, Any]) -> Dict[str, Any]:
    scenarios: List[Tuple[str, Dict[str, Any]]] = []

    # Baseline
    scenarios.append(("baseline", base_params))

    # Two cashiers
    p2 = {**base_params, "capacities": {**base_params["capacities"], "cashier": 2}}
    scenarios.append(("two_cashiers", p2))

    # Priority on cashier (10%)
    p3 = {**base_params, "priority": True}
    scenarios.append(("priority_cashier", p3))

    results = {}
    for name, p in scenarios:
        results[name] = run_replications(p)
    return results
