"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_segnali.png     un tratto di storia: chiusura, media a 200 sedute, uscite e rientri del filtro semplice
  fig2_durate.png      quante uscite durano poco e quante molto, e quante finiscono in whipsaw
  fig3_rendimenti.png  rendimento annuo composto: buy & hold, filtro semplice e con banda, con e senza costi
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
    json.loads((R / "metriche.json").read_text(encoding="utf-8"))

    # 1. segnali
    E = pd.read_csv(R / "esempio.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(E["data"], E["chiusura"], color=GRIGIO, lw=1.3, label="S&P 500")
    ax.plot(E["data"], E["media"], color=BLU, lw=1.6, label="Media a 200 sedute")
    d = E["pos"].diff().fillna(0)
    u, r = E[d < 0], E[d > 0]
    ax.scatter(u["data"], u["chiusura"], marker="v", s=80, color=ARANCIO, zorder=5, label="Uscita")
    ax.scatter(r["data"], r["chiusura"], marker="^", s=80, color=VERDE, zorder=5, label="Rientro")
    ax.set_ylabel("Livello dell'indice")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_segnali.png")
    plt.close(fig)

    # 2. durate
    U = pd.read_csv(R / "uscite.csv")
    bordi = [0, 5, 10, 20, 60, 120, 10 ** 6]
    nomi = ["1-5", "6-10", "11-20", "21-60", "61-120", "oltre 120"]
    U["classe"] = pd.cut(U["sedute"], bordi, labels=nomi)
    tot = U.groupby("classe", observed=False).size()
    whip = U[U["whipsaw"]].groupby("classe", observed=False).size()
    x = np.arange(len(nomi))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x, tot.values - whip.values, color=VERDE, label="Rientro più in basso (uscita utile)")
    ax.bar(x, whip.values, bottom=tot.values - whip.values, color=ARANCIO, label="Rientro a prezzo uguale o più alto (whipsaw)")
    ax.set_xticks(x)
    ax.set_xticklabels(nomi)
    ax.set_xlabel("Durata dell'uscita (sedute)")
    ax.set_ylabel("Numero di uscite")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_durate.png")
    plt.close(fig)

    # 3. rendimenti
    Rn = pd.read_csv(R / "rendimenti.csv").set_index("variante")["cagr"] * 100
    etich = ["Buy & hold", "Filtro\nsenza costi", "Filtro\ncon costi", "Filtro con banda\nsenza costi", "Filtro con banda\ncon costi"]
    colori = [GRIGIO, BLU, BLU, VERDE, VERDE]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(np.arange(5), Rn.values, color=colori, alpha=0.9)
    for i, v in enumerate(Rn.values):
        ax.text(i, v + 0.05, f"{v:.2f}".replace(".", ",") + "%", ha="center", fontsize=11)
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(etich, fontsize=10)
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.set_ylim(0, Rn.max() * 1.15)
    fig.savefig(config.FIGURE / "fig3_rendimenti.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
