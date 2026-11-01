"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_valore_azioni_obbligazioni.png   valore di un dollaro in azioni e obbligazioni (scala logaritmica)
  fig2_quota_per_orizzonte.png          quota di finestre in cui le azioni battono le obbligazioni, per orizzonte
  fig3_finestre_dieci_anni.png          rendimento annuo delle finestre mobili di dieci anni
  fig4_scimmie.png                      valore finale delle scimmie contro azioni e obbligazioni
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
    c = pd.read_csv(R / "curve.csv", parse_dates=["data"])
    f = pd.read_csv(R / "finestre_rif.csv", parse_dates=["data"])
    q = pd.read_csv(R / "quote_orizzonti.csv")
    s = pd.read_csv(R / "scimmie.csv")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(c["data"], c["obblig"], color=BLU, lw=2, label="Obbligazioni (VBMFX)")
    ax.plot(c["data"], c["azioni"], color=ARANCIO, lw=2, label="Azioni (VFINX)")
    ax.set_yscale("log")
    ax.set_ylabel("Valore di 1 dollaro (scala logaritmica)")
    ax.legend(loc="upper left")
    fig.savefig(config.FIGURE / "fig1_valore_azioni_obbligazioni.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    etichette = [f"{int(a)} anni" for a in q["anni"]]
    barre = ax.bar(etichette, q["quota_azioni"] * 100, color=ARANCIO, hatch="//", edgecolor="white")
    for b_, v in zip(barre, q["quota_azioni"] * 100):
        ax.text(b_.get_x() + b_.get_width() / 2, v + 1.5, f"{v:.0f}%", ha="center")
    ax.axhline(50, color=GRIGIO, lw=1.5, ls="--")
    ax.set_ylim(0, 112)
    ax.set_ylabel("Finestre in cui le azioni battono le obbligazioni (%)")
    ax.set_xlabel("Orizzonte")
    fig.savefig(config.FIGURE / "fig2_quota_per_orizzonte.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(f["data"], f["OBBLIG"] * 100, color=BLU, lw=2, label="Obbligazioni")
    ax.plot(f["data"], f["AZIONI"] * 100, color=ARANCIO, lw=2, label="Azioni")
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Rendimento annuo su dieci anni (%)")
    ax.legend(loc="upper right")
    fig.savefig(config.FIGURE / "fig3_finestre_dieci_anni.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    cap = m["capitale"]["valore"]
    ax.hist(s["finale"] * cap, bins=50, color=GRIGIO, alpha=0.85)
    ax.axvline(m["obblig_finale"]["valore"], color=BLU, lw=2.5, label="Tutto in obbligazioni")
    ax.axvline(m["azioni_finale"]["valore"], color=ARANCIO, lw=2.5, label="Tutto in azioni")
    ax.set_xlabel(f"Valore finale di {cap:.0f} dollari scegliendo a caso tra azioni e obbligazioni ogni mese")
    ax.set_ylabel("Scimmie")
    ax.legend()
    fig.savefig(config.FIGURE / "fig4_scimmie.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
