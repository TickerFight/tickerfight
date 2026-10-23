"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_costi_regole.png     rendimento annuo di ogni regola al crescere del costo per operazione
  fig2_proporzionalita.png  perdita osservata contro cambi all'anno x costo massimo (la diagonale è la proporzionalità perfetta)
  fig3_ribilanciamento.png  perdita di rendimento annuo del 50/50 per frequenza di ribilanciamento, costo massimo
  fig4_scimmie.png          rendimento annuo mediano delle scimmie al crescere della frequenza di cambio, per costo
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


def pct(x, _=None):
    return f"{x:.0f}%".replace(".", ",")


def spaziatura(valori: dict, gap: float) -> dict:
    """Posizioni verticali delle etichette: stesso ordine dei valori, distanza minima `gap` (solo per leggibilità)."""
    ordine = sorted(valori, key=valori.get)
    pos = {}
    ultimo = -1e9
    for k in ordine:
        ultimo = max(valori[k], ultimo + gap)
        pos[k] = ultimo
    return pos


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    S = pd.read_csv(R / "costi_regole.csv")
    RB = pd.read_csv(R / "ribilanciamento.csv")
    SC = pd.read_csv(R / "scimmie.csv")

    # --- Figura 1: il rendimento al crescere del costo ---------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))
    fine = {i: S[S["id"] == i]["cagr"].iloc[-1] * 100 for i in config.STRATEGIE}
    et = spaziatura(fine, 0.75)
    for i, (nome, _) in config.STRATEGIE.items():
        d = S[S["id"] == i]
        if i == config.ID_BH:
            col, lw, ls, z = BLU, 3.2, "-", 3
        elif i == "ritorno":
            col, lw, ls, z = ARANCIO, 3.2, "--", 3
        else:
            col, lw, ls, z = GRIGIO, 1.6, "-", 1
        ax.plot(d["costo"] * 100, d["cagr"] * 100, color=col, lw=lw, ls=ls, marker="o", ms=4, zorder=z)
        ax.text(d["costo"].max() * 100 + 0.02, et[i], nome, va="center", fontsize=9.5, color=col if col != GRIGIO else "#444")
    ax.axhline(0, color="#555", lw=1)
    ax.set_xlim(-0.01, config.COSTO_MAX * 100 + 0.40)
    ax.set_xticks([c * 100 for c in config.COSTI], [f"{c * 100:g}".replace(".", ",") for c in config.COSTI])
    ax.set_xlabel("costo per ogni acquisto o vendita (% del valore scambiato)")
    ax.set_ylabel("rendimento annuo composto")
    ax.yaxis.set_major_formatter(pct)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_costi_regole.png")
    plt.close(fig)

    # --- Figura 2: perdita contro cambi x costo ---------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 6))
    lo = S[S["costo"] == 0].set_index("id")
    hi = S[S["costo"] == config.COSTO_MAX].set_index("id")
    x = (lo["cambi_anno"] * config.COSTO_MAX * 100).reindex(list(config.STRATEGIE))
    y = ((lo["cagr"] - hi["cagr"]) * 100).reindex(list(config.STRATEGIE))
    m = max(x.max(), y.max()) * 1.08
    ax.plot([0, m], [0, m], color=ARANCIO, lw=2.2, ls="--", zorder=1)
    ax.scatter(x, y, color=BLU, s=60, zorder=3)
    et2 = spaziatura(y.to_dict(), m * 0.045)
    for i in x.index:
        ax.annotate(config.STRATEGIE[i][0].replace("Prezzo sopra la ", "Sopra la "), (x[i], y[i]), xytext=(x[i] + m * 0.06, et2[i]), textcoords="data",
                    fontsize=8.5, color="#333", va="center", arrowprops=dict(arrowstyle="-", color=GRIGIO, lw=0.8, shrinkA=0, shrinkB=3))
    ax.set_xlabel("cambi all'anno × costo massimo (punti percentuali)")
    ax.set_ylabel("perdita di rendimento annuo osservata (punti percentuali)")
    ax.set_xlim(0, m)
    ax.set_ylim(0, m)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_proporzionalita.png")
    plt.close(fig)

    # --- Figura 3: ribilanciamento -----------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    nomi = list(config.RIBILANCIAMENTI)
    perd = []
    for f in nomi:
        d = RB[RB["frequenza"] == f].set_index("costo")["cagr"]
        perd.append((d.loc[0.0] - d.loc[config.COSTO_MAX]) * 100)
    ax.bar(range(len(nomi)), perd, color=[ARANCIO, GRIGIO, BLU], width=0.55)
    for x_, v in enumerate(perd):
        ax.text(x_, v + max(perd) * 0.02, f"{v:.2f}".replace(".", ",") + " pp", ha="center", fontsize=12)
    ax.set_xticks(range(len(nomi)), [f"ogni {RB[RB['frequenza'] == f]['ogni_sedute'].iloc[0]} sedute\n({f})" if RB[RB['frequenza'] == f]['ogni_sedute'].iloc[0] > 1 else f"ogni seduta\n({f})" for f in nomi])
    ax.set_ylabel("perdita di rendimento annuo (punti percentuali)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_ribilanciamento.png")
    plt.close(fig)

    # --- Figura 4: scimmie --------------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    probs = sorted(SC["prob_cambio"].unique())
    colori = {0.0: BLU, config.COSTO_PROVA: GRIGIO, config.COSTO_MAX: ARANCIO}
    for costo, col in colori.items():
        d = SC[np.isclose(SC["costo"], costo)].sort_values("prob_cambio")
        ax.plot(d["prob_cambio"] * 100, d["cagr_mediano"] * 100, color=col, lw=3 if costo else 2.4, marker="o",
                ls="--" if costo == config.COSTO_MAX else "-", label=("costo " + f"{costo * 100:.1f}%".replace(".", ",")) if costo else "senza costi")
    ax.axhline(0, color="#555", lw=1)
    ax.set_xscale("log")
    ax.set_xticks([p * 100 for p in probs], [f"{p * 100:g}%".replace(".", ",") for p in probs])
    ax.set_xlabel("probabilità di cambiare posizione in ogni seduta")
    ax.set_ylabel("rendimento annuo mediano delle scimmie")
    ax.yaxis.set_major_formatter(pct)
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
