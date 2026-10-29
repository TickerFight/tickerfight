"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore.png   valore di un dollaro in tecnologia e nel resto (scala logaritmica)
  fig2_finestre_5anni.png       rendimento annuo delle finestre mobili di cinque anni, per ETF
  fig3_scimmie.png              valore finale delle scimmie contro tecnologia e resto
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    f = pd.read_csv(R / "finestre_5anni.csv", parse_dates=["data"])
    s = pd.read_csv(R / "scimmie.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(c["data"], c["resto"], color=BLU, lw=2, label="Il resto (otto settori)")
    ax.plot(c["data"], c["xlk"], color=ARANCIO, lw=2, label="Tecnologia (XLK)")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(f["data"], f["RESTO"] * 100, color=BLU, lw=2, label="Il resto")
    ax.plot(f["data"], f["XLK"] * 100, color=ARANCIO, lw=2, label="Tecnologia")
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Rendimento annuo su cinque anni (%)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig2_finestre_5anni.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    cap = m["capitale"]["valore"]
    ax.hist(s["finale"] * cap, bins=50, color=GRIGIO, alpha=0.85)
    ax.axvline(m["resto_finale"]["valore"], color=BLU, lw=2.5, label="Tutto nel resto")
    ax.axvline(m["xlk_finale"]["valore"], color=ARANCIO, lw=2.5, label="Tutto in tecnologia")
    ax.set_xlabel(f"Valore finale di {cap:.0f} dollari scegliendo a caso tra tecnologia e resto ogni mese")
    ax.set_ylabel("Scimmie")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_scimmie.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
