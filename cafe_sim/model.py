import simpy
import numpy as np
from typing import Dict, Any, List, Tuple


def _svc_cashier(rng: np.random.Generator, mean: float) -> float:
    # Exponential service time with given mean
    return float(rng.exponential(scale=mean))


def _svc_tri(rng: np.random.Generator, a: float, m: float, b: float) -> float:
    # Triangular service time (low, mode, high)
    return float(rng.triangular(left=a, mode=m, right=b))


def _sample_order_type(rng: np.random.Generator, probs: List[float]) -> int:
    return int(rng.choice(len(probs), p=probs))


def _maybe_priority(rng: np.random.Generator, enabled: bool, share: float) -> int:
    # Lower value == higher priority in SimPy
    if not enabled:
        return 1
    return 0 if float(rng.random()) < share else 1


def run_single_sim(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Run one replication. Returns raw metrics and time series."""
    rng = np.random.default_rng(seed)
    env = simpy.Environment()

    horizon = float(params["horizon_min"])
    lam = float(params["lam"])  # arrivals per minute
    caps = params["capacities"]
    priority_enabled = bool(params.get("priority", False))
    priority_share = float(params.get("priority_share", 0.1))
    svc = params["service"]
    probs = params["type_probs"]
    mon_dt = float(params.get("monitor_interval", 1.0))

    # Resources
    CashierCls = simpy.PriorityResource if priority_enabled else simpy.Resource
    cashier = CashierCls(env, capacity=int(caps["cashier"]))
    barista = simpy.Resource(env, capacity=int(caps["barista"]))
    kitchen = simpy.Resource(env, capacity=int(caps["kitchen"]))

    # Stats containers
    wait_total: List[float] = []
    service_total: List[float] = []
    served = 0

    svc_sum = {"cashier": 0.0, "barista": 0.0, "kitchen": 0.0}

    q_series = {
        "t": [],
        "cashier_q": [],
        "barista_q": [],
        "kitchen_q": [],
    }

    def monitor():
        while True:
            q_series["t"].append(float(env.now))
            q_series["cashier_q"].append(len(cashier.queue))
            q_series["barista_q"].append(len(barista.queue))
            q_series["kitchen_q"].append(len(kitchen.queue))
            yield env.timeout(mon_dt)

    env.process(monitor())

    def service_stage(resource, duration_sampler, svc_key: str, priority: int = 1) -> Tuple[float, float]:
        # Returns (wait_time, service_time)
        start_wait = env.now
        if isinstance(resource, simpy.PriorityResource):
            req = resource.request(priority=priority)
        else:
            req = resource.request()
        yield req
        wait_time = float(env.now - start_wait)
        svc_time = float(duration_sampler())
        yield env.timeout(svc_time)
        resource.release(req)
        svc_sum[svc_key] += svc_time
        return wait_time, svc_time

    def customer(idx: int):
        nonlocal served
        otype = _sample_order_type(rng, probs)
        pr = _maybe_priority(rng, priority_enabled, priority_share)

        # Define route: 0: drink, 1: sandwich, 2: combo
        total_w = 0.0
        total_s = 0.0

        # Cashier
        w, s = yield from service_stage(
            cashier,
            lambda: _svc_cashier(rng, svc["cashier_mean"]),
            "cashier",
            priority=pr,
        )
        total_w += w
        total_s += s

        if otype == 0:  # drink -> barista
            w, s = yield from service_stage(
                barista,
                lambda: _svc_tri(rng, *svc["barista_tri"]),
                "barista",
            )
            total_w += w
            total_s += s
        elif otype == 1:  # sandwich -> kitchen
            w, s = yield from service_stage(
                kitchen,
                lambda: _svc_tri(rng, *svc["kitchen_tri"]),
                "kitchen",
            )
            total_w += w
            total_s += s
        else:  # combo -> kitchen then barista
            w, s = yield from service_stage(
                kitchen,
                lambda: _svc_tri(rng, *svc["kitchen_tri"]),
                "kitchen",
            )
            total_w += w
            total_s += s
            w, s = yield from service_stage(
                barista,
                lambda: _svc_tri(rng, *svc["barista_tri"]),
                "barista",
            )
            total_w += w
            total_s += s

        wait_total.append(total_w)
        service_total.append(total_s)
        served += 1

    def arrivals():
        i = 0
        while env.now < horizon:
            # Interarrival (exponential with mean 1/lam minutes)
            dt = float(rng.exponential(scale=1.0 / lam)) if lam > 0 else horizon
            yield env.timeout(dt)
            if env.now >= horizon:
                break
            env.process(customer(i))
            i += 1

    env.process(arrivals())
    env.run(until=horizon)

    # Utilization via total busy time / (capacity * horizon)
    util = {
        "cashier": (svc_sum["cashier"] / (float(caps["cashier"]) * horizon)) if horizon > 0 else 0.0,
        "barista": (svc_sum["barista"] / (float(caps["barista"]) * horizon)) if horizon > 0 else 0.0,
        "kitchen": (svc_sum["kitchen"] / (float(caps["kitchen"]) * horizon)) if horizon > 0 else 0.0,
    }

    out = {
        "served": served,
        "wait_total": wait_total,
        "service_total": service_total,
        "utilization": util,
        "queues": q_series,
        "drops": 0,
    }
    return out
