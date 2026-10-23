"""Passo 3 - Grafici dell'articolo bonus. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_prezzo_e_medie.png        prezzo di Apple, le due medie, i periodi in cash e le operazioni
  fig2_valore_portafoglio.png    valore in euro dei 500 euro con la regola e con il buy & hold
  fig3_dal_lordo_al_netto.png    valore finale senza costi, con le commissioni, con commissioni e tasse
  fig4_finestre_mobili.png       differenza finale (regola meno buy & hold) per ogni data di partenza
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE, ROSSO = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f3f", "#b3261e"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})


def euro(x, _=None):
    return f"{x:,.0f}".replace(",", ".") + " €"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    R = config.RISULTATI
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    ops = pd.read_csv(R / "operazioni_regola.csv", parse_dates=["data"])
    sc = pd.read_csv(R / "scenari.csv")
    fm = pd.read_csv(R / "finestre_mobili.csv", parse_dates=["data_inizio", "data_fine"])
    P = config.MODO_PRINCIPALE

    # --- Figura 1: prezzo, medie, periodi in cash, operazioni ---------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.8))
    fuori = ~c["regola_in_posizione"].to_numpy(bool)
    ax.fill_between(c["data"], 0, 1, where=fuori, transform=ax.get_xaxis_transform(), color=GRIGIO, alpha=0.18,
                    lw=0, label="regola in cash")
    ax.plot(c["data"], c["chiusura_usd"], color="#444", lw=1.0, label="Apple, chiusura")
    ax.plot(c["data"], c["sma_veloce"], color=BLU, lw=1.8, label=f"media {config.SMA_VELOCE} giorni")
    ax.plot(c["data"], c["sma_lenta"], color=ARANCIO, lw=1.8, ls="--", label=f"media {config.SMA_LENTA} giorni")
    acq = ops[(ops["lato"] == "acquisto")]
    ven = ops[(ops["lato"] == "vendita") & (ops["motivo"] == "segnale")]
    ax.scatter(acq["data"], acq["prezzo_usd"], marker="^", s=90, color=VERDE, zorder=5, label="acquisto")
    ax.scatter(ven["data"], ven["prezzo_usd"], marker="v", s=90, color=ROSSO, zorder=5, label="vendita")
    ax.set_ylabel("dollari")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(ncol=5, loc="lower left", bbox_to_anchor=(0, 1.0), columnspacing=1.2, handlelength=1.6)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_prezzo_e_medie.png")
    plt.close(fig)

    # --- Figura 2: valore del portafoglio ----------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axhline(config.CAPITALE, color=GRIGIO, lw=1, ls=":")
    ax.plot(c["data"], c["valore_bh_netto"], color=ARANCIO, lw=2.0, ls="--", label="buy & hold")
    ax.plot(c["data"], c["valore_regola_netto"], color=BLU, lw=2.2, label=f"regola {config.SMA_VELOCE}/{config.SMA_LENTA}")
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylabel("valore del portafoglio")
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_valore_portafoglio.png")
    plt.close(fig)

    # --- Figura 3: dal lordo al netto -------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.5))
    passi = [("lordo", "senza costi\nné tasse"), ("comm", "con le\ncommissioni"), ("netto", "con commissioni\ne tasse")]
    x = np.arange(len(passi))
    larg = 0.36
    for k, (nome, colore, etichetta, hatch) in enumerate([("mm", BLU, f"regola {config.SMA_VELOCE}/{config.SMA_LENTA}", ""),
                                                          ("bh", ARANCIO, "buy & hold", "//")]):
        val = [float(sc[(sc.esecuzione == P) & (sc.costi == p) & (sc.strategia == nome)]["valore_finale_eur"].iloc[0]) for p, _ in passi]
        barre = ax.bar(x + (k - 0.5) * larg, val, larg, color=colore, hatch=hatch, edgecolor="white", label=etichetta)
        for b, v in zip(barre, val):
            ax.text(b.get_x() + b.get_width() / 2, v + 8, f"{v:,.0f}".replace(",", "."), ha="center", fontsize=11)
    ax.axhline(config.CAPITALE, color=GRIGIO, lw=1, ls=":")
    ax.set_xticks(x, [t for _, t in passi])
    ax.yaxis.set_major_formatter(euro)
    ax.set_ylabel("valore finale dei 500 €")
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_dal_lordo_al_netto.png")
    plt.close(fig)

    # --- Figura 4: finestre mobili ----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    d = fm["differenza"].to_numpy()
    ax.fill_between(fm["data_inizio"], 0, d, where=d >= 0, color=BLU, alpha=0.35, lw=0, interpolate=True,
                    label="la regola chiude sopra")
    ax.fill_between(fm["data_inizio"], 0, d, where=d < 0, color=ARANCIO, alpha=0.35, lw=0, interpolate=True,
                    hatch="//", label="il buy & hold chiude sopra")
    ax.plot(fm["data_inizio"], d, color="#333", lw=1.2)
    ax.axhline(0, color="#333", lw=1)
    ultimo = fm.iloc[-1]
    ax.scatter([ultimo["data_inizio"]], [ultimo["differenza"]], s=70, color="#333", zorder=5)
    ax.annotate("partenza a ottobre 2021", (ultimo["data_inizio"], ultimo["differenza"]), textcoords="offset points",
                xytext=(-10, -60), ha="right", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#999"), arrowprops=dict(arrowstyle="-", color="#999"))
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel(f"data di partenza (finestre di {config.ANNI_TEST} anni)")
    ax.set_ylabel("regola meno buy & hold, netto")
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_finestre_mobili.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
