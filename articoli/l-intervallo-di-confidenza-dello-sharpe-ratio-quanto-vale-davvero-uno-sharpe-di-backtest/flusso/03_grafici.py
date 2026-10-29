"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_intervalli_per_finestra.png   Sharpe e intervallo (bootstrap a blocchi) per finestra
  fig2_ampiezza_e_anni.png           ampiezza dell'intervallo (formula) in funzione degli anni di dati
  fig3_copertura.png                 quota di finestre il cui intervallo di Lo contiene lo Sharpe delle altre sedute
"""
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
    w = pd.read_csv(R / "intervalli.csv")
    cop = pd.read_csv(R / "copertura.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    y = np.arange(len(w))[::-1]
    nomi = [f"ultimi {int(round(a))} anni" if f != "tot" else f"tutto ({a:.0f} anni)" for f, a in zip(w["finestra"], w["anni"])]
    ax.errorbar(w["sharpe"], y, xerr=[w["sharpe"] - w["bb_lo"], w["bb_hi"] - w["sharpe"]], fmt="o", color=ARANCIO, capsize=5, lw=2)
    ax.axvline(0, color="#555", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(nomi)
    ax.set_xlabel("Sharpe annualizzato e intervallo al 95% (bootstrap a blocchi)")
    fig.savefig(config.FIGURE / "fig1_intervalli_per_finestra.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    amp = w["lo_hi"] - w["lo_lo"]
    ax.plot(w["anni"], amp, "o", color=ARANCIO, ms=9, label="Ampiezza osservata")
    s = np.linspace(w["anni"].min(), w["anni"].max(), 100)
    ax.plot(s, amp.iloc[-1] * np.sqrt(w["anni"].iloc[-1] / s), color=GRIGIO, lw=2, label="Andamento 1 / radice degli anni")
    ax.set_xlabel("Anni di dati")
    ax.set_ylabel("Ampiezza dell'intervallo di Lo al 95% (Sharpe)")
    ax.legend()
    fig.savefig(config.FIGURE / "fig2_ampiezza_e_anni.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    xs = np.arange(len(cop))
    ax.bar(xs, cop["copertura"] * 100, 0.5, color=BLU, label="Copertura onesta (formula di Lo)")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{a} anni" for a in cop["anni"]])
    ax.axhline(95, color=ARANCIO, lw=2, label="Livello nominale (95%)")
    ax.set_ylim(0, 112)
    ax.set_ylabel("Finestre il cui intervallo contiene lo Sharpe delle altre sedute (%)")
    ax.legend(loc="lower right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_copertura.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
