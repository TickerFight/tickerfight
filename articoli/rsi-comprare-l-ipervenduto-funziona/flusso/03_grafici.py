"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_rendimenti_dopo_eventi.png   rendimento medio a dieci sedute: dopo RSI<30, giorno qualunque, dopo RSI>70
  fig2_curve.png                    crescita di 1 dollaro: regola e buy & hold
  fig3_spostamenti.png              Sharpe degli spostamenti circolari e della regola
"""
import json

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
    v = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]

    fig, ax = plt.subplots(figsize=(9, 5))
    nomi = ["Dopo RSI sotto 30", "Giorno qualunque", "Dopo RSI sopra 70"]
    val = [v["m10_sotto"]["valore"] * 100, v["m10_tutti"]["valore"] * 100, v["m10_sopra"]["valore"] * 100]
    ax.bar(nomi, val, color=[BLU, GRIGIO, ARANCIO])
    ax.set_ylabel("Rendimento medio nelle dieci sedute successive, %")
    fig.savefig(config.FIGURE / "fig1_rendimenti_dopo_eventi.png")
    plt.close(fig)

    cv = pd.read_csv(R / "curve.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(pd.to_datetime(cv.index), cv["buy_hold"], color=GRIGIO, lw=2, label="Buy & hold")
    ax.plot(pd.to_datetime(cv.index), cv["regola"], color=BLU, lw=2, label="Regola RSI")
    ax.set_yscale("log")
    ax.set_ylabel("Crescita di 1 dollaro (scala logaritmica)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_curve.png")
    plt.close(fig)

    sp = pd.read_csv(R / "spostamenti.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(sp["sharpe"], bins=50, color=GRIGIO)
    ax.axvline(v["reg_sr"]["valore"], color=ARANCIO, lw=3, label="Regola RSI")
    ax.set_xlabel("Sharpe della stessa posizione spostata a caso nel tempo")
    ax.set_ylabel("Spostamenti")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_spostamenti.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
