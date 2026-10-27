"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_giorni.png        valore finale netto di ogni giorno del mese rispetto alla mediana, con la fascia delle scimmie
  fig2_scarto.png        scarto osservato tra giorno migliore e peggiore contro quello delle serie senza calendario
  fig3_stabilita.png     giorno migliore nella prima e nella seconda metà della storia
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
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    giorni = pd.read_csv(R / "giorni.csv", index_col="giorno")
    scarti = pd.read_csv(R / "scarti_permutati.csv")

    # --- Figura 1: giorni del mese ---------------------------------------------------------------------------
    n = len(ind)
    righe = (n + 2) // 3
    fig, assi = plt.subplots(righe, 3, figsize=(13, 3.6 * righe), sharex=True, squeeze=False)
    for ax, i in zip(assi.ravel(), ind):
        sl, nome = i["slug"], i["nome"]
        val = giorni[nome].values
        med = float(np.median(val))
        rel = (val / med - 1) * 100
        lo, hi = (v(sl, "sc_p5") / med - 1) * 100, (v(sl, "sc_p95") / med - 1) * 100
        ax.axhspan(lo, hi, color=GRIGIO, alpha=0.25, lw=0, label="scimmie (5°-95° percentile)")
        colori = [ARANCIO if g == v(sl, "giorno_mig") else BLU for g in giorni.index]
        ax.bar(giorni.index, rel, color=colori, width=0.8)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(nome, fontsize=11)
        ax.set_ylabel("rispetto alla mediana (%)")
    for ax in assi.ravel()[n:]:
        ax.axis("off")
    for ax in assi[-1]:
        ax.set_xlabel("giorno del mese")
    assi.ravel()[0].legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_giorni.png")
    plt.close(fig)

    # --- Figura 2: scarto osservato contro serie senza calendario -----------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for k, i in enumerate(ind):
        sl, tk = i["slug"], i["ticker"]
        s = scarti[tk].values * 100
        ax.vlines(k, np.percentile(s, 5), np.percentile(s, 95), color=GRIGIO, lw=10, alpha=0.5)
        ax.plot(k, np.median(s), "_", color="black", ms=18)
        oss = v(sl, "scarto") * 100
        ax.plot(k, oss, "o", color=ARANCIO if v(sl, "p_holm") < 0.05 else BLU, ms=9)
    ax.set_xticks(range(n))
    ax.set_xticklabels([i["nome"].split(" (")[0] for i in ind], rotation=20, ha="right")
    ax.set_ylabel("scarto tra giorno migliore e peggiore (%)")
    ax.set_ylim(bottom=0)
    fig.savefig(config.FIGURE / "fig2_scarto.png")
    plt.close(fig)

    # --- Figura 3: stabilità del giorno migliore ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for k, i in enumerate(ind):
        sl = i["slug"]
        g1, g2 = v(sl, "g_prima"), v(sl, "g_dopo")
        ax.plot([k, k], [g1, g2], color=GRIGIO, lw=2, zorder=1)
        ax.plot(k, g1, "o", color=BLU, ms=9, zorder=2, label="prima metà" if k == 0 else None)
        ax.plot(k, g2, "s", color=ARANCIO, ms=9, zorder=2, label="seconda metà" if k == 0 else None)
    ax.set_xticks(range(n))
    ax.set_xticklabels([i["nome"].split(" (")[0] for i in ind], rotation=20, ha="right")
    ax.set_ylabel("giorno migliore del mese")
    ax.set_ylim(0, 29)
    ax.legend(loc="upper right")
    fig.savefig(config.FIGURE / "fig3_stabilita.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
