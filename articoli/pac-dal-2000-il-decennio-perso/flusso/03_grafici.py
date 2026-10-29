"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_piano_2000.png        l'indice e, mese per mese, PAC, lump sum e totale versato del piano che parte a gennaio 2000
  fig2_tutte_le_partenze.png rendimento totale netto del PAC e del lump sum a dieci anni, per ogni mese di partenza
  fig3_confronto_caso.png    quota di piani peggiori del 2000 su serie rimescolate, contro quella reale
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    m = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    c = pd.read_csv(R / "curva_2000.csv", parse_dates=["data"])
    P = pd.read_csv(R / "partenze.csv")
    P["data"] = pd.PeriodIndex(P["partenza"], freq="M").to_timestamp()
    Q = pd.read_csv(R / "quote_perm.csv")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw={"height_ratios": [1, 1.4]})
    a1.plot(c["data"], c["prezzo"], color=GRIGIO, lw=2)
    a1.set_ylabel("S&P 500")
    a2.plot(c["data"], c["versato"], color="#555", lw=1.6, ls="--", label="Totale versato")
    a2.plot(c["data"], c["pac"], color=BLU, lw=2.4, label="Piano di accumulo")
    a2.plot(c["data"], c["lump_sum"], color=ARANCIO, lw=2.4, label="Tutto investito il primo giorno")
    a2.set_ylabel("Valore lordo")
    a2.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_piano_2000.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(P["data"], P["lump_sum"] * 100, color=ARANCIO, lw=1.2, alpha=0.8, label="Tutto investito il primo giorno")
    ax.plot(P["data"], P["pac"] * 100, color=BLU, lw=1.8, label="Piano di accumulo")
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.25)
    for anno, nome in ((config.ANNO_CASO, str(config.ANNO_CASO)), (config.ANNO_CRISI, str(config.ANNO_CRISI))):
        d = pd.Timestamp(f"{anno}-01-01")
        ax.axvline(d, color=GRIGIO, lw=1, ls=":")
        ax.text(d, ax.get_ylim()[1] * 0.80, nome, ha="center", fontsize=11, color="#333",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.set_xlabel("Mese di partenza del piano di dieci anni")
    ax.set_ylabel("Rendimento totale netto a dieci anni (%)")
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.savefig(config.FIGURE / "fig2_tutte_le_partenze.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.hist(Q["quota_peggiori"] * 100, bins=40, color=GRIGIO, alpha=0.85)
    ax.axvline(m["quota_peggiori"]["valore"] * 100, color=ARANCIO, lw=2.5, label="Storia reale")
    ax.set_xlabel("Quota di piani con rendimento pari o peggiore di quello del 2000 (%)")
    ax.set_ylabel("Serie rimescolate")
    ax.legend()
    fig.savefig(config.FIGURE / "fig3_confronto_caso.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
