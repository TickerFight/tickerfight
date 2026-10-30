"""Passo 2 - Il filtro a 200 sedute, crisi per crisi, sull'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv; produce in risultati/: metriche.json, episodi.csv.
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
MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    c = close.to_numpy()
    pos = fx.posizione_sma(c, config.MEDIA)
    rr, bh, p = fx.rendimenti_regola(c, pos, 0.0)
    date = close.index[1:][~np.isnan(pos[:-1])]
    # indici della curva: 0 = prima del primo rendimento (data = giorno precedente)
    date_curva = [close.index[1:][~np.isnan(pos[:-1])][0] - pd.Timedelta(days=1)] + list(date)
    eb = np.concatenate([[1.0], np.cumprod(1 + bh)])
    er = np.concatenate([[1.0], np.cumprod(1 + rr)])
    ep = fx.episodi(bh, config.SOGLIA_EPISODIO)

    reg("prima_data", str(close.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("data_inizio_regola", str(date[0].date()), "data_lunga", "Primo giorno con il segnale della media", "dati/")
    reg("media", config.MEDIA, "int", "Lunghezza della media mobile", "config.py")
    reg("soglia_episodio", config.SOGLIA_EPISODIO, "pct0", "Perdita minima del buy & hold per contare un episodio", "config.py")
    reg("sessioni_rapido", config.SESSIONI_RAPIDO, "int", "Sedute massime dal massimo al minimo per un episodio rapido", "config.py")
    reg("h2_quota", config.H2_QUOTA, "pct0", "Ipotesi 2: quota minima di episodi con protezione debole", "config.py")
    reg("h3_uscita", config.H3_USCITA, "pct0", "Ipotesi 3: perdita dell'indice alla mediana al momento dell'uscita", "config.py")
    reg("h6_episodi", config.H6_EPISODI, "int", "Ipotesi 6: numero minimo di episodi", "config.py")
    reg("n_episodi", len(ep), "int", "Episodi con perdita del buy & hold di almeno il 20%", "funzioni.episodi")

    righe = []
    for pk, tr in ep:
        j = next((k for k in range(pk, len(p)) if p[k] == 0.0), tr)
        j = min(j, tr)
        rb = eb[tr + GA] / eb[tr] - 1 if tr + GA < len(eb) else np.nan
        rg = er[tr + GA] / er[tr] - 1 if tr + GA < len(er) else np.nan
        righe.append({"massimo": str(date_curva[pk].date()), "minimo": str(date_curva[tr].date()), "durata": tr - pk,
                      "perdita_bh": eb[tr] / eb[pk] - 1, "perdita_reg": er[tr] / er[pk] - 1,
                      "sedute_uscita": j - pk, "calo_all_uscita": eb[j] / eb[pk] - 1, "rimbalzo_bh": rb, "rimbalzo_reg": rg})
    e = pd.DataFrame(righe)
    e["quota_persa"] = e["perdita_reg"] / e["perdita_bh"]
    e["etichetta"] = [f"{MESI[int(d[5:7]) - 1]} {d[:4]}" for d in e["massimo"]]
    e.to_csv(config.RISULTATI / "episodi.csv", index=False, float_format="%.5f")

    reg("dd_reg_tot", fx.max_drawdown(rr), "pct0", "Drawdown massimo della regola su tutto il campione (anche fuori dagli episodi del buy & hold)", "funzioni.max_drawdown")
    reg("dd_bh_tot", fx.max_drawdown(bh), "pct0", "Drawdown massimo del buy & hold su tutto il campione", "funzioni.max_drawdown")
    reg("perdita_reg_max_ep", float(e["perdita_reg"].min()), "pct0", "La perdita peggiore della regola dentro un episodio del buy & hold", "funzioni")
    mi = e["perdita_bh"].idxmin()
    reg("peggiore_bh", float(e["perdita_bh"].min()), "pct0", "Perdita del buy & hold nell'episodio peggiore", "funzioni")
    reg("peggiore_reg", float(e.loc[mi, "perdita_reg"]), "pct0", "Perdita della regola nello stesso episodio", "funzioni")
    reg("peggiore_massimo", e.loc[mi, "massimo"], "data_lunga", "Data del massimo dell'episodio peggiore", "funzioni")
    reg("n_meno", int((e["perdita_reg"] > e["perdita_bh"]).sum()), "int", "Episodi in cui la regola perde meno del buy & hold", "funzioni")
    reg("n_debole", int((e["quota_persa"] > 0.5).sum()), "int", "Episodi in cui la regola evita meno della metà della perdita", "funzioni")
    reg("quota_debole", float((e["quota_persa"] > 0.5).mean()), "pct0", "Quota di episodi con protezione debole", "funzioni")
    reg("quota_persa_media", float(e["quota_persa"].mean()), "pct0", "Quota media della perdita del buy & hold che la regola subisce", "funzioni")
    reg("uscita_sedute_med", float(e["sedute_uscita"].median()), "num1", "Sedute mediane dal massimo all'uscita della regola", "funzioni")
    reg("uscita_calo_med", float(e["calo_all_uscita"].median()), "pct1", "Calo mediano dell'indice dal massimo al momento dell'uscita", "funzioni")
    ok_r = e.dropna(subset=["rimbalzo_bh"])
    reg("n_rimbalzo", len(ok_r), "int", "Episodi con dodici mesi di dati dopo il minimo", "funzioni")
    reg("rimbalzo_bh_med", float(ok_r["rimbalzo_bh"].median()), "pct0", "Rendimento mediano del buy & hold nei dodici mesi dopo il minimo", "funzioni")
    reg("rimbalzo_reg_med", float(ok_r["rimbalzo_reg"].median()), "pct0", "Rendimento mediano della regola nei dodici mesi dopo il minimo", "funzioni")
    reg("n_rimbalzo_perso", int((ok_r["rimbalzo_reg"] < ok_r["rimbalzo_bh"]).sum()), "int", "Episodi in cui la regola rende meno del buy & hold nei dodici mesi dopo il minimo", "funzioni")
    rap = e[e["durata"] < config.SESSIONI_RAPIDO]
    len_ = e[e["durata"] >= config.SESSIONI_RAPIDO]
    reg("n_rapidi", len(rap), "int", "Episodi rapidi", "funzioni")
    reg("n_lenti", len(len_), "int", "Episodi lenti", "funzioni")
    reg("persa_rapidi", float(rap["quota_persa"].mean()) if len(rap) else 0.0, "pct0", "Quota media persa dalla regola negli episodi rapidi", "funzioni")
    reg("persa_lenti", float(len_["quota_persa"].mean()) if len(len_) else 0.0, "pct0", "Quota media persa dalla regola negli episodi lenti", "funzioni")

    h = [len(e) > 0 and bool((e["perdita_reg"] > e["perdita_bh"]).all()),
         RIS["quota_debole"]["valore"] >= config.H2_QUOTA,
         RIS["uscita_calo_med"]["valore"] <= -config.H3_USCITA,
         RIS["n_rimbalzo_perso"]["valore"] > RIS["n_rimbalzo"]["valore"] / 2,
         RIS["persa_rapidi"]["valore"] > RIS["persa_lenti"]["valore"],
         len(e) >= config.H6_EPISODI]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
