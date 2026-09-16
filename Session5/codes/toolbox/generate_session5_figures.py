"""Regenerate the French Session 5 policy-comparison figures from DICE."""

from pathlib import Path

import matplotlib.pyplot as plt

import DICE


HERE = Path(__file__).resolve().parent


def policy_paths():
    params = DICE.Params()
    baseline = DICE.init_states(params)
    time = range(1, params.nT)
    baseline[:, params.i_mu] = 0.03
    baseline = DICE.update_path(baseline, time, params)

    laissez_faire = DICE.run_optimal_policy(
        baseline, time, params, (params.s_lower, params.s_upper), [params.i_s]
    )
    optimal = DICE.run_optimal_policy(
        baseline, time, params,
        [(params.s_lower, params.s_upper), (0, 1)], [params.i_s, params.i_mu]
    )
    return params, laissez_faire, optimal


def plot_policy_comparison(params, laissez_faire, optimal):
    consumption_per_capita = 1000 * optimal[:, params.i_C] / optimal[:, params.i_L]
    consumption_per_capita_bau = 1000 * laissez_faire[:, params.i_C] / laissez_faire[:, params.i_L]
    damage_factor = 1 / (1 + params.a2 * optimal[:, params.i_T_AT] ** params.a3)
    damage_factor_bau = 1 / (1 + params.a2 * laissez_faire[:, params.i_T_AT] ** params.a3)
    series = [
        (optimal[:, params.i_Y], laissez_faire[:, params.i_Y], "Production $Y_t$"),
        (consumption_per_capita, consumption_per_capita_bau, "Consommation par habitant $c_t$"),
        (optimal[:, params.i_mu], laissez_faire[:, params.i_mu], "Taux de réduction $\\mu_t$"),
        (optimal[:, params.i_s], laissez_faire[:, params.i_s], "Taux d'épargne $s_t$"),
        (optimal[:, params.i_E], laissez_faire[:, params.i_E], "Émissions (GtCO$_2$) $E_t$"),
        (damage_factor, damage_factor_bau, "Facteur de dommages $\\Omega_t$"),
        (optimal[:, params.i_T_AT], laissez_faire[:, params.i_T_AT], "Température atmosphérique $T_t^{AT}$"),
        (optimal[:, params.i_M_AT], laissez_faire[:, params.i_M_AT], "Carbone atmosphérique (GtC) $M_t^{AT}$"),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(10, 6))
    for axis, (series_optimal, series_bau, title) in zip(axes.flat, series):
        axis.plot(optimal[:, params.i_time], series_optimal, color="#1b9e77",
                  linewidth=1.8, label="Politique d'atténuation")
        axis.plot(laissez_faire[:, params.i_time], series_bau,
                  color="#d95f02", linestyle="--", linewidth=1.5,
                  label="Laisser-faire")
        axis.set_title(title, fontsize=8)
        axis.tick_params(labelsize=7)
        axis.grid(alpha=0.35)
    axes[-1, -1].legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(HERE / "images" / "figure_1.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_welfare_tradeoff(params, laissez_faire, optimal):
    time = optimal[:, params.i_time]
    consumption_loss = 100 * (optimal[:, params.i_C] / laissez_faire[:, params.i_C] - 1)
    warming_avoided = optimal[:, params.i_T_AT] - laissez_faire[:, params.i_T_AT]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    plots = [
        (optimal[:, params.i_Tax], "Coût social du carbone (USD/t)"),
        (consumption_loss, "Variation de consommation (% vs laisser-faire)"),
        (warming_avoided, "Réchauffement évité ($^\\circ$C vs laisser-faire)"),
    ]
    for axis, (series, title) in zip(axes, plots):
        axis.plot(time, series, color="#1f77b4", linewidth=1.8)
        axis.set_title(title, fontsize=9)
        axis.tick_params(labelsize=8)
        axis.grid(alpha=0.35)
    fig.tight_layout()
    fig.savefig(HERE / "images" / "figure_3.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    parameters, business_as_usual, optimal_policy = policy_paths()
    plot_policy_comparison(parameters, business_as_usual, optimal_policy)
    plot_welfare_tradeoff(parameters, business_as_usual, optimal_policy)
