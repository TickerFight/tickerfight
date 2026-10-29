"""Passo 2 - Tasse sulle plusvalenze: filtro a 200 sedute contro buy & hold, sull'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  rendimenti.csv       rendimento annuo composto delle varianti (lordo, netto, con costi, senza compensazione)
  aliquote.csv         vantaggio netto del filtro sul buy & hold per aliquota da 0% a 40%
  imposte_anni.csv     imposta pagata dal filtro in ogni anno solare, in percentuale del capitale a inizio anno
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
    i0 = config.SMA_GIORNI - 1
    cv, sma, idx = cv_tutti[i0:], sma_tutti[i0:], c.index[i0:]
    lr = np.log(cv[1:] / cv[:-1])
    n = len(lr)
    anni = (idx[-1] - idx[0]).days / 365.25
    yrs = idx[:n].year.to_numpy()
    pos_f = f.posizione_semplice(cv, sma)[:n]
    pos_bh = np.ones(n, dtype=int)

    def sim(pos, aliq, costo=0.0, cred=config.ANNI_CREDITO):
        return f.simula_fisco(lr, pos, yrs, aliq, costo, cred)

    bh_l, bh_n = sim(pos_bh, 0.0), sim(pos_bh, config.ALIQUOTA)
    f_l, f_n = sim(pos_f, 0.0), sim(pos_f, config.ALIQUOTA)
    f_nc = sim(pos_f, config.ALIQUOTA, config.COSTO)
    f_nz = sim(pos_f, config.ALIQUOTA, 0.0, -1)
    cg = lambda r: f.cagr_da_capitale(r["capitale"], anni)

    reg("dati_prima_data", str(idx[0].date()), "data_lunga", "Prima chiusura con la media a 200 sedute calcolabile", "dati/")
    reg("dati_ultima_data", str(idx[-1].date()), "data_lunga", "Ultima chiusura dei dati", "dati/")
    reg("dati_anni", anni, "num1", "Anni di storia analizzati", "dati/")
    reg("sma_giorni", config.SMA_GIORNI, "int", "Sedute della media mobile", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py")
    reg("costo", config.COSTO, "pct2", "Costo di ogni cambio di posizione (variante con costi)", "config.py")
    reg("anni_credito", config.ANNI_CREDITO, "int", "Anni solari successivi in cui valgono le minusvalenze", "config.py")
    reg("quota_top", config.QUOTA_ANNI_TOP, "pct0", "Quota di anni con più imposta, ipotesi 5", "config.py")

    cagr = dict(bh_lordo=cg(bh_l), bh_netto=cg(bh_n), filtro_lordo=cg(f_l), filtro_netto=cg(f_n), filtro_netto_costi=cg(f_nc), filtro_netto_senza_compensazione=cg(f_nz))
    for k, v in cagr.items():
        reg(f"cagr_{k}", v, "pct2", f"Rendimento annuo composto: {k.replace('_', ' ')}")
    pd.DataFrame([dict(variante=k, cagr=v) for k, v in cagr.items()]).to_csv(config.RISULTATI / "rendimenti.csv", index=False, float_format="%.6f")
    reg("cap_bh_l", bh_l["capitale"], "int", "Capitale finale del buy & hold lordo (partendo da 1)")
    reg("cap_bh_n", bh_n["capitale"], "int", "Capitale finale del buy & hold netto")
    reg("cap_f_l", f_l["capitale"], "int", "Capitale finale del filtro lordo")
    reg("cap_f_n", f_n["capitale"], "int", "Capitale finale del filtro netto")
    diff_l = cagr["filtro_lordo"] - cagr["bh_lordo"]
    diff_n = cagr["filtro_netto"] - cagr["bh_netto"]
    reg("diff_l", diff_l, "pp2", "Filtro meno buy & hold, lordo, punti all'anno")
    reg("diff_n", diff_n, "pp2", "Filtro meno buy & hold, dopo le imposte, punti all'anno (negativo = filtro peggio)")
    reg("diff_n_assoluta", abs(diff_n), "pp2", "Valore assoluto della differenza netta, punti all'anno")
    reg("diff_nc", cagr["filtro_netto_costi"] - cagr["bh_netto"], "pp2", "Filtro con imposte e costi meno buy & hold netto, punti all'anno")
    reg("diff_nc_assoluta", abs(cagr["filtro_netto_costi"] - cagr["bh_netto"]), "pp2", "Valore assoluto della differenza con imposte e costi")
    riduzione = 1.0 - diff_n / diff_l if diff_l > 0 else 0.0   # se il filtro non ha vantaggio lordo la riduzione non è definita: 0
    reg("riduzione_vantaggio", riduzione, "pct0", "Quota del vantaggio lordo del filtro tolta dalle imposte (oltre il 100% se il vantaggio diventa uno svantaggio)")
    reg("imposta_bh_punti", cagr["bh_lordo"] - cagr["bh_netto"], "pp2", "Punti all'anno tolti dall'imposta al buy & hold")
    reg("imposta_f_punti", cagr["filtro_lordo"] - cagr["filtro_netto"], "pp2", "Punti all'anno tolti dall'imposta al filtro")
    reg("compensazione_punti", cagr["filtro_netto"] - cagr["filtro_netto_senza_compensazione"], "pp2", "Punti all'anno recuperati grazie alla compensazione delle minusvalenze")
    q_bh = 1.0 - (bh_n["capitale"] - 1.0) / (bh_l["capitale"] - 1.0)
    q_f = 1.0 - (f_n["capitale"] - 1.0) / (f_l["capitale"] - 1.0)
    reg("quota_bh", q_bh, "pct0", "Quota del guadagno finale lordo che se ne va in imposte, buy & hold")
    reg("quota_f", q_f, "pct0", "Quota del guadagno finale lordo che se ne va in imposte, filtro")

    # realizzi
    reg("n_realizzi", len(f_n["realizzi"]), "int", "Plusvalenze o minusvalenze realizzate dal filtro (uscite più la liquidazione finale)")
    reg("n_guadagni", int((np.array(f_n["realizzi"]) > 0).sum()), "int", "Realizzi in plusvalenza")
    reg("n_perdite", int((np.array(f_n["realizzi"]) < 0).sum()), "int", "Realizzi in minusvalenza")
    reg("quota_perdite", float((np.array(f_n["realizzi"]) < 0).mean()), "pct0", "Quota di realizzi in minusvalenza")

    # imposte per anno
    anni_lista = sorted(set(int(y) for y in yrs))
    righe = []
    for a in anni_lista:
        t = f_n["imposte"].get(a, 0.0)
        righe.append(dict(anno=a, imposta=t, capitale_inizio=f_n["capitale_anno"][a], imposta_pct_capitale=t / f_n["capitale_anno"][a]))
    I = pd.DataFrame(righe)
    I.to_csv(config.RISULTATI / "imposte_anni.csv", index=False, float_format="%.6f")
    reg("anni_tot", len(I), "int", "Anni solari coperti")
    con = int((I["imposta"] > 0).sum())
    reg("anni_con_imposta", con, "int", "Anni in cui il filtro paga imposta")
    reg("quota_anni_imposta", con / len(I), "pct0", "Quota di anni in cui il filtro paga imposta")
    k = int(np.ceil(config.QUOTA_ANNI_TOP * len(I)))
    ordinate = np.sort(I["imposta_pct_capitale"].to_numpy())[::-1]
    reg("anni_top", k, "int", "Numero di anni nella quota più pesante")
    reg("quota_top_imposte", float(ordinate[:k].sum() / ordinate.sum()), "pct0", "Quota delle imposte totali (in percentuale del capitale a inizio anno) pagata dagli anni più pesanti")
    reg("imposta_max", float(I["imposta_pct_capitale"].max()), "pct1", "Imposta massima in un anno, in percentuale del capitale a inizio anno")
    reg("anno_max", int(I.loc[I["imposta_pct_capitale"].idxmax(), "anno"]), "annonum", "Anno con l'imposta più pesante")

    # aliquote
    righe_a, tab = [], []
    def diff_a(a):
        return cg(sim(pos_f, a)) - cg(sim(pos_bh, a))
    for a in config.ALIQUOTE:
        key = f"a{int(round(a * 1000))}"
        bh_a, f_a = cg(sim(pos_bh, a)), cg(sim(pos_f, a))
        reg(f"{key}_aliq", a, "pct1", f"Aliquota della riga {key}", "config.py")
        reg(f"{key}_bh", bh_a, "pct2", f"Rendimento annuo composto del buy & hold con aliquota {a}")
        reg(f"{key}_f", f_a, "pct2", f"Rendimento annuo composto del filtro con aliquota {a}")
        reg(f"{key}_d", f_a - bh_a, "pp2", f"Filtro meno buy & hold con aliquota {a}, punti all'anno")
    for a in np.arange(0.0, 0.4001, 0.02):
        righe_a.append(dict(aliquota=a, differenza=diff_a(a)))
    pd.DataFrame(righe_a).to_csv(config.RISULTATI / "aliquote.csv", index=False, float_format="%.6f")
    lo, hi = 0.0, 0.6
    if diff_a(hi) > 0:
        pareggio = hi
    elif diff_a(lo) <= 0:
        pareggio = lo
    else:
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if diff_a(mid) > 0 else (lo, mid)
        pareggio = (lo + hi) / 2
    reg("aliquota_pareggio", pareggio, "pct1", "Aliquota per cui il filtro rende come il buy & hold dopo le imposte (ricerca per bisezione)")

    reg("h1_riduzione", config.H1_RIDUZIONE, "pct0", "Ipotesi 1: soglia", "config.py")
    reg("h4_quota", config.H4_QUOTA, "pct0", "Ipotesi 4: soglia", "config.py")
    reg("h5_quota", config.H5_QUOTA, "pct0", "Ipotesi 5: soglia", "config.py")
    reg("h6_aliquota", config.H6_ALIQUOTA, "pct0", "Ipotesi 6: soglia", "config.py")
    h = [riduzione >= config.H1_RIDUZIONE,
         cagr["filtro_netto"] < cagr["bh_netto"],
         q_f > q_bh,
         con / len(I) >= config.H4_QUOTA,
         RIS["quota_top_imposte"]["valore"] >= config.H5_QUOTA,
         pareggio < config.H6_ALIQUOTA]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {[int(x) for x in h]}")


if __name__ == "__main__":
    main()
