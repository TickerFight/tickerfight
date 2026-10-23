"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_anni_sp500.png       rendimento della finestra di sette sedute, anno per anno, sull'S&P 500
  fig2_scimmie.png          rendimento medio delle scimmie contro quello della finestra reale, indice per indice
  fig3_rendimento_annuo.png rendimento annuo netto: strategia e buy & hold, indice per indice
  fig4_prima_dopo.png       rendimento medio della finestra prima e dopo il 1999, indice per indice
  fig5_griglia_sp500.png    varianti della finestra sull'S&P 500: eccesso sul caso per ogni combinazione di sedute
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def virgola(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    nomi = {i["slug"]: i["nome"] for i in ind}
    slugs = [i["slug"] for i in ind]
    fin = pd.read_csv(R / "finestre.csv")
    sc = pd.read_csv(R / "scimmie_medie.csv")
    gr = pd.read_csv(R / "griglia.csv")
    primo = ind[0]

    # --- Figura 1: anno per anno sul primo indice (S&P 500) -----------------------------------------------------
    a = fin[fin["indice"] == primo["ticker"]]
    fig, ax = plt.subplots(figsize=(11, 5))
    anni = a["anno"].to_numpy() + 1
    r = a["rendimento"].to_numpy() * 100
    ax.bar(anni, r, color=np.where(r > 0, BLU, ARANCIO), width=0.8)
    ax.axhline(v(primo["slug"], "media") * 100, color="#333", lw=1.4, ls="--")
    ax.axhline(0, color="#555", lw=1)
    ax.text(anni[-1] + 1, v(primo["slug"], "media") * 100 + 0.15, "media " + virgola(v(primo["slug"], "media") * 100, 2) + "%", fontsize=10, ha="right")
    ax.set_xlabel("anno di gennaio della finestra")
    ax.set_ylabel("rendimento della finestra di sette sedute")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    ax.legend(handles=[Patch(color=BLU, label="finestra in positivo"), Patch(color=ARANCIO, label="finestra in perdita")], loc="lower left")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_anni_sp500.png")
    plt.close(fig)

    # --- Figura 2: le scimmie --------------------------------------------------------------------------------------
    righe = 2
    colonne = int(np.ceil(len(slugs) / righe))
    fig, assi = plt.subplots(righe, colonne, figsize=(4.0 * colonne, 6.6))
    assi = np.atleast_1d(assi).ravel()
    for ax, i in zip(assi, ind):
        sl = i["slug"]
        ax.hist(sc[i["ticker"]] * 100, bins=40, color=GRIGIO, alpha=0.6, edgecolor="white")
        ax.axvline(v(sl, "media") * 100, color=BLU, lw=2.4)
        ax.set_title(nomi[sl].split(" (")[0], fontsize=11)
        ax.set_yticks([])
        ax.xaxis.set_major_formatter(lambda x, _: f"{x:.1f}%".replace(".", ","))
        ax.tick_params(axis="x", labelsize=9)
    for ax in assi[len(ind):]:
        ax.axis("off")
    assi[0].plot([], [], color=BLU, lw=2.4, label="finestra reale")
    assi[0].bar([0], [0], color=GRIGIO, alpha=0.6, label="scimmie")
    assi[0].legend(fontsize=9, loc="upper right")
    fig.supxlabel("rendimento medio per anno di una finestra di sette sedute")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_scimmie.png")
    plt.close(fig)

    # --- Figura 3: strategia contro buy & hold ------------------------------------------------------------------
    ordine = sorted(slugs, key=lambda sl: v(sl, "cagr_bh"))
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for k, sl in enumerate(ordine):
        ch, cb = v(sl, "cagr_h") * 100, v(sl, "cagr_bh") * 100
        ax.barh(k + 0.19, ch, height=0.36, color=BLU, hatch="//" if ch > cb else None, edgecolor="white")
        ax.barh(k - 0.19, cb, height=0.36, color=ARANCIO, hatch="//" if cb > ch else None, edgecolor="white")
        ax.text(max(ch, 0) + 0.1, k + 0.19, virgola(ch) + "%", va="center", fontsize=10)
        ax.text(max(cb, 0) + 0.1, k - 0.19, virgola(cb) + "%", va="center", fontsize=10)
    ax.set_yticks(range(len(ordine)), [nomi[sl] for sl in ordine])
    ax.axvline(0, color="#555", lw=1)
    ax.set_xlabel("rendimento annuo composto netto di costi e tasse")
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=BLU, label="solo la finestra di sette sedute"), Patch(color=ARANCIO, label="buy & hold"),
                       Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la barra vincente")],
              loc="lower right", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_rendimento_annuo.png")
    plt.close(fig)

    # --- Figura 4: prima e dopo --------------------------------------------------------------------------------
    ok = [sl for sl in slugs if f"{sl}_media_prima" in V and f"{sl}_media_dopo" in V and v(sl, "n_prima") >= 5 and v(sl, "n_dopo") >= 5]
    if ok:
        fig, ax = plt.subplots(figsize=(10, 4.6))
        for k, sl in enumerate(ok):
            p, d = v(sl, "media_prima") * 100, v(sl, "media_dopo") * 100
            ax.plot([p, d], [k, k], color=GRIGIO, lw=2)
            ax.scatter([p], [k], color=BLU, s=70, zorder=3)
            ax.scatter([d], [k], color=ARANCIO, s=70, zorder=3)
        ax.axvline(0, color="#555", lw=1)
        ax.set_yticks(range(len(ok)), [nomi[sl] for sl in ok])
        ax.set_xlabel("rendimento medio della finestra di sette sedute, in %")
        ax.scatter([], [], color=BLU, label=f"fino al {config.ANNO_DIVISIONE - 1}")
        ax.scatter([], [], color=ARANCIO, label=f"dal {config.ANNO_DIVISIONE}")
        ax.legend(loc="best")
        ax.grid(axis="y", visible=False)
        fig.tight_layout()
        fig.savefig(config.FIGURE / "fig4_prima_dopo.png")
        plt.close(fig)

    # --- Figura 5: la griglia delle varianti sul primo indice ------------------------------------------------------
    g = gr[gr["indice"] == primo["ticker"]]
    ks, ms = list(config.GRIGLIA_DICEMBRE), list(config.GRIGLIA_GENNAIO)
    M = np.zeros((len(ks), len(ms)))
    for r_, kk in enumerate(ks):
        for c_, mm in enumerate(ms):
            M[r_, c_] = float(g[(g["k"] == kk) & (g["m"] == mm)]["eccesso"].iloc[0]) * 100
    lim = float(np.abs(M).max())
    mappa = LinearSegmentedColormap.from_list("bo", [ARANCIO, "white", BLU])
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    im = ax.imshow(M, cmap=mappa, vmin=-lim, vmax=lim, aspect="auto")
    for r_ in range(len(ks)):
        for c_ in range(len(ms)):
            ax.text(c_, r_, f"{M[r_, c_]:+.2f}".replace(".", ","), ha="center", va="center", fontsize=10)
    ax.set_xticks(range(len(ms)), ms)
    ax.set_yticks(range(len(ks)), ks)
    ax.add_patch(Rectangle((ms.index(config.SEDUTE_GENNAIO) - 0.5, ks.index(config.SEDUTE_DICEMBRE) - 0.5), 1, 1, fill=False, ec="black", lw=2.5))
    ax.grid(False)
    ax.set_xlabel("sedute di gennaio incluse")
    ax.set_ylabel("ultime sedute di dicembre incluse")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("eccesso sul caso, punti percentuali")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_griglia_sp500.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
