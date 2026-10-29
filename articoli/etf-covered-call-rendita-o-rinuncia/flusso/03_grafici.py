"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore.png      valore di un dollaro nei quattro ETF (scala logaritmica)
  fig2_cattura.png     cattura dei mesi di rialzo e di ribasso, per le due coppie
  fig3_stessa_vol.png  covered call contro portafoglio indice e liquidità con la stessa volatilità
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
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    mx = pd.read_csv(R / "miste.csv", parse_dates=["data"])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(c["data"], c["spy"], color=BLU, lw=2, label="SPY (S&P 500)")
    ax.plot(c["data"], c["xyld"], color=BLU, lw=2, ls="--", label="XYLD (covered call sull'S&P 500)")
    ax.plot(c["data"], c["qqq"], color=ARANCIO, lw=2, label="QQQ (Nasdaq-100)")
    ax.plot(c["data"], c["qyld"], color=ARANCIO, lw=2, ls="--", label="QYLD (covered call sul Nasdaq-100)")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    etich = ["XYLD su SPY", "QYLD su QQQ"]
    x = np.arange(2)
    su = [V["xyld_cat_su"]["valore"] * 100, V["qyld_cat_su"]["valore"] * 100]
    giu = [V["xyld_cat_giu"]["valore"] * 100, V["qyld_cat_giu"]["valore"] * 100]
    ax.bar(x - 0.2, su, width=0.4, color=VERDE, label="Mesi di rialzo dell'indice")
    ax.bar(x + 0.2, giu, width=0.4, color=ARANCIO, label="Mesi di ribasso dell'indice")
    ax.axhline(100, color=GRIGIO, ls="--", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(etich)
    ax.set_ylabel("Quota dell'indice catturata (%)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_cattura.png")
    plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=False)
    for ax, (cc, nome, colore) in zip(axs, (("xyld", "XYLD", BLU), ("qyld", "QYLD", ARANCIO))):
        ax.plot(c["data"], c[cc], color=colore, lw=2, label=nome)
        ax.plot(mx["data"], mx[f"mix_{cc}"], color=GRIGIO, lw=2, label="Indice e liquidità, stessa volatilità")
        ax.set_title(f"{nome}: peso dell'indice {V[cc + '_w']['valore'] * 100:.0f}%".replace(".", ","), loc="left", fontsize=12)
        ax.legend(loc="upper left", fontsize=9)
        ax.tick_params(axis="x", rotation=30)
    axs[0].set_ylabel("Valore di 1 dollaro")
    fig.savefig(config.FIGURE / "fig3_stessa_vol.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
