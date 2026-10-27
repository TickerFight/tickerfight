"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_valore_promesso.png    500 euro: il valore reale del buy & hold e quello "promesso" dalla media dei rendimenti semplici
  fig2_decenni.png            per ogni decennio, divario contro mezza varianza
  fig3_giorno_per_giorno.png  differenza tra rendimento semplice e logaritmico, seduta per seduta
  fig4_frequenze.png          il divario calcolato con dati giornalieri, mensili e annuali
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


def virgola(x: float, dec: int = 1) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    v = lambda k: V[k]["valore"]

    # --- Figura 1: valore reale e valore promesso -------------------------------------------------------------
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(c["data"], c["valore_promesso"], color=ARANCIO, lw=2.0, ls="--", label="promesso dalla media dei rendimenti semplici")
    ax.plot(c["data"], c["valore_reale"], color=BLU, lw=2.2, label="reale (buy & hold)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
    ax.set_ylabel(f"valore di {config.CAPITALE:.0f} euro, scala logaritmica")
    ax.legend(loc="upper left", fontsize=11)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_valore_promesso.png")
    plt.close(fig)

    # --- Figura 2: decenni -----------------------------------------------------------------------------------
    d = pd.read_csv(R / "decenni.csv")
    fig, ax = plt.subplots(figsize=(8.6, 6))
    lim = max(d["gap"].max(), d["mezza_varianza"].max()) * 100 * 1.12
    ax.plot([0, lim], [0, lim], color=GRIGIO, lw=1.6, ls="--", label="divario = mezza varianza")
    ax.scatter(d["mezza_varianza"] * 100, d["gap"] * 100, color=BLU, s=70, zorder=3, label="decenni")
    for _, riga in d.iterrows():
        ax.annotate(riga["etichetta"], (riga["mezza_varianza"] * 100, riga["gap"] * 100), textcoords="offset points",
                    xytext=(6, -12), fontsize=9)
    ax.set_xlim(0, lim)
    ax.set_ylim(min(0.0, float(d["gap"].min()) * 100 * 1.4), lim)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("mezza varianza, punti percentuali l'anno")
    ax.set_ylabel("media semplice meno rendimento composto, punti l'anno")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_decenni.png")
    plt.close(fig)

    # --- Figura 3: giorno per giorno ---------------------------------------------------------------------------
    g = pd.read_csv(R / "giorni.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.scatter(g["semplice"] * 100, (g["semplice"] - g["logaritmico"]) * 100, s=6, color=BLU, alpha=0.5)
    x = np.linspace(g["semplice"].min(), g["semplice"].max(), 300)
    ax.plot(x * 100, (x - np.log1p(x)) * 100, color=ARANCIO, lw=1.6, ls="--")
    ax.axhline(config.SOGLIA_GIORNO * 100, color=GRIGIO, lw=1.2, ls=":")
    ax.set_xlabel("rendimento semplice della seduta, %")
    ax.set_ylabel("semplice meno logaritmico, punti percentuali")
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_giorno_per_giorno.png")
    plt.close(fig)

    # --- Figura 4: frequenze ---------------------------------------------------------------------------------------
    f = pd.read_csv(R / "frequenze.csv")
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    xs = np.arange(len(f))
    ax.bar(xs, f["gap"] * 100, color=BLU, width=0.55, label="media semplice meno rendimento composto")
    ax.scatter(xs, f["mezza_varianza"] * 100, color=ARANCIO, s=90, zorder=3, marker="D", label="mezza varianza")
    for k, y in enumerate(f["gap"] * 100):
        ax.text(k, y + 0.05, virgola(y, 2), ha="center", fontsize=11)
    ax.set_xticks(xs, [s for s in f["frequenza"]])
    ax.set_ylabel("punti percentuali l'anno")
    ax.set_ylim(0, f["gap"].max() * 100 * 1.6)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_frequenze.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
