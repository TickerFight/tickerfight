"""Passo 2 - La media mobile a 200 sedute sull'S&P 500, un secolo di storia.

Legge SOLO dati/gspc_giornaliero.csv; produce in risultati/: metriche.json, decadi.csv, curve.csv.
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
    rc, _, _ = fx.rendimenti_regola(c, pos, config.COSTO)
    date = close.index[1:][~np.isnan(pos[:-1])]
    anni = (len(rr)) / GA

    reg("prima_data", str(close.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("data_inizio_regola", str(date[0].date()), "data_lunga", "Primo giorno con il segnale della media", "dati/")
    reg("n_giorni", len(rr), "int", "Sedute del campione della regola", "dati/")
    reg("anni_tot", anni, "num1", "Anni di borsa del campione della regola", "dati/")
    reg("media", config.MEDIA, "int", "Lunghezza della media mobile", "config.py")
    reg("costo", config.COSTO, "pct1", "Costo a ogni cambio di posizione", "config.py")
    reg("h2_rapporto", config.H2_RAPPORTO_DD, "pct0", "Ipotesi 2: rapporto massimo tra i drawdown", "config.py")
    reg("h4_ordini", config.H4_ORDINI_ANNO, "int", "Ipotesi 4: operazioni all'anno", "config.py")

    reg("reg_cagr", fx.cagr(rr, GA), "pct2", "Rendimento annuo composto della regola", "funzioni.cagr")
    reg("bh_cagr", fx.cagr(bh, GA), "pct2", "Rendimento annuo composto del buy & hold", "funzioni.cagr")
    reg("reg_sr", fx.sharpe(rr, GA), "num2", "Sharpe della regola", "funzioni.sharpe")
    reg("bh_sr", fx.sharpe(bh, GA), "num2", "Sharpe del buy & hold", "funzioni.sharpe")
    reg("reg_dd", fx.max_drawdown(rr), "pct0", "Massimo drawdown della regola", "funzioni.max_drawdown")
    reg("bh_dd", fx.max_drawdown(bh), "pct0", "Massimo drawdown del buy & hold", "funzioni.max_drawdown")
    reg("rapporto_dd", fx.max_drawdown(rr) / fx.max_drawdown(bh), "pct0", "Drawdown della regola diviso quello del buy & hold", "rapporto")
    reg("quota", float(np.mean(p)), "pct0", "Quota di sedute in cui la regola è investita", "funzioni")
    nc = fx.n_cambi(p)
    reg("n_ordini", nc, "int", "Cambi di posizione della regola", "funzioni.n_cambi")
    reg("ordini_anno", nc / anni, "num1", "Cambi di posizione all'anno", "funzioni")
    reg("reg_sr_costo", fx.sharpe(rc, GA), "num2", "Sharpe della regola con il costo per cambio di posizione", "funzioni.sharpe")
    reg("reg_cagr_costo", fx.cagr(rc, GA), "pct2", "Rendimento annuo composto della regola con il costo", "funzioni.cagr")
    reg("costo_totale_anno", float(config.COSTO * nc / anni), "pct2", "Costo medio annuo dei cambi di posizione", "config.py e funzioni")

    righe = []
    for d0 in config.DECENNI:
        sel = (date.year >= d0) & (date.year < d0 + 10)
        if sel.sum() < 100:
            continue
        righe.append({"decennio": d0, "regola": fx.cagr(rr[sel], GA), "buy_hold": fx.cagr(bh[sel], GA), "giorni": int(sel.sum())})
    dec = pd.DataFrame(righe)
    dec.to_csv(config.RISULTATI / "decadi.csv", index=False, float_format="%.5f")
    vinti = int((dec["regola"] > dec["buy_hold"]).sum())
    reg("n_decenni", len(dec), "int", "Decenni (anche incompleti, con almeno cento sedute) nel campione", "funzioni")
    reg("decenni_vinti", vinti, "int", "Decenni in cui la regola batte il buy & hold per rendimento annuo composto", "funzioni")
    for d0 in (1930, 2000):
        r = dec[dec["decennio"] == d0].iloc[0]
        reg(f"reg_{d0}", float(r["regola"]), "pct1", f"Rendimento annuo composto della regola, decennio {d0}", "funzioni")
        reg(f"bh_{d0}", float(r["buy_hold"]), "pct1", f"Rendimento annuo composto del buy & hold, decennio {d0}", "funzioni")
    pre = date.year < 1990
    reg("anno_pre", 1990, "annonum", "Anno che divide il campione in prima e dopo", "config.py")
    reg("reg_cagr_pre", fx.cagr(rr[pre], GA), "pct1", "Rendimento annuo della regola prima del 1990", "funzioni")
    reg("bh_cagr_pre", fx.cagr(bh[pre], GA), "pct1", "Rendimento annuo del buy & hold prima del 1990", "funzioni")
    reg("reg_cagr_post", fx.cagr(rr[~pre], GA), "pct1", "Rendimento annuo della regola dal 1990", "funzioni")
    reg("bh_cagr_post", fx.cagr(bh[~pre], GA), "pct1", "Rendimento annuo del buy & hold dal 1990", "funzioni")
    pd.DataFrame({"regola": np.cumprod(1 + rr), "buy_hold": np.cumprod(1 + bh)}, index=date).resample("YE").last().to_csv(config.RISULTATI / "curve.csv", float_format="%.5f")

    h = [RIS["reg_cagr"]["valore"] < RIS["bh_cagr"]["valore"],
         RIS["rapporto_dd"]["valore"] <= config.H2_RAPPORTO_DD,
         RIS["reg_sr"]["valore"] > RIS["bh_sr"]["valore"],
         RIS["ordini_anno"]["valore"] > config.H4_ORDINI_ANNO,
         vinti < len(dec) / 2,
         RIS["reg_sr_costo"]["valore"] > RIS["bh_sr"]["valore"]]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
