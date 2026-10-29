"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_contesto.png    S&P 500 (scala log) e VIX con la soglia e gli episodi
  fig2_orizzonti.png   rendimento medio degli episodi contro scimmie e generico, per orizzonte
  fig3_episodi.png     rendimento a un anno di ogni episodio
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


def pct_fmt(dec=0):
    return plt.FuncFormatter(lambda x, _: f"{x * 100:.{dec}f}%".replace(".", ","))


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    cur = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    ep = pd.read_csv(R / "episodi.csv", parse_dates=["segnale"])
    sc = pd.read_csv(R / "scimmie.csv")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True, gridspec_kw={"height_ratios": [1.2, 1]})
    a1.plot(cur["data"], cur["spx"], color=BLU, lw=1.5)
    a1.set_yscale("log")
    a1.set_ylabel("S&P 500 (scala log)")
    a1.set_title("Quando il VIX supera 30", loc="left", fontsize=13)
    a2.plot(cur["data"], cur["vix"], color=ARANCIO, lw=1.0)
    a2.axhline(config.SOGLIA_BASE, color=GRIGIO, ls="--", lw=1.2)
    for dt in ep["segnale"]:
        a1.axvline(dt, color=GRIGIO, alpha=0.5, lw=0.8)
        a2.axvline(dt, color=GRIGIO, alpha=0.5, lw=0.8)
    a2.set_ylabel("VIX")
    fig.savefig(config.FIGURE / "fig1_contesto.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(sc))
    ax.bar(x - 0.2, sc["media_ep"], width=0.4, color=BLU, label="Dopo VIX sopra 30")
    ax.bar(x + 0.2, sc["media_gen"], width=0.4, color=GRIGIO, label="Seduta qualunque")
    ax.errorbar(x + 0.2, sc["media_gen"], yerr=[sc["media_gen"] - sc["lo"], sc["hi"] - sc["media_gen"]], fmt="none", ecolor="black", capsize=4, lw=1,
                label="Intervallo al 95% delle scimmie")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{h} sedute" for h in sc["orizzonte"]])
    ax.yaxis.set_major_formatter(pct_fmt())
    ax.set_ylabel("Rendimento medio")
    ax.set_title("Rendimento medio dopo l'acquisto", loc="left", fontsize=13)
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_orizzonti.png")
    plt.close(fig)

    e = ep.dropna(subset=["r252"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    colori = [BLU if r > 0 else ARANCIO for r in e["r252"]]
    ax.bar(np.arange(len(e)), e["r252"], color=colori)
    ax.set_xticks(np.arange(len(e)))
    ax.set_xticklabels([str(s.year) for s in e["segnale"]], rotation=60, fontsize=10)
    ax.axhline(0, color="black", lw=0.8)
    ax.yaxis.set_major_formatter(pct_fmt())
    ax.set_ylabel("Rendimento a un anno dall'acquisto")
    ax.set_title("Episodio per episodio", loc="left", fontsize=13)
    fig.savefig(config.FIGURE / "fig3_episodi.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
