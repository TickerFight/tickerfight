"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_bic_per_ordine.png      BIC di ogni ordine (p, q) rispetto al migliore, sull'intero periodo
  fig2_errore_cumulato.png     differenza cumulata degli errori quadratici (media storica meno ARIMA), fuori campione
  fig3_bootstrap_r2.png        distribuzione bootstrap dell'R quadro fuori campione
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
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    b = pd.read_csv(R / "bic_ordini.csv")
    pr = pd.read_csv(R / "previsioni.csv")
    bo = pd.read_csv(R / "bootstrap_r2.csv")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    etich = [f"({p},{q})" for p, q in zip(b["p"], b["q"])]
    col = [ARANCIO if d == 0 else BLU for d in b["delta_bic"]]
    ax.bar(etich, b["delta_bic"], color=col)
    ax.set_xlabel("Ordine del modello (p, q)")
    ax.set_ylabel("BIC meno il BIC del migliore (più basso è meglio)")
    fig.savefig(config.FIGURE / "fig1_bic_per_ordine.png")
    plt.close(fig)

    e_m = (pr["reale"] - pr["arima"]) ** 2
    e_b = (pr["reale"] - pr["media_storica"]) ** 2
    cum = (e_b - e_m).cumsum() * 1e4
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(pd.PeriodIndex(pr["mese"], freq="M").to_timestamp(), cum, color=ARANCIO, lw=2)
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Errore quadratico cumulato: media storica meno ARIMA (sopra lo zero vince ARIMA)")
    fig.savefig(config.FIGURE / "fig2_errore_cumulato.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(bo["r2_oos"] * 100, bins=50, color=GRIGIO, alpha=0.85)
    ax.axvline(0, color="#555", lw=1.5)
    ax.axvline(m["r2_oos"]["valore"] * 100, color=ARANCIO, lw=2.5, label="Valore osservato")
    ax.set_xlabel("R quadro fuori campione (%) nei ricampionamenti")
    ax.set_ylabel("Ricampionamenti")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_bootstrap_r2.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
