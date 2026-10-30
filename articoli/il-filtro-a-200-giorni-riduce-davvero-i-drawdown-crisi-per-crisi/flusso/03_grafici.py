"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_perdite_per_episodio.png   perdita del buy & hold e della regola in ogni episodio
  fig2_uscita.png                 calo dell'indice al momento dell'uscita della regola
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    e = pd.read_csv(R / "episodi.csv")
    xs = np.arange(len(e))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(xs - 0.2, e["perdita_bh"] * 100, 0.4, color=GRIGIO, label="Buy & hold")
    ax.bar(xs + 0.2, e["perdita_reg"] * 100, 0.4, color=BLU, label="Regola")
    ax.axhline(0, color="#555", lw=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(e["etichetta"], rotation=60, ha="right", fontsize=10)
    ax.set_ylabel("Perdita dal massimo al minimo dell'episodio, %")
    ax.legend()
    fig.savefig(config.FIGURE / "fig1_perdite_per_episodio.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(xs, e["calo_all_uscita"] * 100, color=ARANCIO)
    ax.set_xticks(xs)
    ax.set_xticklabels(e["etichetta"], rotation=60, ha="right", fontsize=10)
    ax.set_ylabel("Calo dell'indice dal massimo quando la regola esce, %")
    fig.savefig(config.FIGURE / "fig2_uscita.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
