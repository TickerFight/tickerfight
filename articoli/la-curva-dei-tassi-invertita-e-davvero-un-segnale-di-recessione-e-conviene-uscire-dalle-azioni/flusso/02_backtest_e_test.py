"""Passo 2 - Curva dei tassi invertita: episodi, recessioni NBER, strategia e confronto con il caso.

Legge SOLO dati/serie_giornaliere.csv e produce in risultati/:
  metriche.json    ogni numero dell'articolo, con descrizione e origine
  mensile.csv      serie di fine-mese: indice, tassi, spread, segnale, rendimenti della strategia e del buy & hold
  episodi.csv      per ogni episodio di inversione: inizio, fine, durata, se è seguito da recessione e con quale anticipo
  recessioni.csv   per ogni recessione NBER: se è stata preceduta da un'inversione e da quanto
  spostamenti.csv  rendimento annuo composto delle strategie con segnale spostato nel tempo
Il segnale di fine mese t decide la posizione del mese t+1 (nessun look-ahead).
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as fx

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    m = fx.mensile(g[["GSPC", "TNX", "IRX"]])
    m = m[(m["GSPC"] > 0)]
    ultima_seduta = g.index[-1]
    if (m.index[-1] - ultima_seduta).days > 4:       # ultimo mese incompleto: scartato
        m = m.iloc[:-1]
    m["spread"] = m["TNX"] - m["IRX"]
    n = len(m)
    primo = m.index[0]
    inv = (m["spread"] < config.SPREAD_SOGLIA).to_numpy()
    eps = fx.episodi(inv, config.MIN_MESI_EPISODIO, config.GAP_UNIONE)

    reg("prima_data", str(m.index[0].date()), "data_lunga", "Primo fine-mese con tutte e tre le serie", "dati/")
    reg("data_ultima", str(m.index[-1].date()), "data_lunga", "Ultimo fine-mese completo dei dati (l'eventuale mese in corso è scartato)", "dati/")
    reg("anno_inizio", str(m.index[0].date()), "anno", "Anno del primo fine-mese con tutte e tre le serie", "dati/")
    reg("n_mesi", n, "int", "Fine-mese nel campione", "dati/")
    reg("anni_campione", n / 12, "num1", "Anni del campione (mesi diviso 12)", "dati/")
    reg("mesi_invertiti", int(inv.sum()), "int", "Fine-mese con 10 anni sotto 3 mesi", "mensile.csv")
    reg("quota_invertiti", float(inv.mean()), "pct1", "Quota dei fine-mese con curva invertita", "mensile.csv")
    reg("spread_min", float(m["spread"].min()), "num2", "Spread 10 anni - 3 mesi più basso a fine mese (punti percentuali)", "mensile.csv")
    reg("spread_min_data", str(m["spread"].idxmin().date()), "data_lunga", "Fine-mese dello spread più basso", "mensile.csv")
    reg("spread_med", float(m["spread"].median()), "num2", "Spread mediano 10 anni - 3 mesi (punti percentuali)", "mensile.csv")
    reg("n_episodi", len(eps), "int", "Episodi di inversione (almeno 3 fine-mese invertiti, uniti se separati da meno di 6 mesi)", "episodi.csv")
    reg("min_mesi", config.MIN_MESI_EPISODIO, "int", "Fine-mese invertiti minimi per un episodio", "config.py")
    reg("gap_unione", config.GAP_UNIONE, "int", "Mesi di curva normale sotto i quali due serie invertite sono un solo episodio", "config.py")
    reg("orizzonte", config.ORIZZONTE, "int", "Mesi entro cui deve iniziare la recessione perché l'inversione sia «seguita»", "config.py")

    # --- Recessioni: sono state precedute da un'inversione? ---
    rec_idx = [fx.indice_mesi(p, primo) for p, _ in config.RECESSIONI]
    righe_r, n_prec, anticipi_r = [], 0, []
    for (picco, minimo), s in zip(config.RECESSIONI, rec_idx):
        prec = [e for e in eps if e[0] <= s and e[1] >= s - config.ORIZZONTE]
        ok = len(prec) > 0
        n_prec += int(ok)
        ant = s - prec[-1][0] if ok else None
        righe_r.append({"picco": picco, "minimo": minimo, "preceduta": int(ok), "mesi_da_inizio_inversione": ant})
        if ok:
            anticipi_r.append(ant)
    pd.DataFrame(righe_r).to_csv(config.RISULTATI / "recessioni.csv", index=False)
    reg("n_recessioni", len(config.RECESSIONI), "int", "Recessioni NBER dal 1969 in poi", "config.py, RECESSIONI")
    reg("n_precedute", n_prec, "int", "Recessioni precedute da un'inversione nei 24 mesi prima dell'inizio", "recessioni.csv")
    reg("h1_min", config.H1_MIN_RECESSIONI, "int", "Soglia dell'ipotesi 1", "config.py")
    reg("h1_ok", int(n_prec >= config.H1_MIN_RECESSIONI), "int", "1 se l'ipotesi 1 è rispettata", "recessioni.csv")
    mancate = [r for r in righe_r if not r["preceduta"]]
    reg("n_mancate", len(mancate), "int", "Recessioni non precedute da alcuna inversione", "recessioni.csv")
    reg("mancate_testo", ", ".join(r["picco"] for r in mancate) if mancate else "nessuna", "testo", "Mesi di inizio delle recessioni non precedute da inversione", "recessioni.csv")

    # --- Episodi: seguiti da recessione? ---
    righe_e = []
    for a, b in eps:
        censurato = a + config.ORIZZONTE > n - 1
        segue = [s for s in rec_idx if a <= s <= a + config.ORIZZONTE]
        righe_e.append({"inizio": str(m.index[a].date()), "fine": str(m.index[b].date()), "mesi_durata": b - a + 1,
                        "censurato": int(censurato), "seguito": int(bool(segue)),
                        "anticipo_mesi": (segue[0] - a) if segue else None})
    E = pd.DataFrame(righe_e)
    E.to_csv(config.RISULTATI / "episodi.csv", index=False)
    giudicabili = E[(E["censurato"] == 0) | (E["seguito"] == 1)]
    n_giud = len(giudicabili)
    n_segu = int(giudicabili["seguito"].sum())
    quota = n_segu / n_giud if n_giud else 0.0
    reg("n_censurati", int(((E["censurato"] == 1) & (E["seguito"] == 0)).sum()), "int", "Episodi troppo recenti per essere giudicati (meno di 24 mesi dall'inizio alla fine dei dati)", "episodi.csv")
    reg("n_giudicabili", n_giud, "int", "Episodi giudicabili", "episodi.csv")
    reg("n_seguiti", n_segu, "int", "Episodi giudicabili seguiti da una recessione entro 24 mesi", "episodi.csv")
    reg("n_falsi", n_giud - n_segu, "int", "Episodi giudicabili non seguiti da recessione entro 24 mesi (falsi allarmi)", "episodi.csv")
    reg("quota_seguiti", quota, "pct0", "Quota di episodi giudicabili seguiti da recessione", "episodi.csv")
    reg("h2_min", config.H2_QUOTA_MIN, "pct0", "Soglia dell'ipotesi 2", "config.py")
    reg("h2_ok", int(quota >= config.H2_QUOTA_MIN), "int", "1 se l'ipotesi 2 è rispettata", "episodi.csv")
    falsi = giudicabili[giudicabili["seguito"] == 0]
    reg("falsi_testo", ", ".join(str(pd.Timestamp(d).year) for d in falsi["inizio"]) if len(falsi) else "nessuno", "testo", "Anni di inizio degli episodi non seguiti da recessione", "episodi.csv")
    ant = giudicabili.loc[giudicabili["seguito"] == 1, "anticipo_mesi"].astype(float).to_numpy()
    if len(ant) == 0:
        raise SystemExit("Nessun episodio seguito da recessione: dati inattesi.")
    reg("ant_mediano", float(np.median(ant)), "num1", "Anticipo mediano (mesi) tra inizio dell'inversione e inizio della recessione", "episodi.csv")
    reg("ant_min", float(ant.min()), "int", "Anticipo minimo (mesi)", "episodi.csv")
    reg("ant_max", float(ant.max()), "int", "Anticipo massimo (mesi)", "episodi.csv")
    reg("ant_ampiezza", float(ant.max() - ant.min()), "int", "Differenza tra anticipo massimo e minimo (mesi)", "episodi.csv")
    reg("h3_med_min", config.H3_MEDIANA_MIN, "int", "Limite inferiore dell'anticipo mediano (ipotesi 3)", "config.py")
    reg("h3_med_max", config.H3_MEDIANA_MAX, "int", "Limite superiore dell'anticipo mediano (ipotesi 3)", "config.py")
    reg("h3_amp", config.H3_AMPIEZZA_MIN, "int", "Ampiezza minima dell'anticipo (ipotesi 3)", "config.py")
    h3 = config.H3_MEDIANA_MIN <= np.median(ant) <= config.H3_MEDIANA_MAX and (ant.max() - ant.min()) >= config.H3_AMPIEZZA_MIN
    reg("h3_ok", int(h3), "int", "1 se l'ipotesi 3 è rispettata", "episodi.csv")
    durate = E["mesi_durata"].astype(float)
    reg("durata_med", float(durate.median()), "num1", "Durata mediana di un episodio (mesi, dall'inizio alla fine)", "episodi.csv")
    reg("durata_max", float(durate.max()), "int", "Durata massima di un episodio (mesi)", "episodi.csv")

    # --- Strategia: liquidità quando la curva è invertita ---
    p = m["GSPC"].to_numpy()
    r_az = p[1:] / p[:-1] - 1                       # rendimento del mese t+1
    r_cash = m["IRX"].to_numpy()[:-1] / 100 / 12    # liquidità remunerata al tasso a 3 mesi di fine mese t
    fuori = inv[:-1]                                # segnale a fine mese t -> posizione mese t+1
    r_str = fx.rendimenti_strategia(r_az, r_cash, fuori)
    m["r_azioni"] = np.concatenate([[np.nan], r_az])
    m["r_strategia"] = np.concatenate([[np.nan], r_str])
    m["inv"] = inv.astype(int)
    m.to_csv(config.RISULTATI / "mensile.csv", float_format="%.6f")
    c_bh, c_st = fx.cagr(r_az), fx.cagr(r_str)
    d_bh, d_st = fx.max_drawdown(r_az), fx.max_drawdown(r_str)
    reg("cagr_bh", c_bh, "pct1", "Rendimento annuo composto del buy & hold sull'S&P 500 (solo prezzi)", "mensile.csv")
    reg("cagr_str", c_st, "pct1", "Rendimento annuo composto della strategia (liquidità al tasso a 3 mesi quando la curva è invertita)", "mensile.csv")
    reg("dd_bh", d_bh, "pct1", "Drawdown massimo mensile del buy & hold", "mensile.csv")
    reg("dd_str", d_st, "pct1", "Drawdown massimo mensile della strategia", "mensile.csv")
    reg("molt_bh", float(np.prod(1 + r_az)), "num1", "Quante volte è moltiplicato il capitale con il buy & hold", "mensile.csv")
    reg("molt_str", float(np.prod(1 + r_str)), "num1", "Quante volte è moltiplicato il capitale con la strategia", "mensile.csv")
    reg("quota_fuori", float(fuori.mean()), "pct1", "Quota dei mesi trascorsi in liquidità dalla strategia", "mensile.csv")
    reg("diff_cagr", (c_st - c_bh), "pp1", "Rendimento annuo della strategia meno quello del buy & hold (punti percentuali)", "mensile.csv")
    h4 = (c_st < c_bh) and (d_st > d_bh)
    reg("h4_ok", int(h4), "int", "1 se l'ipotesi 4 è rispettata (rende meno e ha un drawdown meno profondo)", "mensile.csv")
    # due sottoperiodi: fino al 1989 compreso e dal 1990 in poi
    anni_r = m.index[1:].year.to_numpy()
    for nome, sel in (("a", anni_r <= 1989), ("b", anni_r >= 1990)):
        reg(f"cagr_bh_{nome}", fx.cagr(r_az[sel]), "pct1", f"Rendimento annuo composto del buy & hold nel sottoperiodo {'fino al 1989' if nome == 'a' else 'dal 1990 in poi'}", "mensile.csv")
        reg(f"cagr_str_{nome}", fx.cagr(r_str[sel]), "pct1", f"Rendimento annuo composto della strategia nel sottoperiodo {'fino al 1989' if nome == 'a' else 'dal 1990 in poi'}", "mensile.csv")
    reg("anno_taglio", 1989, "annonum", "Ultimo anno del primo sottoperiodo", "02_backtest_e_test.py")
    reg("anno_taglio2", 1990, "annonum", "Primo anno del secondo sottoperiodo", "02_backtest_e_test.py")
    # rendimento medio delle azioni nei 12 mesi dopo l'inizio di ogni episodio
    fw = []
    for a, b in eps:
        if a + 12 <= n - 1:
            fw.append(p[a + 12] / p[a] - 1)
    reg("fw12_med", float(np.median(fw)), "pct1", "Rendimento mediano dell'S&P 500 nei 12 mesi successivi all'inizio di un episodio (solo prezzi)", "episodi.csv")
    reg("fw12_pos", int(sum(x > 0 for x in fw)), "int", "Episodi dopo i quali l'S&P 500 è salito nei 12 mesi successivi", "episodi.csv")
    reg("fw12_n", len(fw), "int", "Episodi con 12 mesi di dati successivi", "episodi.csv")

    # --- Il caso: stesso segnale spostato circolarmente nel tempo ---
    rng = np.random.default_rng(config.SEME)
    nn = len(fuori)
    shifts = rng.integers(config.SPOSTAMENTO_MIN, nn - config.SPOSTAMENTO_MIN + 1, size=config.N_SPOSTAMENTI)
    cs, ds = [], []
    for k in shifts:
        f = np.roll(fuori, int(k))
        rs = fx.rendimenti_strategia(r_az, r_cash, f)
        cs.append(fx.cagr(rs))
        ds.append(fx.max_drawdown(rs))
    cs, ds = np.array(cs), np.array(ds)
    pd.DataFrame({"spostamento_mesi": shifts, "cagr": cs, "drawdown_max": ds}).to_csv(config.RISULTATI / "spostamenti.csv", index=False, float_format="%.6f")
    pval = float((np.sum(cs >= c_st) + 1) / (len(cs) + 1))
    reg("n_sposta", config.N_SPOSTAMENTI, "int", "Strategie con segnale spostato nel tempo", "config.py")
    reg("sposta_min", config.SPOSTAMENTO_MIN, "int", "Spostamento minimo (mesi)", "config.py")
    reg("sposta_med", float(np.median(cs)), "pct1", "Rendimento annuo composto mediano delle strategie spostate", "spostamenti.csv")
    reg("sposta_p5", float(np.quantile(cs, 0.05)), "pct1", "5° percentile del rendimento annuo delle strategie spostate", "spostamenti.csv")
    reg("sposta_p95", float(np.quantile(cs, 0.95)), "pct1", "95° percentile del rendimento annuo delle strategie spostate", "spostamenti.csv")
    reg("sposta_p", pval, "pct1", "Quota di strategie spostate che rende almeno quanto la strategia vera", "spostamenti.csv")
    reg("sposta_sopra_bh", float(np.mean(cs >= c_bh)), "pct1", "Quota di strategie spostate che rende almeno quanto il buy & hold", "spostamenti.csv")
    reg("sposta_dd_med", float(np.median(ds)), "pct1", "Drawdown massimo mediano delle strategie spostate", "spostamenti.csv")
    reg("soglia_p", config.SOGLIA_P, "pct0", "Soglia dell'ipotesi 5", "config.py")
    reg("h5_ok", int(pval > config.SOGLIA_P), "int", "1 se l'ipotesi 5 è rispettata (la strategia vera non si distingue dal caso)", "spostamenti.csv")

    reg("anno_em", 1998, "annonum", "Anno di pubblicazione di Estrella e Mishkin", "Review of Economics and Statistics, vol. 80")
    reg("anno_eh", 1991, "annonum", "Anno di pubblicazione di Estrella e Hardouvelis", "Journal of Finance, vol. 46")
    reg("anno_prima_rec", int(config.RECESSIONI[0][0][:4]), "annonum", "Anno di inizio della prima recessione NBER considerata", "config.py, RECESSIONI")
    i90 = fx.indice_mesi("1989-05", primo)
    reg("spread_1989", float(m["spread"].iloc[i90]), "num2", "Spread 10 anni - 3 mesi a fine maggio 1989 (punti percentuali): l'unico fine-mese invertito prima della recessione del 1990", "mensile.csv")
    reg("anno_1989", 1989, "annonum", "Anno dello spread quasi nullo prima della recessione del 1990", "mensile.csv")
    reg("anno_1990", int(config.RECESSIONI[4][0][:4]), "annonum", "Anno di inizio della recessione non preceduta da inversione", "config.py, RECESSIONI")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {len(eps)} episodi")
    print(f"H1 {n_prec}/{len(config.RECESSIONI)}; H2 {n_segu}/{n_giud}; anticipi {ant}; H4 cagr {c_st:.3%} vs {c_bh:.3%}, dd {d_st:.1%} vs {d_bh:.1%}; H5 p={pval:.3f}")


if __name__ == "__main__":
    main()
