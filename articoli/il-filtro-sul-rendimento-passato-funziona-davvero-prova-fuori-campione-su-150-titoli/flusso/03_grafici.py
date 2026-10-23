"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e dati/ e salva i PNG in figure/.

  fig1_portafogli.png        valore giorno per giorno: buy & hold, regola su tutti, strategia con il filtro
  fig2_gruppi.png            quota di titoli su cui la regola batte il buy & hold, per gruppo di rendimento passato
  fig3_valori_finali.png     valore finale dei tre portafogli, fuori campione e nel periodo di riferimento
  fig4_scelta_casuale.png    valore finale con la regola assegnata a caso a un terzo dei titoli, contro il filtro
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO, VERDE = "#1f5fa8", "#c9610a", "#8a8a8a", "#2a7f3f"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})


def euro(x, _=None):
    return f"{x:,.0f}".replace(",", ".") + " €"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    R = config.RISULTATI
    tab = pd.read_csv(R / "titoli.csv")
    cur = pd.read_csv(R / "curva_portafoglio.csv", parse_dates=["data"])
    cas = pd.read_csv(R / "simulazioni_casuali.csv")["finale_portafoglio"].to_numpy()
    rif = pd.read_csv(config.FILE_RIFERIMENTO)
    n = len(tab)

    # --- Figura 1: portafogli ---------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.axhline(config.CAPITALE * n, color=GRIGIO, lw=1, ls=":")
    ax.plot(cur["data"], cur["valore_bh"], color=ARANCIO, lw=2.0, ls="--", label="buy & hold su tutti")
    ax.plot(cur["data"], cur["valore_regola"], color=BLU, lw=1.8, label=f"regola {config.SMA_VELOCE}/{config.SMA_LENTA} su tutti")
    ax.plot(cur["data"], cur["valore_filtro"], color=VERDE, lw=2.2, label="filtro: regola solo sul terzo con rendimento passato basso")
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylabel(f"valore dei {n} titoli")
    ax.legend(ncol=1, loc="upper left", fontsize=11)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_portafogli.png")
    plt.close(fig)

    # --- Figura 2: gruppi per rendimento passato --------------------------------------------------------
    nr = len(rif)
    ordine_r = rif["ret"].rank(method="first").astype(int)
    ntr = nr // 3
    rif["gruppo"] = np.where(ordine_r <= ntr, "basso", np.where(ordine_r > nr - ntr, "alto", "medio"))
    rif["vince"] = rif["differenza"] > 0
    fig, ax = plt.subplots(figsize=(10, 5.5))
    periodi = [("fuori campione\n(fino a ottobre 2021)", tab), ("periodo di riferimento\n(2021-2026)", rif)]
    x = np.arange(2)
    larg = 0.26
    for k, (g, col, hatch, nome) in enumerate((("basso", BLU, "", "rendimento passato basso"),
                                              ("medio", GRIGIO, "", "medio"),
                                              ("alto", ARANCIO, "//", "rendimento passato alto"))):
        val = [float(d[d["gruppo"] == g]["vince"].mean()) * 100 for _, d in periodi]
        barre = ax.bar(x + (k - 1) * larg, val, larg, color=col, alpha=0.8, hatch=hatch, edgecolor="white", label=nome)
        for b, v in zip(barre, val):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.8, f"{v:.0f}%", ha="center", fontsize=11)
    ax.set_xticks(x, [p for p, _ in periodi])
    ax.set_ylabel("titoli su cui la regola batte il buy & hold")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_gruppi.png")
    plt.close(fig)

    # --- Figura 3: valori finali ------------------------------------------------------------------------
    fr_bh, fr_mm = rif["finale_bh_netto"].sum(), rif["finale_mm_netto"].sum()
    fr_fl = np.where(rif["gruppo"] == "basso", rif["finale_mm_netto"], rif["finale_bh_netto"]).sum()
    fig, assi = plt.subplots(1, 2, figsize=(13, 5.5))
    dati = [("fuori campione (fino a ottobre 2021)", n, tab["finale_bh"].sum(), tab["finale_mm"].sum(), tab["finale_filtro"].sum()),
            ("periodo di riferimento (2021-2026)", nr, fr_bh, fr_mm, fr_fl)]
    for ax, (titolo, nn, bh, mm, fl) in zip(assi, dati):
        vals = [bh, mm, fl]
        barre = ax.bar([0, 1, 2], vals, color=[ARANCIO, BLU, VERDE], alpha=0.85, edgecolor="white")
        barre[0].set_hatch("//")
        for b, v in zip(barre, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.01, f"{v:,.0f}".replace(",", "."), ha="center", fontsize=11)
        ax.axhline(config.CAPITALE * nn, color=GRIGIO, lw=1, ls=":")
        ax.set_xticks([0, 1, 2], ["buy & hold\nsu tutti", "regola\nsu tutti", "filtro"])
        ax.set_title(titolo, fontsize=12)
        ax.yaxis.set_major_formatter(euro)
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, max(vals) * 1.12)
    assi[0].set_ylabel("valore finale netto")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_valori_finali.png")
    plt.close(fig)

    # --- Figura 4: scelta casuale ----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.hist(cas, bins=40, color=GRIGIO, alpha=0.6, edgecolor="white")
    ax.axvline(tab["finale_filtro"].sum(), color=VERDE, lw=2.5, label="filtro (terzo con rendimento passato basso)")
    ax.axvline(tab["finale_bh"].sum(), color=ARANCIO, lw=2, ls="--", label="buy & hold su tutti")
    ax.axvline(tab["finale_mm"].sum(), color=BLU, lw=2, label="regola su tutti")
    ax.xaxis.set_major_formatter(euro)
    ax.set_xlabel("valore finale con la regola assegnata a caso a un terzo dei titoli")
    ax.set_ylabel("numero di sorteggi")
    ax.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scelta_casuale.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
