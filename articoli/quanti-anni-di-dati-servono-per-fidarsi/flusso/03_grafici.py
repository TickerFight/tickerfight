"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_sharpe_finestre.png  Sharpe dell'S&P 500 su finestre di 5, 10 e 20 anni, per mese di partenza
  fig2_ventaglio.png        intervallo tra 5° e 95° percentile dello Sharpe per durata della finestra
  fig3_simulazione.png      strategia con Sharpe vero noto: probabilità di Sharpe negativo e potenza del test per durata
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f4f"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    se = pd.read_csv(R / "sharpe_serie.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5))
    for col, nome, colore, lw in (("anni_5", "Finestre di cinque anni", ARANCIO, 1.2), ("anni_10", "Finestre di dieci anni", BLU, 1.8), ("anni_20", "Finestre di venti anni", VERDE, 2.2)):
        ax.plot(se["data"], se[col], color=colore, lw=lw, label=nome)
    ax.axhline(0, color="#333", lw=1)
    ax.set_ylabel("Sharpe dell'S&P 500 (tasso zero)")
    ax.set_xlabel("Mese di partenza della finestra")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_sharpe_finestre.png")
    plt.close(fig)

    sf = pd.read_csv(R / "sharpe_finestre.csv")
    x = np.arange(len(sf))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, sf["p5"], sf["p95"], color=BLU, alpha=0.25, label="Dal 5° al 95° percentile")
    ax.plot(x, sf["p50"], color=BLU, lw=2.2, marker="o", label="Mediana")
    ax.plot(x, sf["minimo"], color=ARANCIO, lw=1.2, ls="--", label="Minimo")
    ax.plot(x, sf["massimo"], color=VERDE, lw=1.2, ls="--", label="Massimo")
    ax.axhline(0, color="#333", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{a} anni" if a > 1 else "1 anno" for a in sf["anni"]])
    ax.set_ylabel("Sharpe dell'S&P 500 (tasso zero)")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_ventaglio.png")
    plt.close(fig)

    S = pd.read_csv(R / "simulazione.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(S["anni"], S["p_neg"] * 100, color=ARANCIO, lw=2.2, label="Il backtest mostra uno Sharpe negativo")
    ax.plot(S["anni"], S["potenza"] * 100, color=BLU, lw=2.2, label="Il backtest riconosce che lo Sharpe non è zero")
    ax.axhline(config.POTENZA * 100, color=GRIGIO, ls="--", lw=1)
    ax.axvline(V["anni_potenza"]["valore"], color=GRIGIO, ls=":", lw=1.2)
    ax.set_xlabel("Anni di dati del backtest")
    ax.set_ylabel("Probabilità (%)")
    ax.set_ylim(0, 100)
    ax.legend(loc="center right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_simulazione.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
