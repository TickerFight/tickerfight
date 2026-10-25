"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_valore.png        valore di 1 dollaro nelle tre aree (scala logaritmica)
  fig2_finestre.png      rendimento annuo delle finestre mobili di cinque anni
  fig3_quote.png         quota di finestre vinte da ciascuna area, per lunghezza della finestra
  fig4_correlazione.png  correlazione a un anno mobile tra le tre coppie, con le due crisi
  fig5_scimmie.png       valore finale delle scimmie contro il buy & hold nelle tre aree
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
COL = {"USA": BLU, "Europa": GRIGIO, "Emergenti": ARANCIO}
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI
SL = {"USA": "usa", "Europa": "eur", "Emergenti": "em"}


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    v = lambda k: V[k]["valore"]

    # --- Figura 1 ------------------------------------------------------------------------------------------
    cur = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(9, 5))
    for a in ("USA", "Europa", "Emergenti"):
        ax.plot(cur["data"], cur[a], color=COL[a], lw=1.8 if a == "USA" else 1.4, ls="-" if a != "Europa" else "--", label=a)
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.set_title("Dove sarebbe finito 1 dollaro, dividendi reinvestiti", loc="left", fontsize=13)
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    # --- Figura 2 ------------------------------------------------------------------------------------------
    w = pd.read_csv(R / "finestre_5anni.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(9, 5))
    for a in ("USA", "Europa", "Emergenti"):
        ax.plot(w["data"], w[a] * 100, color=COL[a], lw=1.8 if a == "USA" else 1.4, ls="-" if a != "Europa" else "--", label=a)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Rendimento annuo su cinque anni (%)")
    ax.set_title("Chi è in testa cambia: rendimento annuo su finestre mobili di cinque anni", loc="left", fontsize=13)
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig2_finestre.png")
    plt.close(fig)

    # --- Figura 3 ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    fins = [f for f in config.FINESTRE_ANNI if f"w{f}_n" in V]
    x = np.arange(len(fins))
    for i, a in enumerate(("USA", "Europa", "Emergenti")):
        q = [v(f"w{f}_quota_{SL[a]}") * 100 for f in fins]
        ax.bar(x + (i - 1) * 0.26, q, 0.26, color=COL[a], label=a, hatch="//" if a == "USA" else None,
               edgecolor="white" if a == "USA" else COL[a])
        for xi, qi in zip(x + (i - 1) * 0.26, q):
            ax.text(xi, qi + 1, f"{qi:.0f}%", ha="center", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{f} anni" for f in fins])
    ax.set_ylabel("Quota di finestre vinte (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Quante volte ciascuna area è prima, per lunghezza della finestra", loc="left", fontsize=13)
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig3_quote.png")
    plt.close(fig)

    # --- Figura 4 ------------------------------------------------------------------------------------------
    vc = pd.read_csv(R / "vol_corr.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(vc["data"], vc["corr_ue"], color=BLU, lw=1.8, label="USA - Europa")
    ax.plot(vc["data"], vc["corr_um"], color=ARANCIO, lw=1.6, label="USA - emergenti")
    ax.plot(vc["data"], vc["corr_em"], color=GRIGIO, lw=1.3, ls="--", label="Europa - emergenti")
    ax.axhline(config.SOGLIA_CORR, color="black", lw=0.8, ls=":")
    for kk, (et, ini, fin) in enumerate(config.CRISI):
        ax.axvspan(pd.Timestamp(ini), pd.Timestamp(fin), color=GRIGIO, alpha=0.25, lw=0)
        ax.text(pd.Timestamp(ini), 0.5, et, fontsize=9, rotation=90, va="bottom", ha="right")
    ax.set_ylim(0.4, 1)
    ax.set_ylabel("Correlazione dei rendimenti giornalieri a un anno")
    ax.set_title("Le aree si muovono insieme, e di più nelle crisi?", loc="left", fontsize=13)
    ax.legend(loc="lower center", ncol=3)
    fig.savefig(config.FIGURE / "fig4_correlazione.png")
    plt.close(fig)

    # --- Figura 5 ------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie.csv")["valore_finale"] * config.CAPITALE
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(sc, bins=60, color=GRIGIO, alpha=0.8)
    for a in ("USA", "Europa", "Emergenti"):
        val = v(f"{SL[a]}_finale")
        ax.axvline(val, color=COL[a], lw=2.2, ls="-" if a != "Europa" else "--", label=f"Buy & hold {a}: {val:,.0f}".replace(",", "."))
    ax.axvspan(v("usa_finale"), max(sc.max(), v("usa_finale")) * 1.02, facecolor="none", hatch="//", edgecolor=BLU, lw=0, alpha=0.5)
    ax.set_xlabel(f"Valore finale di {config.CAPITALE:.0f} dollari (dollari)")
    ax.set_ylabel("Numero di scimmie")
    ax.set_title("Scegliere l'area a caso ogni mese: dove arrivano le scimmie", loc="left", fontsize=13)
    ax.legend(loc="upper right")
    fig.savefig(config.FIGURE / "fig5_scimmie.png")
    plt.close(fig)
    print("Figure salvate in figure/")


if __name__ == "__main__":
    main()
