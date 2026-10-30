"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_sott_acqua.png        il drawdown dell'S&P 500 a ogni seduta dal 1927
  fig2_profondita_durata.png ogni episodio: profondità e durata totale
  fig3_discesa_recupero.png  discesa e recupero dei drawdown >= 10%
  fig4_contro_il_caso.png    drawdown massimo delle serie rimescolate e quello reale
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
pct = lambda x, _: f"{x:.0f}%"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    S = pd.read_csv(R / "drawdown_serie.csv", parse_dates=["Date"])
    E = pd.read_csv(R / "episodi.csv", parse_dates=["picco", "minimo", "recupero"])
    Q = pd.read_csv(R / "rimescolate.csv")

    # Figura 1
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.fill_between(S["Date"], S["drawdown"] * 100, 0, color=BLU, alpha=0.55, lw=0)
    ax.plot(S["Date"], S["drawdown"] * 100, color=BLU, lw=0.6)
    ax.axhline(-20, color=ARANCIO, lw=1.3, ls="--")
    ax.text(S["Date"].iloc[0], -18.5, "−20%", color=ARANCIO, fontsize=10)
    ax.yaxis.set_major_formatter(pct)
    ax.set_ylabel("distanza dal massimo storico")
    ax.set_xlabel("anno")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_sott_acqua.png")
    plt.close(fig)

    # Figura 2
    C = E[~E["aperto"]]
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.scatter(C["giorni_totali"] / 365.25, C["profondita"] * 100, color=BLU, s=38, alpha=0.8, label="drawdown recuperati")
    A = E[E["aperto"]]
    if len(A):
        ax.scatter([(S["Date"].iloc[-1] - A["picco"].iloc[0]).days / 365.25], A["profondita"] * 100, color=ARANCIO, s=70, marker="D", label="ancora in corso")
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 5, 10, 25], ["3 mesi", "6 mesi", "1 anno", "2 anni", "5 anni", "10 anni", "25 anni"])
    ax.set_xlabel("durata dal massimo al nuovo massimo (scala logaritmica)")
    ax.set_ylabel("profondità del drawdown")
    ax.yaxis.set_major_formatter(pct)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_profondita_durata.png")
    plt.close(fig)

    # Figura 3 (assi logaritmici: il 1929 è un caso a parte)
    G = C[C["profondita"] >= config.SOGLIA_RECUPERO_ANALISI].copy()
    x = G["giorni_discesa"].clip(lower=1) / config.GIORNI_MESE
    y = G["giorni_recupero"].clip(lower=1) / config.GIORNI_MESE
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    sopra = y > x
    ax.scatter(x[sopra], y[sopra], color=ARANCIO, s=40, label="il recupero dura più della discesa")
    ax.scatter(x[~sopra], y[~sopra], color=BLU, s=40, label="la discesa dura più del recupero")
    lo = min(x.min(), y.min()) * 0.8
    hi = max(x.max(), y.max()) * 1.25
    ax.plot([lo, hi], [lo, hi], color=GRIGIO, lw=1.3, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("mesi di discesa (dal massimo al minimo), scala logaritmica")
    ax.set_ylabel("mesi di recupero (dal minimo al nuovo massimo), scala logaritmica")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_discesa_recupero.png")
    plt.close(fig)

    # Figura 4
    reale = E["profondita"].max() * 100
    fig, ax = plt.subplots(figsize=(10, 5.0))
    ax.hist(Q["dd_max"] * 100, bins=30, color=GRIGIO, alpha=0.75)
    ax.axvline(reale, color=ARANCIO, lw=2.6)
    ax.text(reale, ax.get_ylim()[1] * 0.92, " serie vera", color=ARANCIO, ha="right", fontsize=11)
    ax.xaxis.set_major_formatter(pct)
    ax.set_xlabel("drawdown massimo")
    ax.set_ylabel("numero di serie rimescolate")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_contro_il_caso.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
