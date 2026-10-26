"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_fondo_contro_indice.png   rendimento di ogni periodo: fondo contro S&P 500 TR (il «profilo» del buffer)
  fig2_per_classe.png            differenza media fondo meno indice per classe di rendimento dell'indice
  fig3_per_anno.png              rendimento medio per anno di partenza: fondi e S&P 500 TR
  fig4_contro_80_20.png          rendimento di ogni periodo: fondo contro portafoglio 80% indice e 20% liquidità
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
    w = pd.read_csv(R / "finestre.csv", parse_dates=["inizio", "fine"])
    C = pd.read_csv(R / "classi.csv")
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]

    # Figura 1: profilo di rendimento
    x, y = w["r_spy"] * 100, w["r_fondo"] * 100
    fig, ax = plt.subplots(figsize=(7.5, 7))
    ax.scatter(x, y, s=22, color=GRIGIO, alpha=0.75)
    lim = [min(x.min(), y.min()) - 2, max(x.max(), y.max()) + 2]
    ax.plot(lim, lim, color=ARANCIO, lw=1.6, label="fondo = indice")
    ax.axhline(0, color="#555", lw=0.8)
    ax.axvline(0, color="#555", lw=0.8)
    ax.axvline(config.SOGLIA_FORTE * 100, color=BLU, lw=1.2, ls="--", label="soglia di forte rialzo")
    ax.set_xlabel("rendimento a 12 mesi dell'S&P 500 total return (%)")
    ax.set_ylabel("rendimento a 12 mesi del buffer ETF (%)")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_fondo_contro_indice.png")
    plt.close(fig)

    # Figura 2: differenza per classe
    fig, ax = plt.subplots(figsize=(9, 5))
    etichette = [f"indice in ribasso\n({int(n)} periodi)" if i == 0 else
                 (f"indice tra 0 e {config.SOGLIA_FORTE:.0%}\n({int(n)} periodi)" if i == 1 else f"indice oltre {config.SOGLIA_FORTE:.0%}\n({int(n)} periodi)")
                 for i, n in enumerate(C["n"])]
    vals = C["diff_media"].fillna(0) * 100
    ax.bar(etichette, vals, color=[BLU if v >= 0 else ARANCIO for v in vals], width=0.55)
    for i, v in enumerate(vals):
        ax.text(i, v + (0.4 if v >= 0 else -1.2), f"{v:+.1f}".replace(".", ","), ha="center", fontsize=11)
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("fondo meno indice (punti percentuali)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_per_classe.png")
    plt.close(fig)

    # Figura 3: per anno di partenza
    a = w.groupby("anno_partenza")[["r_fondo", "r_spy"]].mean() * 100
    fig, ax = plt.subplots(figsize=(11, 5))
    xx = np.arange(len(a))
    ax.bar(xx - 0.2, a["r_spy"], width=0.4, color=GRIGIO, label="S&P 500 total return")
    ax.bar(xx + 0.2, a["r_fondo"], width=0.4, color=BLU, label="buffer ETF (media dei fondi)")
    ax.set_xticks(xx, [str(int(i)) for i in a.index])
    ax.axhline(0, color="#555", lw=1)
    ax.set_xlabel("anno di partenza del periodo di 12 mesi")
    ax.set_ylabel("rendimento medio (%)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_per_anno.png")
    plt.close(fig)

    # Figura 4: contro il portafoglio 80/20
    x, y = w["r_mix"] * 100, w["r_fondo"] * 100
    fig, ax = plt.subplots(figsize=(7.5, 7))
    ax.scatter(x, y, s=22, color=GRIGIO, alpha=0.75)
    lim = [min(x.min(), y.min()) - 2, max(x.max(), y.max()) + 2]
    ax.plot(lim, lim, color=ARANCIO, lw=1.6, label="fondo = 80% indice e 20% liquidità")
    ax.axhline(0, color="#555", lw=0.8)
    ax.axvline(0, color="#555", lw=0.8)
    ax.set_xlabel("rendimento a 12 mesi del portafoglio 80/20 (%)")
    ax.set_ylabel("rendimento a 12 mesi del buffer ETF (%)")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_contro_80_20.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
