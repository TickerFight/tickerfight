"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_quota_per_lunghezza.png   quota di vittorie del lump sum per lunghezza del PAC, quattro indici
  fig2_decenni.png               quota di vittorie del PAC a 12 rate per decennio di partenza (S&P 500)
  fig3_valori_finali.png         distribuzione del valore finale in euro, lump sum e PAC a 12 rate (S&P 500)
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
    ind = json.loads((R / "indici_usati.json").read_text(encoding="utf-8"))
    nomi = {i["slug"]: i["nome"].split(" (")[0] for i in ind}
    quote = pd.read_csv(R / "quote_per_lunghezza.csv")
    tk_p = config.INDICE_PRINCIPALE

    # --- Figura 1: quota del lump sum per lunghezza del PAC ----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = np.arange(len(config.RATE))
    for t in quote.ticker.unique():
        s = quote[quote.ticker == t].sort_values("rate")
        if t == tk_p:
            ax.fill_between(x, s.ic_lo * 100, s.ic_hi * 100, color=BLU, alpha=0.15, lw=0)
            ax.plot(x, s.quota_lump * 100, color=BLU, lw=2.8, marker="o", label="S&P 500 (fascia di confidenza 95%)")
            for xi, q in zip(x, s.quota_lump):
                ax.text(xi, q * 100 + 2.5, f"{q * 100:.0f}%", ha="center", color=BLU, fontsize=11, fontweight="bold")
        else:
            nome = [i["nome"].split(" (")[0] for i in ind if i["ticker"] == t][0]
            ax.plot(x, s.quota_lump * 100, color=GRIGIO, lw=1.4, marker=".", ls="--" if nome != "DAX" else "-", label=nome)
    ax.axhline(50, color="black", lw=1)
    ax.set_xticks(x, [f"{n} rate" for n in config.RATE])
    ax.set_ylim(30, 100)
    ax.set_xlabel("Lunghezza del PAC")
    ax.set_ylabel("Partenze in cui vince il lump sum (%)")
    ax.legend(loc="lower right", fontsize=10)
    fig.savefig(config.FIGURE / "fig1_quota_per_lunghezza.png")
    plt.close(fig)

    # --- Figura 2: decenni -------------------------------------------------------------------------------------------
    dec = pd.read_csv(R / "per_decennio.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    qpac = (1 - dec.quota_lump) * 100
    for xi, q, d in zip(range(len(dec)), qpac, dec.decennio):
        if q > 50:
            ax.bar(xi, q, 0.7, color=ARANCIO, hatch="//", edgecolor="white")
        else:
            ax.bar(xi, q, 0.7, color=BLU)
        ax.text(xi, q + 1.5, f"{q:.0f}%", ha="center", fontsize=10)
    ax.axhline(50, color="black", lw=1)
    ax.set_xticks(range(len(dec)), [f"{d}" for d in dec.decennio])
    ax.set_ylim(0, 100)
    ax.set_xlabel("Decennio di partenza")
    ax.set_ylabel(f"Partenze in cui vince il PAC (%)")
    fig.savefig(config.FIGURE / "fig2_decenni.png")
    plt.close(fig)

    # --- Figura 3: valori finali -------------------------------------------------------------------------------------
    pt = pd.read_csv(R / "partenze_sp500.csv")
    B = config.BUDGET
    lump, pac = pt["lump"].values / B, pt[f"pac_{config.N_PRINCIPALE}"].values / B
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    hi = float(np.ceil(np.quantile(np.r_[lump, pac], 0.995) * 4) / 4)
    bins = np.linspace(0, hi, 50)
    ax.hist(np.clip(lump, 0, hi), bins=bins, color=BLU, alpha=0.85, label="Lump sum")
    ax.hist(np.clip(pac, 0, hi), bins=bins, histtype="step", color=ARANCIO, lw=2.2, label=f"PAC a {config.N_PRINCIPALE} rate")
    ax.axvline(1.0, color="black", lw=1)
    for v, c, lab in ((np.quantile(lump, 0.05), BLU, "5° percentile"), (np.quantile(pac, 0.05), ARANCIO, "5° percentile")):
        ax.axvline(v, color=c, lw=1.4, ls="--")
    ax.set_xlabel("Valore dopo 60 mesi diviso il budget (1 = il budget di partenza); tratteggi: 5° percentile")
    ax.set_ylabel("Mesi di partenza")
    ax.legend(loc="upper right", fontsize=10)
    fig.savefig(config.FIGURE / "fig3_valori_finali.png")
    plt.close(fig)
    print("Figure salvate in", config.FIGURE)


if __name__ == "__main__":
    main()
