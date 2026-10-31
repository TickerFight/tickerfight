"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png       valore finale di 1.000 euro: lordo e netto nei tre scenari di costo, per le regole principali
  fig2_curve_mesi_fuori.png  valore nel tempo (netto, commissione fissa) con i mesi in liquidità del filtro principale
  fig3_soglie.png            perdita massima lorda e rendimento annuo netto di tutte le regole, con e senza filtro
  fig4_scimmie.png           valore finale netto delle scimmie (stessi mesi in liquidità, scelti a caso) contro il filtro
"""
import json

import matplotlib
import matplotlib.ticker

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
M = f"c{config.SCENARIO_PRINCIPALE}"


def it(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    info = json.loads((R / "regole_usate.json").read_text(encoding="utf-8"))
    P, S = info["principale"], info["seconda"]
    BP, BS = f"m{config.PRINCIPALE[0]}", f"m{config.SECONDA[0]}"
    v = lambda k: V[k]["valore"]

    # --- Figura 1: dal lordo al netto ---------------------------------------------------------------------------------
    etich = {"bh": "buy & hold\nS&P 500", BP: "momentum 6 mesi\nsenza filtro", P: "momentum 6 mesi\nfiltro VIX 25",
             BS: "momentum 12 mesi\nsenza filtro", S: "momentum 12 mesi\nfiltro VIX 25"}
    scen = [("lordo", "lordo (nessun costo, nessuna tassa)", GRIGIO, 1.0),
            ("c0", f"netto, commissione {config.SCENARI_COSTO[0][0]}", BLU, 0.4),
            ("c1", f"netto, commissione {config.SCENARI_COSTO[1][0]}", BLU, 1.0),
            ("c2", f"netto, commissione {config.SCENARI_COSTO[2][0]}", ARANCIO, 1.0)]
    regole = ["bh", BP, P, BS, S]
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    migliore = max(range(len(regole)), key=lambda j: v(f"{regole[j]}_{M}_finale"))
    for j, rid in enumerate(regole):
        for q, (sid, _, col, al) in enumerate(scen):
            val = v(f"{rid}_{sid}_finale")
            ax.bar(j + (q - 1.5) * 0.2, val, width=0.19, color=col, alpha=al,
                   hatch="//" if (sid == M and j == migliore) else None, edgecolor="white")
            ax.text(j + (q - 1.5) * 0.2, val, it(val), ha="center", va="bottom", fontsize=8.5, rotation=90)
    ax.axhline(config.CAPITALE, color="#555", lw=1, ls=":")
    ax.set_xticks(range(len(regole)), [etich[r] for r in regole], fontsize=10)
    ax.set_ylabel("valore finale di 1.000 €")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ax.grid(axis="x", visible=False)
    fig.legend(handles=[Patch(facecolor=c, alpha=a, label=l) for _, l, c, a in scen] +
               [Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la vincente (scenario 2 €)")],
               loc="lower center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_lordo_netto.png")
    plt.close(fig)

    # --- Figura 2: curve e mesi fuori ---------------------------------------------------------------------------------
    cur = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    mesi = pd.read_csv(R / "mesi_filtro.csv", parse_dates=["data_ordine"])
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    d = mesi["data_ordine"].to_numpy()
    liq = mesi["liquidita"].to_numpy()
    for j in range(len(d)):
        if liq[j]:
            fine = d[j + 1] if j + 1 < len(d) else cur["data"].iloc[-1]
            ax.axvspan(d[j], fine, color=ARANCIO, alpha=0.18, lw=0)
    ax.plot(cur["data"], cur["bh"], color=GRIGIO, lw=2.2, label="buy & hold S&P 500")
    ax.plot(cur["data"], cur[BP], color="#333", lw=1.6, ls=":", label="momentum 6 mesi, senza filtro")
    ax.plot(cur["data"], cur[P], color=BLU, lw=2.2, label="momentum 6 mesi, filtro VIX 25")
    ax.axhline(config.CAPITALE, color="#555", lw=1, ls=":")
    ax.set_yscale("log")
    ax.set_yticks([300, 500, 1000, 2000, 4000, 8000])
    ax.yaxis.set_major_formatter(lambda y, _: it(y))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylabel("valore di mercato di 1.000 € (scala logaritmica)")
    h, l = ax.get_legend_handles_labels()
    ax.legend(h + [Patch(color=ARANCIO, alpha=0.18)], l + ["mesi in liquidità (VIX sopra 25)"], fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_curve_mesi_fuori.png")
    plt.close(fig)

    # --- Figura 3: tutte le combinazioni -------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.9))
    ths = list(config.SOGLIE_VIX)
    x = np.arange(len(ths) + 1)
    larg = 0.36
    for q, (L, col) in enumerate(zip(config.LOOKBACKS, [BLU, ARANCIO])):
        d1 = [v(f"m{L}_lordo_dd") * 100] + [v(f"f{L}_{th}_lordo_dd") * 100 for th in ths]
        d2 = [v(f"m{L}_{M}_cagr") * 100] + [v(f"f{L}_{th}_{M}_cagr") * 100 for th in ths]
        xs = x + (q - 0.5) * larg
        a1.bar(xs, d1, width=larg - 0.02, color=col, label=f"osservazione {L} sedute")
        a2.bar(xs, d2, width=larg - 0.02, color=col)
        for xi, y in zip(xs, d1):
            a1.text(xi, y, it(y), ha="center", va="bottom", fontsize=9)
        for xi, y in zip(xs, d2):
            a2.text(xi, y, it(y, 1), ha="center", va="bottom", fontsize=9)
    a2.axhline(v(f"bh_{M}_cagr") * 100, color=GRIGIO, lw=2.2, ls="--", label="buy & hold S&P 500")
    a1.axhline(v("bh_lordo_dd") * 100, color=GRIGIO, lw=2.2, ls="--")
    for a in (a1, a2):
        a.set_xticks(x, ["senza\nfiltro"] + [f"VIX > {t}" for t in ths], fontsize=10)
        a.grid(axis="x", visible=False)
    a1.set_title("Perdita massima dal picco, lordo (%)", fontsize=12)
    a2.set_title("Rendimento annuo, netto con 2 € a ordine (%)", fontsize=12)
    a1.set_ylim(0, a1.get_ylim()[1] * 1.12)
    a2.set_ylim(0, a2.get_ylim()[1] * 1.12)
    h1, l1 = a1.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, loc="lower center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_soglie.png")
    plt.close(fig)

    # --- Figura 4: scimmie ----------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_finali.csv")
    fig, assi = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for ax, rid, base, tit in zip(assi, (P, S), (BP, BS), ("6 mesi", "12 mesi")):
        ax.hist(sc[rid], bins=50, color=GRIGIO, alpha=0.7)
        ax.axvline(v(f"{rid}_{M}_finale"), color=BLU, lw=2.4, label="con filtro VIX 25")
        ax.axvline(v(f"{base}_{M}_finale"), color=ARANCIO, lw=2.0, ls="--", label="senza filtro")
        ax.axvline(v(f"bh_{M}_finale"), color="#333", lw=2.0, ls=":", label="buy & hold S&P 500")
        ax.set_title(f"Momentum a {tit}", fontsize=12)
        ax.set_xlabel("valore finale netto di 1.000 €")
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
    assi[-1].legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
