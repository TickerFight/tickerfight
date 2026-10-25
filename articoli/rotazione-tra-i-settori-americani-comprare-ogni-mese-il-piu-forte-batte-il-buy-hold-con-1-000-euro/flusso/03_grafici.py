"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png       valore finale di 1.000 euro: lordo e netto nei tre scenari di costo, per regola
  fig2_ordini_costi.png      ordini all'anno e costi totali (commissioni e tasse) delle sei rotazioni
  fig3_curve.png             valore nel tempo (netto, commissione fissa): rotazioni, nove settori tenuti e buy & hold
  fig4_scimmie.png           valore finale netto delle scimmie contro la rotazione, il buy & hold e i nove settori tenuti
  fig5_varianti.png          rendimento annuo, lordo e netto, delle sei rotazioni contro il buy & hold
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
    v = lambda k: V[k]["valore"]
    etich = {"bh": "buy & hold\nS&P 500", "eq": "nove settori\ntenuti", P: "rotazione\n6 mesi, 1 settore", S: "rotazione\n6 mesi, 3 settori"}

    # --- Figura 1: dal lordo al netto -------------------------------------------------------------------------------
    scen = [("lordo", "lordo (nessun costo, nessuna tassa)", GRIGIO, 1.0),
            ("c0", f"netto, commissione {config.SCENARI_COSTO[0][0]}", BLU, 0.4),
            ("c1", f"netto, commissione {config.SCENARI_COSTO[1][0]}", BLU, 1.0),
            ("c2", f"netto, commissione {config.SCENARI_COSTO[2][0]}", ARANCIO, 1.0)]
    regole = ["bh", "eq", P, S]
    fig, ax = plt.subplots(figsize=(11, 5.6))
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

    # --- Figura 2: ordini e costi ---------------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 5))
    x = np.arange(len(config.LOOKBACKS))
    for q, (k, col) in enumerate(zip(config.N_SETTORI, [BLU, ARANCIO])):
        rids = [f"r{L}_{k}" for L in config.LOOKBACKS]
        o = [v(f"{r}_ordini_anno") for r in rids]
        comm = np.array([v(f"{r}_{M}_costo") for r in rids])
        tas = np.array([v(f"{r}_{M}_tasse") for r in rids])
        xs = x + (q - 0.5) * 0.36
        a1.bar(xs, o, width=0.34, color=col, label=f"{k} {'settore' if k == 1 else 'settori'}")
        for xi, oi in zip(xs, o):
            a1.text(xi, oi, it(oi, 1), ha="center", va="bottom", fontsize=10)
        a2.bar(xs, comm, width=0.34, color=col)
        a2.bar(xs, tas, width=0.34, bottom=comm, color=col, alpha=0.4)
        for xi, c_, t_ in zip(xs, comm, tas):
            a2.text(xi, c_ + t_, it(c_ + t_), ha="center", va="bottom", fontsize=10)
    for a in (a1, a2):
        a.set_xticks(x, [f"{L} sedute\n(~{round(L / 21)} mesi)" for L in config.LOOKBACKS], fontsize=10)
        a.grid(axis="x", visible=False)
    a1.set_ylabel("ordini all'anno (acquisti e vendite)")
    a2.set_ylabel(f"euro pagati in tutto (scenario {config.SCENARI_COSTO[config.SCENARIO_PRINCIPALE][0]})")
    a1.legend(fontsize=10)
    a2.legend(handles=[Patch(color=GRIGIO, label="commissioni (colore pieno)"), Patch(color=GRIGIO, alpha=0.4, label="tasse (colore chiaro)")], fontsize=9, loc="upper left")
    a2.set_ylim(0, a2.get_ylim()[1] * 1.15)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_ordini_costi.png")
    plt.close(fig)

    # --- Figura 3: curve ------------------------------------------------------------------------------------------------
    cur = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    ax.plot(cur["data"], cur["bh"], color=GRIGIO, lw=2.2, label="buy & hold S&P 500")
    ax.plot(cur["data"], cur["eq"], color="#333", lw=1.6, ls=":", label="nove settori tenuti")
    ax.plot(cur["data"], cur[P], color=BLU, lw=2.2, label="rotazione, 6 mesi, 1 settore")
    ax.plot(cur["data"], cur[S], color=ARANCIO, lw=2.0, ls="--", label="rotazione, 6 mesi, 3 settori")
    ax.axhline(config.CAPITALE, color="#555", lw=1, ls=":")
    ax.set_yscale("log")
    ax.set_yticks([600, 1000, 2000, 4000, 8000])
    ax.yaxis.set_major_formatter(lambda y, _: it(y))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylabel("valore di mercato di 1.000 € (scala logaritmica)")
    ax.legend(fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_curve.png")
    plt.close(fig)

    # --- Figura 4: scimmie ----------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_finali.csv")
    fig, assi = plt.subplots(1, 2, figsize=(11.5, 4.8))
    for ax, rid, tit in zip(assi, (P, S), ("1 settore", "3 settori")):
        ax.hist(sc[rid], bins=50, color=GRIGIO, alpha=0.7)
        ax.axvline(v(f"{rid}_{M}_finale"), color=BLU, lw=2.4, label="rotazione")
        ax.axvline(v(f"bh_{M}_finale"), color="#333", lw=2.0, ls=":", label="buy & hold S&P 500")
        ax.axvline(v(f"eq_{M}_finale"), color=ARANCIO, lw=2.0, ls="--", label="nove settori tenuti")
        ax.set_title(f"Rotazione a 6 mesi, {tit}", fontsize=12)
        ax.set_xlabel("valore finale netto di 1.000 €")
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
    assi[-1].legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)

    # --- Figura 5: varianti -----------------------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, sid, tit in ((a1, "lordo", "lordo"), (a2, M, "netto, commissione 2 €")):
        for k, col, mk in zip(config.N_SETTORI, [BLU, ARANCIO], ["o", "s"]):
            ax.plot(range(len(config.LOOKBACKS)), [v(f"r{L}_{k}_{sid}_cagr") * 100 for L in config.LOOKBACKS], color=col, marker=mk, lw=2,
                    label=f"rotazione, {k} {'settore' if k == 1 else 'settori'}")
        ax.axhline(v(f"bh_{sid}_cagr") * 100, color=GRIGIO, lw=2.2, label="buy & hold S&P 500")
        ax.set_xticks(range(len(config.LOOKBACKS)), [f"{L} sedute" for L in config.LOOKBACKS])
        ax.set_title(tit, fontsize=12)
        ax.yaxis.set_major_formatter(lambda y, _: f"{y:.1f}%".replace(".", ","))
    a1.set_ylabel("rendimento annuo composto")
    a1.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_varianti.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
