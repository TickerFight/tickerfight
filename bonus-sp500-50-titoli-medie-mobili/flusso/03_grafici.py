"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_classifica.png               differenza finale (regola meno buy & hold) per ognuno dei 50 titoli
  fig2_rendimento_e_differenza.png  rendimento del buy & hold e differenza, un punto per titolo
  fig3_portafoglio.png              valore del portafoglio dei 50 titoli con la regola e con il buy & hold
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})


def euro(x, _=None):
    return f"{x:,.0f}".replace(",", ".") + " €"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    R = config.RISULTATI
    tab = pd.read_csv(R / "classifica.csv")
    pf = pd.read_csv(R / "curva_portafoglio.csv", parse_dates=["data"])

    # --- Figura 1: classifica ---------------------------------------------------------------------------
    t = tab.iloc[::-1].reset_index(drop=True)          # il migliore in alto
    fig, ax = plt.subplots(figsize=(10, 12))
    pos = t["differenza"].to_numpy() >= 0
    y = np.arange(len(t))
    ax.barh(y[pos], t["differenza"][pos], color=BLU, alpha=0.75, label="la regola chiude sopra")
    ax.barh(y[~pos], t["differenza"][~pos], color=ARANCIO, alpha=0.45, hatch="//", edgecolor="white",
            label="il buy & hold chiude sopra")
    ax.axvline(0, color="#333", lw=1)
    ax.set_yticks(y, t["ticker"], fontsize=9)
    ax.xaxis.set_major_formatter(euro)
    ax.set_xlabel("regola meno buy & hold, valore finale netto di 500 € investiti")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_classifica.png")
    plt.close(fig)

    # --- Figura 2: rendimento del buy & hold contro differenza ------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    x = tab["rend_bh_netto"].to_numpy() * 100
    d = tab["differenza"].to_numpy()
    ax.axhline(0, color="#333", lw=1)
    ax.axvline(0, color=GRIGIO, lw=1, ls=":")
    ax.scatter(x[d >= 0], d[d >= 0], s=55, color=BLU, label="la regola chiude sopra", zorder=3)
    ax.scatter(x[d < 0], d[d < 0], s=55, color=ARANCIO, marker="s", label="il buy & hold chiude sopra", zorder=3)
    estremi = set(tab.nlargest(3, "differenza").index) | set(tab.nsmallest(3, "differenza").index)
    for i in estremi:
        ax.annotate(tab.loc[i, "ticker"], (x[i], d[i]), textcoords="offset points", xytext=(6, 5), fontsize=10)
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:,.0f}%".replace(",", "."))
    ax.set_xlabel("rendimento netto del buy & hold nei cinque anni")
    ax.set_ylabel("regola meno buy & hold, netto")
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_rendimento_e_differenza.png")
    plt.close(fig)

    # --- Figura 3: portafoglio dei 50 titoli ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axhline(config.CAPITALE * len(tab), color=GRIGIO, lw=1, ls=":")
    ax.plot(pf["data"], pf["valore_bh_netto"], color=ARANCIO, lw=2.0, ls="--", label="buy & hold")
    ax.plot(pf["data"], pf["valore_regola_netto"], color=BLU, lw=2.2, label=f"regola {config.SMA_VELOCE}/{config.SMA_LENTA}")
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylabel("valore dei 50 titoli")
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_portafoglio.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
