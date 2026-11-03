"""Passo 3 - Grafici. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png   rendimento annuo della regola: lordo e netto con 0, 1 e 3 euro, contro il buy & hold netto
  fig2_griglia.png       valore finale netto di regola e buy & hold al crescere della commissione (0-10 euro)
  fig3_scimmie.png       valore finale della regola meno la mediana delle scimmie, nei tre scenari di costo
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white",
                     "legend.frameon": False})
R = config.RISULTATI
M = f"c{config.SCENARIO_PRINCIPALE}"


def breve(n):
    return n.split(" (")[0]


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "strumenti_usati.json").read_text(encoding="utf-8"))
    gr = pd.read_csv(R / "griglia.csv")
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    slugs = [i["slug"] for i in ind]
    nomi = {i["slug"]: breve(i["nome"]) for i in ind}
    tk = {i["slug"]: i["ticker"] for i in ind}
    ns = len(slugs)
    sc = [("lordo", "lordo"), ("c0", "0 euro"), ("c1", "1 euro"), ("c2", "3 euro")]
    pos = np.arange(len(sc))

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), sharey=True, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        cols = [GRIGIO, BLU, BLU, BLU]
        ax.bar(pos, [v(sl, f"t_{sid}_cagr") * 100 for sid, _ in sc], 0.6, color=cols)
        ax.axhline(v(sl, "bh_c0_cagr") * 100, color=ARANCIO, ls="--", lw=1.6, label="buy & hold, netto")
        ax.set_xticks(pos, [n for _, n in sc])
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("rendimento annuo composto (%)")
    assi[0][0].legend(fontsize=9, loc="upper right")
    fig.suptitle("La stessa regola: lordo e netto con 0, 1 e 3 euro a ordine", y=1.02)
    fig.savefig(config.FIGURE / "fig1_lordo_netto.png"); plt.close(fig)

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        g = gr[gr["strumento"] == tk[sl]]
        ax.plot(g["commissione"], g["regola"], color=BLU, lw=2, label="regola di trend")
        ax.plot(g["commissione"], g["buy_hold"], color=ARANCIO, ls="--", lw=2, label="buy & hold")
        for x in (0, 1, 3):
            ax.axvline(x, color=GRIGIO, lw=0.8, alpha=0.6)
        ax.set_xlabel("commissione per ordine (euro)")
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("valore finale netto di 1.000 euro")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("Quanto resta al crescere della commissione (le righe grigie sono 0, 1 e 3 euro)", y=1.02)
    fig.savefig(config.FIGURE / "fig2_griglia.png"); plt.close(fig)

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), squeeze=False)
    cs = ["c0", "c1", "c2"]
    p3 = np.arange(3)
    for ax, sl in zip(assi[0], slugs):
        med = np.array([v(sl, f"{c}_sc_mediana") for c in cs])
        lo = np.array([v(sl, f"{c}_sc_p5") for c in cs]) - med
        hi = np.array([v(sl, f"{c}_sc_p95") for c in cs]) - med
        reale = np.array([v(sl, f"t_{c}_finale") for c in cs]) - med
        ax.fill_between(p3, lo, hi, color=GRIGIO, alpha=0.3, label="scimmie, dal 5° al 95° percentile")
        ax.plot(p3, reale, color=BLU, marker="o", label="regola")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(p3, ["0 euro", "1 euro", "3 euro"])
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("euro finali meno la mediana delle scimmie")
    assi[0][0].legend(fontsize=8, loc="upper right", frameon=True, framealpha=0.9)
    fig.suptitle("La regola contro le scimmie (stessa durata investita, stesso numero di periodi)", y=1.02)
    fig.savefig(config.FIGURE / "fig3_scimmie.png"); plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
