"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_rendimenti.png   rendimento annuo composto: buy & hold e filtro, lordo e netto, e filtro con costi
  fig2_aliquote.png     vantaggio netto del filtro sul buy & hold al variare dell'aliquota, con l'aliquota di pareggio
  fig3_imposte_anni.png imposta pagata dal filtro in ogni anno, in percentuale del capitale a inizio anno
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

    Rn = pd.read_csv(R / "rendimenti.csv").set_index("variante")["cagr"] * 100
    ordine = ["bh_lordo", "bh_netto", "filtro_lordo", "filtro_netto", "filtro_netto_costi"]
    etich = ["Buy & hold\nlordo", "Buy & hold\nnetto", "Filtro\nlordo", "Filtro\nnetto", "Filtro netto\ncon costi"]
    colori = [GRIGIO, GRIGIO, BLU, BLU, ARANCIO]
    fig, ax = plt.subplots(figsize=(10, 5))
    vals = [Rn[k] for k in ordine]
    ax.bar(np.arange(5), vals, color=colori, alpha=0.9)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.05, f"{v:.2f}".replace(".", ",") + "%", ha="center", fontsize=11)
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(etich, fontsize=10)
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.set_ylim(0, max(vals) * 1.15)
    fig.savefig(config.FIGURE / "fig1_rendimenti.png")
    plt.close(fig)

    A = pd.read_csv(R / "aliquote.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(A["aliquota"] * 100, A["differenza"] * 100, color=BLU, lw=2.4)
    ax.axhline(0, color="#333", lw=1)
    ax.axvline(V["aliquota_pareggio"]["valore"] * 100, color=ARANCIO, ls="--", lw=1.4, label="Aliquota di pareggio")
    ax.axvline(config.ALIQUOTA * 100, color=GRIGIO, ls=":", lw=1.4, label="Aliquota del 26%")
    ax.set_xlabel("Aliquota sulle plusvalenze (%)")
    ax.set_ylabel("Filtro meno buy & hold, dopo le imposte (punti all'anno)")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_aliquote.png")
    plt.close(fig)

    I = pd.read_csv(R / "imposte_anni.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(I["anno"], I["imposta_pct_capitale"] * 100, color=ARANCIO, width=0.8)
    ax.set_xlabel("Anno solare")
    ax.set_ylabel("Imposta pagata dal filtro (% del capitale a inizio anno)")
    fig.savefig(config.FIGURE / "fig3_imposte_anni.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
