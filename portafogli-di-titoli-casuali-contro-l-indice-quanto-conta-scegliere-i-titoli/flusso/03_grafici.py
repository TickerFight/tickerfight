"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_curve.png         lo SPY, l'universo a pesi uguali e la fascia dei portafogli casuali da K_PRINCIPALE titoli
  fig2_fascia_per_k.png  fascia 5°-95° percentile del rendimento annuo per numero di titoli, con SPY e universo
  fig3_quote.png         quota di portafogli che batte lo SPY e l'universo a pesi uguali, per numero di titoli
  fig4_persistenza.png   eccesso di rendimento sullo SPY nelle due metà del periodo, portafogli da K_PRINCIPALE titoli
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


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    kp = config.K_PRINCIPALE

    # --- Figura 1: curve ---------------------------------------------------------------------------------------------
    c = pd.read_csv(R / "curve.csv", parse_dates=["Date"])
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.fill_between(c.Date, c.fascia_bassa, c.fascia_alta, color=ARANCIO, alpha=0.22, lw=0,
                    label=f"{kp} titoli a caso: dal 5° al 95° percentile")
    ax.plot(c.Date, c.fascia_mediana, color=ARANCIO, lw=1.6, ls="--", label=f"{kp} titoli a caso: mediana")
    ax.plot(c.Date, c.universo_pesi_uguali, color=GRIGIO, lw=1.6, label="Tutto l'universo a pesi uguali")
    ax.plot(c.Date, c.spy, color=BLU, lw=2.4, label="SPY (S&P 500)")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro investito (scala logaritmica)")
    ax.legend(loc="upper left", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_curve.png")
    plt.close(fig)

    # --- Figura 2: fascia per k --------------------------------------------------------------------------------------
    s = pd.read_csv(R / "riassunto_k.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = np.arange(len(s))
    for xi, r in zip(x, s.itertuples()):
        ax.vlines(xi, r.cagr_p5 * 100, r.cagr_p95 * 100, color=ARANCIO, lw=14, alpha=0.35)
        ax.plot(xi, r.cagr_med * 100, "o", color=ARANCIO, ms=9)
        ax.text(xi + 0.14, r.cagr_p95 * 100, f"{r.cagr_p95 * 100:.1f}%", va="center", fontsize=10, color=ARANCIO)
        ax.text(xi + 0.14, r.cagr_p5 * 100, f"{r.cagr_p5 * 100:.1f}%", va="center", fontsize=10, color=ARANCIO)
    ax.axhline(V["spy_cagr"]["valore"] * 100, color=BLU, lw=2.2, label="SPY")
    ax.axhline(V["ew_cagr"]["valore"] * 100, color=GRIGIO, lw=1.6, ls="--", label="Tutto l'universo a pesi uguali")
    ax.set_xticks(x, [f"{k} titoli" for k in s.k])
    ax.set_xlim(-0.5, len(s) - 0.4)
    ax.set_ylabel("Rendimento annuo composto (%)")
    ax.legend(loc="lower right", fontsize=10)
    fig.savefig(config.FIGURE / "fig2_fascia_per_k.png")
    plt.close(fig)

    # --- Figura 3: quote ---------------------------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    w = 0.36
    b1 = ax.bar(x - w / 2, s.quota_spy * 100, w, color=BLU, label="contro lo SPY")
    b2 = ax.bar(x + w / 2, s.quota_ew * 100, w, color=GRIGIO, label="contro l'universo a pesi uguali")
    for q, b in ((s.quota_spy, b1), (s.quota_ew, b2)):
        for qi, bi in zip(q, b):
            if qi > 0.5:
                bi.set_hatch("//")
                bi.set_edgecolor("white")
            ax.text(bi.get_x() + bi.get_width() / 2, qi * 100 + 1.5, f"{qi * 100:.0f}%", ha="center", fontsize=10)
    ax.axhline(50, color="black", lw=1)
    ax.set_xticks(x, [f"{k} titoli" for k in s.k])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Portafogli che battono il confronto (%)")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_quote.png")
    plt.close(fig)

    # --- Figura 4: persistenza ---------------------------------------------------------------------------------------
    p = pd.read_csv(R / "persistenza.csv")
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    ax.scatter(p.eccesso_h1 * 100, p.eccesso_h2 * 100, s=8, color=BLU, alpha=0.45)
    ax.axhline(0, color="black", lw=1)
    ax.axvline(0, color="black", lw=1)
    ax.set_xlabel("Prima metà: rendimento annuo meno SPY (punti percentuali)")
    ax.set_ylabel("Seconda metà: rendimento annuo meno SPY (punti percentuali)")
    ax.text(0.03, 0.96, f"correlazione {V['corr_meta']['valore']:.2f}".replace(".", ","), transform=ax.transAxes, va="top", fontsize=11)
    fig.savefig(config.FIGURE / "fig4_persistenza.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
