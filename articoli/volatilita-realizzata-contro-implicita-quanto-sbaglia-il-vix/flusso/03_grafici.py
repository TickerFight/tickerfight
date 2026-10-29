"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_vix_e_realizzata.png  VIX e volatilità realizzata successiva, un punto al mese (campione non sovrapposto)
  fig2_dispersione.png       volatilità realizzata successiva contro VIX, con la retta di regressione
  fig3_premio_per_fascia.png premio medio per fascia del VIX
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
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    M = pd.read_csv(R / "mesi.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(M["data"], M["vix"], color=BLU, lw=1.8, label="VIX (volatilità attesa)")
    ax.plot(M["data"], M["rv_successiva"], color=ARANCIO, lw=1.4, label="Volatilità realizzata nel mese successivo")
    ax.set_ylabel("Punti di volatilità annua")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_vix_e_realizzata.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    ax.scatter(M["vix"], M["rv_successiva"], s=12, color=BLU, alpha=0.5)
    lim = max(M["vix"].max(), M["rv_successiva"].max()) * 1.03
    ax.plot([0, lim], [0, lim], color=GRIGIO, ls="--", lw=1.2, label="VIX uguale alla volatilità realizzata")
    xs = np.array([0, lim])
    ax.plot(xs, V["reg_a"]["valore"] + V["reg_b"]["valore"] * xs, color=ARANCIO, lw=2, label="Retta di regressione")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("VIX (punti)")
    ax.set_ylabel("Volatilità realizzata nel mese successivo (punti)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_dispersione.png")
    plt.close(fig)

    F = pd.read_csv(R / "fasce.csv")
    etichette = []
    for _, r in F.iterrows():
        etichette.append(f"VIX sotto {r['a']:.0f}" if r["da"] == 0 else (f"VIX sopra {r['da']:.0f}" if r["a"] > 500 else f"VIX {r['da']:.0f}-{r['a']:.0f}"))
    fig, ax = plt.subplots(figsize=(10, 5))
    colori = [VERDE if p >= 0 else ARANCIO for p in F["premio"]]
    ax.bar(np.arange(len(F)), F["premio"], color=colori, alpha=0.9)
    ax.axhline(0, color="#333", lw=1)
    ax.set_xticks(np.arange(len(F)))
    ax.set_xticklabels(etichette)
    ax.set_ylabel("Premio medio: VIX meno volatilità realizzata (punti)")
    fig.savefig(config.FIGURE / "fig3_premio_per_fascia.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
