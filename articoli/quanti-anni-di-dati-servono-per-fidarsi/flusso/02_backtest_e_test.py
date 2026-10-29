"""Passo 2 - Quanti anni di dati servono per fidarsi? Sharpe dell'S&P 500 su finestre di N anni e simulazione di una strategia con Sharpe vero noto.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  sharpe_finestre.csv  per ogni durata: percentili, minimo, massimo e quote di finestre con Sharpe negativo, positivo e t oltre 1,96
  sharpe_serie.csv     Sharpe di ogni finestra di 5, 10 e 20 anni, per mese di partenza (per il grafico)
  simulazione.csv      per ogni durata in anni: probabilità di Sharpe negativo e potenza del test, con Sharpe vero noto
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
    date = c.index[1:]
    r = (c.to_numpy()[1:] / c.to_numpy()[:-1]) - 1.0
    inizi_tutti = f.inizi_mese(date)
    rng = np.random.default_rng(config.SEME)

    reg("dati_prima_data", str(date[0].date()), "data_lunga", "Prima seduta con un rendimento", "dati/")
    reg("dati_ultima_data", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("dati_anni", (date[-1] - date[0]).days / 365.25, "num1", "Anni di storia dei dati", "dati/")
    reg("sharpe_totale", float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(GA)), "num2", "Sharpe dell'S&P 500 sull'intera storia (tasso zero)")
    reg("sharpe_vero", config.SHARPE_VERO, "num1", "Sharpe vero della strategia simulata", "config.py")
    reg("sim_n", config.SIM_N, "int", "Backtest simulati per ogni durata", "config.py")
    reg("potenza", config.POTENZA, "pct0", "Potenza richiesta al test", "config.py")
    reg("giorni_anno", GA, "int", "Sedute in un anno", "config.py")

    righe, serie = [], {}
    for N in config.ORIZZONTI:
        lung = N * GA
        inizi = inizi_tutti[inizi_tutti + lung <= len(r)]
        sh = f.sharpe_finestre(r, inizi, lung, GA)
        t = sh * np.sqrt(N)
        q = np.quantile(sh, [0.05, 0.25, 0.5, 0.75, 0.95])
        righe.append(dict(anni=N, finestre=len(sh), p5=q[0], p25=q[1], p50=q[2], p75=q[3], p95=q[4], minimo=sh.min(), massimo=sh.max(),
                          quota_neg=(sh < 0).mean(), quota_pos=(sh > 0).mean(), quota_t_sopra=(t > config.Z_BILATERALE).mean(),
                          quota_t_sotto=(t < -config.Z_BILATERALE).mean()))
        reg(f"r{N}_n", len(sh), "int", f"Finestre di {N} anni (una per mese di partenza)")
        reg(f"r{N}_neg", float((sh < 0).mean()), "pct0", f"Quota di finestre di {N} anni con Sharpe negativo")
        reg(f"r{N}_pos", float((sh > 0).mean()), "pct0", f"Quota di finestre di {N} anni con Sharpe positivo")
        reg(f"r{N}_p5", float(q[0]), "num2", f"5° percentile dello Sharpe su finestre di {N} anni")
        reg(f"r{N}_p50", float(q[2]), "num2", f"Mediana dello Sharpe su finestre di {N} anni")
        reg(f"r{N}_p95", float(q[4]), "num2", f"95° percentile dello Sharpe su finestre di {N} anni")
        reg(f"r{N}_min", float(sh.min()), "num2", f"Sharpe minimo su finestre di {N} anni")
        reg(f"r{N}_max", float(sh.max()), "num2", f"Sharpe massimo su finestre di {N} anni")
        reg(f"r{N}_ampiezza", float(q[4] - q[0]), "num2", f"Ampiezza tra 5° e 95° percentile dello Sharpe, finestre di {N} anni")
        reg(f"r{N}_t_sopra", float((t > config.Z_BILATERALE).mean()), "pct0", f"Quota di finestre di {N} anni in cui il t supera la soglia (Sharpe significativamente positivo)")
        reg(f"r{N}_t_sotto", float((t < -config.Z_BILATERALE).mean()), "pct0", f"Quota di finestre di {N} anni in cui il t è sotto la soglia negativa (Sharpe significativamente negativo)")
        if N in (5, 10, 20):
            serie[N] = pd.Series(sh, index=date[inizi])
    pd.DataFrame(righe).to_csv(config.RISULTATI / "sharpe_finestre.csv", index=False, float_format="%.5f")
    pd.concat({f"anni_{k}": v for k, v in serie.items()}, axis=1).rename_axis("data").reset_index().to_csv(
        config.RISULTATI / "sharpe_serie.csv", index=False, float_format="%.5f")

    # simulazione con Sharpe vero noto
    sim = []
    for N in config.ANNI_SIM:
        s = f.sharpe_simulato(N, config.SHARPE_VERO, GA, config.SIM_N, rng)
        t = s * np.sqrt(N)
        sim.append(dict(anni=N, p_neg=float((s < 0).mean()), potenza=float((np.abs(t) > config.Z_BILATERALE).mean()),
                        p5=float(np.quantile(s, 0.05)), p95=float(np.quantile(s, 0.95))))
    S = pd.DataFrame(sim)
    S.to_csv(config.RISULTATI / "simulazione.csv", index=False, float_format="%.5f")
    for N in (1, 2, 3, 5, 10, 20, 30):
        row = S[S["anni"] == N].iloc[0]
        reg(f"s{N}_neg", float(row["p_neg"]), "pct0", f"Probabilità che un backtest di {N} anni mostri Sharpe negativo con Sharpe vero {config.SHARPE_VERO}")
        reg(f"s{N}_potenza", float(row["potenza"]), "pct0", f"Probabilità che un backtest di {N} anni distingua lo Sharpe vero dallo zero (95%, due code)")
        reg(f"s{N}_p5", float(row["p5"]), "num2", f"5° percentile dello Sharpe misurato in backtest di {N} anni")
        reg(f"s{N}_p95", float(row["p95"]), "num2", f"95° percentile dello Sharpe misurato in backtest di {N} anni")
    ok = S[S["potenza"] >= config.POTENZA]
    anni_potenza = int(ok["anni"].iloc[0]) if len(ok) else int(S["anni"].max()) + 1
    reg("anni_potenza", anni_potenza, "int", "Anni minimi per una potenza dell'80% con Sharpe vero noto (dalla simulazione)")
    reg("anni_teorici", float(((config.Z_BILATERALE + 0.8416212) / config.SHARPE_VERO) ** 2), "num1", "Anni teorici per potenza dell'80% (formula approssimata), per confronto", "formula")

    reg("h1_quota", config.H1_QUOTA, "pct0", "Ipotesi 1: soglia", "config.py")
    reg("h2_quota", config.H2_QUOTA, "pct0", "Ipotesi 2: soglia", "config.py")
    reg("h3_riduzione", config.H3_RIDUZIONE, "pct0", "Ipotesi 3: riduzione minima dell'ampiezza", "config.py")
    reg("h4_sharpe", config.H4_SHARPE, "num2", "Ipotesi 4: soglia dello Sharpe minimo a venti anni", "config.py")
    reg("h5_quota", config.H5_QUOTA, "pct0", "Ipotesi 5: soglia", "config.py")
    reg("h6_anni", config.H6_ANNI, "int", "Ipotesi 6: soglia in anni", "config.py")
    riduzione = 1.0 - RIS["r20_ampiezza"]["valore"] / RIS["r5_ampiezza"]["valore"]
    reg("riduzione_ampiezza", riduzione, "pct0", "Riduzione dell'ampiezza dello Sharpe passando da cinque a venti anni")
    h = [RIS["r1_neg"]["valore"] > config.H1_QUOTA,
         RIS["r10_pos"]["valore"] >= config.H2_QUOTA,
         riduzione >= config.H3_RIDUZIONE,
         RIS["r20_min"]["valore"] < config.H4_SHARPE,
         RIS["s5_neg"]["valore"] > config.H5_QUOTA,
         anni_potenza > config.H6_ANNI]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(v), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json; esiti {h}")


if __name__ == "__main__":
    main()
