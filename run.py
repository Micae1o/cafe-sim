import os
from cafe_sim import params_default
from cafe_sim.experiments import run_replications, compare_scenarios
from cafe_sim.viz import plot_distributions, plot_queues, plot_utilization, plot_scenario_comparison


def main() -> None:
    params = dict(params_default)
    params["horizon_min"] = 480
    params["replications"] = 10

    out_base = os.path.join("out", "baseline")
    os.makedirs(out_base, exist_ok=True)

    agg = run_replications(params)
    plot_distributions(agg, out_base)
    if agg.get("last_q_series"):
        plot_queues(agg["last_q_series"], out_base)
    plot_utilization(agg, out_base)

    out_scen = os.path.join("out", "scenarios")
    os.makedirs(out_scen, exist_ok=True)
    results = compare_scenarios(params)
    plot_scenario_comparison(results, out_scen)

    mw_mean, mw_ci = agg["mean_wait_ci"]
    served_mean, served_ci = agg["served_mean_ci"]
    print(f"Mean wait: {mw_mean:.3f} ± {mw_ci:.3f} min")
    print(f"Served: {served_mean:.1f} ± {served_ci:.1f}")
    print(f"Figures saved to: {out_base} and {out_scen}")


if __name__ == "__main__":
    main()
