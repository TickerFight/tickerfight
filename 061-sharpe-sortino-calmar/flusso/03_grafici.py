"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_classifiche.png      il posto di ogni regola nelle tre classifiche (Sharpe, Sortino, Calmar), intero periodo
  fig2_persistenza.png      correlazione di rango tra la classifica di un decennio e quella del successivo, per metrica
  fig3_bootstrap.png        quota di serie ricampionate in cui vince la stessa regola dell'intero periodo
  fig4_scimmie.png          le tre metriche delle scimmie (regole casuali) e il filtro a 200 giorni
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
METRICHE = ("sharpe", "sortino", "calmar")
NOMI = {"sharpe": "Sharpe", "sortino": "Sortino", "calmar": "Calmar"}
COL = {"sharpe": BLU, "sortino": GRIGIO, "calmar": ARANCIO}


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    S = pd.read_csv(R / "strategie_campione.csv")
    C = pd.read_csv(R / "correlazioni_blocchi.csv")
    B = pd.read_csv(R / "bootstrap_vincitori.csv")
    M = pd.read_csv(R / "scimmie.csv")

    # --- Figura 1: la stessa regola, tre posti ------------------------------------------------------------------
    posti = S[[f"posto_{k}" for k in METRICHE]].to_numpy()
    spread = posti.max(axis=1) - posti.min(axis=1)
    k_sp = int(np.argmax(spread))
    k_bh = int(S.index[S["id"] == config.ID_BH][0])
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for k in range(len(S)):
        if k == k_bh:
            col, lw, z = BLU, 3.2, 3
        elif k == k_sp and spread[k_sp] > 0:
            col, lw, z = ARANCIO, 3.2, 3
        else:
            col, lw, z = GRIGIO, 1.5, 1
        ax.plot([0, 1, 2], posti[k], color=col, lw=lw, marker="o", zorder=z, ls="--" if col == ARANCIO else "-")
        ax.text(-0.06, posti[k][0], f"{S['nome'][k]}  {posti[k][0]:.0f}", ha="right", va="center", fontsize=9.5, color=col if col != GRIGIO else "#444")
        ax.text(2.06, posti[k][2], f"{posti[k][2]:.0f}  {S['nome'][k]}", ha="left", va="center", fontsize=9.5, color=col if col != GRIGIO else "#444")
    ax.set_ylim(len(S) + 0.5, 0.5)
    ax.set_xlim(-0.05, 2.05)
    ax.set_xticks([0, 1, 2], ["Sharpe", "Sortino", "Calmar"], fontsize=13)
    ax.xaxis.tick_top()
    ax.set_yticks([])
    ax.grid(axis="x", visible=False)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_classifiche.png")
    plt.close(fig)

    # --- Figura 2: persistenza tra decenni consecutivi --------------------------------------------------------------
    P = C[C["tipo"] == "spearman_consecutivi"]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    rng = np.random.default_rng(0)
    for x, km in enumerate(METRICHE):
        v = P.loc[P["coppia"] == km, "tau_sh_so"].to_numpy()
        ax.bar(x, np.nanmean(v), color=COL[km], width=0.55, alpha=0.9, zorder=2)
        ax.scatter(x + rng.uniform(-0.15, 0.15, len(v)), v, color="white", edgecolor="#333", s=34, zorder=3)
    ax.axhline(0, color="#555", lw=1.2)
    ax.set_xticks(range(3), [NOMI[k] for k in METRICHE])
    ax.set_ylabel("correlazione di rango tra un decennio e il successivo")
    ax.set_ylim(-1, 1)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_persistenza.png")
    plt.close(fig)

    # --- Figura 3: bootstrap --------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.0))
    q = B["quota_stesso_vincitore"].to_numpy() * 100
    ax.bar(range(3), q, color=[COL[k] for k in METRICHE], width=0.55)
    for x, v in enumerate(q):
        ax.text(x, v + 1.5, f"{v:.0f}%", ha="center", fontsize=12)
    ax.set_xticks(range(3), [NOMI[k] for k in METRICHE])
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    ax.set_ylabel("serie ricampionate in cui vince la stessa regola")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_bootstrap.png")
    plt.close(fig)

    # --- Figura 4: le scimmie ---------------------------------------------------------------------------------------------
    iq = int(S.index[S["id"] == config.ID_FILTRO][0])
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, km in zip(axs, METRICHE):
        ax.hist(M[km], bins=30, color=GRIGIO, alpha=0.8)
        ax.axvline(S[km][iq], color=ARANCIO, lw=2.6, ls="--")
        perc = (M[km] < S[km][iq]).mean() * 100
        ax.set_title(f"{NOMI[km]}: il filtro batte il {perc:.1f}% delle scimmie".replace(".", ","), fontsize=10.5)
        ax.set_yticks([])
        ax.grid(False)
        ax.spines["left"].set_visible(False)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
