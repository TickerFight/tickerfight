"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_volatilita.png   volatilità del mese successivo per quintile del percentile del VIX
  fig2_rendimento.png   rendimento medio del mese successivo per quintile
  fig3_valore.png       valore di 1 euro: regola A, regola B, buy & hold
  fig4_perdite.png      perdite dal massimo: regola A contro buy & hold
  fig5_scimmie.png      Sharpe delle scimmie contro le due regole
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
ETICHETTE_Q = ["1° (VIX basso)", "2°", "3°", "4°", "5° (VIX alto)"]


def pct_fmt(dec=0):
    return plt.FuncFormatter(lambda x, _: f"{x * 100:.{dec}f}%".replace(".", ","))


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    Q = pd.read_csv(R / "quintili.csv")
    cur = pd.read_csv(R / "curve.csv", parse_dates=["data"])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(Q["quintile"], Q["vol_media"], color=BLU, alpha=0.85, hatch="//", edgecolor="white")
    ax.set_xticks(Q["quintile"])
    ax.set_xticklabels(ETICHETTE_Q, fontsize=10)
    ax.yaxis.set_major_formatter(pct_fmt())
    ax.set_xlabel("Quintile del percentile del VIX a fine mese")
    ax.set_ylabel("Volatilità annua del mese successivo")
    ax.set_title("Con il VIX alto, il mese dopo è più mosso", loc="left", fontsize=13)
    fig.savefig(config.FIGURE / "fig1_volatilita.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(Q["quintile"], Q["rend_medio"], color=ARANCIO, alpha=0.85)
    ax.axhline(V["rend_medio_tutti"]["valore"], color=GRIGIO, ls="--", lw=1.3, label="Media di tutti i mesi")
    ax.set_xticks(Q["quintile"])
    ax.set_xticklabels(ETICHETTE_Q, fontsize=10)
    ax.yaxis.set_major_formatter(pct_fmt(1))
    ax.set_xlabel("Quintile del percentile del VIX a fine mese")
    ax.set_ylabel("Rendimento medio del mese successivo")
    ax.set_title("E il rendimento del mese dopo?", loc="left", fontsize=13)
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig2_rendimento.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cur["data"], cur["buyhold"], color=ARANCIO, lw=1.7, label="Buy & hold")
    ax.plot(cur["data"], cur["regola_a"], color=BLU, lw=1.8, label="Regola A: fuori quando il VIX è alto")
    ax.plot(cur["data"], cur["regola_b"], color=GRIGIO, lw=1.4, ls="--", label="Regola B: dentro solo quando il VIX è alto")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 euro (scala logaritmica)")
    ax.set_title("S&P 500: quanto vale 1 euro investito all'inizio", loc="left", fontsize=13)
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_valore.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(cur["data"], cur["dd_buyhold"], 0, color=ARANCIO, alpha=0.35, label="Buy & hold")
    ax.fill_between(cur["data"], cur["dd_a"], 0, color=BLU, alpha=0.55, label="Regola A")
    ax.yaxis.set_major_formatter(pct_fmt())
    ax.set_ylabel("Distanza dal massimo precedente")
    ax.set_title("S&P 500: le perdite dal massimo", loc="left", fontsize=13)
    ax.legend(loc="lower left")
    fig.savefig(config.FIGURE / "fig4_perdite.png")
    plt.close(fig)

    sc = pd.read_csv(R / "scimmie_sharpe.csv")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    for ax, k, tit in zip(axs, ["a", "b"], ["Regola A", "Regola B"]):
        ax.hist(sc[k], bins=40, color=GRIGIO, alpha=0.7)
        ax.axvline(V[f"{k}_sh_lordo"]["valore"], color=BLU, lw=2.2)
        ax.set_title(f"{tit}: p = {V[f'{k}_p_sc']['valore']:.3f}".replace(".", ","), fontsize=12, loc="left")
        ax.set_yticks([])
        ax.set_xlabel("Sharpe lordo")
    fig.suptitle("Sharpe delle scimmie (stessa quota in azioni, mesi a caso) e della regola (linea blu)", x=0.01, ha="left", fontsize=13)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_scimmie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
