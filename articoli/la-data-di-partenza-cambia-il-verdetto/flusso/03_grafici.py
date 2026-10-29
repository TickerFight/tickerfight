"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore.png     valore di 1 per regola e buy & hold, scala logaritmica
  fig2_diff_10anni.png  differenza di rendimento annuo (regola meno buy & hold) per ogni mese di partenza, finestre di dieci anni
  fig3_quote.png      quota di partenze in cui vince la regola, per misura e per durata
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(c["data"], c["buyhold"], color=ARANCIO, lw=1.8, label="Buy & hold")
    ax.plot(c["data"], c["regola"], color=BLU, lw=1.8, label="Filtro a 200 sedute")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    W = pd.read_csv(R / f"finestre_{config.ORIZZONTE_PRINCIPALE}.csv", parse_dates=["data"])
    diff = (W["cagr_r"] - W["cagr_b"]) * 100
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(W["data"], diff, 0, where=diff >= 0, color=BLU, alpha=0.75, label="La regola batte il buy & hold")
    ax.fill_between(W["data"], diff, 0, where=diff < 0, color=ARANCIO, alpha=0.75, label="Il buy & hold batte la regola")
    ax.axhline(0, color="#333", lw=1)
    for anno in (config.ANNO_SFAVOREVOLE, config.ANNO_FAVOREVOLE):
        ax.axvline(pd.Timestamp(f"{anno}-01-01"), color=GRIGIO, ls=":", lw=1.2)
        ax.text(pd.Timestamp(f"{anno}-01-01"), diff.max() * 0.92, str(anno), ha="center", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.set_xlabel("Mese di partenza della finestra di dieci anni")
    ax.set_ylabel("Differenza di rendimento annuo (punti)")
    ax.legend(loc="lower left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_diff_10anni.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(config.ORIZZONTI))
    for k, (chiave, nome, col) in enumerate((("quota_rend", "Rendimento annuo più alto", BLU), ("quota_sharpe", "Sharpe più alto", GRIGIO),
                                              ("quota_dd", "Perdita massima minore", ARANCIO))):
        ax.bar(x + (k - 1) * 0.27, [V[f"h{h}_{chiave}"]["valore"] * 100 for h in config.ORIZZONTI], width=0.27, color=col, label=nome)
    ax.axhline(50, color="#333", lw=1, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} anni" for h in config.ORIZZONTI])
    ax.set_ylabel("Quota di partenze in cui vince la regola (%)")
    ax.legend(loc="upper left", fontsize=10, ncol=1)
    ax.set_ylim(0, 105)
    fig.savefig(config.FIGURE / "fig3_quote.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
