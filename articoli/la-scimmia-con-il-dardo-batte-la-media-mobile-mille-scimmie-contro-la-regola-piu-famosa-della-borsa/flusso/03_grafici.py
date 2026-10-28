"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_quota_scimmie_battute.png   per indice e lunghezza: quota di scimmie battute sullo Sharpe e sul rendimento annuo
  fig2_sharpe_sp500.png            distribuzione dello Sharpe delle scimmie (S&P 500) con regola e buy & hold
  fig3_rendimento_sp500.png        distribuzione del rendimento annuo delle scimmie (S&P 500) con regola e buy & hold
  fig4_perdita_massima.png         perdita massima di regola, scimmie e buy & hold per indice
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


def istogramma(x, regola, bh, etichetta, nome, fmt, titolo_x):
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.hist(x, bins=40, color=GRIGIO, alpha=0.7, label=f"{len(x):,} scimmie a blocchi".replace(",", "."))
    ax.axvline(regola, color=BLU, lw=2.5, label=f"Media a {config.LUNGHEZZA_PRINCIPALE} sedute: {fmt(regola)}")
    ax.axvline(bh, color=ARANCIO, lw=2.5, ls="--", label=f"Buy & hold: {fmt(bh)}")
    ax.set_xlabel(titolo_x)
    ax.set_ylabel("Scimmie")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / nome)
    plt.close(fig)


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    C = pd.read_csv(R / "confronti.csv")
    D = np.load(R / "distribuzioni.npz")
    sp = C[(C.ticker == config.INDICE_PRINCIPALE) & (C.lunghezza == config.LUNGHEZZA_PRINCIPALE)].iloc[0]
    nomi = {t: n.split(" (")[0] for t, n, _ in config.INDICI}

    # --- Figura 1
    fig, assi = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    larg = 0.16
    for ax, col, tit in ((assi[0], "perc_bl_sharpe", "Rapporto di Sharpe"), (assi[1], "perc_bl_cagr", "Rendimento annuo")):
        for j, n in enumerate(config.LUNGHEZZE):
            q = [C[(C.ticker == t) & (C.lunghezza == n)][col].iloc[0] * 100 for t, _, _ in config.INDICI]
            ax.bar(np.arange(len(q)) + (j - 2) * larg, q, larg * 0.92, color=BLU, alpha=0.35 + 0.15 * j, label=f"{n} sedute")
        ax.axhline(95, color=ARANCIO, lw=1.5, ls="--")
        ax.axhline(50, color=GRIGIO, lw=1)
        ax.set_xticks(range(len(config.INDICI)), [nomi[t] for t, _, _ in config.INDICI], fontsize=10)
        ax.set_title(tit)
        ax.set_ylim(0, 100)
    assi[0].set_ylabel("Scimmie battute dalla regola (%)")
    fig.legend(*assi[0].get_legend_handles_labels(), loc="lower center", ncol=5, fontsize=10, bbox_to_anchor=(0.5, -0.07))
    fig.savefig(config.FIGURE / "fig1_quota_scimmie_battute.png")
    plt.close(fig)

    istogramma(D["bl_sharpe"], sp.regola_sharpe_lordo, sp.bh_sharpe, "", "fig2_sharpe_sp500.png", lambda v: f"{v:.2f}".replace(".", ","),
               "Rapporto di Sharpe annualizzato")
    istogramma(D["bl_cagr"] * 100, sp.regola_cagr_lordo * 100, sp.bh_cagr * 100, "", "fig3_rendimento_sp500.png",
               lambda v: f"{v:.1f}%".replace(".", ","), "Rendimento annuo composto (%)")

    # --- Figura 4
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sub = C[C.lunghezza == config.LUNGHEZZA_PRINCIPALE].set_index("ticker").loc[[t for t, _, _ in config.INDICI]]
    x = np.arange(len(sub))
    for j, (col, lab, c) in enumerate((("regola_mdd_lordo", f"Media a {config.LUNGHEZZA_PRINCIPALE} sedute", BLU),
                                       ("bl_mdd_media", "Scimmie a blocchi (media)", GRIGIO), ("bh_mdd", "Buy & hold", ARANCIO))):
        ax.bar(x + (j - 1) * 0.27, sub[col] * 100, 0.25, color=c, label=lab)
    ax.set_xticks(x, [nomi[t] for t in sub.index])
    ax.set_ylabel("Perdita massima (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=10)
    fig.savefig(config.FIGURE / "fig4_perdita_massima.png")
    plt.close(fig)
    print("Figure salvate")


if __name__ == "__main__":
    main()
