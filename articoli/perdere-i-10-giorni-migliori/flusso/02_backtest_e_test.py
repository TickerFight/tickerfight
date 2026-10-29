"""Passo 2 - Perdere i 10 giorni migliori: rendimento composto saltando i giorni estremi, finestre mobili, regime e filtro a 200 sedute.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine
  tabella_giorni.csv     per ogni numero di giorni saltati: rendimento composto senza i migliori, senza i peggiori, senza entrambi
  giorni_estremi.csv     i 10 giorni migliori e i 10 peggiori: data, rendimento, regime, vicinanza
  finestre_perdita.csv   per ogni mese di partenza: perdita in punti all'anno saltando i 10 giorni migliori della finestra (10 e 20 anni)
  serie_indice.csv       chiusura settimanale e media a 200 sedute (per il grafico)
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


def si_no(b) -> str:
    return "sì" if b else "no"


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df["Close"].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    cv = c.to_numpy()
    date = c.index[1:]
    r = cv[1:] / cv[:-1] - 1.0
    lr = np.log1p(r)
    n = len(r)
    anni = (c.index[-1] - c.index[0]).days / 365.25
    sotto = f.sotto_media(cv, config.SMA_GIORNI)
    tot = lr.sum()
    cagr_bh = f.cagr_da_log(tot, anni)

    reg("dati_prima_data", str(c.index[0].date()), "data_lunga", "Prima chiusura dei dati", "dati/")
    reg("dati_ultima_data", str(c.index[-1].date()), "data_lunga", "Ultima chiusura dei dati", "dati/")
    reg("dati_anni", anni, "num1", "Anni di storia dei dati", "dati/")
    reg("sedute", n, "int", "Rendimenti giornalieri usati", "dati/")
    reg("cagr_bh", cagr_bh, "pct2", "Rendimento annuo composto del buy & hold sull'intera storia (indice di prezzo)")
    reg("sma_giorni", config.SMA_GIORNI, "int", "Sedute della media mobile del filtro", "config.py")
    reg("vicinanza", config.VICINANZA, "int", "Distanza massima in sedute per dire che un giorno è vicino a uno dei peggiori", "config.py")

    # --- A. saltare i giorni estremi sull'intera storia
    righe = []
    for N in config.N_GIORNI:
        ib = f.indici_estremi(r, N, True)
        ip = f.indici_estremi(r, N, False)
        sb, sp = lr[ib].sum(), lr[ip].sum()
        cb = f.cagr_da_log(tot - sb, anni)
        cp = f.cagr_da_log(tot - sp, anni)
        cx = f.cagr_da_log(tot - sb - sp, anni)
        righe.append(dict(giorni=N, cagr_senza_migliori=cb, cagr_senza_peggiori=cp, cagr_senza_entrambi=cx))
        reg(f"cb{N}", cb, "pct2", f"Rendimento annuo composto saltando i {N} giorni migliori")
        reg(f"cp{N}", cp, "pct2", f"Rendimento annuo composto saltando i {N} giorni peggiori")
        reg(f"cx{N}", cx, "pct2", f"Rendimento annuo composto saltando i {N} migliori e i {N} peggiori")
        reg(f"lb{N}", cagr_bh - cb, "pp2", f"Punti all'anno persi saltando i {N} giorni migliori")
        reg(f"gp{N}", cp - cagr_bh, "pp2", f"Punti all'anno guadagnati saltando i {N} giorni peggiori")
        reg(f"dx{N}", cx - cagr_bh, "pp2", f"Differenza in punti all'anno saltando i {N} migliori e i {N} peggiori (positiva = meglio del buy & hold)")
        reg(f"quota_b{N}", float(sb / tot), "pct0", f"Quota del rendimento logaritmico totale contenuta nei {N} giorni migliori")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "tabella_giorni.csv", index=False, float_format="%.6f")
    B = config.N_BASE
    ib = f.indici_estremi(r, B, True)
    ip = f.indici_estremi(r, B, False)
    reg("n_base", B, "int", "Giorni migliori e peggiori del caso principale", "config.py")
    reg("somma_b", float(np.expm1(lr[ib].sum())), "pct0", "Rendimento composto dei soli 10 giorni migliori messi in fila")
    reg("max_b", float(r[ib[0]]), "pct2", "Rendimento del giorno migliore")
    reg("min_p", float(r[ip[0]]), "pct2", "Rendimento del giorno peggiore")
    reg("medio_b", float(r[ib].mean()), "pct1", "Rendimento medio dei 10 giorni migliori")
    reg("medio_p", float(r[ip].mean()), "pct1", "Rendimento medio dei 10 giorni peggiori")
    reg("sedute_per_10", n / B, "int", "Sedute ogni giorno saltato nel caso principale (n sedute diviso 10)")

    # --- B. i giorni estremi: regime e vicinanza
    vic_b = f.vicino_a(ib, ip, config.VICINANZA)
    vic_p = f.vicino_a(ip, ib, config.VICINANZA)
    est = []
    for i, p in enumerate(ib, 1):
        reg(f"mg{i}_data", str(date[p].date()), "data", f"Data del {i}° giorno migliore")
        reg(f"mg{i}_rend", float(r[p]), "pct1", f"Rendimento del {i}° giorno migliore")
        reg(f"mg{i}_sotto", si_no(sotto[p]), "testo", f"Il {i}° giorno migliore veniva dopo una chiusura sotto la media a {config.SMA_GIORNI} sedute?")
        est.append(dict(tipo="migliore", posto=i, data=str(date[p].date()), rendimento=r[p], chiusura=cv[p + 1], sotto_media=bool(sotto[p]), vicino=bool(vic_b[i - 1])))
    for i, p in enumerate(ip, 1):
        reg(f"pg{i}_data", str(date[p].date()), "data", f"Data del {i}° giorno peggiore")
        reg(f"pg{i}_rend", float(r[p]), "pct1", f"Rendimento del {i}° giorno peggiore")
        reg(f"pg{i}_sotto", si_no(sotto[p]), "testo", f"Il {i}° giorno peggiore veniva dopo una chiusura sotto la media a {config.SMA_GIORNI} sedute?")
        est.append(dict(tipo="peggiore", posto=i, data=str(date[p].date()), rendimento=r[p], chiusura=cv[p + 1], sotto_media=bool(sotto[p]), vicino=bool(vic_p[i - 1])))
    pd.DataFrame(est).to_csv(config.RISULTATI / "giorni_estremi.csv", index=False, float_format="%.6f")
    n_sotto_b = int(sotto[ib].sum())
    n_sotto_p = int(sotto[ip].sum())
    reg("sotto_b_n", n_sotto_b, "int", "Dei 10 giorni migliori, quanti vengono dopo una chiusura sotto la media a 200 sedute")
    reg("sotto_b_quota", n_sotto_b / B, "pct0", "Quota dei 10 giorni migliori che vengono sotto la media a 200 sedute")
    reg("sotto_p_n", n_sotto_p, "int", "Dei 10 giorni peggiori, quanti vengono dopo una chiusura sotto la media a 200 sedute")
    reg("sotto_tutti", float(sotto.mean()), "pct0", "Quota di tutte le sedute che vengono sotto la media a 200 sedute (riferimento)")
    reg("vic_b_n", int(vic_b.sum()), "int", "Dei 10 giorni migliori, quanti cadono entro 30 sedute da uno dei 10 peggiori")
    reg("vic_p_n", int(vic_p.sum()), "int", "Dei 10 giorni peggiori, quanti cadono entro 30 sedute da uno dei 10 migliori")
    vic_tutti = f.vicino_a(np.arange(n), ip, config.VICINANZA)
    reg("vic_base", float(vic_tutti.mean()), "pct1", "Quota di tutte le sedute entro 30 sedute da uno dei 10 peggiori (riferimento)")

    # --- C. finestre mobili
    inizi_tutti = f.inizi_mese(date)
    serie = {}
    for N in config.FINESTRE_ANNI:
        lung = N * GA
        inizi = inizi_tutti[inizi_tutti + lung <= n]
        bh, sal = f.perdita_finestre(lr, inizi, lung, B, float(N))
        perdita = bh - sal
        q = np.quantile(perdita, [0.10, 0.50, 0.90])
        pos = bh > 0
        reg(f"w{N}_n", len(inizi), "int", f"Finestre di {N} anni (una per mese di partenza)")
        reg(f"w{N}_p10", float(q[0]), "pp2", f"10° percentile della perdita (punti all'anno) saltando i 10 giorni migliori, finestre di {N} anni")
        reg(f"w{N}_p50", float(q[1]), "pp2", f"Perdita mediana (punti all'anno) saltando i 10 giorni migliori, finestre di {N} anni")
        reg(f"w{N}_p90", float(q[2]), "pp2", f"90° percentile della perdita (punti all'anno), finestre di {N} anni")
        reg(f"w{N}_max", float(perdita.max()), "pp2", f"Perdita massima (punti all'anno), finestre di {N} anni")
        reg(f"w{N}_bh_med", float(np.median(bh)), "pct1", f"Rendimento annuo composto mediano del buy & hold, finestre di {N} anni")
        reg(f"w{N}_meta", float((perdita[pos] >= bh[pos] / 2).mean()), "pct0", f"Tra le finestre di {N} anni con rendimento positivo, quota in cui saltare i 10 giorni migliori toglie almeno metà del rendimento")
        reg(f"w{N}_neg", float((sal < 0).mean()), "pct0", f"Quota di finestre di {N} anni in cui, saltando i 10 giorni migliori, il rendimento annuo diventa negativo")
        reg(f"w{N}_neg_bh", float((bh < 0).mean()), "pct0", f"Quota di finestre di {N} anni in cui il buy & hold ha già rendimento negativo")
        serie[N] = pd.Series(perdita, index=date[inizi])
    pd.concat({f"perdita_{k}_anni": v for k, v in serie.items()}, axis=1).rename_axis("data").reset_index().to_csv(
        config.RISULTATI / "finestre_perdita.csv", index=False, float_format="%.6f")

    # --- D. controllo: 10 giorni a caso
    rng = np.random.default_rng(config.SEME)
    perd = np.empty(config.CASUALI_N)
    for k in range(config.CASUALI_N):
        idx = rng.choice(n, B, replace=False)
        perd[k] = cagr_bh - f.cagr_da_log(tot - lr[idx].sum(), anni)
    reg("caso_n", config.CASUALI_N, "int", "Estrazioni di 10 giorni a caso", "config.py")
    reg("caso_media", float(perd.mean()), "pp2", "Perdita media (punti all'anno) saltando 10 giorni a caso")
    reg("caso_p5", float(np.quantile(perd, 0.05)), "pp2", "5° percentile della perdita saltando 10 giorni a caso")
    reg("caso_p95", float(np.quantile(perd, 0.95)), "pp2", "95° percentile della perdita saltando 10 giorni a caso")

    # --- E. il filtro a 200 sedute
    strat = np.where(sotto, 0.0, r)
    cagr_f = f.cagr_da_log(np.log1p(strat).sum(), anni)
    reg("cagr_filtro", cagr_f, "pct2", "Rendimento annuo composto del filtro a 200 sedute (fuori = rendimento zero)")
    reg("diff_filtro", cagr_f - cagr_bh, "pp2", "Differenza del filtro rispetto al buy & hold, punti all'anno (negativa = peggio)")
    reg("esposizione", float(1 - sotto.mean()), "pct0", "Quota di sedute in cui il filtro è investito")
    reg("filtro_manca_b", n_sotto_b, "int", "Dei 10 giorni migliori, quanti il filtro salta")
    reg("filtro_evita_p", n_sotto_p, "int", "Dei 10 giorni peggiori, quanti il filtro evita")
    c_ser = pd.DataFrame({"chiusura": c, "media": c.rolling(config.SMA_GIORNI).mean()})
    c_ser.iloc[::5].rename_axis("data").reset_index().to_csv(config.RISULTATI / "serie_indice.csv", index=False, float_format="%.4f")

    # --- ipotesi
    reg("h1_punti", config.H1_PUNTI, "pp1", "Ipotesi 1: soglia in punti all'anno", "config.py")
    reg("h2_punti", config.H2_PUNTI, "pp1", "Ipotesi 2: soglia in punti all'anno", "config.py")
    reg("h3_quota", config.H3_QUOTA, "pct0", "Ipotesi 3: soglia", "config.py")
    reg("h5_vicini", config.H5_VICINI, "int", "Ipotesi 5: soglia (giorni su dieci)", "config.py")
    h = [(cagr_bh - RIS["cb10"]["valore"]) >= config.H1_PUNTI,
         RIS["w20_p50"]["valore"] >= config.H2_PUNTI,
         n_sotto_b / B >= config.H3_QUOTA,
         RIS["gp10"]["valore"] > RIS["lb10"]["valore"],
         int(vic_b.sum()) >= config.H5_VICINI,
         cagr_f < cagr_bh]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {[int(x) for x in h]}")


if __name__ == "__main__":
    main()
