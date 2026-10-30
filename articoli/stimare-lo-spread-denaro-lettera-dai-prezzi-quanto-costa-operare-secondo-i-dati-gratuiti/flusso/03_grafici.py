"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_stima_e_tick.png         stima media di Corwin-Schultz e minimo teorico per ETF
  fig2_stima_e_volatilita.png   SPY: stima mensile contro volatilità del mese
  fig3_serie_mensile_spy.png    SPY: stima mensile nel tempo
"""
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
    e = pd.read_csv(R / "per_etf.csv")
    mm = pd.read_csv(R / "mensile_spy.csv", index_col=0)

    fig, ax = plt.subplots(figsize=(10, 5))
    xs = np.arange(len(e))
    ax.bar(xs - 0.2, e["cs"] * 100, 0.4, color=BLU, label="Stima media (Corwin-Schultz)")
    ax.bar(xs + 0.2, e["tick"] * 100, 0.4, color=ARANCIO, label="Minimo teorico (un centesimo)")
    ax.set_xticks(xs)
    ax.set_xticklabels(e["etf"])
    ax.set_ylabel("Spread, % del prezzo")
    ax.legend()
    fig.savefig(config.FIGURE / "fig1_stima_e_tick.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(mm["vol"] * 100, mm["cs"] * 100, s=14, color=BLU, alpha=0.6)
    crisi = config.MESE_CRISI
    if crisi in mm.index:
        ax.scatter([mm.loc[crisi, "vol"] * 100], [mm.loc[crisi, "cs"] * 100], s=80, color=ARANCIO, label="Marzo 2020")
        ax.legend()
    ax.set_xlabel("Volatilità giornaliera del mese, %")
    ax.set_ylabel("Stima mensile dello spread di SPY, %")
    fig.savefig(config.FIGURE / "fig2_stima_e_volatilita.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(pd.to_datetime(mm.index.astype(str)), mm["cs"] * 100, color=BLU, lw=1.6)
    ax.set_ylabel("Stima mensile dello spread di SPY, %")
    fig.savefig(config.FIGURE / "fig3_serie_mensile_spy.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
