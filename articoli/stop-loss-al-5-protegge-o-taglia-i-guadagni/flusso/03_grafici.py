"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png       valore finale di 1.000 euro: lordo e netto nei tre scenari di costo, per regola e strumento
  fig2_ordini_costi.png      ordini all'anno e costi totali (commissioni e tasse) della regola con e senza stop
  fig3_perdita_massima.png   perdita massima dal picco: buy & hold, regola di trend, regola con stop
  fig4_scimmie.png           valore finale netto delle scimmie contro la regola con stop, il trend e il buy & hold
  fig5_soglie.png            rendimento annuo netto e stop scattati al variare della soglia dello stop
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
ID_STOP = f"s{int(round(config.STOP * 100))}"
SOGLIE = [config.STOP] + list(config.SOGLIE_CONTROLLO)
IDS = sorted(SOGLIE)


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
    pct = f"{config.STOP:.0%}"
    regole = [("bh", "buy & hold"), ("tr", "trend"), (ID_STOP, f"trend + stop {pct}")]

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
        ax.set_xticks(range(len(regole)), [n for _, n in regole], fontsize=10)
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
    for q, (rid, nome_r, col) in enumerate([("tr", "trend", ARANCIO), (ID_STOP, f"trend + stop {pct}", BLU)]):
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
    for j, sl in enumerate(slugs):
        dd = [v(sl, f"{rid}_dd") * 100 for rid, _ in regole]
        migl = int(np.argmin(dd))
        for q, ((rid, nome_r), col) in enumerate(zip(regole, [GRIGIO, ARANCIO, BLU])):
            ax.bar(j + (q - 1) * 0.27, dd[q], width=0.25, color=col, hatch="//" if q == migl else None, edgecolor="white")
            ax.text(j + (q - 1) * 0.27, dd[q], f"{it(dd[q])}%", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(range(len(slugs)), [nomi[sl] for sl in slugs])
    ax.set_ylabel("perdita massima dal picco")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Patch(color=GRIGIO, label="buy & hold"), Patch(color=ARANCIO, label="trend"),
                       Patch(color=BLU, label=f"trend + stop {pct}"),
                       Patch(facecolor="white", edgecolor="#555", hatch="//", label="tratteggio: la perdita più piccola")], fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_perdita_massima.png")
    plt.close(fig)

    # --- Figura 4: scimmie ----------------------------------------------------------------------------------------------
    sc = pd.read_csv(R / "scimmie_finali.csv")
    fig, assi = plt.subplots(1, len(slugs), figsize=(5.2 * len(slugs), 4.8), squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        col = f"{sl}_{ID_STOP}"
        if col in sc:
            ax.hist(sc[col], bins=50, color=GRIGIO, alpha=0.7)
        for rid, etichetta, c, ls in [(ID_STOP, f"trend + stop {pct}", BLU, "-"), ("tr", "trend", ARANCIO, "--"), ("bh", "buy & hold", "#333", ":")]:
            ax.axvline(v(sl, f"{rid}_{M}_finale"), color=c, ls=ls, lw=2.2, label=etichetta)
        ax.set_title(nomi[sl], fontsize=12)
        ax.set_xlabel("valore finale netto di 1.000 €")
        ax.set_yticks([])
        ax.grid(axis="y", visible=False)
    assi[0][-1].legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)

    # --- Figura 5: soglie -----------------------------------------------------------------------------------------------
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.8))
    xs = [int(round(x * 100)) for x in IDS]
    asse = np.arange(len(xs) + 1)
    etich = [f"{x}%" for x in xs] + ["nessuno"]
    for sl, col, mk in zip(slugs, [BLU, ARANCIO, GRIGIO], ["o", "s", "^"]):
        ids = [f"s{x}" for x in xs] + ["tr"]
        a1.plot(asse, [v(sl, f"{i}_{M}_cagr") * 100 for i in ids], color=col, marker=mk, lw=2, label=nomi[sl])
    for q, (sl, col) in enumerate(zip(slugs, [BLU, ARANCIO, GRIGIO])):
        a2.bar(asse[:-1] + (q - 1) * 0.26, [v(sl, f"s{x}_n_stop") for x in xs], width=0.24, color=col, label=nomi[sl])
    for a, y in ((a1, "rendimento annuo netto"), (a2, "stop loss scattati in tutto il periodo")):
        a.set_xticks(asse if a is a1 else asse[:-1], etich if a is a1 else etich[:-1])
        a.set_xlabel("soglia dello stop loss")
        a.set_ylabel(y)
    a1.yaxis.set_major_formatter(lambda y, _: f"{y:.1f}%".replace(".", ","))
    a2.set_yticks(range(0, 4))
    a2.grid(axis="x", visible=False)
    a1.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_soglie.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
