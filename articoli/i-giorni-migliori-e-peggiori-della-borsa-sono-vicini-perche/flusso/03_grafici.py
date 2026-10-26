"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_vicinanza_indici.png   quota di giorni peggiori con un giorno migliore entro 10 sedute: vera contro caso, per indice
  fig2_curva_distanza.png     S&P 500: quota entro d sedute, vera contro storie rimescolate
  fig3_quinti_volatilita.png  S&P 500: dove cadono i giorni estremi rispetto alla volatilità di ieri
  fig4_anni_estremi.png       S&P 500: giorni estremi per anno
  fig5_filtro_scimmie.png     S&P 500: rendimento annuo del filtro, del buy & hold e delle scimmie
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
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    v = lambda k: V[k]["valore"]
    nomi = {i["slug"]: i["nome"].split(" (")[0] for i in ind}
    slugs = [i["slug"] for i in ind]
    tk_p = config.INDICE_PRINCIPALE
    sp = [i["slug"] for i in ind if i["ticker"] == tk_p][0]

    # --- Figura 1 -----------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = np.arange(len(slugs))
    larg = 0.36
    for j, (chiave, nulla, col, lab) in enumerate((("quota_pm", "null_quota_pm", BLU, "Storia vera"), ("z_quota_pm", "z_null_quota_pm", "#7fa6d1", "Storia vera, divisa per la volatilità di ieri"))):
        pos = x + (j - 0.5) * larg
        q = [v(f"{s}_{chiave}") * 100 for s in slugs]
        ax.bar(pos, q, larg * 0.92, color=col, label=lab)
        for xi, s, qq in zip(pos, slugs, q):
            nm = v(f"{s}_{nulla}") * 100
            ax.plot([xi - larg * 0.46, xi + larg * 0.46], [nm, nm], color=ARANCIO, lw=2, ls="--")
            ax.text(xi, 1.5, f"{qq:.0f}%", ha="center", fontsize=11, color="white", fontweight="bold")
    ax.plot([], [], color=ARANCIO, lw=2, ls="--", label="Caso (media delle storie rimescolate)")
    ax.set_xticks(x, [nomi[s] for s in slugs])
    ax.set_ylabel("Giorni peggiori con un migliore entro 10 sedute (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=1, fontsize=10)
    fig.savefig(config.FIGURE / "fig1_vicinanza_indici.png")
    plt.close(fig)

    # --- Figura 2 -----------------------------------------------------------------------------------------------
    c = pd.read_csv(R / "curva_distanza.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.fill_between(c.d, c.caso_lo * 100, c.caso_hi * 100, color=ARANCIO, alpha=0.25, lw=0, label="Caso: fascia 95%")
    ax.plot(c.d, c.caso_media * 100, color=ARANCIO, ls="--", lw=2, label="Caso: media")
    ax.plot(c.d, c.vera * 100, color=BLU, lw=2.5, label="Storia vera")
    ax.axvline(config.FINESTRA_VICINO, color=GRIGIO, lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("Distanza in sedute (scala logaritmica)")
    ax.set_ylabel("Giorni peggiori con un migliore a distanza ≤ d (%)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_curva_distanza.png")
    plt.close(fig)

    # --- Figura 3 -----------------------------------------------------------------------------------------------
    qn = pd.read_csv(R / "quintili.csv")
    qn = qn[qn.ticker == tk_p]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    xs = np.arange(1, 6)
    ax.bar(xs - larg / 2, qn.peggiori * 100, larg * 0.92, color=ARANCIO, hatch="//", edgecolor="white", label="Giorni peggiori")
    ax.bar(xs + larg / 2, qn.migliori * 100, larg * 0.92, color=BLU, label="Giorni migliori")
    ax.axhline(20, color=GRIGIO, lw=1.5, ls="--")
    ax.text(0.55, 21, "caso: 20%", color=GRIGIO, fontsize=10)
    ax.set_xticks(xs, ["1° (calmo)", "2°", "3°", "4°", "5° (agitato)"])
    ax.set_xlabel("Quinto delle sedute, ordinate per volatilità di ieri")
    ax.set_ylabel("Giorni estremi (%)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_quinti_volatilita.png")
    plt.close(fig)

    # --- Figura 4 -----------------------------------------------------------------------------------------------
    an = pd.read_csv(R / "anni_estremi.csv")
    an = an[an.ticker == tk_p]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    ax.bar(an.anno, an.peggiori, color=ARANCIO, hatch="//", edgecolor="white", label="Giorni peggiori")
    ax.bar(an.anno, an.migliori, bottom=an.peggiori, color=BLU, label="Giorni migliori")
    ax.set_ylabel("Giorni estremi nell'anno")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig4_anni_estremi.png")
    plt.close(fig)

    # --- Figura 5 -----------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_sp500.csv")["cagr"] * 100
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    ax.hist(sc, bins=40, color=GRIGIO, edgecolor="white", label="Scimmie (stesse sedute in liquidità, a caso)")
    for val, col, lab, ls in ((v(f"{sp}_cagr_bh") * 100, "black", "Buy & hold", "-"), (v(f"{sp}_cagr_filtro") * 100, BLU, "Filtro di volatilità", "--")):
        ax.axvline(val, color=col, lw=2.5, ls=ls, label=lab)
    ax.set_xlabel("Rendimento annuo composto (%), indice di prezzo")
    ax.set_ylabel("Scimmie")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig5_filtro_scimmie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
