"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_crescita.png         crescita di 1 dollaro: azioni, 60/40, obbligazioni (scala logaritmica)
  fig2_correlazione.png     tasso a 10 anni e correlazione mobile a 36 mesi tra azioni e obbligazioni
  fig3_tassi_e_rendimento.png  tasso di partenza e rendimento annuo del 60/40 nei 10 anni dopo
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
    m = pd.read_csv(R / "mensili.csv")
    t = pd.PeriodIndex(m["mese"], freq="M").to_timestamp(how="end")
    fw = pd.read_csv(R / "finestre_10anni.csv")

    # Figura 1
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    for col, c, lab, lw in (("azioni", BLU, "100% azioni", 2.2), ("mix", ARANCIO, "60/40", 2.8), ("obbligazioni", GRIGIO, "100% obbligazioni a 10 anni", 2.0)):
        ax.plot(t, (1 + m[col]).cumprod(), color=c, lw=lw, label=lab)
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_crescita.png")
    plt.close(fig)

    # Figura 2
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.4, 6.2), sharex=True, gridspec_kw={"height_ratios": [1, 1.3]})
    a1.plot(t, m["tasso10_prec"], color=GRIGIO, lw=2)
    a1.axhline(config.SOGLIA_ALTI, color=GRIGIO, ls="--", lw=1)
    a1.axhline(config.SOGLIA_BASSI, color=GRIGIO, ls="--", lw=1)
    a1.set_ylabel("Rendimento a 10 anni (%)")
    rc = m["azioni"].rolling(36).corr(m["obbligazioni"])
    a2.plot(t, rc, color=BLU, lw=2.4)
    a2.axhline(0, color="black", lw=1)
    a2.fill_between(t, 0, rc, where=rc < 0, color=ARANCIO, alpha=0.35, lw=0)
    a2.set_ylabel("Correlazione azioni/obbligazioni\n(finestra mobile di 36 mesi)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_correlazione.png")
    plt.close(fig)

    # Figura 3
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.scatter(fw["tasso10"], fw["mix"] * 100, s=14, color=ARANCIO, alpha=0.7, label="60/40")
    ax.scatter(fw["tasso10"], fw["ob"] * 100, s=10, color=GRIGIO, alpha=0.5, label="100% obbligazioni a 10 anni")
    ax.axvline(config.SOGLIA_BASSI, color="black", ls="--", lw=1)
    ax.axvline(config.SOGLIA_ALTI, color="black", ls="--", lw=1)
    ax.set_xlabel("Rendimento a 10 anni alla partenza (%)")
    ax.set_ylabel("Rendimento annuo nei 10 anni dopo (%)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig3_tassi_e_rendimento.png")
    plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
