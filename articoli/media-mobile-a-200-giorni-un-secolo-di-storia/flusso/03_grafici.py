"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_curve.png     crescita di 1 dollaro: regola e buy & hold (scala logaritmica)
  fig2_decenni.png   rendimento annuo composto per decennio
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
    cv = pd.read_csv(R / "curve.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(pd.to_datetime(cv.index), cv["buy_hold"], color=GRIGIO, lw=2, label="Buy & hold")
    ax.plot(pd.to_datetime(cv.index), cv["regola"], color=BLU, lw=2, label="Media mobile a 200 sedute")
    ax.set_yscale("log")
    ax.set_ylabel("Crescita di 1 dollaro (scala logaritmica)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig1_curve.png")
    plt.close(fig)

    d = pd.read_csv(R / "decadi.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    xs = np.arange(len(d))
    ax.bar(xs - 0.2, d["buy_hold"] * 100, 0.4, color=GRIGIO, label="Buy & hold")
    ax.bar(xs + 0.2, d["regola"] * 100, 0.4, color=BLU, label="Regola")
    ax.axhline(0, color="#555", lw=1)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{x}s" for x in d["decennio"]])
    ax.set_ylabel("Rendimento annuo composto, %")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_decenni.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
