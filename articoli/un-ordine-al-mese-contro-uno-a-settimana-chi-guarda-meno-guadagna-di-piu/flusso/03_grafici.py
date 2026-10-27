"""Passo 3 - Grafici. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_lordo_netto.png   rendimento annuo di buy & hold e delle tre frequenze, lordo e netto (2 euro), per strumento
  fig2_ordini_costi.png  ordini all'anno e euro pagati ogni anno in commissioni e tasse, per frequenza
  fig3_differenza.png    rendimento annuo settimanale meno mensile nei quattro scenari, per strumento
  fig4_scimmie.png       valore finale della regola meno la mediana delle scimmie, con la fascia delle scimmie
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
RID = [x for x, _ in config.FREQUENZE]
ETI = {"g": "ogni seduta", "s": "settimana", "m": "mese"}


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
    pos = np.arange(len(RID))

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), sharey=True, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        ax.bar(pos - 0.2, [v(sl, f"{r}_lordo_cagr") * 100 for r in RID], 0.4, color=GRIGIO, label="lordo")
        ax.bar(pos + 0.2, [v(sl, f"{r}_{M}_cagr") * 100 for r in RID], 0.4, color=BLU, label="netto, 2 euro a ordine")
        ax.axhline(v(sl, f"bh_{M}_cagr") * 100, color=ARANCIO, ls="--", lw=1.6, label="buy & hold, netto")
        ax.set_xticks(pos, [ETI[r] for r in RID])
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("rendimento annuo composto (%)")
    assi[0][0].legend(fontsize=9, loc="upper right")
    fig.suptitle("Quando si guarda il segnale: rendimento annuo lordo e netto", y=1.02)
    fig.savefig(config.FIGURE / "fig1_lordo_netto.png"); plt.close(fig)

    fig, assi = plt.subplots(1, 2, figsize=(11, 4.8))
    larg = 0.25
    for j, (sl, col) in enumerate(zip(slugs, (BLU, ARANCIO, GRIGIO))):
        assi[0].bar(pos + (j - 1) * larg, [v(sl, f"{r}_ordini_anno") for r in RID], larg, color=col, label=nomi[sl])
        assi[1].bar(pos + (j - 1) * larg, [(v(sl, f"{r}_{M}_costo") + v(sl, f"{r}_{M}_tasse")) / v(sl, "anni") for r in RID], larg, color=col)
    for ax in assi:
        ax.set_xticks(pos, [ETI[r] for r in RID])
    assi[0].set_ylabel("ordini all'anno"); assi[1].set_ylabel("euro l'anno: commissioni più tasse (2 euro a ordine)")
    assi[0].legend(fontsize=9)
    fig.suptitle("Quanti ordini e quanto si paga, per frequenza", y=1.02)
    fig.savefig(config.FIGURE / "fig2_ordini_costi.png"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 5))
    scen = [("lordo", "lordo"), ("c0", "commissione zero"), ("c1", "2 euro"), ("c2", "0,1%")]
    for j, (sl, col) in enumerate(zip(slugs, (BLU, ARANCIO, GRIGIO))):
        ax.bar(np.arange(4) + (j - 1) * larg, [v(sl, f"dsm_{sid}") * 100 for sid, _ in scen], larg, color=col, label=nomi[sl])
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(np.arange(4), [n for _, n in scen])
    ax.set_ylabel("settimanale meno mensile (punti l'anno)")
    ax.set_title("La differenza c'è già prima dei costi")
    ax.legend(fontsize=9)
    fig.savefig(config.FIGURE / "fig3_differenza.png"); plt.close(fig)

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 5), squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        med = np.array([v(sl, f"{r}_sc_mediana") for r in RID])
        lo = np.array([v(sl, f"{r}_sc_p5") for r in RID]) - med
        hi = np.array([v(sl, f"{r}_sc_p95") for r in RID]) - med
        reale = np.array([v(sl, f"{r}_{M}_finale") for r in RID]) - med
        ax.fill_between(pos, lo, hi, color=GRIGIO, alpha=0.3, label="scimmie, dal 5° al 95° percentile")
        ax.plot(pos, reale, color=BLU, marker="o", label="regola")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(pos, [ETI[r] for r in RID])
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("euro finali meno la mediana delle scimmie")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("La regola contro le scimmie (stessa durata investita, stesso numero di periodi)", y=1.02)
    fig.savefig(config.FIGURE / "fig4_scimmie.png"); plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
