"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_ottimizzazione_e_prova.png   per ogni finestra: rendimento annuo della coppia scelta in ottimizzazione e in prova
  fig2_dimensione_griglia.png       quanto sale il rendimento in ottimizzazione e quanto in prova, al crescere delle coppie provate
  fig3_posto_in_prova.png           il posto della coppia ottimizzata tra tutte quelle della griglia, nel periodo di prova
  fig4_coppie_scelte.png            le coppie scelte finestra dopo finestra
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
    W = pd.read_csv(R / "finestre.csv", parse_dates=["inizio_prova", "fine_prova", "inizio_ott", "fine_ott"])
    E = pd.read_csv(R / "esperimento_griglia.csv")
    etich = [str(d.year) for d in W["inizio_prova"]]
    x = np.arange(len(W))

    # --- Figura 1 ------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.4))
    for k in x:
        ax.plot([k, k], [W["cagr_ott"][k] * 100, W["cagr_prova"][k] * 100], color=GRIGIO, lw=1.6, zorder=1)
    ax.scatter(x, W["cagr_ott"] * 100, color=BLU, s=60, zorder=3, label="in ottimizzazione (dieci anni, la coppia è scelta qui)")
    ax.scatter(x, W["cagr_prova"] * 100, color=ARANCIO, s=60, marker="D", zorder=3, label="in prova (i cinque anni dopo, mai visti)")
    ax.scatter(x, W["cagr_prova_bh"] * 100, color=GRIGIO, s=40, marker="_", linewidths=2.5, zorder=2, label="buy & hold, stessi cinque anni")
    ax.axhline(0, color="#555", lw=1)
    ax.set_xticks(x, etich, rotation=45, ha="right", fontsize=10)
    ax.yaxis.set_major_formatter(pct)
    ax.set_xlabel("anno di inizio del periodo di prova")
    ax.set_ylabel("rendimento annuo composto netto dei costi")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9, columnspacing=1.0, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_ottimizzazione_e_prova.png")
    plt.close(fig)

    # --- Figura 2 ------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.2))
    d = E["dimensione"].to_numpy()
    ax.plot(d, E["cagr_ott"] * 100, color=BLU, lw=2.4, marker="o", label="in ottimizzazione")
    ax.plot(d, E["cagr_prova"] * 100, color=ARANCIO, lw=2.4, marker="D", label="in prova")
    ax.fill_between(d, E["cagr_prova"] * 100, E["cagr_ott"] * 100, color=GRIGIO, alpha=0.2, lw=0)
    ax.set_xscale("log", base=2)
    ax.set_xticks(d, [str(int(v)) for v in d])
    ax.yaxis.set_major_formatter(pct)
    ax.set_xlabel("coppie di medie provate (il migliore in ottimizzazione viene scelto)")
    ax.set_ylabel("rendimento annuo medio del migliore")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_dimensione_griglia.png")
    plt.close(fig)

    # --- Figura 3 ------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.0))
    colori = [BLU if r > 0.5 else ARANCIO for r in W["rango_prova"]]
    ax.bar(x, W["rango_prova"] * 100, color=colori, width=0.7)
    ax.axhline(50, color="#555", lw=1.3, ls="--")
    ax.text(len(x) - 0.5, 52, "metà: come una coppia scelta a caso", ha="right", fontsize=10)
    ax.set_xticks(x, etich, rotation=45, ha="right", fontsize=10)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(pct)
    ax.set_xlabel("anno di inizio del periodo di prova")
    ax.set_ylabel("quota di coppie della griglia che fa meno")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_posto_in_prova.png")
    plt.close(fig)

    # --- Figura 4 ------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(x, W["lenta"], color=BLU, lw=2.2, marker="o", label="media lenta scelta")
    ax.plot(x, W["veloce"], color=ARANCIO, lw=2.2, marker="D", label="media veloce scelta")
    ax.set_xticks(x, etich, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("anno di inizio del periodo di prova")
    ax.set_ylabel("giorni")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_coppie_scelte.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
