"""Passo 2 - Comprare dopo un calo rapido del 10% sull'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv; produce in risultati/: metriche.json, eventi.csv.
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
NOMI = {21: "1m", 63: "3m", 252: "12m"}


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEME)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    c = close.to_numpy()
    date = close.index
    anni = date.year.to_numpy()
    ev = fx.eventi_calo(c, config.FINESTRA, config.SOGLIA_CALO, config.PAUSA)

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_rend", len(c) - 1, "int", "Rendimenti giornalieri", "dati/")
    reg("anni_tot", (len(c) - 1) / 252, "num1", "Anni di borsa nei dati", "dati/")
    reg("finestra", config.FINESTRA, "int", "Sedute della finestra del massimo di riferimento", "config.py")
    reg("soglia_calo", config.SOGLIA_CALO, "pct0", "Calo minimo dal massimo", "config.py")
    reg("pausa", config.PAUSA, "int", "Sedute di pausa dopo un evento", "config.py")
    reg("h1_ecc", config.H1_ECCESSO, "pct0", "Ipotesi 1: eccesso minimo a dodici mesi", "config.py")
    reg("h3_quota", config.H3_QUOTA, "pct0", "Ipotesi 3: quota minima di eventi negativi a tre mesi", "config.py")
    reg("h4_calo", config.H4_CALO, "pct0", "Ipotesi 4: ulteriore calo minimo", "config.py")
    reg("h4_quota", config.H4_QUOTA, "pct0", "Ipotesi 4: quota di eventi", "config.py")
    reg("anno_escluso", config.ANNO_ESCLUSO_FINO, "annonum", "Ultimo anno degli eventi tolti nell'ipotesi 5", "config.py")
    reg("soglia_p", config.SOGLIA_P, "num2", "Soglia di significatività", "config.py")
    reg("n_casuali", config.N_CASUALI, "int", "Estrazioni casuali", "config.py")
    reg("n_eventi", len(ev), "int", "Eventi di calo rapido", "funzioni.eventi_calo")
    reg("primo_evento", str(date[ev[0]].date()), "data_lunga", "Data del primo evento", "funzioni")
    reg("ultimo_evento", str(date[ev[-1]].date()), "data_lunga", "Data dell'ultimo evento", "funzioni")

    righe = []
    for h in config.ORIZZONTI:
        av = fx.rend_avanti(c, h)
        ok_ev = ev[~np.isnan(av[ev])]
        tutti = av[~np.isnan(av)]
        n = NOMI[h]
        reg(f"n_{n}", len(ok_ev), "int", f"Eventi con {n} di dati successivi", "funzioni")
        reg(f"m_{n}", float(av[ok_ev].mean()), "pct1", f"Rendimento medio dopo l'evento, orizzonte {n}", "funzioni")
        reg(f"t_{n}", float(tutti.mean()), "pct1", f"Rendimento medio di un giorno qualunque, orizzonte {n}", "funzioni")
        reg(f"ecc_{n}", float(av[ok_ev].mean() - tutti.mean()), "pp2", f"Eccesso, orizzonte {n}, punti percentuali", "funzioni")
        reg(f"neg_{n}", float((av[ok_ev] < 0).mean()), "pct0", f"Quota di eventi con rendimento negativo, orizzonte {n}", "funzioni")
        reg(f"neg_tutti_{n}", float((tutti < 0).mean()), "pct0", f"Quota di giorni qualunque con rendimento negativo, orizzonte {n}", "funzioni")
        if h == 252:
            p = fx.pval_casuali(av, float(av[ok_ev].mean()), len(ok_ev), config.N_CASUALI, rng)
            reg("pval", p, "pval", "Quota di estrazioni casuali con rendimento medio a dodici mesi almeno pari a quello degli eventi", "funzioni.pval_casuali")
            s = ok_ev[anni[ok_ev] > config.ANNO_ESCLUSO_FINO]
            tt = av[(anni > config.ANNO_ESCLUSO_FINO) & ~np.isnan(av)]
            reg("n_senza", len(s), "int", "Eventi a dodici mesi dopo il 1939", "funzioni")
            reg("ecc_senza", float(av[s].mean() - tt.mean()), "pp2", "Eccesso a dodici mesi senza gli eventi fino al 1939, punti percentuali", "funzioni")
            reg("m_senza", float(av[s].mean()), "pct1", "Rendimento medio a dodici mesi dopo gli eventi dopo il 1939", "funzioni")
            reg("peggiore_12m", float(av[ok_ev].min()), "pct0", "Il peggior rendimento a dodici mesi dopo un evento", "funzioni")
            reg("migliore_12m", float(av[ok_ev].max()), "pct0", "Il miglior rendimento a dodici mesi dopo un evento", "funzioni")
            for d_i in ok_ev:
                righe.append({"data": str(date[d_i].date()), "r12": av[d_i], "r3": fx.rend_avanti(c, 63)[d_i]})
    mn = fx.minimo_avanti(c, 63)
    ok_mn = ev[~np.isnan(mn[ev])]
    reg("quota_calo_ulteriore", float((mn[ok_mn] <= -config.H4_CALO).mean()), "pct0", "Quota di eventi con un ulteriore calo di almeno il 5% nei 63 giorni successivi", "funzioni.minimo_avanti")
    reg("calo_medio", float(mn[ok_mn].mean()), "pct1", "Ulteriore calo medio massimo nei 63 giorni successivi", "funzioni.minimo_avanti")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "eventi.csv", index=False, float_format="%.5f")

    h = [RIS["ecc_12m"]["valore"] >= config.H1_ECCESSO,
         RIS["m_1m"]["valore"] < RIS["t_1m"]["valore"],
         RIS["neg_3m"]["valore"] >= config.H3_QUOTA,
         RIS["quota_calo_ulteriore"]["valore"] > config.H4_QUOTA,
         RIS["ecc_senza"]["valore"] > 0,
         RIS["pval"]["valore"] < config.SOGLIA_P]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
