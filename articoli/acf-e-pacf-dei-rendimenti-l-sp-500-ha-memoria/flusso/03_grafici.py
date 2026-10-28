"""Passo 3 - Grafici dell'articolo. Legge SOLO dati/ e risultati/ e salva i PNG in figure/.

  fig1_acf_pacf_rendimenti.png   ACF e PACF dei rendimenti, ritardi 1-20, con la banda al 99%
  fig2_memoria_dei_movimenti.png ACF dei rendimenti e dei valori assoluti fino al ritardo 100
  fig3_acf_per_finestra.png      ACF al ritardo 1 dei rendimenti in ogni finestra di dieci anni
  fig4_rimescolamenti.png        ACF al ritardo 1 dei rendimenti rimescolati contro quella reale
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
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
    banda = m["banda99"]["valore"]
    T = pd.read_csv(R / "acf_intero.csv")
    Lg = pd.read_csv(R / "acf_lunga.csv")
    W = pd.read_csv(R / "acf_finestre.csv", parse_dates=["inizio", "fine"])
    P = pd.read_csv(R / "permutazioni.csv")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, col, tit in ((a1, "acf_rend", "Autocorrelazione (ACF)"), (a2, "pacf_rend", "Autocorrelazione parziale (PACF)")):
        ax.bar(T["ritardo"], T[col], color=BLU, width=0.6)
        ax.axhspan(-banda, banda, color=GRIGIO, alpha=0.25, lw=0)
        ax.axhline(0, color="#555", lw=1)
        ax.set_ylabel(tit)
    a2.set_xlabel("Ritardo (sedute)")
    a2.set_xticks(range(1, config.NLAG + 1, 1))
    fig.savefig(config.FIGURE / "fig1_acf_pacf_rendimenti.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(Lg["ritardo"], Lg["acf_abs"], color=ARANCIO, lw=1.8, label="Valori assoluti dei rendimenti")
    ax.plot(Lg["ritardo"], Lg["acf_rend"], color=BLU, lw=1.8, label="Rendimenti")
    ax.axhspan(-banda, banda, color=GRIGIO, alpha=0.25, lw=0)
    ax.axhline(0, color="#555", lw=1)
    ax.set_xlabel("Ritardo (sedute)")
    ax.set_ylabel("Autocorrelazione")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_memoria_dei_movimenti.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(W))
    ax.bar(x, W["acf1_rend"], color=[BLU if v >= 0 else ARANCIO for v in W["acf1_rend"]], width=0.7)
    ax.axhline(0, color="#555", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d.year}" for d in W["inizio"]], rotation=45, ha="right")
    ax.set_ylabel("ACF al ritardo 1 dei rendimenti")
    ax.set_xlabel("Inizio della finestra di dieci anni")
    fig.savefig(config.FIGURE / "fig3_acf_per_finestra.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(P["acf1_rend"], bins=40, color=GRIGIO, alpha=0.8)
    ax.axvline(m["acf1"]["valore"], color=ARANCIO, lw=2.5, label="Dati reali")
    ax.set_xlabel("ACF al ritardo 1 dei rendimenti rimescolati")
    ax.set_ylabel("Rimescolamenti")
    ax.legend()
    fig.savefig(config.FIGURE / "fig4_rimescolamenti.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    import json
    main()
