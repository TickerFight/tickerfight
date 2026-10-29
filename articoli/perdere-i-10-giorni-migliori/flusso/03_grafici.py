"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_giorni_saltati.png    rendimento annuo composto saltando i giorni migliori, i peggiori o entrambi (10, 20 e 40 giorni)
  fig2_finestre.png          perdita in punti all'anno saltando i 10 giorni migliori, per mese di partenza di finestre di 10 e 20 anni
  fig3_mappa_giorni.png      indice in scala logaritmica con i 10 giorni migliori e i 10 peggiori e la media a 200 sedute
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f4f"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]

    # 1. barre
    T = pd.read_csv(R / "tabella_giorni.csv")
    T = T[T["giorni"].isin([10, 20, 40])]
    x = np.arange(len(T))
    w = 0.26
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, T["cagr_senza_migliori"] * 100, w, color=ARANCIO, label="Senza i giorni migliori")
    ax.bar(x, T["cagr_senza_peggiori"] * 100, w, color=VERDE, label="Senza i giorni peggiori")
    ax.bar(x + w, T["cagr_senza_entrambi"] * 100, w, color=BLU, label="Senza i migliori e i peggiori")
    ax.axhline(V["cagr_bh"]["valore"] * 100, color="#333", lw=1.5, ls="--", label="Buy & hold")
    ax.axhline(0, color="#333", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{g} giorni" for g in T["giorni"]])
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_giorni_saltati.png")
    plt.close(fig)

    # 2. finestre
    F = pd.read_csv(R / "finestre_perdita.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(F["data"], F["perdita_10_anni"] * 100, color=ARANCIO, lw=1.2, label="Finestre di 10 anni")
    ax.plot(F["data"], F["perdita_20_anni"] * 100, color=BLU, lw=2.0, label="Finestre di 20 anni")
    ax.axhline(V["lb10"]["valore"] * 100, color=GRIGIO, ls="--", lw=1.2, label="Intera storia")
    ax.set_ylabel("Punti all'anno persi saltando i 10 giorni migliori")
    ax.set_xlabel("Mese di partenza della finestra")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_finestre.png")
    plt.close(fig)

    # 3. mappa
    S = pd.read_csv(R / "serie_indice.csv", parse_dates=["data"])
    E = pd.read_csv(R / "giorni_estremi.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(S["data"], S["chiusura"], color=GRIGIO, lw=1.2, label="S&P 500")
    ax.plot(S["data"], S["media"], color=BLU, lw=1.0, alpha=0.8, label="Media a 200 sedute")
    m, p = E[E["tipo"] == "migliore"], E[E["tipo"] == "peggiore"]
    ax.scatter(m["data"], m["chiusura"], marker="^", s=70, color=VERDE, zorder=5, label="10 giorni migliori")
    ax.scatter(p["data"], p["chiusura"], marker="v", s=70, color=ARANCIO, zorder=5, label="10 giorni peggiori")
    ax.set_yscale("log")
    ax.set_ylabel("Livello dell'indice (scala logaritmica)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_mappa_giorni.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
