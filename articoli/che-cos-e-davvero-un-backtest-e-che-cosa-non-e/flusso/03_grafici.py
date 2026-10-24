"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG in figure/.

  fig1_curve.png        valore di 10.000 euro: regola e buy & hold (scala logaritmica)
  fig2_epoche.png       rendimento annuo di regola e buy & hold nelle tre epoche
  fig3_finestre.png     differenza di rendimento annuo (regola meno buy & hold) per ogni finestra di dieci anni
  fig4_casuali.png      la regola contro i calendari casuali: rendimento annuo e perdita massima
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


def pct(x, _=None):
    return f"{x:.0f}%"


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    V = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    v = lambda k: V[k]["valore"]

    # --- Figura 1: curve ---------------------------------------------------------------------------------------
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.plot(c["data"], config.CAPITALE * c["valore_bh"], color=GRIGIO, lw=1.8, label="buy & hold")
    ax.plot(c["data"], config.CAPITALE * c["valore_regola"], color=BLU, lw=2.0, label="sopra la media a 200 giorni, altrimenti cassa")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:,.0f}".replace(",", "."))
    ax.set_ylabel("valore di 10.000 euro, scala logaritmica")
    ax.legend(loc="upper left", fontsize=11)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_curve.png")
    plt.close(fig)

    # --- Figura 2: epoche -----------------------------------------------------------------------------------------
    e = pd.read_csv(R / "epoche.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(e))
    w = 0.36
    ax.bar([i - w / 2 for i in x], e["cagr_bh"] * 100, w, color=GRIGIO, label="buy & hold")
    ax.bar([i + w / 2 for i in x], e["cagr_regola"] * 100, w, color=BLU, label="regola")
    for i, (a, b) in enumerate(zip(e["cagr_bh"] * 100, e["cagr_regola"] * 100)):
        ax.text(i - w / 2, a + (0.3 if a >= 0 else -1.0), f"{a:.1f}%".replace(".", ","), ha="center", fontsize=11)
        ax.text(i + w / 2, b + (0.3 if b >= 0 else -1.0), f"{b:.1f}%".replace(".", ","), ha="center", fontsize=11)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(list(x), list(e["periodo"]))
    ax.yaxis.set_major_formatter(pct)
    ax.set_ylabel("rendimento annuo composto, senza costi")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=11)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig2_epoche.png")
    plt.close(fig)

    # --- Figura 3: finestre di dieci anni --------------------------------------------------------------------------
    f = pd.read_csv(R / "finestre.csv", parse_dates=["inizio", "fine"])
    d = f["diff"] * 100
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.fill_between(f["fine"], 0, d, where=d >= 0, color=BLU, alpha=0.85, label="la regola batte il buy & hold", interpolate=True)
    ax.fill_between(f["fine"], 0, d, where=d < 0, color=GRIGIO, alpha=0.85, label="vince il buy & hold", interpolate=True)
    ax.axhline(0, color="black", lw=0.8)
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:+.0f}".replace("+", "+").replace("-", "−"))
    ax.set_ylabel("regola meno buy & hold, punti l'anno")
    ax.set_xlabel("fine della finestra di dieci anni")
    ax.legend(loc="lower left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_finestre.png")
    plt.close(fig)

    # --- Figura 4: calendari casuali ---------------------------------------------------------------------------------
    k = pd.read_csv(R / "casuali.csv")
    fig, assi = plt.subplots(1, 2, figsize=(13, 4.8))
    a = assi[0]
    a.hist(k["cagr"] * 100, bins=40, color=GRIGIO, alpha=0.85)
    a.axvline(v("cagr_regola") * 100, color=BLU, lw=2.6, label="la regola")
    a.axvline(v("cagr_bh") * 100, color=ARANCIO, lw=2.2, ls="--", label="buy & hold")
    a.set_xlabel("rendimento annuo composto")
    a.set_ylabel("calendari casuali")
    a.xaxis.set_major_formatter(pct)
    a.legend(fontsize=10)
    b = assi[1]
    b.hist(k["perdita_massima"] * 100, bins=40, color=GRIGIO, alpha=0.85)
    b.axvline(-v("dd_regola") * 100, color=BLU, lw=2.6, label="la regola")
    b.axvline(-v("dd_bh") * 100, color=ARANCIO, lw=2.2, ls="--", label="buy & hold")
    b.set_xlabel("perdita massima dal picco")
    b.xaxis.set_major_formatter(lambda x, _: f"{x:.0f}%".replace("-", "−"))
    b.legend(fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_casuali.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
