"""Passo 2 - Il lunedì è davvero il giorno peggiore? Rendimento dell'S&P 500 per giorno della settimana.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  giorni_settimana.csv per giorno: sedute, media, mediana, quota di giorni positivi, intervallo al 95% della media (punti base)
  periodi.csv          media per giorno nei due sotto-periodi e senza i 10 giorni peggiori (punti base)
  permutazioni.csv     distribuzione simulata della differenza tra giorno migliore e peggiore (punti base)
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as f

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"
PB = 10000.0                                       # punti base: centesimi di punto percentuale
NG = config.NOMI_GIORNI


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    r_all = c.pct_change().dropna()
    r_all = r_all[r_all.index >= pd.Timestamp(config.INIZIO_ANALISI)]
    g_all = r_all.index.dayofweek.to_numpy()
    if (g_all > 4).any():
        raise SystemExit("Trovate sedute di sabato o domenica dopo l'inizio dell'analisi.")
    r = r_all.to_numpy()
    anni = (r_all.index[-1] - r_all.index[0]).days / 365.25
    rng = np.random.default_rng(config.SEME)

    reg("dati_prima_data", str(r_all.index[0].date()), "data_lunga", "Prima seduta analizzata", "dati/")
    reg("dati_ultima_data", str(r_all.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("dati_anni", anni, "num1", "Anni di storia analizzati", "dati/")
    reg("sedute", len(r), "int", "Sedute (rendimenti giornalieri) analizzate", "dati/")
    reg("anno_inizio", r_all.index[0].year, "annonum", "Anno di inizio dell'analisi", "config.py")
    reg("p1_i", config.PERIODO_1[0], "annonum", "Primo anno del primo sotto-periodo", "config.py")
    reg("p1_f", config.PERIODO_1[1], "annonum", "Ultimo anno del primo sotto-periodo", "config.py")
    reg("p2_i", config.PERIODO_2[0], "annonum", "Primo anno del secondo sotto-periodo", "config.py")
    reg("n_perm", config.N_PERMUTAZIONI, "int", "Permutazioni del test", "config.py")
    reg("top_peggiori", config.TOP_PEGGIORI, "int", "Giorni peggiori tolti nel test di robustezza", "config.py")
    reg("media_tutti", float(r.mean() * PB), "num1", "Rendimento medio giornaliero di tutte le sedute, punti base")

    # --- giorni della settimana, tutto il periodo
    righe = []
    m_all = f.medie_per_gruppo(r, g_all)
    for d in range(5):
        x = r[g_all == d]
        se = x.std(ddof=1) / np.sqrt(len(x))
        righe.append(dict(giorno=NG[d], sedute=len(x), media_pb=x.mean() * PB, mediana_pb=np.median(x) * PB, quota_positivi=(x > 0).mean(),
                          lo_pb=(x.mean() - 1.96 * se) * PB, hi_pb=(x.mean() + 1.96 * se) * PB))
        reg(f"g{d}_n", len(x), "int", f"Sedute di {NG[d]}")
        reg(f"g{d}_media", x.mean() * PB, "num1", f"Rendimento medio di {NG[d]}, punti base")
        reg(f"g{d}_mediana", np.median(x) * PB, "num1", f"Rendimento mediano di {NG[d]}, punti base")
        reg(f"g{d}_pos", float((x > 0).mean()), "pct1", f"Quota di {NG[d]} con rendimento positivo")
        reg(f"g{d}_lo", (x.mean() - 1.96 * se) * PB, "num1", f"Estremo inferiore dell'intervallo al 95% della media di {NG[d]}, punti base")
        reg(f"g{d}_hi", (x.mean() + 1.96 * se) * PB, "num1", f"Estremo superiore dell'intervallo al 95% della media di {NG[d]}, punti base")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "giorni_settimana.csv", index=False, float_format="%.5f")
    reg("min_giorno", NG[int(np.argmin(m_all))], "testo", "Giorno con la media più bassa, tutto il periodo")
    reg("max_giorno", NG[int(np.argmax(m_all))], "testo", "Giorno con la media più alta, tutto il periodo")
    reg("differenza_estremi", float((m_all.max() - m_all.min()) * PB), "num1", "Differenza tra la media del giorno migliore e del peggiore, punti base")

    # --- sotto-periodi
    anno = r_all.index.year.to_numpy()
    p1 = (anno >= config.PERIODO_1[0]) & (anno <= config.PERIODO_1[1])
    p2 = (anno >= config.PERIODO_2[0]) & (anno <= config.PERIODO_2[1])
    m1 = f.medie_per_gruppo(r[p1], g_all[p1])
    m2 = f.medie_per_gruppo(r[p2], g_all[p2])
    # senza i giorni peggiori
    peggiori = np.argsort(r)[:config.TOP_PEGGIORI]
    tieni = np.ones(len(r), dtype=bool)
    tieni[peggiori] = False
    m3 = f.medie_per_gruppo(r[tieni], g_all[tieni])
    n_lun_peggiori = int((g_all[peggiori] == 0).sum())
    reg("peggiori_lunedi", n_lun_peggiori, "int", "Dei 10 giorni peggiori, quanti sono lunedì")
    reg("peggiore_rend", float(r[peggiori[0]]), "pct1", "Rendimento del giorno peggiore")
    reg("peggiore_data", str(r_all.index[peggiori[0]].date()), "data_lunga", "Data del giorno peggiore")
    reg("peggiore_giorno", NG[int(g_all[peggiori[0]])], "testo", "Giorno della settimana del giorno peggiore")
    tab = []
    for d in range(5):
        reg(f"p1_g{d}", m1[d] * PB, "num1", f"Media di {NG[d]} nel primo sotto-periodo, punti base")
        reg(f"p2_g{d}", m2[d] * PB, "num1", f"Media di {NG[d]} nel secondo sotto-periodo, punti base")
        reg(f"s_g{d}", m3[d] * PB, "num1", f"Media di {NG[d]} senza i 10 giorni peggiori, punti base")
        tab.append(dict(giorno=NG[d], periodo1_pb=m1[d] * PB, periodo2_pb=m2[d] * PB, senza_peggiori_pb=m3[d] * PB))
    pd.DataFrame(tab).to_csv(config.RISULTATI / "periodi.csv", index=False, float_format="%.5f")
    reg("min_giorno_p1", NG[int(np.argmin(m1))], "testo", "Giorno con la media più bassa nel primo sotto-periodo")
    reg("min_giorno_p2", NG[int(np.argmin(m2))], "testo", "Giorno con la media più bassa nel secondo sotto-periodo")
    reg("max_giorno_p2", NG[int(np.argmax(m2))], "testo", "Giorno con la media più alta nel secondo sotto-periodo")
    reg("min_giorno_s", NG[int(np.argmin(m3))], "testo", "Giorno con la media più bassa senza i 10 giorni peggiori")

    # --- permutazione
    p_val, sim = f.p_permutazione(r, g_all.copy(), config.N_PERMUTAZIONI, rng)
    pd.DataFrame({"differenza_pb": sim * PB}).to_csv(config.RISULTATI / "permutazioni.csv", index=False, float_format="%.4f")
    reg("p_valore", p_val, "pval", "P-value del test di permutazione (differenza tra giorno migliore e peggiore), tutto il periodo")
    reg("perm_p95", float(np.quantile(sim, 0.95) * PB), "num1", "95° percentile della differenza tra giorno migliore e peggiore nelle permutazioni, punti base")
    p1_val, _ = f.p_permutazione(r[p1], g_all[p1].copy(), 5000, rng)
    p2_val, _ = f.p_permutazione(r[p2], g_all[p2].copy(), 5000, rng)
    reg("p_valore_1", p1_val, "pval", "P-value del test di permutazione nel primo sotto-periodo (5.000 permutazioni)")
    reg("p_valore_2", p2_val, "pval", "P-value del test di permutazione nel secondo sotto-periodo (5.000 permutazioni)")

    # --- strategia senza lunedì
    lr = np.log1p(r)
    lun = g_all == 0
    tot = float(lr.sum())
    cagr_bh = float(np.exp(tot / anni) - 1)
    senza = tot - float(lr[lun].sum())
    cagr_s = float(np.exp(senza / anni) - 1)
    n_lun = int(lun.sum())
    senza_c = senza + 2 * n_lun * np.log(1 - config.COSTO)
    cagr_sc = float(np.exp(senza_c / anni) - 1)
    reg("cagr_bh", cagr_bh, "pct2", "Rendimento annuo composto del buy & hold")
    reg("cagr_senza", cagr_s, "pct2", "Rendimento annuo composto stando in liquidità ogni lunedì, senza costi")
    reg("diff_senza", cagr_s - cagr_bh, "pp2", "Differenza, punti all'anno (positiva = meglio del buy & hold)")
    reg("costo", config.COSTO, "pct2", "Costo per operazione della variante con costi", "config.py")
    reg("cagr_senza_costi", cagr_sc, "pct2", "Rendimento annuo composto senza lunedì con costo per operazione")
    reg("diff_senza_costi_assoluta", abs(cagr_sc - cagr_bh), "pp1", "Valore assoluto della differenza con i costi, punti all'anno")
    reg("operazioni_anno", 2 * n_lun / anni, "int", "Operazioni all'anno (due per ogni lunedì saltato)")
    cp = f.costo_pareggio(lr[lun])
    reg("costo_pareggio", cp, "pct2", "Costo per operazione che azzera il vantaggio (0 se nessun vantaggio)")
    reg("costo_pareggio_pb", cp * PB, "num1", "Costo di pareggio per operazione, punti base")

    # --- ipotesi
    reg("h3_p", config.H3_P, "pct0", "Ipotesi 3: soglia del p-value", "config.py")
    reg("h6_costo_pb", config.H6_COSTO * PB, "num1", "Ipotesi 6: soglia del costo di pareggio, punti base", "config.py")
    h = [int(np.argmin(m_all)) == 0,
         int(np.argmin(m2)) != 0,
         p_val < config.H3_P,
         int(np.argmin(m3)) != 0,
         cagr_s > cagr_bh,
         cp < config.H6_COSTO]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {[int(x) for x in h]}")


if __name__ == "__main__":
    main()
