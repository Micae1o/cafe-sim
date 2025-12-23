__all__ = [
    "params_default",
]

params_default = {
    "horizon_min": 480,
    "lam": 0.5,
    "capacities": {"cashier": 1, "barista": 1, "kitchen": 1},
    "service": {
        "cashier_mean": 1.5,
        "barista_tri": (0.5, 1.5, 3.0),
        "kitchen_tri": (3.0, 5.0, 8.0),
    },
    "type_probs": [0.4, 0.35, 0.25],
    "priority": False,
    "priority_share": 0.1,
    "replications": 10,
    "monitor_interval": 1.0,
    "seed": 42,
}
