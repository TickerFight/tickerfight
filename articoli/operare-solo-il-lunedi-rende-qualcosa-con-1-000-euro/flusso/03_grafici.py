"""Passo 3 - Grafici. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_media_giorni.png   rendimento medio di una seduta per giorno della settimana, per strumento
  fig2_lordo_netto.png    regola del lunedì: valore finale di 1.000 euro, lordo e netto nei tre scenari, contro il buy & hold netto
  fig3_scimmie.png        valore finale lordo di ogni giorno meno la mediana delle scimmie, con la loro fascia
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
RID = [x for x, _, _ in config.GIORNI]
ETI = [n[:3] for _, n, _ in config.GIORNI]


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

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 4.8), sharey=True, squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        vals = [v(sl, f"{r}_media") * 100 for r in RID]
        ax.bar(pos, vals, color=[ARANCIO if r == "d0" else BLU for r in RID])
        ax.axhline(v(sl, "media_tutti") * 100, color=GRIGIO, ls="--", lw=1.5, label="media di tutte le sedute")
        ax.set_xticks(pos, ETI)
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("rendimento medio di una seduta (%)")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("Rendimento medio di una seduta, per giorno della settimana (lunedì in arancione)", y=1.02)
    fig.savefig(config.FIGURE / "fig1_media_giorni.png"); plt.close(fig)

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 4.8), sharey=True, squeeze=False)
    scen = [("lordo", "lordo", GRIGIO), ("c0", "netto, commissione zero", BLU), ("c1", "netto, 2 euro a ordine", ARANCIO), ("c2", "netto, 0,1%", "#5b8fc9")]
    for ax, sl in zip(assi[0], slugs):
        ax.bar(np.arange(4), [v(sl, f"d0_{sid}_finale") for sid, _, _ in scen], color=[c for _, _, c in scen])
        ax.axhline(v(sl, "bh_c0_finale"), color="black", ls="--", lw=1.4, label="buy & hold, netto")
        ax.axhline(config.CAPITALE, color=GRIGIO, ls=":", lw=1, label="capitale iniziale")
        ax.set_xticks(np.arange(4), ["lordo", "0 euro", "2 euro", "0,1%"])
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("valore finale di 1.000 euro (euro)")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("Solo il lunedì: dal lordo al netto", y=1.02)
    fig.savefig(config.FIGURE / "fig2_lordo_netto.png"); plt.close(fig)

    fig, assi = plt.subplots(1, ns, figsize=(5.2 * ns, 4.8), squeeze=False)
    for ax, sl in zip(assi[0], slugs):
        med = np.array([v(sl, f"{r}_sc_mediana") for r in RID])
        lo = np.array([v(sl, f"{r}_sc_p5") for r in RID]) - med
        hi = np.array([v(sl, f"{r}_sc_p95") for r in RID]) - med
        reale = np.array([v(sl, f"{r}_lordo_finale") for r in RID]) - med
        ax.fill_between(pos, lo, hi, color=GRIGIO, alpha=0.3, label="scimmie, dal 5° al 95° percentile")
        ax.plot(pos, reale, color=BLU, marker="o", label="giorno fisso")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(pos, ETI)
        ax.set_title(nomi[sl], fontsize=12)
    assi[0][0].set_ylabel("euro finali (lordo) meno la mediana delle scimmie")
    assi[0][0].legend(fontsize=9)
    fig.suptitle("Ogni giorno contro le scimmie (stesso numero di sedute investite)", y=1.02)
    fig.savefig(config.FIGURE / "fig3_scimmie.png"); plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
