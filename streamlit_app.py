import os
import time
import streamlit as st
from cafe_sim import params_default
from cafe_sim.experiments import run_replications, compare_scenarios
from cafe_sim.viz import (
    plot_distributions,
    plot_queues,
    plot_utilization,
    plot_scenario_comparison,
)

st.set_page_config(page_title="Cafe Simulation", layout="centered")
st.title("Симулятор роботи кафе (SimPy)")

with st.sidebar:
    st.header("Параметри")
    horizon_min = st.number_input("Тривалість моделювання (хв)", min_value=5, max_value=480, value=30, step=5)
    lam = st.number_input("Інтенсивність приходу λ (клієнтів/хв)", min_value=0.1, max_value=5.0, value=0.5, step=0.1)

    st.subheader("Канали (capacity)")
    cap_cashier = st.number_input("Каса", min_value=1, max_value=5, value=1, step=1)
    cap_barista = st.number_input("Бариста", min_value=1, max_value=5, value=1, step=1)
    cap_kitchen = st.number_input("Кухня", min_value=1, max_value=5, value=1, step=1)

    st.subheader("Обслуговування")
    cashier_mean = st.number_input("Каса, середній час (хв)", min_value=0.2, max_value=10.0, value=1.5, step=0.1)
    b_a = st.number_input("Бариста, мін (хв)", min_value=0.1, max_value=10.0, value=0.5, step=0.1)
    b_m = st.number_input("Бариста, мода (хв)", min_value=0.1, max_value=10.0, value=1.5, step=0.1)
    b_b = st.number_input("Бариста, макс (хв)", min_value=0.2, max_value=15.0, value=3.0, step=0.1)
    k_a = st.number_input("Кухня, мін (хв)", min_value=0.5, max_value=30.0, value=3.0, step=0.5)
    k_m = st.number_input("Кухня, мода (хв)", min_value=0.5, max_value=30.0, value=5.0, step=0.5)
    k_b = st.number_input("Кухня, макс (хв)", min_value=1.0, max_value=60.0, value=8.0, step=0.5)

    st.subheader("Типи замовлень (частки)")
    p_drink = st.slider("Напій", 0.0, 1.0, 0.40, 0.01)
    p_sand = st.slider("Сендвіч", 0.0, 1.0, 0.35, 0.01)
    p_combo = st.slider("Комбо", 0.0, 1.0, 0.25, 0.01)
    s = p_drink + p_sand + p_combo
    if s == 0:
        st.warning("Суми часток = 0. Встановлено дефолт 0.4/0.35/0.25")
        p_drink, p_sand, p_combo = 0.4, 0.35, 0.25
    else:
        p_drink, p_sand, p_combo = p_drink / s, p_sand / s, p_combo / s

    st.subheader("Інше")
    replications = st.number_input("Кількість прогонів", min_value=5, max_value=50, value=10, step=1)
    seed = st.number_input("Seed", min_value=0, max_value=10_000, value=42, step=1)
    use_priority = st.checkbox("Приоритети на касі (10% мобільні)", value=False)
    run_scenarios = st.checkbox("Порівняти сценарії (1 vs 2 каси, FIFO vs приор.)", value=True)

run = st.button("Запустити моделювання")

if run:
    p = dict(params_default)
    p["horizon_min"] = int(horizon_min)
    p["lam"] = float(lam)
    p["capacities"] = {"cashier": int(cap_cashier), "barista": int(cap_barista), "kitchen": int(cap_kitchen)}
    p["service"] = {
        "cashier_mean": float(cashier_mean),
        "barista_tri": (float(b_a), float(b_m), float(b_b)),
        "kitchen_tri": (float(k_a), float(k_m), float(k_b)),
    }
    p["type_probs"] = [float(p_drink), float(p_sand), float(p_combo)]
    p["replications"] = int(replications)
    p["seed"] = int(seed)
    p["priority"] = bool(use_priority)

    out_dir = os.path.join("out", "streamlit", f"sess_{int(time.time())}")
    os.makedirs(out_dir, exist_ok=True)

    st.write("Виконується...")
    agg = run_replications(p)

    plot_distributions(agg, out_dir)
    if agg.get("last_q_series"):
        plot_queues(agg["last_q_series"], out_dir)
    plot_utilization(agg, out_dir)

    st.subheader("Результати (базовий сценарій)")
    mw_mean, mw_ci = agg["mean_wait_ci"]
    served_mean, served_ci = agg["served_mean_ci"]
    st.write(f"Сер. очікування: {mw_mean:.3f} ± {mw_ci:.3f} хв")
    st.write(f"Обслуговано: {served_mean:.1f} ± {served_ci:.1f}")

    st.image(os.path.join(out_dir, "hist_wait.png"), caption="Розподіл часу очікування", width="content")
    st.image(os.path.join(out_dir, "hist_service.png"), caption="Розподіл часу обслуговування", width="content")
    st.image(os.path.join(out_dir, "queues.png"), caption="Довжина черг у часі", width="content")
    st.image(os.path.join(out_dir, "utilization.png"), caption="Завантаження ресурсів", width="content")

    if run_scenarios:
        st.subheader("Порівняння сценаріїв")
        res = compare_scenarios(p)
        plot_scenario_comparison(res, out_dir)
        st.image(os.path.join(out_dir, "scenarios_mean_wait.png"), caption="Сер. очікування за сценаріями", width="content")
        st.image(os.path.join(out_dir, "scenarios_served.png"), caption="К-сть обслугованих за сценаріями", width="content")

    st.success(f"Готово. Графіки збережено в {out_dir}")
