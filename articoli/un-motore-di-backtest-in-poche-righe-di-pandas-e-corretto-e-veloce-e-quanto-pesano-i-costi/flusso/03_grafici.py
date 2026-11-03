"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_tempi.png          tempo del motore vettoriale e del ciclo 
  fig2_curve_50_200.png   le medie 50/200: valore di 500 euro senza costi, con costi, buy & hold
  fig3_costi.png          rendimento annuo di ogni regola contro il costo per cambio di posizione
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI
TITOLI = {"un_giorno": "un giorno", "media_20": "media a 20 giorni", "medie_50_200": "medie 50/200"}


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]

    t = pd.read_csv(R / "tempi.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(t))
    ax.bar([i - 0.2 for i in x], t["vettoriale_ms"], width=0.38, color=BLU, label="motore vettoriale")
    ax.bar([i + 0.2 for i in x], t["ciclo_ms"], width=0.38, color=ARANCIO, label="ciclo giorno per giorno")
    for i, (a, b) in enumerate(zip(t["vettoriale_ms"], t["ciclo_ms"])):
        ax.text(i - 0.2, a * 1.08, f"{a:.1f}".replace(".", ","), ha="center", fontsize=11)
        ax.text(i + 0.2, b * 1.08, f"{b:.1f}".replace(".", ","), ha="center", fontsize=11)
    ax.set_ylim(0, max(t["ciclo_ms"]) * 1.15)
    ax.set_xticks(list(x), [TITOLI[r] for r in t["regola"]])
    ax.set_ylabel("millisecondi per un backtest completo")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_tempi.png")
    plt.close(fig)

    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(c["data"], config.CAPITALE * c["valore_lordo"], color=BLU, lw=1.8, label="medie 50/200, senza costi")
    ax.plot(c["data"], config.CAPITALE * c["valore_netto"], color=BLU, lw=1.8, ls=":", label="medie 50/200, con costi")
    ax.plot(c["data"], config.CAPITALE * c["valore_bh"], color=GRIGIO, lw=1.6, ls="--", label="buy & hold")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
    ax.set_ylabel("valore di 500 euro, scala logaritmica")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_curve_50_200.png")
    plt.close(fig)

    k = pd.read_csv(R / "costi.csv")
    fig, ax = plt.subplots(figsize=(10, 5.4))
    colori = {"un_giorno": ARANCIO, "media_20": GRIGIO, "medie_50_200": BLU}
    for rid, d in k.groupby("regola", sort=False):
        ax.plot(d["costo"] * 100, d["cagr"] * 100, marker="o", lw=2.2, color=colori[rid], label=TITOLI[rid])
    ax.axhline(V["cagr_bh"]["valore"] * 100, color=GRIGIO, lw=1.6, ls="--", label="buy & hold (senza costi)")
    ax.set_xlabel("costo per ogni cambio di posizione, % del capitale")
    ax.set_ylabel("rendimento annuo composto")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
    ax.legend(loc="best", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_costi.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
