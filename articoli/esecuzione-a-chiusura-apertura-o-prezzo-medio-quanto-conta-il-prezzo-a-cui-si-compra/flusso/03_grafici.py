"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_regola_veloce_quattro_prezzi.png   valore di 1 dollaro della regola veloce con i quattro prezzi, e buy & hold
  fig2_cagr_per_prezzo.png                CAGR delle due regole per prezzo di esecuzione, contro il buy & hold
  fig3_costi.png                          CAGR della regola veloce (apertura) al variare del costo per operazione
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f3f"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    cv = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    co = pd.read_csv(R / "costi.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    for col, nome, colore in (("bh", "Buy & hold", GRIGIO), ("s20_st", "Stessa chiusura", ARANCIO), ("s20_ap", "Apertura del giorno dopo", BLU),
                              ("s20_pm", "Prezzo medio del giorno dopo", VERDE), ("s20_cd", "Chiusura del giorno dopo", "#7a3b8f")):
        ax.plot(cv["data"], cv[col], lw=2, color=colore, label=nome)
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_regola_veloce_quattro_prezzi.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    nomi = ["Stessa\nchiusura", "Apertura\ndopo", "Prezzo medio\ndopo", "Chiusura\ndopo"]
    xs = np.arange(4)
    for off, tag, lab, col in ((-0.2, "s200", "Media a 200 sedute", BLU), (0.2, "s20", "Media a 20 sedute", ARANCIO)):
        ax.bar(xs + off, [m[f"{tag}_{s}_cagr"]["valore"] * 100 for s in ("st", "ap", "pm", "cd")], 0.4, color=col, label=lab)
    ax.axhline(m["bh_cagr"]["valore"] * 100, color="#222", lw=2, ls="--", label="Buy & hold")
    ax.set_xticks(xs)
    ax.set_xticklabels(nomi)
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_cagr_per_prezzo.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(co["costo"] * 100, co["cagr"] * 100, "o-", color=ARANCIO, lw=2, label="Media a 20 sedute, apertura del giorno dopo")
    ax.axhline(m["bh_cagr"]["valore"] * 100, color="#222", lw=2, ls="--", label="Buy & hold")
    ax.set_xlabel("Costo per ogni cambio di posizione (%)")
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_costi.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
