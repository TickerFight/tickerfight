"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_peggiore_ogni_anno.png    rendimento del settore peggiore di ogni anno contro l'S&P 500
  fig2_capitale.png             capitale nel tempo: peggiore con senno di poi, S&P 500, regola realizzabile, media dei settori
  fig3_scimmie.png              rendimento annuo delle scimmie contro S&P 500, regola realizzabile e peggiore con senno di poi
  fig4_frequenze.png            capitale finale scegliendo il peggiore ogni anno, trimestre, mese
  fig5_lordo_netto.png          capitale finale lordo e netto di costi e tasse
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def migliaia(y, _=None):
    return f"{y:,.0f}".replace(",", ".")


def piccoli(y, _=None):
    """Etichette dell'asse logaritmico anche sotto l'unità (0,01 / 0,1 / 1 / 10 ...)."""
    s = f"{y:,.0f}" if y >= 1 else f"{y:.{max(0, int(-np.floor(np.log10(y))))}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    v = lambda k: V[k]["valore"]
    anni = pd.read_csv(R / "anni.csv")
    curve = pd.read_csv(R / "curve_capitale.csv")
    scim = pd.read_csv(R / "scimmie.csv")["cagr"].values * 100

    # --- Figura 1: il settore migliore di ogni anno contro l'indice ---
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(anni))
    ax.bar(x, anni["rendimento_peggiore"] * 100, color=BLU, label="Settore peggiore dell'anno")
    ax.plot(x, anni["rendimento_spy"] * 100, "o", color=ARANCIO, ms=5, label="S&P 500 (SPY)")
    for xi, t, r in zip(x, anni["settore_peggiore"], anni["rendimento_peggiore"]):
        ax.text(xi, min(r * 100, 0) - 1.2, t, rotation=90, ha="center", va="top", fontsize=8.5, color=BLU)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x[::2], anni["anno"].astype(str)[::2], rotation=45)
    ax.set_ylabel("Rendimento nell'anno (%)")
    ax.set_title("Ogni anno il settore peggiore perde: l'indice di solito sta sopra", loc="left")
    ax.set_ylim(bottom=anni["rendimento_peggiore"].min() * 100 * 1.25, top=max(anni["rendimento_spy"].max(), anni["rendimento_peggiore"].max()) * 100 * 1.15)
    ax.legend(loc="lower right")
    fig.savefig(config.FIGURE / "fig1_peggiore_ogni_anno.png")
    plt.close(fig)

    # --- Figura 2: crescita del capitale ---
    fig, ax = plt.subplots(figsize=(9, 5))
    x0 = [curve["anno"].iloc[0] - 1] + list(curve["anno"])
    cap0 = config.CAPITALE_INIZIALE
    for col, colore, lab, stile in (("peggiore_senno_di_poi", BLU, "Settore peggiore, con il senno di poi", "--"),
                                    ("spy", GRIGIO, "S&P 500 (SPY)", "-"),
                                    ("regola_realizzabile", ARANCIO, "Compra il perdente dell'anno prima", "-"),
                                    ("media_settori", "#7fa6d1", "Media dei nove settori", ":")):
        serie = curve[col].values
        ys = [cap0, cap0] + list(serie[1:]) if col == "regola_realizzabile" else [cap0] + list(serie)
        ax.plot(x0, ys, color=colore, ls=stile, lw=2.4 if col == "peggiore_senno_di_poi" else 2, label=lab)
    ax.set_yscale("log")
    ax.set_ylabel("Capitale (dollari, scala logaritmica)")
    ax.yaxis.set_major_formatter(mt.FuncFormatter(migliaia))
    ax.set_title(f"Da {migliaia(cap0)} dollari: sbagliare sempre il settore fa sparire il capitale", loc="left")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig2_capitale.png")
    plt.close(fig)

    # --- Figura 3: le scimmie ---
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.hist(scim, bins=60, color="#7fa6d1")
    for val, col, lab, ls in ((v("cagr_spy") * 100, GRIGIO, "S&P 500", "-"),
                              (v("cagr_copia") * 100, ARANCIO, "Perdente dell'anno prima", "-"),
                              (v("cagr_pegg") * 100, BLU, "Peggiore, senno di poi", "--")):
        ax.axvline(val, color=col, lw=2.5, ls=ls, label=f"{lab}: {val:.1f}%".replace(".", ","))
    ax.set_xlabel("Rendimento annuo composto (%)")
    ax.set_ylabel("Numero di scimmie")
    ax.set_title("Diecimila scimmie scelgono un settore a caso ogni anno", loc="left")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig3_scimmie.png")
    plt.close(fig)

    # --- Figura 4: ogni anno, trimestre, mese ---
    fig, ax = plt.subplots(figsize=(8, 4.8))
    vals = [v(f"cap_{n}") for n in ("anno", "trimestre", "mese")]
    barre = ax.bar(["Ogni anno", "Ogni trimestre", "Ogni mese"], vals, color=BLU)
    ax.axhline(v("cap_spy"), color=GRIGIO, lw=2, label="S&P 500 (SPY)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mt.FuncFormatter(piccoli))
    for b, val in zip(barre, vals):
        ax.text(b.get_x() + b.get_width() / 2, val * 1.15, (f"{val:,.4f}" if val < 1 else f"{val:,.2f}").replace(",", "§").replace(".", ",").replace("§", "."), ha="center", fontsize=11)
    ax.set_ylabel("Capitale finale (dollari, scala logaritmica)")
    ax.set_title("Più spesso si sbaglia, più il capitale si dissolve", loc="left")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig4_frequenze.png")
    plt.close(fig)

    # --- Figura 5: lordo e netto ---
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(2)
    lordo = [v("cap_pegg"), v("cap_spy")]
    netto = [v("net_pegg"), v("net_spy")]
    ax.bar(x - 0.19, lordo, 0.36, color="#7fa6d1", label="Lordo")
    ax.bar(x + 0.19, netto, 0.36, color=BLU, label="Netto di costi e tasse")
    for xi, a, b in zip(x, lordo, netto):
        ax.text(xi - 0.19, a * 1.08, migliaia(a), ha="center", fontsize=10)
        ax.text(xi + 0.19, b * 1.08, migliaia(b), ha="center", fontsize=10)
    ax.set_xticks(x, ["Settore peggiore\ncon il senno di poi", "S&P 500 (SPY)"])
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mt.FuncFormatter(migliaia))
    ax.set_ylabel("Capitale finale (dollari, scala logaritmica)")
    ax.set_title("Le perdite non si tassano, i costi sì", loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.3, 1.0))
    fig.savefig(config.FIGURE / "fig5_lordo_netto.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
