"""Passo 3 - Grafici dell'articolo. Legge SOLO i file in risultati/ e salva i PNG e la GIF in figure/.

  fig1_cono.png                 il cono in 2D: fasce dei percorsi casuali, regola e buy & hold
  fig2_cono_3d.png              il cono in 3D: tempo, valore e densità dei percorsi casuali, con la regola sopra
  fig2_cono_3d.gif              lo stesso grafico in 3D, che ruota
  fig3_percentile_nel_tempo.png il percentile della regola tra i percorsi casuali, giorno per giorno
  fig4_finale_e_perdita.png     valore finale e perdita massima: percorsi casuali contro regola e buy & hold
"""
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

import config  # noqa: E402

BLU, ARANCIO, GRIGIO = "#1f5fa8", "#c9610a", "#8a8a8a"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 120, "savefig.bbox": "tight",
                     "savefig.facecolor": "white", "legend.frameon": False})


def euro(x, _=None):
    return f"{x:,.0f}".replace(",", ".") + " €"


def liscia(m: np.ndarray, k: int = 3) -> np.ndarray:
    """Media mobile leggera lungo le colonne (fasce di valore) e le righe (tempo), solo per rendere la superficie leggibile."""
    ker = np.ones(k) / k
    m = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k // 2, mode="edge"), ker, mode="valid"), 1, m)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k // 2, mode="edge"), ker, mode="valid"), 0, m)


def disegna_3d(ax, T, V, Z, fasce, azim, elev=26):
    ax.plot_surface(T, V, Z, cmap="Greys", rstride=1, cstride=1, linewidth=0, antialiased=True, alpha=0.95)
    anni = T[:, 0]
    valori = V[0]
    for col, nome, stile in (("regola", "regola", "-"), ("buy_hold", "buy & hold", "--")):
        y = fasce[col].to_numpy()
        j = np.clip(np.searchsorted(valori, y), 0, len(valori) - 1)
        z = Z[np.arange(len(anni)), j] + Z.max() * 0.03
        ax.plot(anni, y, z, color=BLU if col == "regola" else ARANCIO, lw=3.2, ls=stile, label=nome)
    ax.set_xlabel("anni dall'inizio", labelpad=8)
    ax.set_ylabel("valore dei 500 €", labelpad=10)
    ax.set_zlabel("percorsi casuali", labelpad=4)
    ax.yaxis.set_major_formatter(euro)
    ax.zaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1.5, 1.2, 0.7))


def main() -> None:
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    R = config.RISULTATI
    fasce = pd.read_csv(R / "cono_fasce.csv", parse_dates=["data"])
    dens = pd.read_csv(R / "cono_densita.csv", parse_dates=["data"])
    fin = pd.read_csv(R / "percorsi_finali.csv")
    curve = pd.read_csv(R / "curve.csv", parse_dates=["data"])

    # --- Figura 1: il cono in 2D ------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.fill_between(fasce["data"], fasce["p5"], fasce["p95"], color=GRIGIO, alpha=0.20, lw=0, label="dal 5° al 95° percentile dei percorsi casuali")
    ax.fill_between(fasce["data"], fasce["p25"], fasce["p75"], color=GRIGIO, alpha=0.30, lw=0, label="dal 25° al 75°")
    ax.plot(fasce["data"], fasce["p50"], color="#555", lw=1.2, label="mediana")
    ax.plot(curve["data"], curve["valore_bh"], color=ARANCIO, lw=1.8, ls="--", label="buy & hold")
    ax.plot(curve["data"], curve["valore_regola"], color=BLU, lw=2.2, label=f"regola {config.SMA_VELOCE}/{config.SMA_LENTA}")
    ax.axhline(config.CAPITALE, color=GRIGIO, lw=1, ls=":")
    ax.yaxis.set_major_formatter(euro)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylabel("valore dei 500 €")
    ax.legend(ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=10, columnspacing=1.2)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig1_cono.png")
    plt.close(fig)

    # --- Figura 2: il cono in 3D (statica e GIF) ------------------------------------------------------------------
    valori = np.array([float(c) for c in dens.columns[1:]])
    Z = liscia(dens.iloc[:, 1:].to_numpy(float), 5)
    anni = (dens["data"] - dens["data"].iloc[0]).dt.days.to_numpy() / 365.25
    # Il primo periodo ha tutti i percorsi vicini ai 500 €: un picco che schiaccia il resto. Si limita l'altezza (solo per la leggibilità).
    Z = np.minimum(Z, np.percentile(Z[anni > 0.5], 99))
    T, V = np.meshgrid(anni, valori, indexing="ij")
    fig = plt.figure(figsize=(10, 7.2))
    ax = fig.add_subplot(111, projection="3d")
    disegna_3d(ax, T, V, Z, fasce, azim=-62)
    ax.legend(loc="upper left", bbox_to_anchor=(0.02, 0.92), fontsize=11)
    fig.savefig(config.FIGURE / "fig2_cono_3d.png", dpi=130)
    plt.close(fig)

    frames = []
    for az in np.linspace(-62, 298, 45, endpoint=False):
        fig = plt.figure(figsize=(7.2, 5.4))
        ax = fig.add_subplot(111, projection="3d")
        disegna_3d(ax, T, V, Z, fasce, azim=float(az))
        ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.95), fontsize=9)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=80, bbox_inches=None, pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        frames.append(Image.open(buf).convert("P", palette=Image.ADAPTIVE, colors=128))
    frames[0].save(config.FIGURE / "fig2_cono_3d.gif", save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)

    # --- Figura 3: percentile nel tempo ---------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axhspan(25, 75, color=GRIGIO, alpha=0.15, lw=0, label="zona centrale (dal 25° al 75° percentile)")
    ax.axhline(50, color="#555", lw=1)
    ax.plot(fasce["data"], fasce["percentile_regola"] * 100, color=BLU, lw=2.0)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}°")
    ax.set_ylabel("percentile della regola")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig3_percentile_nel_tempo.png")
    plt.close(fig)

    # --- Figura 4: valore finale e perdita massima -----------------------------------------------------------
    import json
    val = json.loads((R / "metriche.json").read_text(encoding="utf-8"))["valori"]
    fm, fb = float(val["finale_mm"]["valore"]), float(val["finale_bh"]["valore"])
    ddm, ddb = float(val["maxdd_mm"]["valore"]), float(val["maxdd_bh"]["valore"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5))
    a1.hist(fin["finale"], bins=50, color=GRIGIO, alpha=0.6, edgecolor="white")
    a1.axvline(fm, color=BLU, lw=2.4, label="regola")
    a1.axvline(fb, color=ARANCIO, lw=2.2, ls="--", label="buy & hold")
    a1.xaxis.set_major_formatter(euro)
    a1.set_xlabel("valore finale netto dei percorsi casuali")
    a1.set_ylabel("numero di percorsi")
    a2.hist(fin["perdita_massima"] * 100, bins=50, color=GRIGIO, alpha=0.6, edgecolor="white")
    a2.axvline(ddm * 100, color=BLU, lw=2.4, label="regola")
    a2.axvline(ddb * 100, color=ARANCIO, lw=2.2, ls="--", label="buy & hold")
    a2.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    a2.set_xlabel("perdita massima dal picco dei percorsi casuali")
    for a in (a1, a2):
        a.legend(loc="upper left", fontsize=10)
    fig.tight_layout()
    fig.savefig(config.FIGURE / "fig4_finale_e_perdita.png")
    plt.close(fig)
    print("Grafici salvati in figure/")


if __name__ == "__main__":
    main()
