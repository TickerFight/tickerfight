"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_spread_e_recessioni.png   spread 10 anni - 3 mesi, curva invertita e recessioni NBER
  fig2_anticipo_episodi.png      per ogni episodio: mesi tra inizio dell'inversione e inizio della recessione (o falso allarme)
  fig3_strategia_e_buy_hold.png  capitale della strategia e del buy & hold (scala logaritmica)
  fig4_contro_il_caso.png        rendimento annuo delle strategie con segnale spostato nel tempo
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
    m = pd.read_csv(R / "mensile.csv", parse_dates=["Date"], index_col="Date")
    E = pd.read_csv(R / "episodi.csv", parse_dates=["inizio", "fine"])
    S = pd.read_csv(R / "spostamenti.csv")
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]

    # Figura 1
    fig, ax = plt.subplots(figsize=(11, 5))
    for picco, minimo in config.RECESSIONI:
        ax.axvspan(pd.Period(picco, "M").start_time, pd.Period(minimo, "M").end_time, color=GRIGIO, alpha=0.35, lw=0)
    ax.plot(m.index, m["spread"], color=BLU, lw=1.2)
    ax.fill_between(m.index, m["spread"], 0, where=m["spread"] < 0, color=ARANCIO, alpha=0.8, interpolate=True)
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("10 anni meno 3 mesi (punti percentuali)")
    ax.set_title("Arancio: curva invertita. Fasce grigie: recessioni dichiarate dal NBER", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_spread_e_recessioni.png")
    plt.close(fig)

    # Figura 2
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(E))
    for i, r in E.iterrows():
        if r["seguito"] == 1:
            ax.bar(i, r["anticipo_mesi"], color=BLU)
            ax.text(i, r["anticipo_mesi"] + 0.4, f"{int(r['anticipo_mesi'])}", ha="center", fontsize=10)
        elif r["censurato"] == 1:
            ax.bar(i, config.ORIZZONTE, color="white", edgecolor=GRIGIO, hatch="//")
            ax.text(i, config.ORIZZONTE + 0.4, "in corso", ha="center", fontsize=10, color="#555")
        else:
            ax.bar(i, config.ORIZZONTE, color="white", edgecolor=ARANCIO, hatch="//", lw=1.5)
            ax.text(i, config.ORIZZONTE + 0.4, "falso allarme", ha="center", fontsize=10, color=ARANCIO)
    ax.set_xticks(x, [d.strftime("%m/%Y") for d in E["inizio"]], rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("inizio dell'episodio di inversione")
    ax.set_ylabel("mesi alla recessione successiva")
    ax.set_ylim(0, config.ORIZZONTE + 4)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_anticipo_episodi.png")
    plt.close(fig)

    # Figura 3
    r = m.dropna(subset=["r_azioni"])
    cb = (1 + r["r_azioni"]).cumprod()
    cs = (1 + r["r_strategia"]).cumprod()
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(cb.index, cb, color=GRIGIO, lw=1.6, label="buy & hold S&P 500")
    ax.plot(cs.index, cs, color=BLU, lw=1.8, ls="--", label="fuori dalle azioni con la curva invertita")
    ax.set_yscale("log")
    ax.set_ylabel("capitale (partenza = 1, scala logaritmica)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_strategia_e_buy_hold.png")
    plt.close(fig)

    # Figura 4
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.hist(S["cagr"] * 100, bins=40, color=GRIGIO, alpha=0.85)
    ax.axvline(V["cagr_str"]["valore"] * 100, color=BLU, lw=2.5, ls="--", label="segnale vero")
    ax.axvline(V["cagr_bh"]["valore"] * 100, color=ARANCIO, lw=2.5, label="buy & hold")
    ax.set_xlabel("rendimento annuo composto (%)")
    ax.set_ylabel("numero di strategie")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_contro_il_caso.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
