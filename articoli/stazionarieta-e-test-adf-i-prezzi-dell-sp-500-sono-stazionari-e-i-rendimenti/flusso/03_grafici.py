"""Passo 3 - Grafici dell'articolo. Legge SOLO dati/ e risultati/ e salva i PNG in figure/.

  fig1_prezzo_e_rendimenti.png   il log-prezzo sale, i rendimenti oscillano
  fig2_pvalue_finestre.png       p-value ADF per finestra: log-prezzo contro rendimenti
  fig3_volatilita_finestre.png   volatilità annualizzata per finestra
  fig4_simulazioni.png           statistica ADF di random walk e di serie stazionarie lente, e dei decenni reali
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
import funzioni as fx  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    r = fx.log_rendimenti(close)
    W = pd.read_csv(R / "adf_finestre.csv", parse_dates=["inizio", "fine"])
    S = pd.read_csv(R / "simulazioni.csv")
    etich = [str(d.year) for d in W["inizio"]]
    x = np.arange(len(W))

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
    a1.plot(close.index, close, color=BLU, lw=1.2)
    a1.set_yscale("log")
    a1.set_ylabel("S&P 500 (scala logaritmica)")
    a2.plot(r.index, r * 100, color=ARANCIO, lw=0.4)
    a2.axhline(0, color="#555", lw=1)
    a2.set_ylabel("rendimento giornaliero (%)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_prezzo_e_rendimenti.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    w = 0.38
    ax.bar(x - w / 2, np.maximum(W["p_liv"], 1e-4), w, color=BLU, label="logaritmo del prezzo")
    ax.bar(x + w / 2, np.maximum(W["p_rend"], 1e-4), w, color=ARANCIO, label="rendimenti giornalieri")
    ax.axhline(config.SOGLIA, color="#555", ls="--", lw=1.2)
    ax.text(len(W) - 0.5, config.SOGLIA * 1.25, "soglia 5%", ha="right", fontsize=10, color="#555")
    ax.set_yscale("log")
    ax.set_xticks(x, etich, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("anno di inizio della finestra di dieci anni")
    ax.set_ylabel("p-value del test ADF (scala logaritmica)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_pvalue_finestre.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x, W["vol_ann"] * 100, color=[ARANCIO if v == W["vol_ann"].max() else (BLU if v == W["vol_ann"].min() else GRIGIO) for v in W["vol_ann"]])
    ax.set_xticks(x, etich, rotation=45, ha="right", fontsize=10)
    ax.set_xlabel("anno di inizio della finestra di dieci anni")
    ax.set_ylabel("volatilità annualizzata (%)")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_volatilita_finestre.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    lim = (min(S["stat_rw"].min(), S["stat_ar"].min(), W["stat_liv"].min()) - 0.3, max(S["stat_rw"].max(), S["stat_ar"].max(), W["stat_liv"].max()) + 0.3)
    bins = np.linspace(*lim, 60)
    ax.hist(S["stat_rw"], bins=bins, color=GRIGIO, alpha=0.8, label="random walk simulati (radice unitaria vera)")
    ax.hist(S["stat_ar"], bins=bins, color=ARANCIO, alpha=0.6, label="serie stazionarie lente simulate")
    crit = np.quantile(S["stat_rw"], config.SOGLIA)
    ax.axvline(crit, color="#555", ls="--", lw=1.4)
    ax.text(crit, ax.get_ylim()[1] * 0.97, " soglia: a sinistra il test rifiuta", fontsize=10, va="top", ha="right", color="#555")
    ymax = ax.get_ylim()[1]
    ax.plot(W["stat_liv"], np.full(len(W), -0.02 * ymax), "|", color=BLU, ms=16, mew=2.2, clip_on=False, label="decenni reali dell'S&P 500 (log-prezzo)")
    ax.set_xlabel("statistica ADF")
    ax.set_ylabel("numero di serie")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.9))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_simulazioni.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
