"""Passo 3 - Grafici dell'articolo. Legge SOLO risultati/ e salva i PNG in figure/.

  fig1_media_per_mese.png     rendimento medio dell'S&P 500 per mese
  fig2_gennaio_per_anno.png   rendimento di gennaio anno per anno
  fig3_differenze.png         gennaio meno altri mesi: S&P 500 prima/dopo, S&P 500 e Russell 2000 nello stesso periodo
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight", "savefig.facecolor": "white", "legend.frameon": False})
R = config.RISULTATI


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    v = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    m = pd.read_csv(R / "medie_mensili.csv")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([s[:3] for s in m["mese"]], m["media"] * 100, color=[ARANCIO if i == 0 else BLU for i in range(12)])
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Rendimento medio del mese, %")
    fig.savefig(config.FIGURE / "fig1_media_per_mese.png")
    plt.close(fig)

    a = pd.read_csv(R / "anni.csv")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(a["anno"], a["gennaio"] * 100, color=[BLU if x > 0 else ARANCIO for x in a["gennaio"]])
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Rendimento di gennaio, %")
    fig.savefig(config.FIGURE / "fig2_gennaio_per_anno.png")
    plt.close(fig)

    nomi = ["S&P 500\nprima", "S&P 500\ndopo", "S&P 500\n(dal 1987)", "Russell 2000\n(dal 1987)"]
    val = [v["diff_p"]["valore"], v["diff_d"]["valore"], v["diff_sp_stesso"]["valore"], v["diff_rut"]["valore"]]
    nomi[0] = nomi[0].replace("prima", "prima dello\nspartiacque")
    nomi[1] = nomi[1].replace("dopo", "dopo lo\nspartiacque")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(nomi, val, color=[GRIGIO, GRIGIO, BLU, ARANCIO])
    ax.axhline(0, color="#555", lw=1)
    ax.set_ylabel("Gennaio meno gli altri mesi, punti percentuali")
    fig.savefig(config.FIGURE / "fig3_differenze.png")
    plt.close(fig)
    print("Figure salvate.")


if __name__ == "__main__":
    main()
