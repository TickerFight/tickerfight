"""Passo 2 - PAC dal 2000: il piano di accumulo contro il lump sum, tutte le date di partenza e il caso.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  partenze.csv         per ogni mese di partenza dal 1928: rendimento totale netto del PAC e del lump sum a dieci anni
  curva_2000.csv       valore lordo mese per mese del piano che parte nel gennaio 2000 (PAC, lump sum, versato)
  curva_1929.csv       lo stesso per il piano che parte nel gennaio 1929
  quote_perm.csv       per ogni serie rimescolata, quota di piani con rendimento pari o peggiore di quello del piano 2000
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
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
           "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    pm = fx.prezzi_mensili(df["Close"].astype(float))
    p = pm.to_numpy(float)
    mesi_idx = pm.index
    n = len(p)
    rng = np.random.default_rng(config.SEME)
    M = config.MESI
    versato = config.VERSAMENTO * M

    pac, ls = fx.piani(p)
    starts = np.arange(len(pac))
    date_s = mesi_idx[starts]
    s2000 = int(np.flatnonzero(date_s == pd.Period(f"{config.ANNO_CASO}-01", freq="M"))[0])
    s1929 = int(np.flatnonzero(date_s == pd.Period(f"{config.ANNO_CRISI}-01", freq="M"))[0])
    pd.DataFrame({"partenza": date_s.astype(str), "pac": pac, "lump_sum": ls}).to_csv(
        config.RISULTATI / "partenze.csv", index=False, float_format="%.6f")
    for s, nome in ((s2000, "curva_2000.csv"), (s1929, "curva_1929.csv")):
        a, b, c = fx.curva_piano(p, s)
        pd.DataFrame({"mese": np.arange(M + 1), "data": mesi_idx[s:s + M + 1].astype(str), "pac": a, "lump_sum": b,
                      "versato": c, "prezzo": p[s:s + M + 1]}).to_csv(config.RISULTATI / nome, index=False, float_format="%.4f")

    reg("prima_data", str(df.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(df.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("anno_primo_piano", int(mesi_idx[0].year), "annonum", "Anno di partenza del primo piano decennale", "dati/")
    reg("anno_ultimo_piano", int(date_s[-1].year), "annonum", "Anno di partenza dell'ultimo piano decennale completo", "dati/")
    reg("n_partenze", len(pac), "int", "Mesi di partenza con un piano decennale completo", "partenze.csv")
    reg("mesi", M, "int", "Versamenti di ogni piano", "config.py, MESI")
    reg("anni_piano", M // 12, "annonum", "Anni di ogni piano", "config.py, MESI")
    reg("versamento", config.VERSAMENTO, "int", "Versamento mensile", "config.py, VERSAMENTO")
    reg("versato", versato, "int", "Totale versato in un piano", "config.py")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione per ogni acquisto e per la vendita finale", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulla plusvalenza", "config.py, ALIQUOTA")
    reg("anno_caso", config.ANNO_CASO, "annonum", "Anno di partenza del piano del caso principale", "config.py, ANNO_CASO")
    reg("anno_caso_fine", config.ANNO_CASO + M // 12 - 1, "annonum", "Ultimo anno di versamento del piano del caso principale", "config.py")
    reg("anno_crisi", config.ANNO_CRISI, "annonum", "Anno di partenza del secondo caso storico", "config.py, ANNO_CRISI")
    reg("h1_punti", config.H3_PUNTI, "pp1", "Ipotesi 1: vantaggio minimo del PAC sul lump sum, in punti percentuali", "config.py")
    reg("h2_margine", config.H1_MARGINE, "pct0", "Ipotesi 2: margine dal totale versato", "config.py")
    reg("h3_quota", config.H2_QUOTA, "pct0", "Ipotesi 3: quota delle date di partenza peggiori", "config.py")
    reg("h4_quota", config.H4_QUOTA, "pct0", "Ipotesi 4: quota massima di piani rimescolati peggiori del piano del 2000", "config.py")
    reg("n_perm", config.N_PERM, "int", "Serie rimescolate", "config.py, N_PERM")

    # --- Il piano del 2000 -------------------------------------------------------------------------------------
    a, b, c = fx.curva_piano(p, s2000)
    reg("prezzo_inizio", float(p[s2000]), "num1", "Chiusura dell'S&P 500 nel primo giorno di borsa del piano 2000", "dati/")
    reg("prezzo_fine", float(p[s2000 + M]), "num1", "Chiusura dell'S&P 500 alla vendita del piano 2000", "dati/")
    reg("prezzo_minimo", float(p[s2000:s2000 + M + 1].min()), "num1", "Minimo delle chiusure mensili durante il piano 2000", "dati/")
    reg("prezzo_minimo_data", f"{MESI_IT[mesi_idx[s2000 + int(np.argmin(p[s2000:s2000 + M + 1]))].month - 1]} {mesi_idx[s2000 + int(np.argmin(p[s2000:s2000 + M + 1]))].year}", "testo", "Mese del minimo delle chiusure mensili durante il piano 2000", "dati/")
    reg("indice_var", float(p[s2000 + M] / p[s2000] - 1), "pct0", "Variazione dell'indice tra l'inizio e la fine del piano 2000", "dati/")
    reg("pac_2000", float(pac[s2000]), "pct1", "Rendimento totale netto del PAC 2000 (valore finale netto diviso il versato, meno uno)", "partenze.csv")
    reg("ls_2000", float(ls[s2000]), "pct1", "Rendimento totale netto del lump sum 2000", "partenze.csv")
    reg("diff_2000", float(pac[s2000] - ls[s2000]), "pp1", "Rendimento del PAC 2000 meno quello del lump sum, in punti percentuali", "partenze.csv")
    reg("pac_2000_finale", float((1 + pac[s2000]) * versato), "int", "Valore finale netto del PAC 2000", "partenze.csv")
    reg("ls_2000_finale", float((1 + ls[s2000]) * versato), "int", "Valore finale netto del lump sum 2000", "partenze.csv")
    reg("pac_2000_max_perdita", float((a[1:] / c[1:] - 1).min()), "pct0", "Peggior rapporto tra valore lordo del PAC 2000 e versato fino a quel mese, meno uno", "curva_2000.csv")
    mmin = int(np.argmin(a[1:] / c[1:] - 1)) + 1
    reg("pac_2000_max_perdita_mese", mmin, "int", "Mese del piano (dal primo) con il peggior rapporto tra valore e versato", "curva_2000.csv")
    reg("ls_2000_max_perdita", float((b / b[0] - 1).min()), "pct0", "Peggior rendimento lordo del lump sum 2000 durante il piano", "curva_2000.csv")
    sotto = np.flatnonzero(a[1:] < c[1:]) + 1
    reg("pac_2000_mesi_sotto", len(sotto), "int", "Mesi (su centoventi) in cui il PAC 2000 vale meno del versato fino a quel momento", "curva_2000.csv")

    # --- Tutte le date di partenza -----------------------------------------------------------------------------
    rango = int((pac < pac[s2000]).sum() + 1)
    quota_real = float((pac <= pac[s2000]).mean())
    reg("rango_2000", rango, "int", "Posto del PAC 2000 tra tutte le partenze, dal peggiore (uno)", "partenze.csv")
    reg("quota_peggiori", quota_real, "pct1", "Quota di partenze con un PAC pari o peggiore di quello del 2000", "partenze.csv")
    ip = int(np.argmin(pac)); iq = int(np.argmax(pac))
    reg("pac_peggiore", float(pac[ip]), "pct0", "Rendimento totale netto del PAC peggiore", "partenze.csv")
    reg("pac_peggiore_anno", int(date_s[ip].year), "annonum", "Anno di partenza del PAC peggiore", "partenze.csv")
    reg("pac_migliore", float(pac[iq]), "pct0", "Rendimento totale netto del PAC migliore", "partenze.csv")
    reg("pac_migliore_anno", int(date_s[iq].year), "annonum", "Anno di partenza del PAC migliore", "partenze.csv")
    reg("pac_mediano", float(np.median(pac)), "pct0", "Rendimento totale netto mediano del PAC decennale", "partenze.csv")
    reg("n_pac_negativi", int((pac < 0).sum()), "int", "Partenze in cui il PAC chiude sotto il versato", "partenze.csv")
    reg("quota_pac_negativi", float((pac < 0).mean()), "pct1", "Quota di partenze in cui il PAC chiude sotto il versato", "partenze.csv")
    reg("n_ls_negativi", int((ls < 0).sum()), "int", "Partenze in cui il lump sum chiude sotto la somma investita", "partenze.csv")
    reg("quota_ls_negativi", float((ls < 0).mean()), "pct1", "Quota di partenze in cui il lump sum chiude sotto la somma investita", "partenze.csv")
    reg("quota_pac_batte_ls", float((pac > ls).mean()), "pct0", "Quota di partenze in cui il PAC fa meglio del lump sum", "partenze.csv")
    reg("quota_pac_batte_ls_neg", float((pac[ls < 0] > ls[ls < 0]).mean()) if (ls < 0).any() else 0.0, "pct0", "Tra le partenze in cui il lump sum perde, quota in cui il PAC fa meglio", "partenze.csv")
    reg("pac_mediano_ls_mediano", float(np.median(ls)), "pct0", "Rendimento totale netto mediano del lump sum decennale", "partenze.csv")

    # --- 1929 ----------------------------------------------------------------------------------------------------
    a9, b9, c9 = fx.curva_piano(p, s1929)
    reg("pac_1929", float(pac[s1929]), "pct1", "Rendimento totale netto del PAC che parte a gennaio 1929", "partenze.csv")
    reg("ls_1929", float(ls[s1929]), "pct1", "Rendimento totale netto del lump sum che parte a gennaio 1929", "partenze.csv")
    reg("indice_var_1929", float(p[s1929 + M] / p[s1929] - 1), "pct0", "Variazione dell'indice tra l'inizio e la fine del piano 1929", "dati/")
    reg("pac_1929_max_perdita", float((a9[1:] / c9[1:] - 1).min()), "pct0", "Peggior rapporto tra valore lordo del PAC 1929 e versato, meno uno", "curva_1929.csv")

    # --- Serie rimescolate ------------------------------------------------------------------------------------------
    quote = np.empty(config.N_PERM)
    neg = np.empty(config.N_PERM)
    for k in range(config.N_PERM):
        pr = fx.serie_rimescolata(p, rng)
        pp, _ = fx.piani(pr)
        quote[k] = (pp <= pac[s2000]).mean()
        neg[k] = (pp < 0).mean()
    pd.DataFrame({"quota_peggiori": quote, "quota_negativi": neg}).to_csv(config.RISULTATI / "quote_perm.csv", index=False, float_format="%.6f")
    reg("perm_quota_media", float(quote.mean()), "pct1", "Quota media di piani con rendimento pari o peggiore di quello del 2000 sulle serie rimescolate", "quote_perm.csv")
    reg("perm_quota_p95", float(np.percentile(quote, 95)), "pct1", "Novantacinquesimo percentile della quota di piani peggiori del 2000 sulle serie rimescolate", "quote_perm.csv")
    reg("perm_neg_media", float(neg.mean()), "pct1", "Quota media di piani in perdita (sotto il versato) sulle serie rimescolate", "quote_perm.csv")
    reg("perm_serie_sopra_reale", float((quote >= quota_real).mean()), "pct1", "Quota di serie rimescolate in cui la quota di piani peggiori del 2000 è pari o superiore a quella reale", "quote_perm.csv")

    # --- Verdetti sulle ipotesi -----------------------------------------------------------------------------------
    h1 = bool(pac[s2000] - ls[s2000] >= config.H3_PUNTI)
    h2 = bool(abs(pac[s2000]) <= config.H1_MARGINE)
    h3 = bool(quota_real <= config.H2_QUOTA)
    h4 = bool(quote.mean() < config.H4_QUOTA)
    h5 = bool(pac[s1929] < 0)
    for i, v in enumerate([h1, h2, h3, h4, h5], 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(h1 + h2 + h3 + h4 + h5), "int", "Ipotesi confermate (su cinque)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
