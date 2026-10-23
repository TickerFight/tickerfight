"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_caso_studio.png        il titolo del caso di studio: prezzo, medie e periodi in cash
  fig2_caratteristiche.png    differenza regola meno buy & hold contro ciascuna caratteristica, un punto per titolo
  fig3_correlazioni.png       correlazioni di rango con intervallo di confidenza, sviluppo contro validazione
  fig4_terzili.png            quota di titoli su cui vince la regola, terzo con indice basso contro terzo con indice alto
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})


def euro(x, _=None):
    return f"{x:,.0f}".replace(",", ".") + " €"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    R = config.RISULTATI
    tab = pd.read_csv(R / "caratteristiche.csv")
    cor = pd.read_csv(R / "correlazioni.csv")
    terz = pd.read_csv(R / "terzili.csv")
    caso = pd.read_csv(R / "caso_studio.csv", parse_dates=["data"])

    # --- Figura 1: caso di studio -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.8))
    fuori = ~caso["regola_in_posizione"].to_numpy(bool)
    ax.fill_between(caso["data"], 0, 1, where=fuori, transform=ax.get_xaxis_transform(), color=GRIGIO, alpha=0.18,
                    lw=0, label="regola in cash")
    ax.plot(caso["data"], caso["chiusura_usd"], color="#444", lw=1.0, label=f"{config.CASO_STUDIO}, chiusura")
    ax.plot(caso["data"], caso["sma_veloce"], color=BLU, lw=1.8, label=f"media {config.SMA_VELOCE} giorni")
    ax.plot(caso["data"], caso["sma_lenta"], color=ARANCIO, lw=1.8, ls="--", label=f"media {config.SMA_LENTA} giorni")
    ax.set_ylabel("dollari")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), columnspacing=1.2, handlelength=1.6)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_caso_studio.png")
    plt.close(fig)

    # --- Figura 2: caratteristiche contro differenza ----------------------------------------------------
    etichette = {"vol": "volatilità dell'anno precedente", "ret": "rendimento dei 12 mesi precedenti",
                 "inc": "incroci tra le medie nei 200 giorni precedenti"}
    fig, assi = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, f in zip(assi, ("vol", "ret", "inc")):
        for camp, col, mk, nome in (("sv", GRIGIO, "s", "sviluppo"), ("va", BLU, "o", "validazione")):
            t = tab[tab.campione == camp]
            x = t[f].to_numpy() * (100 if f != "inc" else 1)
            if f == "inc":
                x = x + np.random.default_rng(1).uniform(-0.15, 0.15, len(x))     # solo per vedere i punti sovrapposti
            ax.scatter(x, t["differenza"], s=32, color=col, marker=mk, alpha=0.75, label=nome)
        ax.axhline(0, color="#333", lw=1)
        va = cor[(cor.campione == "va") & (cor.caratteristica == f)].iloc[0]
        ax.set_title(f"validazione: correlazione {va['rho']:+.2f}".replace(".", ","), fontsize=12)
        ax.set_xlabel(etichette[f] + (" (%)" if f != "inc" else ""))
        ax.yaxis.set_major_formatter(euro)
    assi[0].set_ylabel("regola meno buy & hold, netto")
    assi[0].legend(loc="lower left", bbox_to_anchor=(0, 1.12), ncol=2)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_caratteristiche.png")
    plt.close(fig)

    # --- Figura 3: correlazioni con intervallo di confidenza ----------------------------------------------
    nomi = {"vol": "volatilità\n(atteso +)", "ret": "rendimento passato\n(atteso −)", "inc": "incroci\n(atteso −)",
            "comp": "indice composito\n(atteso +)"}
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ordine = ["vol", "ret", "inc", "comp"]
    y0 = np.arange(len(ordine))[::-1]
    for off, camp, col, mk, nome in ((0.16, "sv", GRIGIO, "s", "sviluppo (titoli già visti)"), (-0.16, "va", BLU, "o", "validazione (titoli nuovi)")):
        for yy, f in zip(y0, ordine):
            r = cor[(cor.campione == camp) & (cor.caratteristica == f)].iloc[0]
            ax.errorbar(r["rho"], yy + off, xerr=[[r["rho"] - r["ic_inf"]], [r["ic_sup"] - r["rho"]]], fmt=mk, color=col,
                        ms=8, capsize=4, lw=1.6, label=nome if f == "vol" else None)
    ax.axvline(0, color="#333", lw=1)
    ax.set_yticks(y0, [nomi[f] for f in ordine])
    ax.set_xlabel("correlazione di rango con la differenza regola meno buy & hold (barre: intervallo di confidenza al 95%)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_correlazioni.png")
    plt.close(fig)

    # --- Figura 4: terzili ----------------------------------------------------------------------------------
    tr = pd.read_csv(R / "terzili_rendimento.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    camp_nomi = [("sv", "sviluppo"), ("va", "validazione")]
    x = np.arange(len(camp_nomi))
    larg = 0.34
    for k, (g, col, hatch, nome) in enumerate((("indice basso", ARANCIO, "//", "terzo con l'indice più basso"),
                                              ("indice alto", BLU, "", "terzo con l'indice più alto"))):
        val = [float(terz[(terz.campione == c) & (terz.gruppo == g)]["quota_vince"].iloc[0]) * 100 for c, _ in camp_nomi]
        barre = ax1.bar(x + (k - 0.5) * larg, val, larg, color=col, alpha=0.8, hatch=hatch, edgecolor="white", label=nome)
        for b, v in zip(barre, val):
            ax1.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.0f}%", ha="center", fontsize=11)
    ax1.set_xticks(x, [n for _, n in camp_nomi])
    ax1.set_title("indice composito (volatilità, rendimento passato, incroci)", fontsize=12)
    ax1.legend(loc="upper left", fontsize=10)
    larg = 0.26
    for k, (g, col, hatch, nome) in enumerate((("basso", BLU, "", "rendimento passato basso"),
                                              ("medio", GRIGIO, "", "medio"),
                                              ("alto", ARANCIO, "//", "rendimento passato alto"))):
        val = [float(tr[(tr.campione == c) & (tr.gruppo == g)]["quota_vince"].iloc[0]) * 100 for c, _ in camp_nomi]
        barre = ax2.bar(x + (k - 1) * larg, val, larg, color=col, alpha=0.8, hatch=hatch, edgecolor="white", label=nome)
        for b, v in zip(barre, val):
            ax2.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.0f}%", ha="center", fontsize=11)
    ax2.set_xticks(x, [n for _, n in camp_nomi])
    ax2.set_title("solo rendimento dei 12 mesi precedenti (lettura descrittiva)", fontsize=12)
    ax2.legend(loc="upper left", fontsize=10)
    ax1.set_ylabel("titoli su cui la regola batte il buy & hold")
    ax1.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    for a in (ax1, ax2):
        a.grid(axis="x", visible=False)
        a.set_ylim(0, 50)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_terzili.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
