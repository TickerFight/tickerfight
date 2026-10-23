"""Passo 3 - Grafici dell'articolo.

Legge risultati/ (prodotti dal passo 2) e scrive figure/*.png.
Nessun numero viene ricalcolato qui: i valori mostrati nei grafici vengono da
risultati/metriche.json e dai CSV, così grafici e testo non possono divergere.

Stile: palette validata con validate_palette.js del skill dataviz
(blu = strategia, arancione = buy & hold, grigio = strategie a timing casuale).
Il colore segue l'entità in tutti i grafici: la strategia è sempre blu, il
buy & hold sempre arancione.
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

import config

SUP, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRIGLIA, ASSE = "#e1e0d9", "#c3c2b7"
BLU, ARANCIO, NEUTRO = "#2a78d6", "#eb6834", "#c3c2b7"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "figure.facecolor": SUP, "axes.facecolor": SUP, "savefig.facecolor": SUP,
    "axes.edgecolor": ASSE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRIGLIA, "grid.linewidth": 0.8,
})

FONTE = "Fonte: Yahoo Finance (^GSPC), elaborazione TickerFight. Indice di prezzo, senza dividendi."


def it(x, dec=2):
    """Numero con virgola decimale e vero segno meno."""
    return f"{x:.{dec}f}".replace(".", ",").replace("-", "−")


def pct(x, dec=1):
    return it(x * 100, dec) + "%"


def migliaia(n):
    return f"{n:,}".replace(",", ".")


def data_it(iso):
    return pd.Timestamp(iso).strftime("%d/%m/%Y")


def titolo(fig, testo, sotto):
    fig.text(0.012, 0.965, testo, ha="left", va="top", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.012, 0.912, sotto, ha="left", va="top", fontsize=9.5, color=INK2)


def fonte(fig, testo=FONTE):
    fig.text(0.012, 0.012, testo, ha="left", va="bottom", fontsize=8, color=MUTED)


def punto(ax, x, y, colore, s=55):
    """Marcatore con anello del colore della superficie, per restare leggibile sulle linee."""
    ax.scatter([x], [y], s=s, color=colore, edgecolors=SUP, linewidths=2, zorder=6, clip_on=False)


def salva(fig, nome):
    config.FIGURE.mkdir(parents=True, exist_ok=True)
    fig.savefig(config.FIGURE / nome, dpi=160)
    plt.close(fig)
    print("scritto", nome)


# ---------------------------------------------------------------------------
def fig_equity(curve, V):
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    fig.subplots_adjust(left=0.07, right=0.79, top=0.82, bottom=0.12)
    ax.plot(curve["Date"], curve["eq_bh"], color=ARANCIO, lw=1.6, label="Buy & hold")
    ax.plot(curve["Date"], curve["eq_strategia"], color=BLU, lw=1.6, label="Regola 50/200 (investito o cash)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(
        lambda v, _: (migliaia(int(v)) + "×") if v >= 1 else it(v, 1) + "×"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    ax.grid(axis="x", visible=False)
    x0, x1 = curve["Date"].iloc[0], curve["Date"].iloc[-1]
    ax.set_xlim(x0, x1 + (x1 - x0) * 0.015)           # un po' d'aria perché il punto finale non venga tagliato
    ultimo = [("Buy & hold", ARANCIO, curve["eq_bh"].iloc[-1]),
              ("Regola 50/200", BLU, curve["eq_strategia"].iloc[-1])]
    fig.canvas.draw()
    x1_num = matplotlib.dates.date2num(x1)
    pt = [ax.transData.transform((x1_num, float(y)))[1] * 72 / fig.dpi for _, _, y in ultimo]
    vicini = abs(pt[0] - pt[1]) < 15                  # etichette troppo vicine: allontanale di pochi punti
    alto = 0 if ultimo[0][2] >= ultimo[1][2] else 1
    for i, (nome, colore, y) in enumerate(ultimo):
        punto(ax, x1, y, colore)
        scost = (8 if i == alto else -8) if vicini else 0
        ax.annotate(f"{nome}  {it(y, 1)}×", xy=(x1, y), xytext=(10, scost), textcoords="offset points",
                    ha="left", va="center", fontsize=9, color=INK2, annotation_clip=False)
    ax.legend(loc="upper left", frameon=False, labelcolor=INK2)
    titolo(fig, "Valore di 1 investito, scala logaritmica",
           f"S&P 500 dal {data_it(V['data_inizio_test'])} al {data_it(V['data_fine_dati'])}: "
           "regola 50/200 contro buy & hold")
    fonte(fig)
    salva(fig, "fig1_equity_curve.png")


def fig_esempio_media_mobile(es, V):
    t_out, t_in = pd.Timestamp(V["es_data_uscita"]), pd.Timestamp(V["es_data_rientro"])
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.14)
    ax.axvspan(t_out, t_in, color=NEUTRO, alpha=0.35, lw=0, zorder=0)
    ax.plot(es["Date"], es["close"], color=MUTED, lw=1.0, label="Prezzo di chiusura")
    ax.plot(es["Date"], es["sma_veloce"], color=INK, lw=2.0, label=f"Media a {V['sma_veloce']} giorni (veloce)")
    ax.plot(es["Date"], es["sma_lenta"], color=INK2, lw=2.0, ls=(0, (5, 3)), label=f"Media a {V['sma_lenta']} giorni (lenta)")
    for t, c, testo, dx in [(t_out, "close", "Uscita: la veloce\nscende sotto la lenta", -12),
                            (t_in, "close", "Rientro: la veloce\nrisale sopra la lenta", 12)]:
        y = float(es.loc[es["Date"] == t, c].iloc[0])
        punto(ax, t, y, BLU)
        ax.annotate(testo, (t, y), xytext=(dx, -60 if dx < 0 else -48), textcoords="offset points",
                    ha="right" if dx < 0 else "left", fontsize=9, color=INK)
    ax.text(t_out + (t_in - t_out) / 2, ax.get_ylim()[0] + 0.03 * (ax.get_ylim()[1] - ax.get_ylim()[0]),
            "Strategia in cash", ha="center", va="bottom", fontsize=9, color=INK2)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: migliaia(int(v))))
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    titolo(fig, "Come funziona la media mobile: un caso reale",
           f"S&P 500 tra {data_it(es['Date'].iloc[0])} e {data_it(es['Date'].iloc[-1])}: la regola esce e rientra seguendo l'incrocio delle due medie")
    fonte(fig)
    salva(fig, "fig0_esempio_media_mobile.png")


def fig_confronto_gemella(c, V):
    from matplotlib.collections import LineCollection
    VERDE, ROSSO = "#2f8f5b", "#d03b35"
    fig, assi = plt.subplots(2, 1, figsize=(9.6, 6.6), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.97, top=0.84, bottom=0.12, hspace=0.32)
    x = matplotlib.dates.date2num(c["Date"])
    y = np.log10(c["close"].to_numpy())
    punti = np.column_stack([x, y]).reshape(-1, 1, 2)
    seg = np.concatenate([punti[:-1], punti[1:]], axis=1)
    for ax, col, tit, rend in [(assi[0], "posizione", "Regola vera (segnale delle medie)",
                                 f"rendimento {pct(V['cagr_str'], 2)} l'anno, perdita massima {pct(V['maxdd_str'])}"),
                                (assi[1], "posizione_gemella", "Una gemella: stessi periodi, in ordine casuale",
                                 f"rendimento {pct(V['gem_cagr'], 2)} l'anno, perdita massima {pct(V['gem_maxdd'])}")]:
        p = c[col].to_numpy()[1:]
        colori = np.where(p == 1, VERDE, ROSSO)
        ax.add_collection(LineCollection(seg, colors=colori, linewidths=2.0))
        ax.set_xlim(x.min(), x.max()); ax.set_ylim(y.min() - 0.1, y.max() + 0.1)
        ax.set_title(f"{tit}  -  {rend}", loc="left", fontsize=10, color=INK, fontweight="bold")
        ax.set_yticks([1, 2, 3]); ax.set_yticklabels(["10", "100", "1.000"])
        ax.set_ylabel("S&P 500 (punti), scala log", fontsize=8.5)
        ax.xaxis_date(); ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(10))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    fig.legend(handles=[Line2D([0], [0], color=VERDE, lw=3, label="Dentro il mercato"),
                        Line2D([0], [0], color=ROSSO, lw=3, label="Fuori dal mercato (cash)")],
               loc="lower center", ncol=2, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.035))
    titolo(fig, "Stessi pezzi, ordine diverso: la regola vera e una gemella a confronto",
           f"Entrambe stanno dentro il mercato il {pct(V['esposizione'], 0)} dei giorni e cambiano posizione {migliaia(int(V['n_cambi']))} volte")
    fonte(fig)
    salva(fig, "fig_confronto_gemella.png")


def fig_griglia_gemelle(gr, V):
    VERDE, ROSSO = "#2f8f5b", "#d03b35"
    cols = ["regola"] + [c for c in gr.columns if c.startswith("g")]
    n = len(cols)
    x = matplotlib.dates.date2num(gr["Date"])
    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    fig.subplots_adjust(left=0.13, right=0.98, top=0.83, bottom=0.15)
    # periodi storici di grandi ribassi (solo per orientare la lettura)
    for a, b, et in [("1929-09-01", "1932-07-01", "1929–32"), ("2000-03-01", "2002-10-01", "2000–02"),
                     ("2007-10-01", "2009-03-01", "2007–09")]:
        xa, xb = matplotlib.dates.date2num(pd.Timestamp(a)), matplotlib.dates.date2num(pd.Timestamp(b))
        ax.axvspan(xa, xb, ymin=0, ymax=1, color=GRIGLIA, alpha=0.55, lw=0, zorder=0)
        ax.text((xa + xb) / 2, (n - 1) + 1.6 + 0.78 + 0.12, et, ha="center", va="bottom", fontsize=8.5, color=INK2)
    for r, col in enumerate(cols):
        y = (n - 1 - r) * 1.0 + (0.6 if r > 0 else 1.6)
        v = gr[col].to_numpy()
        cambi = np.flatnonzero(np.diff(v) != 0) + 1
        ini = np.concatenate(([0], cambi)); fin = np.concatenate((cambi, [len(v)]))
        for i0, i1, val in zip(ini, fin, v[ini]):
            ax.broken_barh([(x[i0], x[min(i1, len(x) - 1)] - x[i0])], (y, 0.78),
                           facecolors=VERDE if val == 1 else ROSSO, edgecolors="none", zorder=2)
    yt = [(n - 1 - r) + (0.6 if r > 0 else 1.6) + 0.39 for r in range(n)]
    ax.set_yticks(yt)
    ax.set_yticklabels(["Regola vera"] + [f"Gemella {k}" for k in range(1, n)], fontsize=9)
    ax.get_yticklabels()[0].set_fontweight("bold"); ax.get_yticklabels()[0].set_color(INK)
    ax.set_xlim(x.min(), x.max()); ax.set_ylim(-0.4, (n - 1) + 1.6 + 0.78 + 0.75)
    ax.grid(False); ax.tick_params(axis="y", length=0)
    ax.xaxis_date(); ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(10))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    ax.spines["left"].set_visible(False)
    ax.axhline(yt[1] + 0.39 + 0.3, color=INK, lw=1.2, zorder=3)
    fig.legend(handles=[Patch(color=VERDE, label="Dentro il mercato"), Patch(color=ROSSO, label="Fuori dal mercato (cash)"),
                        Patch(color=GRIGLIA, label="Grandi ribassi")],
               loc="lower center", ncol=3, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.035))
    titolo(fig, "Gli stessi pezzi, rimescolati: la regola vera e dodici gemelle",
           f"Ogni riga è una strategia. Tutte stanno dentro il mercato il {pct(V['esposizione'], 0)} dei giorni e cambiano posizione {migliaia(int(V['n_cambi']))} volte")
    fonte(fig)
    salva(fig, "fig_griglia_gemelle.png")


def fig_mosaico_bootstrap(curve, V):
    """Storia vera e due storie alternative del bootstrap, un quadratino per ogni mese (blocco di 21 giorni)."""
    VERDE, ROSSO = "#2f8f5b", "#d03b35"
    rb = curve["eq_bh"].pct_change().dropna().to_numpy()
    rs = curve["eq_strategia"].pct_change().dropna().to_numpy()
    pos = curve["posizione"].iloc[1:].to_numpy()
    date = curve["Date"].iloc[1:].reset_index(drop=True)
    n, L = len(rb), config.BLOCCO_BOOTSTRAP
    sharpe = lambda r: r.mean() / r.std(ddof=1) * np.sqrt(config.GIORNI_ANNO_BORSA)
    d_vera = sharpe(rs) - sharpe(rb)
    rng = np.random.default_rng(config.SEED + 5)
    cand = []
    for _ in range(200):          # 200 ricampionamenti tra cui scegliere due scenari da mostrare
        ini = rng.integers(0, n, size=int(np.ceil(n / L)))
        idx = ((ini[:, None] + np.arange(L)[None, :]).reshape(-1) % n)[:n]
        cand.append((sharpe(rs[idx]) - sharpe(rb[idx]), np.prod(1 + rs[idx]), np.prod(1 + rb[idx]), ini))
    # A: un caso tipico (differenza simile alla vera, regola avanti); B: un caso in cui vince il buy & hold
    A = min([c for c in cand if c[1] > c[2]], key=lambda c: abs(c[0] - d_vera))
    B = min([c for c in cand if c[0] < 0], key=lambda c: abs(c[0] + 0.05))
    nb = int(np.ceil(n / L)); col = 100; righe = int(np.ceil(nb / col))
    dentro = lambda starts: np.array([pos[(s + np.arange(L)) % n].mean() >= 0.5 for s in starts])
    pannelli = [("Storia vera", "i mesi in ordine cronologico", dentro(np.arange(nb) * L),
                 d_vera, np.prod(1 + rs), np.prod(1 + rb)),
                ("Scenario A", "gli stessi mesi, pescati a caso", dentro(A[3]), A[0], A[1], A[2]),
                ("Scenario B", "un altro estratto a caso", dentro(B[3]), B[0], B[1], B[2])]
    fig, assi = plt.subplots(1, 3, figsize=(12.4, 6.6))
    fig.subplots_adjust(left=0.05, right=0.99, top=0.78, bottom=0.17, wspace=0.12)
    for k, (ax, (nome, sotto, c, d, es, eb)) in enumerate(zip(assi, pannelli)):
        griglia = np.full(righe * col, np.nan); griglia[:len(c)] = c.astype(float)
        cmap = matplotlib.colors.ListedColormap([ROSSO, VERDE]); cmap.set_bad(SUP)
        ax.imshow(np.ma.masked_invalid(griglia.reshape(righe, col)), cmap=cmap, vmin=0, vmax=1,
                  aspect="auto", interpolation="nearest")
        for x in np.arange(-.5, col, 1):
            ax.axvline(x, color=SUP, lw=0.5)
        for y in np.arange(-.5, righe, 1):
            ax.axhline(y, color=SUP, lw=0.9)
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_xticks([])
        if k == 0:
            ax.set_yticks(range(righe))
            ax.set_yticklabels([str(date[min(r * col * L, n - 1)].year) for r in range(righe)], fontsize=8, color=MUTED)
            ax.tick_params(length=0)
        else:
            ax.set_yticks([])
        ax.set_title(nome, loc="left", fontsize=11.5, fontweight="bold", color=INK, pad=18)
        ax.text(0, 1.015, sotto, transform=ax.transAxes, fontsize=9, color=INK2, va="bottom")
        segno = "+" if d >= 0 else "−"
        ax.text(0, -0.04, f"Regola {it(es, 0)}×  ·  Buy & hold {it(eb, 0)}×\nDifferenza di Sharpe {segno}{it(abs(d))}",
                transform=ax.transAxes, fontsize=9, color=INK2, va="top")
    fig.text(0.012, 0.965, "Cosa fa il bootstrap: stessi mesi, ordine diverso", fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.012, 0.915, "Ogni quadratino è un mese di borsa vero (circa 21 giorni): verde se la regola era dentro il mercato, rosso se era fuori.\n"
             "Si legge a righe, da sinistra a destra; a sinistra l'anno di inizio di ogni riga. Ogni mese porta con sé il rendimento della regola e dell'indice.",
             fontsize=9.2, color=INK2, va="top")
    fig.legend(handles=[Patch(color=VERDE, label="Regola dentro il mercato"), Patch(color=ROSSO, label="Regola fuori (cash)")],
               loc="lower center", bbox_to_anchor=(0.5, 0.045), frameon=False, ncol=2, fontsize=9, labelcolor=INK2)
    fonte(fig, FONTE + " Nello scenario alcuni mesi compaiono più volte e altri mai.")
    salva(fig, "fig_mosaico_bootstrap.png")


def fig_drawdown(curve, V):
    fig, assi = plt.subplots(2, 1, figsize=(9.6, 6.2), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.85, bottom=0.09, hspace=0.12)
    x0, x1 = curve["Date"].iloc[0], curve["Date"].iloc[-1]
    fondo = min(curve["dd_bh"].min(), curve["dd_strategia"].min())
    serie = (("dd_bh", ARANCIO, "Buy & hold"), ("dd_strategia", BLU, "Regola 50/200"))
    for ax, (col, colore, nome) in zip(assi, serie):
        ax.fill_between(curve["Date"], curve[col], 0, color=colore, alpha=0.10, lw=0)
        ax.plot(curve["Date"], curve[col], color=colore, lw=1.2)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v, 0)))
        ax.grid(axis="x", visible=False)
        ax.set_xlim(x0, x1)
        ax.set_ylim(fondo * 1.15, 0.02)
        i = curve[col].idxmin()
        xd, yd = curve.loc[i, "Date"], curve.loc[i, col]
        punto(ax, xd, yd, colore)
        a_destra = (xd - x0) < (x1 - x0) * 0.5          # etichetta verso il lato libero
        ax.annotate(f"perdita massima {pct(yd, 1)}", xy=(xd, yd), xytext=(11 if a_destra else -11, 0),
                    textcoords="offset points", ha="left" if a_destra else "right", va="center",
                    fontsize=9, color=INK2, bbox=dict(boxstyle="square,pad=0.2", fc=SUP, ec="none"))
        ax.legend(handles=[Line2D([0], [0], color=colore, lw=2, label=nome)], loc="lower right",
                  frameon=False, labelcolor=INK2)
    titolo(fig, "Quanto si perde dal massimo precedente",
           "Distanza percentuale dal picco, giorno per giorno; stessa scala nei due pannelli")
    fonte(fig)
    salva(fig, "fig2_drawdown.png")


def fig_timing_casuale(nulla, V):
    fig, assi = plt.subplots(1, 3, figsize=(11.2, 4.7))
    fig.subplots_adjust(left=0.05, right=0.985, top=0.78, bottom=0.2, wspace=0.18)
    pannelli = (
        ("sharpe", "Indice di Sharpe", lambda v, _: it(v, 2), V["sharpe_str"], V["sharpe_bh"], V["p_sharpe"]),
        ("cagr", "Rendimento annuo composto", lambda v, _: pct(v, 1), V["cagr_str"], V["cagr_bh"], V["p_cagr"]),
        ("maxdd", "Perdita massima", lambda v, _: pct(v, 0), V["maxdd_str"], V["maxdd_bh"], V["p_maxdd"]),
    )
    for ax, (col, nome, fmt, v_str, v_bh, p) in zip(assi, pannelli):
        dati = nulla[col].to_numpy()
        ax.hist(dati, bins=60, color=NEUTRO, edgecolor=SUP, linewidth=0.5)
        ax.axvline(v_bh, color=ARANCIO, lw=2)
        ax.axvline(v_str, color=BLU, lw=2)
        lo, hi = min(dati.min(), v_str, v_bh), max(dati.max(), v_str, v_bh)
        pad = (hi - lo) * 0.06
        ax.set_xlim(lo - pad, hi + pad)
        ax.xaxis.set_major_formatter(FuncFormatter(fmt))
        ax.grid(axis="x", visible=False)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(nome, loc="left", fontsize=10, color=INK, fontweight="bold")
        ax.set_title(f"p = {it(p, 4)}", loc="right", fontsize=9.5, color=INK2)
    fig.legend(handles=[Patch(color=NEUTRO, label="Strategie a timing casuale"),
                        Line2D([0], [0], color=BLU, lw=2, label="Regola 50/200"),
                        Line2D([0], [0], color=ARANCIO, lw=2, label="Buy & hold")],
               loc="lower center", ncol=3, frameon=False, labelcolor=INK2, bbox_to_anchor=(0.5, 0.045))
    titolo(fig, "La regola contro strategie con la stessa esposizione e timing casuale",
           f"{migliaia(V['n_sim'])} strategie con gli stessi giorni investiti e gli stessi cambi di posizione, "
           "ma durate rimescolate")
    fonte(fig, FONTE + " p = quota di strategie casuali che fanno almeno altrettanto bene.")
    salva(fig, "fig3_test_timing_casuale.png")


def fig_bootstrap(boot, V):
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    fig.subplots_adjust(left=0.05, right=0.97, top=0.82, bottom=0.27)
    d = boot["differenza"].to_numpy()
    ax.hist(d, bins=70, color=NEUTRO, edgecolor=SUP, linewidth=0.5)
    ax.axvspan(V["boot_diff_lo"], V["boot_diff_hi"], color=INK, alpha=0.07, lw=0)
    ax.axvline(0, color=INK2, lw=1.2)
    ax.axvline(V["diff_sharpe_obs"], color=INK, lw=2)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: it(v, 2)))
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", visible=False)
    ax.set_xlabel("Differenza di Sharpe: regola 50/200 meno buy & hold")
    fig.legend(handles=[Patch(color=NEUTRO, label="Differenze ricampionate"),
                        Patch(color=INK, alpha=0.07, label="Intervallo al 95%"),
                        Line2D([0], [0], color=INK, lw=2, label="Differenza osservata"),
                        Line2D([0], [0], color=INK2, lw=1.2, label="Zero: nessuna differenza")],
               loc="lower center", ncol=4, frameon=False, labelcolor=INK2, bbox_to_anchor=(0.5, 0.05),
               fontsize=9)
    titolo(fig, "Quanto è incerta la differenza di Sharpe",
           f"Bootstrap a blocchi da {V['blocco_boot']} giorni, {migliaia(V['n_boot'])} ricampionamenti")
    fonte(fig)
    salva(fig, "fig4_bootstrap_differenza_sharpe.png")


def fig_sottoperiodi(V):
    righe = [("Periodo intero", V["sharpe_str"], V["sharpe_bh"], V["p_sharpe"])]
    for i in range(len(config.SOTTOPERIODI)):
        righe.append((V[f"sp{i}_etichetta"], V[f"sp{i}_sharpe_str"], V[f"sp{i}_sharpe_bh"], V[f"sp{i}_p_sharpe"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    fig.subplots_adjust(left=0.2, right=0.84, top=0.8, bottom=0.27)
    y = np.arange(len(righe))[::-1]
    for yy, (nome, s, b, p) in zip(y, righe):
        ax.plot([s, b], [yy, yy], color=ASSE, lw=1, zorder=2)
        punto(ax, b, yy, ARANCIO)
        punto(ax, s, yy, BLU)
        ax.text(1.02, yy, f"p = {it(p, 4)}", transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=9.5, color=INK2)
    ax.text(1.02, len(righe) - 0.45, "Valore p (Sharpe)", transform=ax.get_yaxis_transform(),
            ha="left", va="bottom", fontsize=8.5, color=MUTED)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in righe], color=INK2)
    ax.set_ylim(-0.6, len(righe) - 0.2)
    xs = [v for r in righe for v in r[1:3]]
    pad = (max(xs) - min(xs)) * 0.15
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: it(v, 2)))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Indice di Sharpe")
    fig.legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=BLU, markeredgecolor=SUP,
                               markersize=8, label="Regola 50/200"),
                        Line2D([0], [0], marker="o", color="none", markerfacecolor=ARANCIO, markeredgecolor=SUP,
                               markersize=8, label="Buy & hold")],
               loc="lower center", ncol=2, frameon=False, labelcolor=INK2, bbox_to_anchor=(0.5, 0.05))
    titolo(fig, "Il risultato cambia con l'epoca?",
           "Sharpe di regola e buy & hold nel periodo intero e in tre sotto-periodi")
    fonte(fig)
    salva(fig, "fig5_sottoperiodi.png")


def main() -> None:
    V = {k: v["valore"] for k, v in json.loads(
        (config.RISULTATI / "metriche.json").read_text(encoding="utf-8"))["valori"].items()}
    curve = pd.read_csv(config.RISULTATI / "curve.csv", parse_dates=["Date"])
    nulla = pd.read_csv(config.RISULTATI / "test_casuale_periodo_intero.csv")
    boot = pd.read_csv(config.RISULTATI / "bootstrap_diff_sharpe.csv")
    es = pd.read_csv(config.RISULTATI / "esempio_media_mobile.csv", parse_dates=["Date"])
    fig_esempio_media_mobile(es, V)
    cg = pd.read_csv(config.RISULTATI / "esempio_gemella.csv", parse_dates=["Date"])
    fig_confronto_gemella(cg, V)
    gr = pd.read_csv(config.RISULTATI / "esempio_griglia_gemelle.csv", parse_dates=["Date"])
    fig_griglia_gemelle(gr, V)
    fig_equity(curve, V)
    fig_drawdown(curve, V)
    fig_timing_casuale(nulla, V)
    fig_bootstrap(boot, V)
    fig_mosaico_bootstrap(curve, V)
    fig_sottoperiodi(V)


if __name__ == "__main__":
    main()
