"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_media_per_mese.png   rendimento medio dell'S&P 500 per mese, settembre in arancio
  fig2_settembri.png        rendimento di ogni settembre, dal peggiore al migliore
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(R / "medie_mensili.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([s[:3] for s in m["mese"]], m["media"] * 100, color=[ARANCIO if i == 8 else BLU for i in range(12)])
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Rendimento medio del mese, %")
    fig.savefig(config.FIGURE / "fig1_media_per_mese.png")
    plt.close(fig)

    s = pd.read_csv(R / "settembri.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(range(len(s)), s["rendimento"] * 100, color=[ARANCIO if x < 0 else BLU for x in s["rendimento"]], width=0.9)
    ax.axhline(0, color="#555", lw=1)
    ax.set_xlabel("Settembri, dal peggiore al migliore")
    ax.set_ylabel("Rendimento del mese, %")
    fig.savefig(config.FIGURE / "fig2_settembri.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
