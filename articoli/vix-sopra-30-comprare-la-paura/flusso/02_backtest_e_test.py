"""Passo 2 - VIX sopra 30: che cosa fa l'S&P 500 dopo?

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  episodi.csv       un record per episodio (soglia base): date, VIX, rendimenti a 21/63/126/252 sedute, peggior chiusura nelle 63 successive
  soglie.csv        per ciascuna soglia della griglia: episodi, rendimento medio a un anno, rendimento generico
  scimmie.csv       rendimenti medi delle scimmie a ciascun orizzonte
  curve.csv         S&P 500 e VIX (una seduta su cinque) per il grafico del contesto
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as f

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def carica(ticker):
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit(f"{ticker}: chiusure mancanti o non positive.")
    return c


def main():
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    if any(r["stato"] != "ok" for r in meta["indici"]):
        raise SystemExit("Mancano i dati di S&P 500 o VIX.")
    close, vix = carica(config.TICKER_INDICE), carica(config.TICKER_VIX)
    d = pd.concat({"c": close, "v": vix}, axis=1, join="inner").dropna()
    c, v = d["c"].to_numpy(), d["v"].to_numpy()
    n = len(d)
    anni = (d.index[-1] - d.index[0]).days / 365.25
    rng = np.random.default_rng(config.SEME)
    R = config.RISULTATI
    prima = config.QUIETE + 1       # prima entrata possibile: stessa per episodi e confronto generico
    a = (1 - config.LIVELLO_CONFIDENZA) / 2

    reg("dati_prima_data", str(d.index[0].date()), "data_lunga", "Prima seduta con S&P 500 e VIX insieme", "dati/*.csv")
    reg("dati_ultima_data", str(d.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/*.csv")
    reg("dati_anni", anni, "num1", "Anni di storia usati")
    reg("dati_sedute", n, "annonum", "Sedute usate")
    reg("vix_massimo", float(v.max()), "num1", "Massimo della chiusura del VIX nei dati")
    reg("vix_massimo_data", str(d.index[int(v.argmax())].date()), "data_lunga", "Data del massimo della chiusura del VIX")
    reg("vix_mediano", float(np.median(v)), "num1", "Mediana della chiusura del VIX nei dati")
    reg("quota_sopra_soglia", float((v > config.SOGLIA_BASE).mean()), "pct1", "Quota di sedute con il VIX sopra la soglia base")

    # --- griglia delle soglie ------------------------------------------------------------------
    righe_s, cerca = [], {}
    for sg in config.GRIGLIA_SOGLIE:
        ep = f.episodi(v, sg, config.QUIETE)
        ent = ep + 1
        ent = ent[ent < n]
        r252 = f.rendimenti_forward(c, ent, 252)
        gen = c[np.arange(prima, n - 252) + 252] / c[np.arange(prima, n - 252)] - 1.0
        cerca[sg] = dict(ep=ep, ent=ent, r252=r252, gen=float(gen.mean()))
        righe_s.append(dict(soglia=sg, episodi=len(ep), validi_252=len(r252), media_252=float(r252.mean()) if len(r252) else np.nan,
                            generico_252=float(gen.mean())))
        k = int(sg)
        reg(f"sg{k}_episodi", len(ep), "int", f"Episodi con il VIX sopra {k}")
        reg(f"sg{k}_validi", len(r252), "int", f"Episodi con un anno di dati davanti, soglia {k}")
        if len(r252):
            reg(f"sg{k}_media", float(r252.mean()), "pct1", f"Rendimento medio a un anno degli episodi, soglia {k}")
        reg(f"sg{k}_generico", float(gen.mean()), "pct1", f"Rendimento medio a un anno su una seduta qualunque (stesso periodo), soglia {k}")
    pd.DataFrame(righe_s).to_csv(R / "soglie.csv", index=False, float_format="%.6f")
    valutabili = [s for s in config.GRIGLIA_SOGLIE if len(cerca[s]["r252"]) >= config.EPISODI_MIN_GRIGLIA]
    ok = [s for s in valutabili if cerca[s]["r252"].mean() > cerca[s]["gen"]]
    reg("n_soglie_valutabili", len(valutabili), "int", "Soglie con almeno cinque episodi con un anno di dati davanti")
    reg("n_soglie_ok", len(ok), "int", "Soglie valutabili in cui il rendimento medio a un anno supera quello generico")
    reg("episodi_min_griglia", config.EPISODI_MIN_GRIGLIA, "int", "Numero minimo di episodi per valutare una soglia", "config.py")

    # --- soglia base ---------------------------------------------------------------------------
    B = cerca[config.SOGLIA_BASE]
    ep, ent = B["ep"], B["ent"]
    reg("soglia_base", config.SOGLIA_BASE, "int", "Soglia del VIX", "config.py")
    reg("quiete", config.QUIETE, "int", "Sedute sotto la soglia prima di un nuovo episodio", "config.py")
    reg("n_episodi", len(ep), "int", "Episodi indipendenti con il VIX sopra la soglia base")
    reg("episodi_prima", str(d.index[ep[0]].date()), "data_lunga", "Data del primo episodio")
    reg("episodi_ultima", str(d.index[ep[-1]].date()), "data_lunga", "Data dell'ultimo episodio")

    tab = pd.DataFrame({"segnale": d.index[ep].strftime("%Y-%m-%d"), "acquisto": d.index[ent].strftime("%Y-%m-%d") if len(ent) == len(ep) else "",
                        "vix": v[ep]}) if len(ent) == len(ep) else pd.DataFrame({"segnale": d.index[ep].strftime("%Y-%m-%d"), "vix": v[ep]})
    for h in config.ORIZZONTI:
        col = np.full(len(ep), np.nan)
        e2 = ep + 1
        ok_i = e2 + h < n
        col[ok_i] = c[e2[ok_i] + h] / c[e2[ok_i]] - 1.0
        tab[f"r{h}"] = col
    mn = np.full(len(ep), np.nan)
    e2 = ep + 1
    ok_m = e2 + config.ORIZZONTE_MIN < n
    mn[ok_m] = [c[x + 1:x + config.ORIZZONTE_MIN + 1].min() / c[x] - 1.0 for x in e2[ok_m]]
    tab["min63"] = mn
    tab.to_csv(R / "episodi.csv", index=False, float_format="%.6f")

    righe_sc = []
    for h in config.ORIZZONTI:
        r = f.rendimenti_forward(c, ent, h)
        validi = np.arange(prima, n - h)
        gen = c[validi + h] / c[validi] - 1.0
        sc = f.scimmie_medie(c, validi, len(r), h, config.N_SCIMMIE, rng)
        lo, hi = [float(x) for x in np.quantile(sc, [a, 1 - a])]
        pup = (int((sc >= r.mean()).sum()) + 1) / (config.N_SCIMMIE + 1)
        pdw = (int((sc <= r.mean()).sum()) + 1) / (config.N_SCIMMIE + 1)
        p2 = min(1.0, 2 * min(pup, pdw))
        righe_sc.append(dict(orizzonte=h, k=len(r), media_ep=float(r.mean()), media_gen=float(gen.mean()), lo=lo, hi=hi, p2=p2))
        reg(f"h{h}_validi", len(r), "int", f"Episodi con {h} sedute di dati davanti")
        reg(f"h{h}_media", float(r.mean()), "pct1", f"Rendimento medio degli episodi a {h} sedute")
        reg(f"h{h}_mediana", float(np.median(r)), "pct1", f"Rendimento mediano degli episodi a {h} sedute")
        reg(f"h{h}_quota_pos", float((r > 0).mean()), "pct0", f"Quota di episodi con rendimento positivo a {h} sedute")
        reg(f"h{h}_peggiore", float(r.min()), "pct1", f"Peggior rendimento di un episodio a {h} sedute")
        reg(f"h{h}_migliore", float(r.max()), "pct1", f"Miglior rendimento di un episodio a {h} sedute")
        reg(f"h{h}_generico", float(gen.mean()), "pct1", f"Rendimento medio a {h} sedute da una seduta qualunque")
        reg(f"h{h}_diff", float(r.mean() - gen.mean()), "pp1", f"Differenza tra episodi e generico a {h} sedute")
        reg(f"h{h}_sc_lo", lo, "pct1", f"Estremo basso dell'intervallo al 95% delle scimmie a {h} sedute")
        reg(f"h{h}_sc_hi", hi, "pct1", f"Estremo alto dell'intervallo al 95% delle scimmie a {h} sedute")
        reg(f"h{h}_p", p2, "pval", f"p-value a due code (scimmie) a {h} sedute")
        reg(f"h{h}_p_su", pup, "pval", f"Quota di scimmie con rendimento medio pari o sopra gli episodi, {h} sedute")
    pd.DataFrame(righe_sc).to_csv(R / "scimmie.csv", index=False, float_format="%.6f")

    m63 = f.minimo_successivo(c, ent, config.ORIZZONTE_MIN)
    reg("orizzonte_min", config.ORIZZONTE_MIN, "int", "Sedute osservate dopo l'acquisto per il minimo successivo", "config.py")
    reg("quota_scende_ancora", float((m63 < 0).mean()), "pct0", "Quota di episodi in cui, entro 63 sedute, almeno una chiusura è sotto il prezzo pagato")
    reg("minimo_medio", float(m63.mean()), "pct1", "Peggior chiusura media nelle 63 sedute dopo l'acquisto, rispetto al prezzo pagato")
    reg("minimo_peggiore", float(m63.min()), "pct1", "Peggior chiusura in assoluto nelle 63 sedute dopo un acquisto")
    r252 = f.rendimenti_forward(c, ent, 252)
    reg("peggiore_anno", int(d.index[ent[r252.argmin()]].year), "annonum", "Anno dell'acquisto con il peggior rendimento a un anno")
    reg("migliore_anno", int(d.index[ent[r252.argmax()]].year), "annonum", "Anno dell'acquisto con il miglior rendimento a un anno")
    reg("n_negativi_252", int((r252 <= 0).sum()), "int", "Episodi con rendimento a un anno non positivo")
    # quanti episodi raggruppati in poche crisi: episodi con acquisto nello stesso anno
    anni_ep = pd.Series(d.index[ent].year)
    reg("n_anni_con_episodi", int(anni_ep.nunique()), "int", "Anni di calendario diversi in cui cade almeno un episodio")

    # --- ipotesi --------------------------------------------------------------------------------
    reg("h3_quota", config.H3_QUOTA, "pct0", "Soglia dell'ipotesi 3", "config.py")
    reg("h4_quota", config.H4_QUOTA, "pct0", "Soglia dell'ipotesi 4", "config.py")
    reg("h6_episodi", config.H6_EPISODI, "int", "Soglia dell'ipotesi 6 sul numero di episodi", "config.py")
    reg("soglia_forte", config.SOGLIA_FORTE, "pval", "Livello severo del p-value", "config.py")
    reg("soglia_p", config.SOGLIA, "pval", "Livello ordinario del p-value", "config.py")
    h1 = RIS["h252_media"]["valore"] > RIS["h252_generico"]["valore"]
    h2 = RIS["h21_sc_lo"]["valore"] <= RIS["h21_media"]["valore"] <= RIS["h21_sc_hi"]["valore"]
    h3 = RIS["quota_scende_ancora"]["valore"] > config.H3_QUOTA
    h4 = RIS["h252_quota_pos"]["valore"] > config.H4_QUOTA
    h5 = len(valutabili) > 0 and len(ok) == len(valutabili)
    h6 = len(ep) < config.H6_EPISODI and RIS["h252_p"]["valore"] > config.SOGLIA_FORTE
    esiti = [h1, h2, h3, h4, h5, h6]
    for i, e in enumerate(esiti, 1):
        reg(f"h{i}_esito", "confermata" if e else "smentita", "testo", f"Esito dell'ipotesi {i}", "config.py e metriche")
    reg("n_conf", int(sum(esiti)), "int", "Ipotesi confermate su sei")
    reg("n_smentite", int(6 - sum(esiti)), "int", "Ipotesi smentite su sei")

    reg("n_scimmie", config.N_SCIMMIE, "int", "Numero di scimmie", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello di confidenza", "config.py")
    reg("giorni_anno", config.GIORNI_ANNO, "int", "Sedute in un anno", "config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(R / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    camp = np.arange(0, n, 5)
    pd.DataFrame({"data": d.index[camp], "spx": c[camp], "vix": v[camp]}).to_csv(R / "curve.csv", index=False, float_format="%.4f")
    print(tab.to_string())
    print(pd.DataFrame(righe_sc).to_string())
    print(f"Scritti {len(RIS)} numeri in metriche.json")


if __name__ == "__main__":
    main()
