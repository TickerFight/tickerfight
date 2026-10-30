"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_medie_per_orizzonte.png   rendimento medio dopo l'evento e di un giorno qualunque, a 1, 3 e 12 mesi
  fig2_eventi_12m.png            rendimento a dodici mesi di ogni evento
"""
import json

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
    v = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    fig, ax = plt.subplots(figsize=(10, 5))
    xs = np.arange(3)
    ax.bar(xs - 0.2, [v[f"m_{n}"]["valore"] * 100 for n in ("1m", "3m", "12m")], 0.4, color=BLU, label="Dopo un calo rapido del 10%")
    ax.bar(xs + 0.2, [v[f"t_{n}"]["valore"] * 100 for n in ("1m", "3m", "12m")], 0.4, color=GRIGIO, label="Un giorno qualunque")
    ax.set_xticks(xs)
    ax.set_xticklabels(["1 mese", "3 mesi", "12 mesi"])
    ax.set_ylabel("Rendimento medio, %")
    ax.legend()
    fig.savefig(config.FIGURE / "fig1_medie_per_orizzonte.png")
    plt.close(fig)

    e = pd.read_csv(R / "eventi.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(e["data"].dt.year.astype(str) + "-" + e["data"].dt.month.astype(str).str.zfill(2), e["r12"] * 100,
           color=[BLU if x > 0 else ARANCIO for x in e["r12"]])
    ax.axhline(0, color="#555", lw=1)
    ax.tick_params(axis="x", rotation=90, labelsize=9)
    ax.set_ylabel("Rendimento nei dodici mesi dopo l'evento, %")
    fig.savefig(config.FIGURE / "fig2_eventi_12m.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
