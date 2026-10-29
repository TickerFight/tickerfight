"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_cagr_prezzo_totale.png   rendimento annuo del buy & hold: solo prezzo contro rendimento totale, per strumento
  fig2_spy_curve.png            SPY: valore di 500 euro a soli prezzi e a rendimento totale (scala logaritmica)
  fig3_regola_versioni.png      regola 50/200: rendimento annuo con segnale su Adj Close, su Close e valutata sui soli prezzi
  fig4_apple_grezzo.png         Apple: prezzo grezzo contro prezzo corretto per gli split (scala logaritmica)
"""
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
PCT = lambda x, _: f"{x * 100:.0f}%"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(R / "strumenti.csv")
    nomi = {c: n.split(" (")[0] for c, _, n in config.STRUMENTI}
    etichette = [t.loc[i, "ticker"] for i in t.index]
    x = np.arange(len(t))

    # Figura 1
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.bar(x - 0.2, t["cagr_prezzo"], 0.4, color=ARANCIO, label="solo prezzo (colonna Close)")
    ax.bar(x + 0.2, t["cagr_totale"], 0.4, color=BLU, hatch="//", edgecolor="white", label="rendimento totale (colonna Adj Close)")
    ax.set_xticks(x, etichette)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylabel("rendimento annuo del buy & hold")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_cagr_prezzo_totale.png")
    plt.close(fig)

    # Figura 2
    c = pd.read_csv(R / "curve_spy.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(c["data"], c["prezzo"], color=ARANCIO, lw=2, label="solo prezzo (Close)")
    ax.plot(c["data"], c["totale"], color=BLU, lw=2, ls="--", label="rendimento totale (Adj Close)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    ax.set_ylabel("valore di 500 euro, scala logaritmica")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_spy_curve.png")
    plt.close(fig)

    # Figura 3
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.bar(x - 0.27, t["A"], 0.27, color=BLU, label="corretta: segnale e rendimento su Adj Close")
    ax.bar(x, t["B"], 0.27, color=GRIGIO, label="segnale su Close, rendimento totale")
    ax.bar(x + 0.27, t["C"], 0.27, color=ARANCIO, label="segnale su Close, rendimento solo prezzo")
    ax.set_xticks(x, etichette)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylabel("rendimento annuo della regola 50/200")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_regola_versioni.png")
    plt.close(fig)

    # Figura 4
    a = pd.read_csv(R / "aapl_prezzi.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(a["data"], a["grezzo"], color=ARANCIO, lw=1.6, label="prezzo grezzo (senza correzione degli split)")
    ax.plot(a["data"], a["corretto"], color=BLU, lw=2, ls="--", label="prezzo corretto per gli split")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    ax.set_ylabel("chiusura di Apple in dollari, scala logaritmica")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_apple_grezzo.png")
    plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
