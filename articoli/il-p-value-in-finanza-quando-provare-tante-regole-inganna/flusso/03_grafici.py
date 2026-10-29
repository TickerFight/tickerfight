"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_pvalue_per_regola.png    p-value di ciascuna regola, con le soglie del 5% e di Bonferroni
  fig2_massimo_nullo.png        massimo |t| sotto l'ipotesi nulla (spostamenti circolari), con la regola migliore e quella a 200 sedute
  fig3_falsi_positivi.png       numero di regole «significative» per caso negli spostamenti, contro quello osservato
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    g = pd.read_csv(R / "regole.csv")
    nu = pd.read_csv(R / "nulla.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(g["lunghezza"], np.clip(g["p"], 1e-12, 1), width=4, color=BLU)
    ax.set_yscale("log")
    ax.axhline(0.05, color=ARANCIO, lw=2, label="Soglia del 5%")
    ax.axhline(0.05 / len(g), color="#222", lw=2, ls="--", label="Soglia di Bonferroni")
    ax.set_xlabel("Lunghezza della media mobile (sedute)")
    ax.set_ylabel("P-value (scala logaritmica)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig1_pvalue_per_regola.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(nu["max_t"], bins=40, color=GRIGIO, alpha=0.85)
    ax.axvline(m["t_soglia_max"]["valore"], color=ARANCIO, lw=2, ls="--", label="95° percentile del massimo nullo")
    ax.axvline(abs(m["t_migliore"]["valore"]), color=BLU, lw=2.5, label="Regola migliore")
    ax.axvline(abs(m["t_famosa"]["valore"]), color="#222", lw=2.5, label="Regola a 200 sedute")
    ax.set_xlabel("Massimo |t| tra le cinquanta regole, dopo uno spostamento circolare")
    ax.set_ylabel("Spostamenti")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_massimo_nullo.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(nu["n_sig"], bins=np.arange(nu["n_sig"].max() + 2) - 0.5, color=GRIGIO, alpha=0.85)
    ax.axvline(m["n_sig"]["valore"], color=BLU, lw=2.5, label="Regole significative osservate")
    ax.set_xlabel("Regole con p-value sotto il 5% per puro caso")
    ax.set_ylabel("Spostamenti")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_falsi_positivi.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
