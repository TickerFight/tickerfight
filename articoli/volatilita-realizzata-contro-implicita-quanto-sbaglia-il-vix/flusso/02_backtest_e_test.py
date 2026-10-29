"""Passo 2 - Volatilità realizzata contro implicita: VIX e volatilità dell'S&P 500 che segue.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  fasce.csv         per fascia del VIX: quota di sedute, VIX medio, volatilità realizzata media, premio medio, quota di sedute con premio positivo
  mesi.csv          campione mensile non sovrapposto: data, VIX, volatilità realizzata successiva e passata, premio
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
N = config.RV_GIORNI


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
    lr_tutti = np.log(d["c"].to_numpy()[1:] / d["c"].to_numpy()[:-1])
    # allineamento: la posizione i dei rendimenti è il rendimento del giorno i+1 di d; il VIX e la volatilità del giorno t usano lr fino a t
    idx = d.index[1:]
    v = d["v"].to_numpy()[1:]
    rv_pass = f.vol_realizzata_passata(lr_tutti, N, GA)
    rv_fut = f.vol_realizzata_futura(lr_tutti, N, GA)
    ok = ~np.isnan(rv_pass) & ~np.isnan(rv_fut)
    t = np.flatnonzero(ok)
    vt, rf, rp = v[t], rv_fut[t], rv_pass[t]
    prem = vt - rf
    anni = (idx[t[-1]] - idx[t[0]]).days / 365.25

    reg("dati_prima_data", str(idx[t[0]].date()), "data_lunga", "Prima seduta con VIX, volatilità passata e futura", "dati/*.csv")
    reg("dati_ultima_data", str(idx[t[-1]].date()), "data_lunga", "Ultima seduta con volatilità futura calcolabile", "dati/*.csv")
    reg("dati_anni", anni, "num1", "Anni di storia usati")
    reg("n_giorni", len(t), "int", "Sedute usate")
    reg("rv_giorni", N, "int", "Sedute della volatilità realizzata (circa un mese)", "config.py")
    reg("vix_medio", float(vt.mean()), "num1", "VIX medio, punti")
    reg("rv_medio", float(rf.mean()), "num1", "Volatilità realizzata media nel mese successivo, punti")
    reg("premio_medio", float(prem.mean()), "num1", "Premio medio (VIX meno volatilità realizzata successiva), punti")
    reg("premio_mediano", float(np.median(prem)), "num1", "Premio mediano, punti")
    reg("quota_premio_pos", float((prem > 0).mean()), "pct0", "Quota di sedute in cui il VIX supera la volatilità realizzata successiva")
    i_min = int(np.argmin(prem))
    reg("premio_min", float(-prem[i_min]), "num1", "Sottostima massima: volatilità realizzata successiva meno VIX nel caso peggiore, punti")
    reg("premio_min_data", str(idx[t[i_min]].date()), "data_lunga", "Data del caso di maggiore sottostima del VIX")
    reg("premio_min_vix", float(vt[i_min]), "num1", "VIX nel giorno di maggiore sottostima, punti")
    reg("premio_min_rv", float(rf[i_min]), "num1", "Volatilità realizzata successiva nel giorno di maggiore sottostima, punti")
    reg("quota_sottostima_10", float((prem < -10).mean()), "pct1", "Quota di sedute in cui la volatilità realizzata supera il VIX di oltre 10 punti")
    reg("sottostima_10_punti", 10, "int", "Punti di sottostima della quota precedente", "config.py")

    # --- fasce del VIX
    righe = []
    for k in range(len(config.FASCE) - 1):
        lo, hi = config.FASCE[k], config.FASCE[k + 1]
        m = (vt >= lo) & (vt < hi)
        righe.append(dict(fascia=k, da=lo, a=hi, quota=m.mean(), vix=vt[m].mean(), rv=rf[m].mean(), premio=prem[m].mean(), quota_pos=(prem[m] > 0).mean()))
        reg(f"f{k}_quota", float(m.mean()), "pct0", f"Quota di sedute con il VIX nella fascia {k}")
        reg(f"f{k}_vix", float(vt[m].mean()), "num1", f"VIX medio nella fascia {k}, punti")
        reg(f"f{k}_rv", float(rf[m].mean()), "num1", f"Volatilità realizzata media nella fascia {k}, punti")
        reg(f"f{k}_premio", float(prem[m].mean()), "num1", f"Premio medio nella fascia {k}, punti")
        reg(f"f{k}_pos", float((prem[m] > 0).mean()), "pct0", f"Quota di sedute con premio positivo nella fascia {k}")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "fasce.csv", index=False, float_format="%.4f")
    reg("fascia_1_lim", config.FASCE[1], "int", "Limite superiore della prima fascia del VIX", "config.py")
    reg("fascia_2_lim", config.FASCE[2], "int", "Limite superiore della seconda fascia del VIX", "config.py")
    reg("fascia_3_lim", config.FASCE[3], "int", "Limite superiore della terza fascia del VIX", "config.py")

    # --- regressioni
    a, b, r2 = f.regressione(vt, rf)
    reg("reg_a", a, "num1", "Intercetta della regressione della volatilità realizzata successiva sul VIX, punti")
    reg("reg_b", b, "num2", "Pendenza della regressione della volatilità realizzata successiva sul VIX")
    reg("r2_vix", r2, "num2", "R quadro della regressione sul VIX")
    a2, b2, r2p = f.regressione(rp, rf)
    reg("r2_passato", r2p, "num2", "R quadro della regressione sulla volatilità realizzata dell'ultimo mese")
    reg("pend_passato", b2, "num2", "Pendenza della regressione sulla volatilità realizzata dell'ultimo mese")
    reg("corr_vix", float(np.corrcoef(vt, rf)[0, 1]), "num2", "Correlazione tra VIX e volatilità realizzata successiva")
    reg("corr_passato", float(np.corrcoef(rp, rf)[0, 1]), "num2", "Correlazione tra volatilità realizzata passata e successiva")

    # --- campione mensile non sovrapposto
    sel = np.arange(0, len(t), N)
    pm = prem[sel]
    mesi = pd.DataFrame(dict(data=idx[t][sel], vix=vt[sel], rv_successiva=rf[sel], rv_passata=rp[sel], premio=pm))
    mesi.to_csv(config.RISULTATI / "mesi.csv", index=False, float_format="%.4f")
    pos_somma = float(pm[pm > 0].sum())
    peggiori = np.sort(pm)[:config.N_PEGGIORI]
    reg("mesi_n", len(sel), "int", "Date del campione mensile non sovrapposto")
    reg("mesi_premio_medio", float(pm.mean()), "num1", "Premio medio nel campione mensile, punti")
    reg("mesi_neg_quota", float((pm < 0).mean()), "pct0", "Quota di mesi con premio negativo")
    reg("mesi_positivo_somma", pos_somma, "num1", "Somma dei premi mensili positivi, punti")
    reg("mesi_peggiori_n", config.N_PEGGIORI, "int", "Mesi peggiori considerati", "config.py")
    reg("mesi_peggiori_somma", float(-peggiori.sum()), "num1", "Somma (valore assoluto) dei premi dei mesi peggiori, punti")
    reg("mesi_peggiori_quota", float(-peggiori.sum() / pos_somma), "pct0", "Quota dei premi positivi cancellata dai mesi peggiori")
    reg("mesi_peggiore_premio", float(-peggiori[0]), "num1", "Premio del mese peggiore (valore assoluto), punti")

    reg("h1_quota", config.H1_QUOTA, "pct0", "Ipotesi 1: soglia", "config.py")
    reg("h2_min", config.H2_MIN, "num1", "Ipotesi 2: minimo del premio medio, punti", "config.py")
    reg("h2_max", config.H2_MAX, "num1", "Ipotesi 2: massimo del premio medio, punti", "config.py")
    reg("h5_quota", config.H5_QUOTA, "pct0", "Ipotesi 5: soglia", "config.py")
    reg("h6_pendenza", config.H6_PENDENZA, "num1", "Ipotesi 6: soglia della pendenza", "config.py")
    h = [float((prem > 0).mean()) >= config.H1_QUOTA,
         config.H2_MIN <= float(prem.mean()) <= config.H2_MAX,
         righe[-1]["premio"] > righe[0]["premio"],
         r2 > r2p,
         float(-peggiori.sum() / pos_somma) >= config.H5_QUOTA,
         b < config.H6_PENDENZA]
    for i, x in enumerate(h, 1):
        reg(f"h{i}_esito", int(x), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {[int(x) for x in h]}")


if __name__ == "__main__":
    main()
