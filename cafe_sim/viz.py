from typing import Dict, Any
import os
import numpy as np
import matplotlib.pyplot as plt


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def plot_distributions(agg: Dict[str, Any], outdir: str) -> None:
    _ensure_dir(outdir)
    wait = agg["distributions"]["wait"]
    service = agg["distributions"]["service"]

    if wait:
        plt.figure(figsize=(6, 4))
        plt.hist(wait, bins=30, color="#4C78A8", alpha=0.85)
        plt.title("Waiting time distribution")
        plt.xlabel("minutes")
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, "hist_wait.png"))
        plt.close()

    if service:
        plt.figure(figsize=(6, 4))
        plt.hist(service, bins=30, color="#F58518", alpha=0.85)
        plt.title("Service time distribution")
        plt.xlabel("minutes")
        plt.ylabel("count")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, "hist_service.png"))
        plt.close()


def plot_queues(q_series: Dict[str, Any], outdir: str) -> None:
    _ensure_dir(outdir)
    t = q_series.get("t", [])
    if not t:
        return
    plt.figure(figsize=(7, 4))
    plt.plot(t, q_series.get("cashier_q", []), label="cashier")
    plt.plot(t, q_series.get("barista_q", []), label="barista")
    plt.plot(t, q_series.get("kitchen_q", []), label="kitchen")
    plt.xlabel("time (min)")
    plt.ylabel("queue length")
    plt.title("Queue length over time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "queues.png"))
    plt.close()


def plot_utilization(agg: Dict[str, Any], outdir: str) -> None:
    _ensure_dir(outdir)
    labels = ["cashier", "barista", "kitchen"]
    data = []
    errs = []
    for key in ["util_cashier_ci", "util_barista_ci", "util_kitchen_ci"]:
        mean, hw = agg.get(key, (0.0, 0.0))
        data.append(mean)
        errs.append(hw)
    x = np.arange(len(labels))
    plt.figure(figsize=(6, 4))
    plt.bar(x, data, yerr=errs, color=["#4C78A8", "#F58518", "#54A24B"], alpha=0.9, capsize=4)
    plt.xticks(x, labels)
    plt.ylim(0, 1.0)
    plt.ylabel("utilization")
    plt.title("Resource utilization (mean ± CI)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "utilization.png"))
    plt.close()


def plot_scenario_comparison(results: Dict[str, Dict[str, Any]], outdir: str) -> None:
    _ensure_dir(outdir)
    # Mean wait comparison
    names = list(results.keys())
    means = []
    errs = []
    for n in names:
        m, hw = results[n]["mean_wait_ci"]
        means.append(m)
        errs.append(hw)
    x = np.arange(len(names))
    plt.figure(figsize=(7, 4))
    plt.bar(x, means, yerr=errs, color="#4C78A8", alpha=0.9, capsize=4)
    plt.xticks(x, names, rotation=20)
    plt.ylabel("minutes")
    plt.title("Mean waiting time by scenario (±CI)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "scenarios_mean_wait.png"))
    plt.close()

    # Served comparison
    means = []
    errs = []
    for n in names:
        m, hw = results[n]["served_mean_ci"]
        means.append(m)
        errs.append(hw)
    x = np.arange(len(names))
    plt.figure(figsize=(7, 4))
    plt.bar(x, means, yerr=errs, color="#54A24B", alpha=0.9, capsize=4)
    plt.xticks(x, names, rotation=20)
    plt.ylabel("customers")
    plt.title("Served count by scenario (±CI)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "scenarios_served.png"))
    plt.close()
