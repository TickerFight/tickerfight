"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_rendimento_annuo.png     rendimento annuo netto: strategia Halloween e buy & hold, indice per indice
  fig2_differenza_semestri.png  differenza media tra novembre-aprile e maggio-ottobre, con intervallo di confidenza
  fig3_calendari.png            i dodici calendari di sei mesi: quanto fanno meglio o peggio del buy & hold
  fig4_scimmie.png              valore finale delle scimmie contro strategia e buy & hold, indice per indice
  fig5_prima_dopo.png           la differenza media prima e dopo l'anno dell'articolo che ha reso famoso l'effetto
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


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    nomi = {i["slug"]: i["nome"] for i in ind}
    slugs = [i["slug"] for i in ind]
    cal = pd.read_csv(R / "calendari.csv")
    fin = pd.read_csv(R / "scimmie_finali.csv")

    # --- Figura 1: rendimento annuo ----------------------------------------------------------------------------
    ordine = sorted(slugs, key=lambda sl: v(sl, "cagr_bh"))
    fig, ax = plt.subplots(figsize=(10, 5.6))
    y = np.arange(len(ordine))
    for k, sl in enumerate(ordine):
        ch, cb = v(sl, "cagr_h") * 100, v(sl, "cagr_bh") * 100
        ax.barh(k + 0.19, ch, height=0.36, color=BLU, hatch="//" if ch > cb else None, edgecolor="white")
        ax.barh(k - 0.19, cb, height=0.36, color=ARANCIO, hatch="//" if cb > ch else None, edgecolor="white")
        ax.text(max(ch, 0) + 0.1, k + 0.19, f"{ch:.1f}%".replace(".", ","), va="center", fontsize=10)
        ax.text(max(cb, 0) + 0.1, k - 0.19, f"{cb:.1f}%".replace(".", ","), va="center", fontsize=10)
    ax.set_yticks(y, [nomi[sl] for sl in ordine])
    ax.axvline(0, color="#555", lw=1)
    ax.set_xlabel("rendimento annuo composto netto di costi e tasse")
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=BLU, label="strategia Halloween (novembre-aprile)"),
                       Patch(color=ARANCIO, label="buy & hold"),
                       Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la barra vincente")],
              loc="lower right", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_rendimento_annuo.png")
    plt.close(fig)

    # --- Figura 2: differenza tra i due semestri -----------------------------------------------------------------
    ordine = sorted(slugs, key=lambda sl: v(sl, "diff"))
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for k, sl in enumerate(ordine):
        m, lo, hi = v(sl, "diff") * 100, v(sl, "diff_lo") * 100, v(sl, "diff_hi") * 100
        colore = BLU if lo > 0 else GRIGIO
        ax.errorbar(m, k, xerr=[[m - lo], [hi - m]], fmt="o", color=colore, capsize=4, lw=2, ms=7)
    ax.axvline(0, color="#555", lw=1)
    ax.set_yticks(range(len(ordine)), [nomi[sl] for sl in ordine])
    ax.set_xlabel(f"novembre-aprile meno maggio-ottobre, punti percentuali (intervallo di confidenza al {config.LIVELLO_CONFIDENZA:.0%})".replace("%", " per cento"))
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_differenza_semestri.png")
    plt.close(fig)

    # --- Figura 3: i dodici calendari ---------------------------------------------------------------------------
    mesi = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
    M = np.zeros((len(slugs), 12))
    for r, sl in enumerate(slugs):
        c = cal[cal["indice"] == [i["ticker"] for i in ind if i["slug"] == sl][0]].sort_values("mese_n")
        M[r] = (c["cagr"].to_numpy() - v(sl, "cagr_bh")) * 100
    lim = float(np.abs(M).max())
    mappa = LinearSegmentedColormap.from_list("bo", [ARANCIO, "white", BLU])
    fig, ax = plt.subplots(figsize=(12, 5.6))
    im = ax.imshow(M, cmap=mappa, vmin=-lim, vmax=lim, aspect="auto")
    for r in range(M.shape[0]):
        for c in range(12):
            ax.text(c, r, f"{M[r, c]:+.1f}".replace(".", ","), ha="center", va="center", fontsize=9)
    ax.set_xticks(range(12), mesi)
    ax.set_yticks(range(len(slugs)), [nomi[sl] for sl in slugs])
    ax.add_patch(Rectangle((9.5, -0.5), 1, len(slugs), fill=False, ec="black", lw=2.5))
    ax.grid(False)
    ax.set_xlabel("mese di inizio del semestre investito (il riquadro è novembre, cioè novembre-aprile)")
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("rendimento annuo del calendario meno quello del buy & hold, punti percentuali")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_calendari.png")
    plt.close(fig)

    # --- Figura 4: le scimmie ------------------------------------------------------------------------------------
    righe = 2
    colonne = int(np.ceil(len(slugs) / righe))
    fig, assi = plt.subplots(righe, colonne, figsize=(4.0 * colonne, 6.6))
    assi = np.atleast_1d(assi).ravel()
    for a, i in zip(assi, ind):
        sl = i["slug"]
        a.hist(fin[i["ticker"]], bins=40, color=GRIGIO, alpha=0.6, edgecolor="white")
        a.axvline(v(sl, "finale_h"), color=BLU, lw=2.4)
        a.axvline(v(sl, "finale_bh"), color=ARANCIO, lw=2.2, ls="--")
        a.set_title(nomi[sl], fontsize=11)
        a.set_yticks([])
        a.xaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
        a.tick_params(axis="x", labelsize=9)
    for a in assi[len(ind):]:
        a.axis("off")
    assi[0].plot([], [], color=BLU, lw=2.4, label="strategia Halloween")
    assi[0].plot([], [], color=ARANCIO, lw=2.2, ls="--", label="buy & hold")
    assi[0].bar([0], [0], color=GRIGIO, alpha=0.6, label="scimmie")
    assi[0].legend(fontsize=9, loc="upper right")
    fig.supxlabel("valore finale netto di 500 (nella valuta dell'indice)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)

    # --- Figura 5: prima e dopo ----------------------------------------------------------------------------------
    ok = [sl for sl in slugs if f"{sl}_diff_prima" in V and v(sl, "n_dopo") >= 5]
    if ok:
        fig, ax = plt.subplots(figsize=(10, 4.4))
        for k, sl in enumerate(ok):
            p, d = v(sl, "diff_prima") * 100, v(sl, "diff_dopo") * 100
            ax.plot([p, d], [k, k], color=GRIGIO, lw=2)
            ax.scatter([p], [k], color=BLU, s=70, zorder=3)
            ax.scatter([d], [k], color=ARANCIO, s=70, zorder=3)
        ax.axvline(0, color="#555", lw=1)
        ax.set_yticks(range(len(ok)), [nomi[sl] for sl in ok])
        ax.set_xlabel("novembre-aprile meno maggio-ottobre, punti percentuali")
        ax.scatter([], [], color=BLU, label=f"fino al {config.DATA_PUBBLICAZIONE}")
        ax.scatter([], [], color=ARANCIO, label=f"dopo il {config.DATA_PUBBLICAZIONE}")
        ax.legend(loc="lower right")
        ax.grid(axis="y", visible=False)
        fig.tight_layout()
        fig.savefig(config.FIGURE / "fig5_prima_dopo.png")
        plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
