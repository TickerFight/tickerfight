"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore_dogs_universo_spy.png   valore di un dollaro per Dogs, universo e SPY (scala logaritmica)
  fig2_eccesso_annuo.png              eccesso di rendimento dei Dogs sull'universo, anno per anno
  fig3_scimmie.png                    valore finale delle scimmie contro Dogs, universo e SPY
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f3f"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    a = pd.read_csv(R / "annuali.csv")
    a = a[a["completo"] == 1]
    s = pd.read_csv(R / "scimmie.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(c["data"], c["d10"], color=ARANCIO, lw=2, label="Dogs (dieci titoli)")
    ax.plot(c["data"], c["uni"], color=BLU, lw=2, label="Universo (trenta titoli, pesi uguali)")
    ax.plot(c["data"], c["spy"], color=GRIGIO, lw=2, label="SPY")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore_dogs_universo_spy.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ecc = (a["d10"] - a["uni"]) * 100
    ax.bar(a["anno"], ecc, color=[VERDE if v > 0 else ARANCIO for v in ecc])
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Dogs meno universo (punti percentuali)")
    fig.savefig(config.FIGURE / "fig2_eccesso_annuo.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    cap = m["capitale"]["valore"]
    ax.hist(s["finale"] * cap, bins=50, color=GRIGIO, alpha=0.85)
    ax.axvline(m["d10_finale"]["valore"], color=ARANCIO, lw=2.5, label="Dogs")
    ax.axvline(m["uni_finale"]["valore"], color=BLU, lw=2.5, label="Universo")
    ax.axvline(m["spy_finale"]["valore"], color="#222", lw=2.5, ls="--", label="SPY")
    ax.set_xlabel(f"Valore finale di {cap:.0f} dollari con dieci titoli a caso ogni anno")
    ax.set_ylabel("Scimmie")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_scimmie.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
