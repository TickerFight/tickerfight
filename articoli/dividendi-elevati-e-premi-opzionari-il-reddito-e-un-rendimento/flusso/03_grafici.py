"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore.png     valore di un dollaro (distribuzioni reinvestite): SPY contro i sei ETF da reddito
  fig2_reddito.png    per ogni ETF, rendimento annuo diviso tra reddito distribuito e variazione del prezzo
  fig3_prelievo.png   capitale netto finale con prelievo del 4% e tasse
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
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    t = pd.read_csv(R / "tabella.csv").set_index("etf")

    fig, ax = plt.subplots(figsize=(10, 5))
    for j, s in enumerate(config.DIVIDENDO):
        ax.plot(c["data"], c[s.lower()], color=GRIGIO, lw=1.3, label="ETF a dividendo elevato" if j == 0 else None)
    for j, s in enumerate(config.PREMIO):
        ax.plot(c["data"], c[s.lower()], color=ARANCIO, lw=1.8, ls="--", label="ETF a premio opzionario" if j == 0 else None)
    ax.plot(c["data"], c["spy"], color=BLU, lw=2.4, label="SPY (S&P 500)")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    ordine = ["SPY"] + config.DIVIDENDO + config.PREMIO
    x = np.arange(len(ordine))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, t.loc[ordine, "prezzo"] * 100, color=[BLU if s == "SPY" else GRIGIO if s in config.DIVIDENDO else ARANCIO for s in ordine],
           label="Variazione del prezzo")
    ax.bar(x, t.loc[ordine, "reddito"] * 100, bottom=np.where(t.loc[ordine, "prezzo"] > 0, t.loc[ordine, "prezzo"] * 100, 0),
           color="white", edgecolor="black", hatch="//", label="Reddito distribuito")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(ordine)
    ax.set_ylabel("% annua composta")
    ax.set_ylim(top=t.loc[ordine, ["prezzo", "reddito"]].clip(lower=0).sum(axis=1).max() * 100 * 1.25)
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_reddito.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    v = t.loc[ordine, "finale_con_tasse"]
    ax.bar(x, v, color=[BLU if s == "SPY" else GRIGIO if s in config.DIVIDENDO else ARANCIO for s in ordine])
    ax.axhline(config.CAPITALE, color="black", ls="--", lw=1)
    ax.axhline(v["SPY"], color=BLU, ls="--", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(ordine)
    ax.set_ylabel("Capitale netto finale (dollari)")
    fig.savefig(config.FIGURE / "fig3_prelievo.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
