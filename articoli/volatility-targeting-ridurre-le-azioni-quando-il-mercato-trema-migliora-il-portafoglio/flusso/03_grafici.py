"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_valore.png          valore di 1 euro nell'indice principale: strategia, buy & hold, buy & hold con la stessa volatilità
  fig2_volatilita.png      volatilità realizzata a un anno nell'indice principale, con la linea dell'obiettivo
  fig3_perdite.png         perdite dal massimo nell'indice principale
  fig4_sharpe.png          differenza di Sharpe (strategia meno buy & hold) per indice, con intervallo di confidenza
  fig5_scimmie.png         Sharpe delle scimmie contro la strategia, indice per indice
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    nome_pr = [i["nome"] for i in ind if i["ticker"] == config.INDICE_PRINCIPALE]
    nome_pr = nome_pr[0] if nome_pr else ind[0]["nome"]
    cur = pd.read_csv(R / "curva_principale.csv", parse_dates=["data"])

    # --- Figura 1 ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cur["data"], cur["buyhold"], color=ARANCIO, lw=1.6, label="Buy & hold")
    ax.plot(cur["data"], cur["strategia"], color=BLU, lw=1.8, label="Volatility targeting")
    ax.plot(cur["data"], cur["stessa_vol"], color=GRIGIO, lw=1.3, ls="--", label="Buy & hold con la stessa volatilità")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 euro (scala logaritmica)")
    ax.set_title(f"{nome_pr}: quanto vale 1 euro investito all'inizio", loc="left", fontsize=13)
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore.png")
    plt.close(fig)

    # --- Figura 2 ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cur["data"], cur["vol_buyhold"], color=ARANCIO, lw=1.5, label="Buy & hold")
    ax.plot(cur["data"], cur["vol_strategia"], color=BLU, lw=1.8, label="Volatility targeting")
    ax.axhline(config.OBIETTIVO_VOL, color=GRIGIO, ls="--", lw=1.2, label="Obiettivo")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x * 100:.0f}%".replace(".", ",")))
    ax.set_ylabel("Volatilità annua, finestra di un anno")
    ax.set_title(f"{nome_pr}: la volatilità realizzata", loc="left", fontsize=13)
    ax.legend(loc="upper right")
    fig.savefig(config.FIGURE / "fig2_volatilita.png")
    plt.close(fig)

    # --- Figura 3 ------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(cur["data"], cur["dd_buyhold"], 0, color=ARANCIO, alpha=0.35, label="Buy & hold")
    ax.fill_between(cur["data"], cur["dd_strategia"], 0, color=BLU, alpha=0.55, label="Volatility targeting")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x * 100:.0f}%"))
    ax.set_ylabel("Distanza dal massimo precedente")
    ax.set_title(f"{nome_pr}: le perdite dal massimo", loc="left", fontsize=13)
    ax.legend(loc="lower left")
    fig.savefig(config.FIGURE / "fig3_perdite.png")
    plt.close(fig)

    # --- Figura 4 ------------------------------------------------------------------------------------------
    sl = [i["slug"] for i in ind]
    nomi = [i["nome"].split(" (")[0] for i in ind]
    d = np.array([v(s, "dsh") for s in sl])
    lo = np.array([v(s, "dsh_lo") for s in sl])
    hi = np.array([v(s, "dsh_hi") for s in sl])
    o = np.argsort(d)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(sl))
    for k, j in enumerate(o):
        signif = lo[j] > 0 or hi[j] < 0
        col = BLU if signif else GRIGIO
        ax.barh(k, d[j], color=col, alpha=0.85, hatch="//" if d[j] > 0 else None, edgecolor="white")
        ax.plot([lo[j], hi[j]], [k, k], color="black", lw=1.4)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([nomi[j] for j in o])
    ax.set_xlabel("Sharpe della strategia meno Sharpe del buy & hold (barra nera: intervallo al 95%)")
    ax.legend(handles=[Patch(facecolor=BLU, label="intervallo che esclude lo zero"),
                       Patch(facecolor=GRIGIO, label="intervallo che contiene lo zero"),
                       Patch(facecolor="white", edgecolor="black", hatch="//", label="tratteggio: vince la strategia")],
              loc="lower right", fontsize=10)
    ax.set_title("Il volatility targeting migliora lo Sharpe?", loc="left", fontsize=13)
    fig.savefig(config.FIGURE / "fig4_sharpe.png")
    plt.close(fig)

    # --- Figura 5 ------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_sharpe.csv")
    n = len(sl)
    col = 3 if n > 4 else 2
    righe = int(np.ceil(n / col))
    fig, axs = plt.subplots(righe, col, figsize=(11, 3.3 * righe), sharey=False)
    axs = np.atleast_1d(axs).ravel()
    for k, s in enumerate(sl):
        ax = axs[k]
        x = sc[s].to_numpy()
        ax.hist(x, bins=40, color=GRIGIO, alpha=0.7)
        lin = v(s, "sh_lordo")
        ax.axvline(lin, color=BLU, lw=2.2)
        ax.set_title(f"{nomi[k]}: p = {v(s, 'p_sc'):.3f}".replace(".", ","), fontsize=11, loc="left")
        ax.set_yticks([])
    for ax in axs[n:]:
        ax.axis("off")
    fig.suptitle("Sharpe lordo delle scimmie (stessi pesi, mesi a caso) e della strategia (linea blu)", x=0.01, ha="left", fontsize=13)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_scimmie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
