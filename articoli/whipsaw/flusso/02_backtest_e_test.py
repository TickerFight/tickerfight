"""Passo 2 - Whipsaw: il filtro a 200 sedute sull'S&P 500, falsi segnali, durata delle uscite, costi e banda.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  uscite.csv        ogni uscita completa del filtro semplice: date, prezzi, durata, risultato (log del prezzo di uscita sul prezzo di rientro)
  decenni.csv       per decennio: cambi, cambi all'anno, quota di whipsaw, rendimento del buy & hold e del filtro
  rendimenti.csv    rendimento annuo composto delle cinque varianti
  esempio.csv       un tratto di serie con chiusura, media e posizioni (per il grafico)
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import funzioni as f

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"
GA = config.GIORNI_ANNO


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
    cv_tutti = c.to_numpy()
    sma_tutti = f.media_mobile(cv_tutti, config.SMA_GIORNI)
    i0 = config.SMA_GIORNI - 1                      # prima chiusura con la media calcolabile
    cv, sma, idx = cv_tutti[i0:], sma_tutti[i0:], c.index[i0:]
    lr_tutti = np.log(cv[1:] / cv[:-1])
    n = len(lr_tutti)
    anni = (idx[-1] - idx[0]).days / 365.25
    tot = float(lr_tutti.sum())

    pos_s = f.posizione_semplice(cv, sma)[:n]       # la posizione del giorno t usa la chiusura t
    pos_b = f.posizione_banda(cv, sma, config.BANDA)[:n]
    cagr_bh = f.cagr_da_log(tot, anni)
    cagr_f = f.cagr_da_log(f.log_strategia(lr_tutti, pos_s, 0.0), anni)  # senza costi: ln(1-costo) ~ 0
    cagr_fc = f.cagr_da_log(f.log_strategia(lr_tutti, pos_s, config.COSTO), anni)
    cagr_b = f.cagr_da_log(f.log_strategia(lr_tutti, pos_b, 0.0), anni)
    cagr_bc = f.cagr_da_log(f.log_strategia(lr_tutti, pos_b, config.COSTO), anni)
    cs, cb = f.cambi(pos_s), f.cambi(pos_b)

    reg("dati_prima_data", str(idx[0].date()), "data_lunga", "Prima chiusura con la media a 200 sedute calcolabile", "dati/")
    reg("dati_ultima_data", str(idx[-1].date()), "data_lunga", "Ultima chiusura dei dati", "dati/")
    reg("dati_anni", anni, "num1", "Anni di storia analizzati", "dati/")
    reg("sma_giorni", config.SMA_GIORNI, "int", "Sedute della media mobile", "config.py")
    reg("banda", config.BANDA, "pct0", "Banda attorno alla media", "config.py")
    reg("costo", config.COSTO, "pct2", "Costo di ogni cambio di posizione", "config.py")
    reg("breve", config.DURATA_BREVE, "int", "Sedute: un'uscita è breve se dura al massimo questo numero", "config.py")
    reg("top_n", config.TOP_N, "int", "Uscite migliori contate nell'ipotesi 3", "config.py")

    reg("cagr_bh", cagr_bh, "pct2", "Rendimento annuo composto del buy & hold (stessi anni)")
    reg("cagr_f", cagr_f, "pct2", "Rendimento annuo composto del filtro semplice, senza costi")
    reg("cagr_fc", cagr_fc, "pct2", "Rendimento annuo composto del filtro semplice, con costo a ogni cambio")
    reg("cagr_b", cagr_b, "pct2", "Rendimento annuo composto del filtro con banda, senza costi")
    reg("cagr_bc", cagr_bc, "pct2", "Rendimento annuo composto del filtro con banda, con costo a ogni cambio")
    reg("diff_f", cagr_f - cagr_bh, "pp2", "Filtro semplice senza costi meno buy & hold, punti all'anno")
    reg("diff_fc", cagr_fc - cagr_bh, "pp2", "Filtro semplice con costi meno buy & hold, punti all'anno")
    reg("diff_bc", cagr_bc - cagr_bh, "pp2", "Filtro con banda e costi meno buy & hold, punti all'anno")
    reg("costo_tot", cagr_f - cagr_fc, "pp2", "Punti all'anno tolti dai costi al filtro semplice")
    reg("esposizione", float(pos_s.mean()), "pct0", "Quota di sedute in cui il filtro semplice è investito")
    pd.DataFrame([dict(variante="buy_and_hold", cagr=cagr_bh), dict(variante="semplice_senza_costi", cagr=cagr_f),
                  dict(variante="semplice_con_costi", cagr=cagr_fc), dict(variante="banda_senza_costi", cagr=cagr_b),
                  dict(variante="banda_con_costi", cagr=cagr_bc)]).to_csv(config.RISULTATI / "rendimenti.csv", index=False, float_format="%.6f")

    reg("cambi_f", len(cs), "int", "Cambi di posizione del filtro semplice")
    reg("cambi_b", len(cb), "int", "Cambi di posizione del filtro con banda")
    reg("cambi_anno_f", len(cs) / anni, "num1", "Cambi di posizione all'anno, filtro semplice")
    reg("cambi_anno_b", len(cb) / anni, "num1", "Cambi di posizione all'anno, filtro con banda")
    riduzione = 1.0 - len(cb) / len(cs)
    reg("riduzione_cambi", riduzione, "pct0", "Riduzione dei cambi di posizione grazie alla banda")

    # --- uscite complete
    u, r = f.episodi(pos_s)
    durata = r - u
    risultato = np.log(cv[u] / cv[r])                # > 0: si è rientrati più in basso (uscita utile)
    whip = risultato <= 0
    ep = pd.DataFrame(dict(uscita=idx[u].date, rientro=idx[r].date, prezzo_uscita=cv[u], prezzo_rientro=cv[r],
                           sedute=durata, risultato_log=risultato, whipsaw=whip))
    ep.to_csv(config.RISULTATI / "uscite.csv", index=False, float_format="%.6f")
    reg("ep_n", len(u), "int", "Uscite complete (uscita seguita da rientro)")
    reg("ep_breve_quota", float((durata <= config.DURATA_BREVE).mean()), "pct0", "Quota di uscite che durano al massimo 20 sedute")
    reg("ep_dur_med", float(np.median(durata)), "int", "Durata mediana di un'uscita, in sedute")
    reg("ep_dur_max", int(durata.max()), "int", "Durata della uscita più lunga, in sedute")
    reg("ep_whip_n", int(whip.sum()), "int", "Uscite chiuse con un rientro a prezzo uguale o più alto (whipsaw)")
    reg("ep_whip_quota", float(whip.mean()), "pct0", "Quota di whipsaw tra le uscite complete")
    reg("whip_medio", float(np.mean(np.expm1(-risultato[whip]))), "pct1", "Variazione media del prezzo tra uscita e rientro nei whipsaw (rientro più caro di questa percentuale)")
    pos_r = risultato[~whip]
    reg("util_medio", float(np.mean(np.expm1(-pos_r))), "pct1", "Variazione media del prezzo tra uscita e rientro nelle uscite utili (rientro più basso di questa percentuale: valore negativo)")
    guad = np.sort(pos_r)[::-1]
    top = guad[:config.TOP_N].sum()
    reg("top_quota", float(top / guad.sum()), "pct0", "Quota della somma dei guadagni delle uscite in guadagno che viene dalle 10 migliori")
    reg("util_n", int((~whip).sum()), "int", "Uscite utili (rientro più basso)")
    reg("saldo_uscite", float(np.expm1(risultato.sum())), "pct0", "Effetto composto di tutte le uscite sul valore finale rispetto al buy & hold")
    corte = durata <= config.DURATA_BREVE
    reg("corte_whip_quota", float(whip[corte].mean()), "pct0", "Tra le uscite brevi, quota di whipsaw")
    reg("lunghe_whip_quota", float(whip[~corte].mean()), "pct0", "Tra le uscite più lunghe, quota di whipsaw")

    # --- periodi
    date_cambi = idx[cs]
    def per_anno(a, b):
        k = int(((date_cambi.year >= a) & (date_cambi.year <= b)).sum())
        return k, k / (b - a + 1)
    ka, pa = per_anno(*config.PERIODO_A)
    kb, pb_ = per_anno(*config.PERIODO_B)
    reg("per_a_i", config.PERIODO_A[0], "annonum", "Primo anno del periodo A", "config.py")
    reg("per_a_f", config.PERIODO_A[1], "annonum", "Ultimo anno del periodo A", "config.py")
    reg("per_b_i", config.PERIODO_B[0], "annonum", "Primo anno del periodo B", "config.py")
    reg("per_b_f", config.PERIODO_B[1], "annonum", "Ultimo anno del periodo B", "config.py")
    reg("per_a_anno", pa, "num1", "Cambi di posizione all'anno nel periodo A")
    reg("per_b_anno", pb_, "num1", "Cambi di posizione all'anno nel periodo B")
    rapporto = pa / pb_ if pb_ > 0 else float("inf")
    reg("rapporto_periodi", float(rapporto), "num1", "Cambi all'anno del periodo A diviso quelli del periodo B")

    # --- decenni
    righe = []
    for d0 in config.DECENNI:
        d1 = d0 + 9
        m = (idx[:-1].year >= d0) & (idx[:-1].year <= d1)
        a_dec = (idx[:-1][m][-1] - idx[:-1][m][0]).days / 365.25 + 1 / 252 if m.any() else 0
        if not m.any():
            continue
        lr_d = lr_tutti[m]
        pos_d = pos_s[m]
        k = int(((date_cambi.year >= d0) & (date_cambi.year <= d1)).sum())
        mu = (u >= 0) & (idx[u].year >= d0) & (idx[u].year <= d1)
        wq = float(whip[mu].mean()) if mu.any() else 0.0
        bh_d = f.cagr_da_log(float(lr_d.sum()), a_dec)
        f_d = f.cagr_da_log(float((lr_d * pos_d).sum()), a_dec)
        righe.append(dict(decennio=d0, cambi=k, anni=a_dec, cambi_anno=k / a_dec, uscite=int(mu.sum()), quota_whipsaw=wq, cagr_bh=bh_d, cagr_filtro=f_d))
        reg(f"d{d0}_cambi", k, "int", f"Cambi di posizione nel decennio {d0}")
        reg(f"d{d0}_anno", k / a_dec, "num1", f"Cambi di posizione all'anno nel decennio {d0}")
        reg(f"d{d0}_whip", wq, "pct0", f"Quota di whipsaw tra le uscite del decennio {d0}")
        reg(f"d{d0}_bh", bh_d, "pct1", f"Rendimento annuo composto del buy & hold nel decennio {d0}")
        reg(f"d{d0}_f", f_d, "pct1", f"Rendimento annuo composto del filtro semplice (senza costi) nel decennio {d0}")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "decenni.csv", index=False, float_format="%.5f")

    # --- esempio per il grafico
    a, b = pd.Timestamp(config.ESEMPIO[0]), pd.Timestamp(config.ESEMPIO[1])
    ex = pd.DataFrame({"data": idx[:n], "chiusura": cv[:n], "media": sma[:n], "pos": pos_s, "pos_banda": pos_b})
    ex[(ex["data"] >= a) & (ex["data"] <= b)].to_csv(config.RISULTATI / "esempio.csv", index=False, float_format="%.4f")
    reg("esempio_cambi", int(((idx[cs] >= a) & (idx[cs] <= b)).sum()), "int", "Cambi di posizione del filtro semplice nel tratto del grafico")
    reg("esempio_cambi_b", int(((idx[cb] >= a) & (idx[cb] <= b)).sum()), "int", "Cambi di posizione del filtro con banda nel tratto del grafico")
    reg("esempio_anno_i", a.year, "annonum", "Primo anno del tratto del grafico", "config.py")
    reg("esempio_anno_f", b.year, "annonum", "Ultimo anno del tratto del grafico", "config.py")

    # --- ipotesi
    reg("h1_quota", config.H1_QUOTA, "pct0", "Ipotesi 1: soglia", "config.py")
    reg("h2_quota", config.H2_QUOTA, "pct0", "Ipotesi 2: soglia", "config.py")
    reg("h3_quota", config.H3_QUOTA, "pct0", "Ipotesi 3: soglia", "config.py")
    reg("h5_rapporto", config.H5_RAPPORTO, "num1", "Ipotesi 5: soglia del rapporto", "config.py")
    reg("h6_riduzione", config.H6_RIDUZIONE, "pct0", "Ipotesi 6: soglia della riduzione", "config.py")
    h = [RIS["ep_breve_quota"]["valore"] >= config.H1_QUOTA,
         RIS["ep_whip_quota"]["valore"] >= config.H2_QUOTA,
         RIS["top_quota"]["valore"] >= config.H3_QUOTA,
         cagr_fc > cagr_bh,
         rapporto >= config.H5_RAPPORTO,
         riduzione >= config.H6_RIDUZIONE]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {[int(x) for x in h]}")


if __name__ == "__main__":
    main()
