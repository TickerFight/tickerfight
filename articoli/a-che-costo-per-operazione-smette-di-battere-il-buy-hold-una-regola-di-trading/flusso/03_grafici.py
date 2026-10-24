"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_pareggio.png      costo di pareggio (Sharpe) di ogni regola
  fig2_cambi_pareggio.png  cambi all'anno contro costo di pareggio
  fig3_curve.png         Sharpe al crescere del costo: dove le curve incontrano il buy & hold
  fig4_meta.png          costo di pareggio nelle due metà del periodo
  fig5_scimmie.png       Sharpe delle scimmie contro buy & hold e contro il prezzo sopra la media a 50 giorni
"""
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


def virg(x, dec=2):
    return f"{x:.{dec}f}".replace(".", ",")


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    P = pd.read_csv(R / "pareggio.csv").sort_values("sharpe_tutto")
    C = pd.read_csv(R / "curve_sharpe.csv")
    SC = pd.read_csv(R / "scimmie.csv")
    tip = config.COSTO_TIPICO * 100
    cap = config.COSTO_MAX_RICERCA * 100

    # Figura 1: barre orizzontali del costo di pareggio
    fig, ax = plt.subplots(figsize=(10, 6))
    y = np.arange(len(P))
    val = P["sharpe_tutto"].to_numpy() * 100
    col = [ARANCIO if v < tip else BLU for v in val]
    ax.barh(y, val, color=col, height=0.6)
    for k, (v, st) in enumerate(zip(val, P["sharpe_tutto_stato"])):
        t = "già sotto a costo zero" if st == "gia_sotto" else (f"oltre {cap:g}%" if st == "oltre" else virg(v) + "%")
        ax.text(v + cap * 0.01, k, t, va="center", fontsize=10)
    ax.axvline(tip, color="#444", lw=1.6, ls="--")
    ax.text(tip + cap * 0.01, len(P) - 0.45, "costo tipico " + virg(tip, 1) + "%", fontsize=10, color="#444")
    ax.set_yticks(y, [n for n in P["nome"]])
    ax.set_xlim(0, cap * 0.45)
    ax.set_xlabel("costo per cambio a cui lo Sharpe scende sotto quello del buy & hold (%)")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_pareggio.png")
    plt.close(fig)

    # Figura 2: cambi all'anno contro pareggio
    fig, ax = plt.subplots(figsize=(8.5, 5.8))
    ax.scatter(P["cambi_anno"], P["sharpe_tutto"] * 100, color=BLU, s=70, zorder=3)
    for _, r in P.iterrows():
        ax.annotate(r["nome"].replace("Prezzo sopra la media a ", "Media ").replace(" giorni", ""), (r["cambi_anno"], r["sharpe_tutto"] * 100),
                    xytext=(6, 4), textcoords="offset points", fontsize=8.5, color="#333")
    ax.axhline(tip, color=ARANCIO, lw=2, ls="--")
    ax.set_xscale("log")
    ax.set_xlabel("cambi di posizione all'anno (scala logaritmica)")
    ax.set_ylabel("costo di pareggio sullo Sharpe (%)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_cambi_pareggio.png")
    plt.close(fig)

    # Figura 3: curve dello Sharpe
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    bh = C[C["id"] == config.ID_BH]
    ax.plot(bh["costo"] * 100, bh["sharpe"], color=BLU, lw=3.2, label="Buy & hold")
    for i, col, ls in (("sma10", ARANCIO, "-"), ("sma50", ARANCIO, "--"), ("sma200", GRIGIO, "-")):
        d = C[C["id"] == i]
        ax.plot(d["costo"] * 100, d["sharpe"], color=col, lw=2.4, ls=ls, label=d["nome"].iloc[0])
    ax.axvline(tip, color="#444", lw=1, ls=":")
    ax.set_xlabel("costo per cambio (% del valore scambiato)")
    ax.set_ylabel("Sharpe")
    ax.legend(loc="lower left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_curve.png")
    plt.close(fig)

    # Figura 4: due metà
    fig, ax = plt.subplots(figsize=(10, 5.8))
    Q = pd.read_csv(R / "pareggio.csv").sort_values("cambi_anno")
    x = np.arange(len(Q))
    ax.bar(x - 0.2, Q["sharpe_prima"] * 100, width=0.4, color=BLU, label="prima metà del periodo")
    ax.bar(x + 0.2, Q["sharpe_seconda"] * 100, width=0.4, color=ARANCIO, label="seconda metà")
    ax.set_xticks(x, [n.replace("Prezzo sopra la media a ", "Media ").replace(" giorni", "").replace("Ritorno alla media nel trend", "Ritorno alla media") for n in Q["nome"]], rotation=35, ha="right", fontsize=10)
    ax.set_ylabel("costo di pareggio sullo Sharpe (%)")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_meta.png")
    plt.close(fig)

    # Figura 5: scimmie
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.hist(SC["sharpe_lordo"], bins=40, color=GRIGIO, alpha=0.85)
    bh0 = float(bh[bh["costo"] == 0]["sharpe"].iloc[0])
    m0 = float(C[(C["id"] == config.ID_MEDIA) & (C["costo"] == 0)]["sharpe"].iloc[0])
    ax.axvline(bh0, color=BLU, lw=3, label="Buy & hold")
    ax.axvline(m0, color=ARANCIO, lw=3, ls="--", label="Prezzo sopra la media a 50 giorni")
    ax.set_xlabel("Sharpe a costo zero")
    ax.set_ylabel("numero di scimmie")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig5_scimmie.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
