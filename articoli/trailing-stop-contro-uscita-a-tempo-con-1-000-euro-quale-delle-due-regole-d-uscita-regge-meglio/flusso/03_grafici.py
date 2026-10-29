"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png       valore finale di 1.000 euro: lordo e netto nei tre scenari di costo, per regola e strumento
  fig2_ordini_costi.png      ordini all'anno e costi totali (commissioni e tasse) di trailing stop e uscita a tempo
  fig3_perdita_massima.png   perdita massima dal picco: buy & hold, uscita a tempo, trailing stop
  fig4_scimmie.png           valore finale netto delle scimmie contro le due regole e il buy & hold
  fig5_soglie.png            rendimento annuo netto al variare della soglia del trailing stop e delle sedute dell'uscita a tempo
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
M = f"c{config.SCENARIO_PRINCIPALE}"
ID_TS = f"ts{int(round(config.TRAIL * 100))}"
ID_TT = f"tt{config.TEMPO}"
SOGLIE_TS = sorted([config.TRAIL] + list(config.TRAIL_CONTROLLO))
SEDUTE_TT = sorted([config.TEMPO] + list(config.TEMPO_CONTROLLO))


def it(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def breve(nome: str) -> str:
    return nome.split(" (")[0]


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "strumenti_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    slugs = [i["slug"] for i in ind]
    nomi = {i["slug"]: breve(i["nome"]) for i in ind}
    n_ts, n_tt = f"trailing stop {config.TRAIL:.0%}", f"uscita a {config.TEMPO} sedute"
    regole = [("bh", "buy & hold"), ("tr", "uscita di trend"), (ID_TT, n_tt), (ID_TS, n_ts)]

    # --- Figura 1: dal lordo al netto -------------------------------------------------------------------------------
    scen = [("lordo", "lordo (nessun costo, nessuna tassa)", GRIGIO, 1.0),
            ("c0", f"netto, commissione {config.SCENARI_COSTO[0][0]}", BLU, 0.4),
            ("c1", f"netto, commissione {config.SCENARI_COSTO[1][0]}", BLU, 1.0),
            ("c2", f"netto, commissione {config.SCENARI_COSTO[2][0]}", ARANCIO, 1.0)]
    fig, assi = plt.subplots(1, len(slugs), figsize=(5.2 * len(slugs), 5.4), sharey=False, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        migliore = max(range(len(regole)), key=lambda j: v(sl, f"{regole[j][0]}_{M}_finale"))
        for j, (rid, nome_r) in enumerate(regole):
            for q, (sid, _, col, al) in enumerate(scen):
                val = v(sl, f"{rid}_{sid}_finale")
                ax.bar(j + (q - 1.5) * 0.2, val, width=0.19, color=col, alpha=al,
                       hatch="//" if (sid == M and j == migliore) else None, edgecolor="white")
                if sid == M:
                    ax.text(j + (q - 1.5) * 0.2, val, it(val), ha="center", va="bottom", fontsize=9)
        ax.axhline(config.CAPITALE, color="#555", lw=1, ls=":")
        ax.set_xticks(range(len(regole)), [n.replace(" ", "\n", 1) for _, n in regole], fontsize=9)
        ax.set_title(nomi[sl], fontsize=12)
        ax.set_ylabel("valore finale di 1.000 €" if sl == slugs[0] else "")
        ax.grid(axis="x", visible=False)
    fig.legend(handles=[Patch(facecolor=c, alpha=a, label=l) for _, l, c, a in scen] +
               [Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la vincente (scenario 2 €)")],
               loc="lower center", ncol=3, fontsize=10, bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_lordo_netto.png")
    plt.close(fig)

    # --- Figura 2: ordini e costi ---------------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5))
    x = np.arange(len(slugs))
    for q, (rid, nome_r, col) in enumerate([(ID_TT, n_tt, ARANCIO), (ID_TS, n_ts, BLU)]):
        o = [v(sl, f"{rid}_ordini_anno") for sl in slugs]
        a1.bar(x + (q - 0.5) * 0.36, o, width=0.34, color=col, label=nome_r)
        for xi, oi in zip(x, o):
            a1.text(xi + (q - 0.5) * 0.36, oi, it(oi, 1), ha="center", va="bottom", fontsize=10)
        comm = np.array([v(sl, f"{rid}_{M}_costo") for sl in slugs])
        tas = np.array([v(sl, f"{rid}_{M}_tasse") for sl in slugs])
        a2.bar(x + (q - 0.5) * 0.36, comm, width=0.34, color=col)
        a2.bar(x + (q - 0.5) * 0.36, tas, width=0.34, bottom=comm, color=col, alpha=0.4)
    a1.set_xticks(x, [nomi[sl] for sl in slugs], fontsize=10)
    a2.set_xticks(x, [nomi[sl] for sl in slugs], fontsize=10)
    a1.set_ylabel("ordini all'anno (acquisti e vendite)")
    a2.set_ylabel(f"euro pagati in tutto (scenario {config.SCENARI_COSTO[config.SCENARIO_PRINCIPALE][0]})")
    a1.legend(fontsize=10)
    a2.legend(handles=[Patch(color=GRIGIO, label="commissioni (colore pieno)"), Patch(color=GRIGIO, alpha=0.4, label="tasse (colore chiaro)")], fontsize=9, loc="upper left")
    a1.grid(axis="x", visible=False)
    a2.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_ordini_costi.png")
    plt.close(fig)

    # --- Figura 3: perdita massima --------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.2))
    reg3 = [("bh", "buy & hold", GRIGIO), (ID_TT, n_tt, ARANCIO), (ID_TS, n_ts, BLU)]
    for j, sl in enumerate(slugs):
        dd = [v(sl, f"{rid}_dd") * 100 for rid, _, _ in reg3]
        migl = int(np.argmin(dd))
        for q, (rid, nome_r, col) in enumerate(reg3):
            ax.bar(j + (q - 1) * 0.27, dd[q], width=0.25, color=col, hatch="//" if q == migl else None, edgecolor="white")
            ax.text(j + (q - 1) * 0.27, dd[q], f"{it(dd[q])}%", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(range(len(slugs)), [nomi[sl] for sl in slugs])
    ax.set_ylabel("perdita massima dal picco")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Patch(color=c, label=n) for _, n, c in reg3] +
              [Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la perdita più piccola")], fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_perdita_massima.png")
    plt.close(fig)

    # --- Figura 4: scimmie ----------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_finali.csv")
    fig, assi = plt.subplots(2, len(slugs), figsize=(5.2 * len(slugs), 7.4), squeeze=False)
    for riga, (rid, nome_r) in enumerate([(ID_TS, n_ts), (ID_TT, n_tt)]):
        for ax, sl in zip(assi[riga], slugs):
            col = f"{sl}_{rid}"
            if col in sc:
                ax.hist(sc[col], bins=50, color=GRIGIO, alpha=0.7)
            ax.axvline(v(sl, f"{rid}_{M}_finale"), color=BLU if riga == 0 else ARANCIO, ls="-", lw=2.4, label=nome_r)
            ax.axvline(v(sl, f"bh_{M}_finale"), color="#333", ls=":", lw=2.2, label="buy & hold")
            ax.set_title(f"{nomi[sl]}: {nome_r}", fontsize=11)
            ax.set_xlabel("valore finale netto di 1.000 €")
            ax.set_yticks([])
            ax.grid(axis="y", visible=False)
            if sl == slugs[-1]:
                ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)

    # --- Figura 5: soglie -----------------------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    xs = [int(round(x * 100)) for x in SOGLIE_TS]
    for sl, col, mk in zip(slugs, [BLU, ARANCIO, GRIGIO], ["o", "s", "^"]):
        a1.plot(range(len(xs)), [v(sl, f"ts{x}_{M}_cagr") * 100 for x in xs], color=col, marker=mk, lw=2, label=nomi[sl])
        a2.plot(range(len(SEDUTE_TT)), [v(sl, f"tt{x}_{M}_cagr") * 100 for x in SEDUTE_TT], color=col, marker=mk, lw=2, label=nomi[sl])
    a1.set_xticks(range(len(xs)), [f"{x}%" for x in xs])
    a2.set_xticks(range(len(SEDUTE_TT)), [f"{x}" for x in SEDUTE_TT])
    a1.set_xlabel("soglia del trailing stop")
    a2.set_xlabel("sedute prima dell'uscita a tempo")
    a1.set_ylabel("rendimento annuo netto")
    a1.yaxis.set_major_formatter(lambda y, _: f"{y:.1f}%".replace(".", ","))
    a1.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_soglie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
