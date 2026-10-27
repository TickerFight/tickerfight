"""Passo 3 - Grafici. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png      rendimento annuo al crescere degli ordini: lordo, netto con tre scenari di costo
  fig2_costi.png            commissioni e tasse pagate ogni anno, per frequenza
  fig3_soglia.png           perdita di rendimento annuo rispetto al buy & hold (2 euro) e soglia di sostenibilità
  fig4_scimmie.png          regola a cicli contro scimmie (stesso numero di periodi): differenza dal valore mediano
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white",
                     "legend.frameon": False})
R = config.RISULTATI
M = f"c{config.SCENARIO_PRINCIPALE}"
RID = [f"y{L}" for L in config.CICLI]


def breve(n):
    return n.split(" (")[0]


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    ind = json.loads((R / "strumenti_usati.json").read_text(encoding="utf-8"))
    v = lambda sl, k: V[f"{sl}_{k}"]["valore"]
    slugs = [i["slug"] for i in ind]
    nomi = {i["slug"]: breve(i["nome"]) for i in ind}
    ns = len(slugs)

    # --- Fig. 1 ------------------------------------------------------------------------------------------------------
    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), sharey=True, squeeze=False)
    scen = [("lordo", "lordo", GRIGIO, "-"), ("c0", "netto, commissione 0", BLU, ":"), ("c1", "netto, 2 euro a ordine", BLU, "-"),
            ("c2", "netto, 0,1%", ARANCIO, "-")]
    for ax, sl in zip(assi[0], slugs):
        x = [v(sl, f"{r}_ordini_nom") for r in RID]
        for sid, nome, col, ls in scen:
            y = [v(sl, f"{r}_{sid}_cagr") * 100 for r in RID]
            ax.plot(x, y, color=col, ls=ls, marker="o", label=nome)
            ax.axhline(v(sl, f"bh_{sid}_cagr") * 100, color=col, ls="--", lw=0.8, alpha=0.5)
        ax.set_xscale("log")
        ax.set_title(nomi[sl], fontsize=12)
        ax.set_xlabel("ordini all'anno (scala logaritmica)")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_ylim(-12, 20)
    assi[0][0].set_ylabel("rendimento annuo composto (%)")
    assi[0][0].legend(fontsize=9, loc="lower left")
    fig.suptitle("Il rendimento cala al crescere degli ordini (trattini: buy & hold; punti sotto il bordo = capitale esaurito)", y=1.02)
    fig.savefig(config.FIGURE / "fig1_lordo_netto.png"); plt.close(fig)

    # --- Fig. 2 ------------------------------------------------------------------------------------------------------
    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), sharey=True, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        pos = np.arange(len(RID))
        com = [v(sl, f"{r}_costo_anno") for r in RID]
        tas = [v(sl, f"{r}_tasse_anno") for r in RID]
        ax.bar(pos, com, color=ARANCIO, label="commissioni (2 euro)")
        ax.bar(pos, tas, bottom=com, color=BLU, label="tasse (26%)")
        ax.set_xticks(pos, [f"{v(sl, f'{r}_ordini_nom'):.0f}" for r in RID])
        ax.set_xlabel("ordini all'anno")
        ax.set_title(nomi[sl], fontsize=12)
        ax.axhline(config.CAPITALE * 0.02, color=GRIGIO, ls="--", lw=1)
    assi[0][0].set_ylabel("euro pagati ogni anno")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("Commissioni e tasse pagate ogni anno su 1.000 euro (trattini: 2% del capitale)", y=1.02)
    fig.savefig(config.FIGURE / "fig2_costi.png"); plt.close(fig)

    # --- Fig. 3 ------------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    for sl, col, mk in zip(slugs, (BLU, ARANCIO, GRIGIO), ("o", "s", "^")):
        ax.plot([v(sl, f"{r}_ordini_nom") for r in RID], [max(v(sl, f"{r}_{M}_perdita") * 100, 0.01) for r in RID],
                color=col, marker=mk, label=nomi[sl])
    ax.axhline(config.SOGLIA_SOSTENIBILE * 100, color="black", ls="--", lw=1.2)
    ax.text(0.97, config.SOGLIA_SOSTENIBILE * 100 * 1.15, "soglia di sostenibilità", ha="right", va="bottom",
            transform=ax.get_yaxis_transform(), fontsize=10)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("ordini all'anno (scala logaritmica)")
    ax.set_ylabel("perdita di rendimento annuo\nrispetto al buy & hold (punti, log)")
    ax.set_title("Perdita rispetto al buy & hold con 2 euro a ordine")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_soglia.png"); plt.close(fig)

    # --- Fig. 4 ------------------------------------------------------------------------------------------------------
    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), sharey=False, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        pos = np.arange(len(RID))
        med = np.array([v(sl, f"{r}_sc_mediana") for r in RID])
        lo = np.array([v(sl, f"{r}_sc_p5") for r in RID]) - med
        hi = np.array([v(sl, f"{r}_sc_p95") for r in RID]) - med
        reale = np.array([v(sl, f"{r}_{M}_finale") for r in RID]) - med
        ax.fill_between(pos, lo, hi, color=GRIGIO, alpha=0.3, label="scimmie, dal 5° al 95° percentile")
        ax.plot(pos, reale, color=BLU, marker="o", label="regola a cicli")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(pos, [f"{v(sl, f'{r}_ordini_nom'):.0f}" for r in RID])
        ax.set_xlabel("ordini all'anno")
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("euro finali meno la mediana delle scimmie")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("La regola a cicli contro le scimmie (stesso numero di periodi investiti)", y=1.02)
    fig.savefig(config.FIGURE / "fig4_scimmie.png"); plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
