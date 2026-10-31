"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_crescita.png     crescita di 1 dollaro: Portafoglio Permanente, azioni, 60/40 (scala logaritmica)
  fig2_anni.png         rendimento di ogni anno solare: Portafoglio Permanente contro azioni
  fig3_scimmie.png      Sharpe del PP e delle azioni contro la distribuzione delle scimmie
"""
import numpy as np
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
    m = pd.read_csv(R / "mensili.csv")
    t = pd.PeriodIndex(m["mese"], freq="M").to_timestamp(how="end")

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for col, c, lab, lw in (("azioni", BLU, "100% azioni", 2.2), ("pp", ARANCIO, "Portafoglio Permanente", 2.8), ("m6040", GRIGIO, "60/40", 2.0)):
        ax.plot(t, (1 + m[col]).cumprod(), color=c, lw=lw, label=lab)
    ax.set_yscale("log")
    ax.set_yticks([0.6, 1, 2, 4, 6])
    ax.set_yticklabels(["0,6", "1", "2", "4", "6"])
    ax.minorticks_off()
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_crescita.png")
    plt.close(fig)

    a = pd.read_csv(R / "anni_solari.csv")
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    x = np.arange(len(a))
    ax.bar(x - 0.2, a["az"] * 100, 0.4, color=BLU, label="100% azioni")
    ax.bar(x + 0.2, a["pp"] * 100, 0.4, color=ARANCIO, label="Portafoglio Permanente")
    ax.axhline(0, color="black", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(a["anno"].astype(str), rotation=90, fontsize=9)
    ax.set_ylabel("Rendimento dell'anno solare (%)")
    ax.set_ylim(-42, 42)
    ax.legend(loc="upper center", ncol=2)
    fig.savefig(config.FIGURE / "fig2_anni.png")
    plt.close(fig)

    import json
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    s = pd.read_csv(R / "scimmie.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.hist(s["sharpe"], bins=40, color=GRIGIO, alpha=0.6, label="Scimmie (pesi casuali)")
    ax.axvline(V["pp_sharpe"]["valore"], color=ARANCIO, lw=3, ls="--", label="Portafoglio Permanente")
    ax.axvline(V["az_sharpe"]["valore"], color=BLU, lw=3, label="100% azioni")
    ax.set_xlabel("Sharpe ratio")
    ax.set_ylabel("Numero di portafogli")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig3_scimmie.png")
    plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
