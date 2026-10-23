"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_quota_vittorie.png        quota di vittorie del lump sum per indice e orizzonte, con la fascia delle storie rimescolate
  fig2_distribuzione_sp500.png   differenza PAC meno lump sum (punti del budget) per l'S&P 500 a 12 mesi
  fig3_direzione_mercato.png     quota di vittorie del PAC quando l'indice scende e quando sale
  fig4_sp500_nel_tempo.png       differenza PAC meno lump sum per mese di partenza, S&P 500, 12 mesi
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
    part = pd.read_csv(R / "partenze.csv", parse_dates=["partenza"])
    sp = slug_p = [i["slug"] for i in ind if i["ticker"] == config.INDICE_PRINCIPALE][0]
    tk_p = config.INDICE_PRINCIPALE
    h1, h2 = config.ORIZZONTI

    # --- Figura 1 -----------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = np.arange(len(slugs))
    larg = 0.36
    for j, (h, col) in enumerate(((h1, BLU), (h2, "#7fa6d1"))):
        pos = x + (j - 0.5) * larg
        q = [v(f"{s}_{h}_quota_lump") * 100 for s in slugs]
        ax.bar(pos, q, larg * 0.92, color=col, label=f"Lump sum davanti, {h} mesi")
        for xi, s in zip(pos, slugs):
            ax.plot([xi, xi], [v(f"{s}_{h}_null_lo") * 100, v(f"{s}_{h}_null_hi") * 100], color=ARANCIO, lw=3, solid_capstyle="butt")
            ax.plot([xi - larg * 0.46, xi + larg * 0.46], [v(f"{s}_{h}_null_media") * 100] * 2, color=ARANCIO, lw=1.5, ls="--")
        for xi, qq in zip(pos, q):
            ax.text(xi, 5, f"{qq:.0f}%", ha="center", fontsize=11, color="white", fontweight="bold")
    ax.plot([], [], color=ARANCIO, lw=3, label="Storie rimescolate (fascia 95%)")
    ax.axhline(50, color=GRIGIO, lw=1)
    ax.set_xticks(x, [nomi[s] for s in slugs])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Partenze in cui vince il lump sum (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)
    fig.savefig(config.FIGURE / "fig1_quota_vittorie.png")
    plt.close(fig)

    # --- Figura 2 -----------------------------------------------------------------------------------------------
    d = part[(part.ticker == tk_p) & (part.orizzonte == h1)]["diff_pp"].values
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    lim = float(np.ceil(max(abs(np.quantile(d, 0.005)), abs(np.quantile(d, 0.995))) / 5) * 5)
    bins = np.linspace(-lim, lim, 61)
    n, b, patches = ax.hist(np.clip(d, -lim, lim), bins=bins, color=BLU, edgecolor="white")
    for pa, left in zip(patches, b[:-1]):
        if left >= 0:
            pa.set_facecolor(ARANCIO)
            pa.set_hatch("//")
    ax.axvline(0, color="black", lw=1)
    ax.axvline(np.median(d), color=GRIGIO, lw=1.5, ls="--")
    ax.text(np.median(d), ax.get_ylim()[1] * 0.93, f" mediana {np.median(d):.1f}".replace(".", ","), color=GRIGIO, fontsize=10)
    ax.set_xlabel("PAC meno lump sum, in punti percentuali del budget  (a sinistra vince il lump sum, a destra il PAC)")
    ax.set_ylabel("Mesi di partenza")
    fig.savefig(config.FIGURE / "fig2_distribuzione_sp500.png")
    plt.close(fig)

    # --- Figura 3 -----------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    larg = 0.36
    ax.bar(x - larg / 2, [v(f"{s}_{h1}_pac_vince_se_scende") * 100 for s in slugs], larg * 0.92, color=ARANCIO, hatch="//", label="Quando l'indice scende nei 12 mesi")
    ax.bar(x + larg / 2, [v(f"{s}_{h1}_pac_vince_se_sale") * 100 for s in slugs], larg * 0.92, color=BLU, label="Quando l'indice sale nei 12 mesi")
    for xi, s in zip(x - larg / 2, slugs):
        ax.text(xi, v(f"{s}_{h1}_pac_vince_se_scende") * 100 + 1.2, f"{v(f'{s}_{h1}_pac_vince_se_scende') * 100:.0f}%", ha="center", fontsize=10)
    for xi, s in zip(x + larg / 2, slugs):
        ax.text(xi, v(f"{s}_{h1}_pac_vince_se_sale") * 100 + 1.2, f"{v(f'{s}_{h1}_pac_vince_se_sale') * 100:.0f}%", ha="center", fontsize=10)
    ax.set_xticks(x, [nomi[s] for s in slugs])
    ax.set_ylim(0, 110)
    ax.set_ylabel("Partenze in cui vince il PAC (%)")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_direzione_mercato.png")
    plt.close(fig)

    # --- Figura 4 -----------------------------------------------------------------------------------------------
    s = part[(part.ticker == tk_p) & (part.orizzonte == h1)]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    ax.fill_between(s.partenza, 0, s.diff_pp.clip(lower=0), color=ARANCIO, hatch="//", edgecolor="white", lw=0, label="Vince il PAC")
    ax.fill_between(s.partenza, 0, s.diff_pp.clip(upper=0), color=BLU, lw=0, label="Vince il lump sum")
    ax.axhline(0, color="black", lw=1)
    ax.set_ylabel("PAC meno lump sum (punti del budget)")
    ax.set_xlabel("Mese di partenza")
    ax.legend(loc="lower left", fontsize=10)
    fig.savefig(config.FIGURE / "fig4_sp500_nel_tempo.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
