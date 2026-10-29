"""Passo 2 - Esecuzione a chiusura, apertura o prezzo medio: due regole a media mobile sullo SPY.

Legge SOLO dati/spy_ohlc.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  per_prezzo.csv    per regola e prezzo di esecuzione: CAGR, Sharpe, volatilità, perdita massima (senza e con costo)
  costi.csv         CAGR della regola veloce con esecuzione all'apertura al variare del costo per operazione
  curve.csv         valore di 1 dollaro per la regola veloce con i quattro prezzi e per il buy & hold (una seduta su cinque)
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
GA = config.GIORNI_ANNO
MODI = [("st", "stessa_chiusura", "alla stessa chiusura del segnale"), ("ap", "apertura", "all'apertura del giorno dopo"),
        ("pm", "prezzo_medio", "al prezzo medio del giorno dopo"), ("cd", "chiusura_dopo", "alla chiusura del giorno dopo")]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    for col in ("Open", "High", "Low", "Close"):
        if (df[col] <= 0).any() or df[col].isna().any():
            raise SystemExit(f"{col}: prezzi mancanti o non positivi.")
    O, H, L, C = (df[k].to_numpy(dtype=float) for k in ("Open", "High", "Low", "Close"))
    A = (O + H + L + C) / 4.0
    date = df.index
    n_tot = len(df)
    rng = np.random.default_rng(config.SEME)
    t0 = max(config.MEDIE) + 1                      # primo giorno in cui tutte le regole hanno il segnale del giorno t-2
    sl = slice(t0, n_tot)
    date_c = date[sl]
    anni = len(date_c) / GA

    reg("prima_data", str(date_c[0].date()), "data_lunga", "Primo giorno del campione comune alle due regole", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_sedute", len(date_c), "int", "Sedute del campione comune", "dati/")
    reg("anni", anni, "num1", "Anni del campione comune (sedute diviso 252)", "dati/")
    reg("media_lenta", config.MEDIE[0], "int", "Lunghezza della media mobile lenta", "config.py, MEDIE")
    reg("media_veloce", config.MEDIE[1], "int", "Lunghezza della media mobile veloce", "config.py, MEDIE")
    reg("costo_base", config.COSTO_BASE, "pct2", "Costo per ogni cambio di posizione nel caso con costi", "config.py, COSTO_BASE")
    reg("n_boot", config.N_BOOT, "int", "Ricampionamenti bootstrap", "config.py, N_BOOT")
    reg("blocco", config.BLOCCO, "int", "Sedute per blocco del bootstrap", "config.py, BLOCCO")
    reg("livello_ic", config.LIVELLO_IC, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("h1_punti", config.H1_PUNTI, "pp1", "Ipotesi 1: vantaggio minimo della stessa chiusura, in punti", "config.py")
    reg("h2_punti", config.H2_PUNTI, "pp1", "Ipotesi 2: scarto massimo per la regola lenta, in punti", "config.py")
    reg("h4_quota", config.H4_QUOTA, "pct0", "Ipotesi 4: quota minima del rendimento che avviene di notte", "config.py")

    # --- Buy & hold e componenti del rendimento --------------------------------------------------------------------
    r_bh = np.log(C[1:] / C[:-1])[t0 - 1:]
    mbh = fx.metriche(r_bh, GA)
    for k, v in mbh.items():
        reg(f"bh_{k}", v, {"cagr": "pct1", "vol": "pct1", "sharpe": "num2", "dd": "pct0"}[k] if k != "dd" else "pct0", f"Buy & hold, {k}", "funzioni.metriche")
    RIS["bh_dd"]["valore"] = -mbh["dd"]
    notte = np.log(O[1:] / C[:-1])
    giorno = np.log(C[1:] / O[1:])
    tot = notte.sum() + giorno.sum()
    reg("notte_quota", float(notte.sum() / tot), "pct0", "Quota del rendimento logaritmico totale dello SPY che avviene di notte (chiusura-apertura)", "dati/")
    reg("giorno_quota", float(giorno.sum() / tot), "pct0", "Quota del rendimento logaritmico totale che avviene di giorno (apertura-chiusura)", "dati/")
    reg("cagr_notte", float(np.exp(notte.mean() * GA) - 1), "pct1", "Rendimento annuo composto di chi tiene lo SPY solo di notte", "dati/")
    reg("cagr_giorno", float(np.exp(giorno.mean() * GA) - 1), "pct1", "Rendimento annuo composto di chi tiene lo SPY solo di giorno", "dati/")
    reg("cagr_totale", float(np.exp(np.log(C[-1] / C[0]) / ((n_tot - 1) / GA)) - 1), "pct1", "Rendimento annuo composto dello SPY su tutti i dati", "dati/")

    # --- Le due regole con i quattro prezzi ---------------------------------------------------------------------------
    righe, serie = [], {}
    cagr_matrix = {}
    for n in config.MEDIE:
        pos = fx.posizione(C, n)
        tag = "s200" if n == config.MEDIE[0] else "s20"
        reg(f"{tag}_cambi", fx.cambi(pos[t0 - 2:]), "int", f"Cambi di posizione della regola a {n} sedute nel campione", "funzioni.cambi")
        reg(f"{tag}_cambi_anno", fx.cambi(pos[t0 - 2:]) / anni, "num1", f"Cambi di posizione all'anno, regola a {n} sedute", "funzioni.cambi")
        reg(f"{tag}_quota_inv", float(np.nanmean(pos[t0 - 2:])), "pct0", f"Quota di giorni investiti, regola a {n} sedute", "funzioni.posizione")
        for sig, modo, desc in MODI:
            r0 = fx.log_rendimenti_regola(O, C, A, pos, modo, 0.0)[sl]
            r1 = fx.log_rendimenti_regola(O, C, A, pos, modo, config.COSTO_BASE)[sl]
            m0, m1 = fx.metriche(r0, GA), fx.metriche(r1, GA)
            cagr_matrix[(tag, sig)] = m0["cagr"]
            serie[(tag, sig)] = r0
            serie[(tag, sig, "costo")] = r1
            righe.append({"regola": n, "prezzo": modo, **{k: v for k, v in m0.items()}, **{k + "_costo": v for k, v in m1.items()}})
            reg(f"{tag}_{sig}_cagr", m0["cagr"], "pct1", f"Rendimento annuo composto, regola a {n} sedute, esecuzione {desc}", "funzioni.log_rendimenti_regola")
            reg(f"{tag}_{sig}_sharpe", m0["sharpe"], "num2", f"Sharpe, regola a {n} sedute, esecuzione {desc}", "funzioni.metriche")
            reg(f"{tag}_{sig}_dd", -m0["dd"], "pct0", f"Perdita massima, regola a {n} sedute, esecuzione {desc}", "funzioni.metriche")
            reg(f"{tag}_{sig}_cagr_c", m1["cagr"], "pct1", f"Rendimento annuo composto con costo, regola a {n} sedute, esecuzione {desc}", "funzioni.log_rendimenti_regola")
        v = [cagr_matrix[(tag, s)] for s, _, _ in MODI]
        reg(f"{tag}_scarto", max(v) - min(v), "pp1", f"Scarto tra il migliore e il peggiore prezzo di esecuzione, CAGR, regola a {n} sedute, in punti", "per_prezzo.csv")
        reg(f"{tag}_st_meno_ap", cagr_matrix[(tag, "st")] - cagr_matrix[(tag, "ap")], "pp1", f"CAGR con stessa chiusura meno CAGR con apertura, regola a {n} sedute, in punti", "per_prezzo.csv")
        reg(f"{tag}_ap_meno_cd", cagr_matrix[(tag, "ap")] - cagr_matrix[(tag, "cd")], "pp1", f"CAGR con apertura meno CAGR con chiusura del giorno dopo, regola a {n} sedute, in punti", "per_prezzo.csv")
        reg(f"{tag}_ap_meno_bh", cagr_matrix[(tag, "ap")] - mbh["cagr"], "pp1", f"CAGR con apertura meno CAGR del buy & hold, regola a {n} sedute, in punti", "per_prezzo.csv")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "per_prezzo.csv", index=False, float_format="%.5f")

    # --- Costo per operazione, regola veloce con esecuzione all'apertura -----------------------------------------------------
    pos20 = fx.posizione(C, config.MEDIE[1])
    costi = []
    for i, c in enumerate(config.COSTI_GRIGLIA):
        m = fx.metriche(fx.log_rendimenti_regola(O, C, A, pos20, "apertura", c)[sl], GA)
        costi.append({"costo": c, "cagr": m["cagr"]})
        reg(f"costo{i}", c, "pct2", f"Costo per operazione, punto {i} della griglia", "config.py, COSTI_GRIGLIA")
        reg(f"costo{i}_cagr", m["cagr"], "pct1", f"CAGR della regola veloce, apertura, con questo costo", "funzioni.log_rendimenti_regola")
    pd.DataFrame(costi).to_csv(config.RISULTATI / "costi.csv", index=False, float_format="%.6f")
    lo_c, hi_c = 0.0, 0.05
    f = lambda c: fx.metriche(fx.log_rendimenti_regola(O, C, A, pos20, "apertura", c)[sl], GA)["cagr"] - mbh["cagr"]
    if f(lo_c) > 0 > f(hi_c):
        for _ in range(40):
            mid = (lo_c + hi_c) / 2
            if f(mid) > 0:
                lo_c = mid
            else:
                hi_c = mid
        reg("costo_pareggio", (lo_c + hi_c) / 2, "pct2", "Costo per operazione al quale la regola veloce (apertura) rende come il buy & hold", "bisezione")
    else:
        reg("costo_pareggio", 0.0, "pct2", "Costo di pareggio non trovato (la regola veloce rende meno del buy & hold anche senza costi)", "bisezione")

    # --- Bootstrap della differenza apertura - chiusura del giorno dopo, regola veloce ----------------------------------------
    d = serie[("s20", "ap")] - serie[("s20", "cd")]
    lo, hi = fx.bootstrap_differenza(d, config.N_BOOT, config.BLOCCO, GA, config.LIVELLO_IC, rng)
    reg("boot_media", float(d.mean() * GA), "pp1", "Differenza media annualizzata tra apertura e chiusura del giorno dopo, regola veloce, in punti (log)", "serie giornaliere")
    reg("boot_lo", lo, "pp1", "Estremo inferiore dell'intervallo bootstrap della differenza, in punti", "bootstrap a blocchi")
    reg("boot_hi", hi, "pp1", "Estremo superiore dell'intervallo bootstrap della differenza, in punti", "bootstrap a blocchi")

    # --- Curve ---------------------------------------------------------------------------------------------------------------
    camp = np.arange(0, len(date_c), 5)
    cv = {"data": date_c[camp].strftime("%Y-%m-%d"), "bh": np.exp(np.cumsum(r_bh))[camp]}
    for sig, _, _ in MODI:
        cv[f"s20_{sig}"] = np.exp(np.cumsum(serie[("s20", sig)]))[camp]
    pd.DataFrame(cv).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.5f")

    # --- Verdetti ---------------------------------------------------------------------------------------------------------------
    h = [RIS["s20_st_meno_ap"]["valore"] >= config.H1_PUNTI,
         RIS["s200_scarto"]["valore"] < config.H2_PUNTI,
         RIS["s20_scarto"]["valore"] > RIS["s200_scarto"]["valore"],
         RIS["notte_quota"]["valore"] > config.H4_QUOTA,
         RIS["s20_ap_cagr_c"]["valore"] < mbh["cagr"],
         lo <= 0 <= hi]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
