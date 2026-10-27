"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_relativa.png    valore di 100 dollari sulle piccole diviso quello sulle grandi, nel tempo, per coppia
  fig2_decenni.png     differenza di rendimento annuo composto per decennio, per coppia
  fig3_dieci_anni.png  differenza di rendimento nelle finestre mobili di dieci anni, per coppia
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


def breve(nome: str) -> str:
    return nome.split(" (")[0]


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    coppie = json.loads((R / "coppie_usate.json").read_text(encoding="utf-8"))
    tab = pd.read_csv(R / "coppie.csv")
    serie = {c["slug"]: pd.read_csv(R / f"serie_{c['slug']}.csv") for c in coppie}

    # Figura 1: performance relativa
    fig, ax = plt.subplots(figsize=(9.5, 5))
    colori = [BLU, ARANCIO, GRIGIO]
    for c, col in zip(coppie, colori):
        s = serie[c["slug"]]
        rel = np.exp(np.cumsum(np.log1p(s["piccole"]) - np.log1p(s["grandi"]))) * 100
        ax.plot(pd.to_datetime(s["data"]), rel, color=col, lw=1.8, label=breve(c["nome"]))
    ax.axhline(100, color="black", lw=0.8)
    ax.set_ylabel("piccole rispetto alle grandi (partenza = 100)")
    ax.legend(loc="best")
    fig.savefig(config.FIGURE / "fig1_relativa.png")
    plt.close(fig)

    # Figura 2: decenni
    colonne = [c for c in ("dec1990", "dec2000", "dec2010", "dec2020") if c in tab.columns]
    etichette = {"dec1990": "anni Novanta", "dec2000": "anni Duemila", "dec2010": "anni Dieci", "dec2020": "dal 2020"}
    fig, ax = plt.subplots(figsize=(9.5, 5))
    larg = 0.8 / max(1, len(coppie))
    for k, (c, col) in enumerate(zip(coppie, colori)):
        riga = tab.iloc[k]
        vals = [riga[cl] * 100 if pd.notna(riga[cl]) else np.nan for cl in colonne]
        pos = np.arange(len(colonne)) + k * larg
        ax.bar(pos, vals, width=larg, color=col, label=breve(c["nome"]))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(np.arange(len(colonne)) + larg * (len(coppie) - 1) / 2)
    ax.set_xticklabels([etichette[c] for c in colonne])
    ax.set_ylabel("piccole meno grandi (punti percentuali all'anno)")
    ax.legend(loc="best")
    fig.savefig(config.FIGURE / "fig2_decenni.png")
    plt.close(fig)

    # Figura 3: finestre mobili di dieci anni
    fig, assi = plt.subplots(len(coppie), 1, figsize=(9.5, 3.2 * len(coppie)), sharex=True, squeeze=False)
    for ax, c in zip(assi.ravel(), coppie):
        s = serie[c["slug"]]
        lp, lg = np.log1p(s["piccole"].values), np.log1p(s["grandi"].values)
        w = 120
        if len(lp) < w:
            ax.axis("off")
            continue
        cp, cg = np.concatenate([[0], np.cumsum(lp)]), np.concatenate([[0], np.cumsum(lg)])
        diff = ((cp[w:] - cp[:-w]) - (cg[w:] - cg[:-w])) / (w / 12) * 100          # punti log all'anno
        x = pd.to_datetime(s["data"]).iloc[w - 1:].values
        ax.fill_between(x, 0, diff, where=diff >= 0, color=BLU, alpha=0.8, lw=0)
        ax.fill_between(x, 0, diff, where=diff < 0, color=ARANCIO, alpha=0.8, lw=0)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(breve(c["nome"]), fontsize=11)
        ax.set_ylabel("punti all'anno")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_dieci_anni.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
