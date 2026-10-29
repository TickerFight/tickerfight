"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_giorni.png      rendimento medio per giorno della settimana con intervallo al 95% (punti base)
  fig2_periodi.png     media per giorno nei due sotto-periodi e senza i 10 giorni peggiori
  fig3_permutazione.png distribuzione della differenza tra giorno migliore e peggiore quando i giorni sono mescolati, e valore vero
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
    G = pd.read_csv(R / "giorni_settimana.csv")
    x = np.arange(5)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, G["media_pb"], color=[ARANCIO if i == 0 else BLU for i in x], alpha=0.9)
    ax.errorbar(x, G["media_pb"], yerr=[G["media_pb"] - G["lo_pb"], G["hi_pb"] - G["media_pb"]], fmt="none", ecolor="#333", capsize=5, lw=1.3)
    ax.axhline(0, color="#333", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([n.capitalize() for n in G["giorno"]])
    ax.set_ylabel("Rendimento medio giornaliero (punti base)")
    fig.savefig(config.FIGURE / "fig1_giorni.png")
    plt.close(fig)

    P = pd.read_csv(R / "periodi.csv")
    w = 0.27
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, P["periodo1_pb"], w, color=BLU, label=f"{config.PERIODO_1[0]}-{config.PERIODO_1[1]}")
    ax.bar(x, P["periodo2_pb"], w, color=VERDE, label=f"{config.PERIODO_2[0]}-oggi")
    ax.bar(x + w, P["senza_peggiori_pb"], w, color=GRIGIO, label="Intero periodo, senza i 10 giorni peggiori")
    ax.axhline(0, color="#333", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([n.capitalize() for n in P["giorno"]])
    ax.set_ylabel("Rendimento medio giornaliero (punti base)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_periodi.png")
    plt.close(fig)

    S = pd.read_csv(R / "permutazioni.csv")["differenza_pb"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(S, bins=60, color=GRIGIO, alpha=0.8)
    ax.axvline(V["differenza_estremi"]["valore"], color=ARANCIO, lw=2.2, label="Differenza vera")
    ax.set_xlabel("Differenza tra giorno migliore e peggiore (punti base)")
    ax.set_ylabel("Permutazioni")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_permutazione.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
