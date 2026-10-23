"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_curve_50_200.png       le medie 50/200: valore di 500 euro con look-ahead, onesto e buy & hold (scala logaritmica)
  fig2_tre_regole.png         rendimento annuo di tre regole, con look-ahead, onesto e buy & hold
  fig3_test_ritardo.png       il test del ritardo: rendimento annuo contro ritardo del segnale
  fig4_griglia_medie.png      l'illusione per una griglia di coppie di medie
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

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
    v = lambda k: V[k]["valore"]

    # --- Figura 1: curve della 50/200 -----------------------------------------------------------------------------
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(c["data"], config.CAPITALE * c["valore_cheat"], color=ARANCIO, lw=1.8, label="con look-ahead (segnale e rendimento dello stesso giorno)")
    ax.plot(c["data"], config.CAPITALE * c["valore_onesto"], color=BLU, lw=2.0, label="onesta (il segnale di ieri decide la posizione di oggi)")
    ax.plot(c["data"], config.CAPITALE * c["valore_bh"], color=GRIGIO, lw=1.6, ls="--", label="buy & hold")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
    ax.set_ylabel("valore di 500 euro, scala logaritmica")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_curve_50_200.png")
    plt.close(fig)

    # --- Figura 2: tre regole ------------------------------------------------------------------------------------
    fig, assi = plt.subplots(1, 3, figsize=(14, 4.8))
    for a, (rid, _) in zip(assi, config.REGOLE):
        valori = [v(f"{rid}_cagr_cheat") * 100, v(f"{rid}_cagr_onesto") * 100, v("cagr_bh") * 100]
        a.bar(range(3), valori, color=[ARANCIO, BLU, GRIGIO], width=0.65)
        for k, y in enumerate(valori):
            a.text(k, y + max(valori) * 0.02, f"{y:.1f}%".replace(".", ","), ha="center", fontsize=11)
        a.set_xticks(range(3), ["look-ahead", "onesta", "buy & hold"])
        a.set_title(TITOLI[rid], fontsize=12)
        a.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
        a.grid(axis="x", visible=False)
        a.set_ylim(0, max(valori) * 1.12)
    assi[0].set_ylabel("rendimento annuo composto, senza costi")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_tre_regole.png")
    plt.close(fig)

    # --- Figura 3: test del ritardo ----------------------------------------------------------------------------
    rit = pd.read_csv(R / "ritardi.csv")
    fig, assi = plt.subplots(1, 3, figsize=(14, 4.6))
    for a, (rid, _) in zip(assi, config.REGOLE):
        d = rit[rit["regola"] == rid]
        a.plot(d["ritardo"], d["cagr"] * 100, color=BLU, lw=2.2, marker="o", ms=5)
        a.axhline(v("cagr_bh") * 100, color=GRIGIO, lw=1.6, ls="--", label="buy & hold")
        a.scatter([0], [d["cagr"].iloc[0] * 100], color=ARANCIO, s=90, zorder=3, label="look-ahead")
        a.set_title(TITOLI[rid], fontsize=12)
        a.set_xlabel("ritardo del segnale, sedute")
        a.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    assi[0].set_ylabel("rendimento annuo composto, senza costi")
    assi[0].legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_test_ritardo.png")
    plt.close(fig)

    # --- Figura 4: griglia di medie ---------------------------------------------------------------------------
    g = pd.read_csv(R / "griglia.csv")
    P = g.pivot(index="veloce", columns="lenta", values="illusione") * 100
    mappa = LinearSegmentedColormap.from_list("bo", ["white", ARANCIO])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    im = ax.imshow(P.values, cmap=mappa, aspect="auto", vmin=0, vmax=float(np.nanmax(P.values)))
    for r in range(P.shape[0]):
        for k in range(P.shape[1]):
            if not np.isnan(P.values[r, k]):
                ax.text(k, r, f"{P.values[r, k]:.1f}".replace(".", ","), ha="center", va="center", fontsize=10)
    ax.set_xticks(range(P.shape[1]), [int(x) for x in P.columns])
    ax.set_yticks(range(P.shape[0]), [int(x) for x in P.index])
    ax.set_xlabel("media lenta, giorni")
    ax.set_ylabel("media veloce, giorni")
    if config.SMA_VELOCE in P.index and config.SMA_LENTA in P.columns:
        ax.add_patch(Rectangle((list(P.columns).index(config.SMA_LENTA) - 0.5, list(P.index).index(config.SMA_VELOCE) - 0.5), 1, 1, fill=False, ec="black", lw=2.5))
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("illusione, punti percentuali l'anno")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_griglia_medie.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
