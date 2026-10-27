"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_griglia.png     rendimento annuo netto delle venti regole (osservazione x settori) con i due riferimenti
  fig2_meta.png        rendimento netto di ogni regola nella prima e nella seconda metà del periodo
  fig3_curve.png       valore di 10.000 euro: buy & hold, nove settori tenuti e regola centrale
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
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    regole = json.loads((R / "regole.json").read_text(encoding="utf-8"))
    v = lambda k: V[k]["valore"]
    Ls, Ks = config.LOOKBACKS, config.N_SETTORI
    eq, bh = v("eq_c0_cagr"), v("bh_c0_cagr")

    # Figura 1: griglia, in punti sopra i nove settori tenuti
    M = np.array([[v(f"r{L}_{k}_c0_cagr") - eq for L in Ls] for k in Ks]) * 100
    lim = np.abs(M).max()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    im = ax.imshow(M, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(Ls)))
    ax.set_xticklabels([f"{L} sedute" for L in Ls])
    ax.set_yticks(range(len(Ks)))
    ax.set_yticklabels([f"{k} {'settore' if k == 1 else 'settori'}" for k in Ks])
    ax.grid(False)
    for i in range(len(Ks)):
        for j in range(len(Ls)):
            ax.text(j, i, f"{M[i, j]:+.1f}".replace(".", ","), ha="center", va="center", fontsize=11)
    ax.set_xlabel("periodo di osservazione")
    fig.colorbar(im, ax=ax, label="punti all'anno sopra i nove settori tenuti")
    fig.savefig(config.FIGURE / "fig1_griglia.png")
    plt.close(fig)

    # Figura 2: prime contro seconde metà
    m = pd.read_csv(R / "meta_periodo.csv")
    r = m[~m["regola"].isin(["bh", "eq"])]
    fig, ax = plt.subplots(figsize=(7.2, 6))
    ax.scatter(r["meta1"] * 100, r["meta2"] * 100, color=BLU, s=55, zorder=3)
    best = r.loc[r["meta1"].idxmax()]
    ax.scatter([best["meta1"] * 100], [best["meta2"] * 100], color=ARANCIO, s=110, zorder=4, label="la migliore della prima metà")
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("rendimento annuo netto, prima metà (%)")
    ax.set_ylabel("rendimento annuo netto, seconda metà (%)")
    ax.legend(loc="best")
    fig.savefig(config.FIGURE / "fig2_meta.png")
    plt.close(fig)

    # Figura 3: curve
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(9.5, 5))
    centr = f"r{config.CENTRALE[0]}_{config.CENTRALE[1]}"
    ax.plot(c["data"], c["bh"], color=ARANCIO, lw=1.8, ls="--", label="buy & hold dell'S&P 500")
    ax.plot(c["data"], c["eq"], color=GRIGIO, lw=1.8, label="nove settori tenuti")
    ax.plot(c["data"], c[centr], color=BLU, lw=1.8, label="rotazione centrale")
    ax.set_ylabel("valore in euro, al netto di costi e tasse")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig3_curve.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
