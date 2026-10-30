"""Passo 2 - L'effetto gennaio su S&P 500 e Russell 2000.

Legge SOLO dati/gspc_giornaliero.csv e dati/rut_giornaliero.csv; produce in risultati/: metriche.json, medie_mensili.csv, anni.csv.
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
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def leggi(f):
    df = pd.read_csv(f, parse_dates=["Date"], index_col="Date").sort_index()
    if (df["Close"] <= 0).any() or df["Close"].isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    return df["Close"].astype(float)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEME)
    cs, cr = leggi(config.FILE_DATI), leggi(config.FILE_PICCOLE)
    rs, rr = fx.rendimenti_mensili(cs), fx.rendimenti_mensili(cr)
    reg("prima_data", str(cs.index[0].date()), "data_lunga", "Prima seduta dell'S&P 500", "dati/")
    reg("data_ultima", str(cs.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("prima_data_rut", str(cr.index[0].date()), "data_lunga", "Prima seduta del Russell 2000", "dati/")
    reg("n_mesi", len(rs), "int", "Mesi completi dell'S&P 500", "dati/")
    reg("n_gennai", int((rs.index.month == 1).sum()), "int", "Gennai nel campione S&P 500", "dati/")
    reg("anno_spartiacque", config.ANNO_SPARTIACQUE, "annonum", "Anno dei primi studi sull'effetto gennaio", "config.py")
    reg("n_perm", config.N_PERMUTAZIONI, "int", "Permutazioni delle etichette dei mesi", "config.py")
    reg("h6_quota", config.H6_QUOTA, "pct0", "Ipotesi 6: quota minima di anni in cui il barometro funziona", "config.py")
    reg("soglia_p", config.SOGLIA_P, "num2", "Soglia di significatività", "config.py")

    gen = (rs.index.month == 1)
    d, p = fx.permutazione_differenza(rs.to_numpy(), gen, config.N_PERMUTAZIONI, rng)
    reg("jan_media", float(rs[gen].mean()), "pct2", "Rendimento medio di gennaio, S&P 500", "pandas")
    reg("altri_media", float(rs[~gen].mean()), "pct2", "Rendimento medio degli altri undici mesi, S&P 500", "pandas")
    reg("diff", d, "pp2", "Gennaio meno gli altri mesi, punti percentuali, S&P 500", "funzioni")
    reg("pval", p, "pval", "P-value di permutazione della differenza, S&P 500", "funzioni.permutazione_differenza")
    reg("jan_pos", float((rs[gen] > 0).mean()), "pct0", "Quota di gennai positivi", "pandas")
    reg("altri_pos", float((rs[~gen] > 0).mean()), "pct0", "Quota di altri mesi positivi", "pandas")

    # Medie per mese
    medie = rs.groupby(rs.index.month).mean()
    pd.DataFrame({"mese": MESI, "media": medie.to_numpy()}).to_csv(config.RISULTATI / "medie_mensili.csv", index=False, float_format="%.6f")
    ordine = medie.sort_values(ascending=False).index.tolist()
    reg("rango_jan", ordine.index(1) + 1, "int", "Posizione di gennaio nella classifica dei mesi per rendimento medio (1 = il più alto)", "pandas")
    reg("mese_migliore", MESI[ordine[0] - 1], "testo", "Mese con il rendimento medio più alto", "pandas")
    reg("media_migliore", float(medie.loc[ordine[0]]), "pct2", "Rendimento medio del mese migliore", "pandas")
    reg("mese_peggiore", MESI[ordine[-1] - 1], "testo", "Mese con il rendimento medio più basso", "pandas")
    reg("media_peggiore", float(medie.loc[ordine[-1]]), "pct2", "Rendimento medio del mese peggiore", "pandas")

    # Prima e dopo
    for nome, sel, tag in (("prima", rs.index.year < config.ANNO_SPARTIACQUE, "p"), ("dopo", rs.index.year >= config.ANNO_SPARTIACQUE, "d")):
        x, g = rs[sel], (rs[sel].index.month == 1)
        dd = float(x[g].mean() - x[~g].mean())
        reg(f"diff_{tag}", dd, "pp2", f"Gennaio meno gli altri mesi, periodo {nome} lo spartiacque, S&P 500", "pandas")
        reg(f"n_jan_{tag}", int(g.sum()), "int", f"Gennai {nome} lo spartiacque", "pandas")

    # Piccole capitalizzazioni
    comune = rs.index.intersection(rr.index)
    xs, xr = rs[comune], rr[comune]
    gc = (comune.month == 1)
    dr, pr = fx.permutazione_differenza(xr.to_numpy(), gc, config.N_PERMUTAZIONI, rng)
    ds = float(xs[gc].mean() - xs[~gc].mean())
    reg("n_mesi_rut", len(comune), "int", "Mesi in comune tra S&P 500 e Russell 2000", "dati/")
    reg("diff_rut", dr, "pp2", "Gennaio meno gli altri mesi, Russell 2000, punti percentuali", "funzioni")
    reg("diff_sp_stesso", ds, "pp2", "Gennaio meno gli altri mesi, S&P 500 nello stesso periodo, punti percentuali", "pandas")
    reg("pval_rut", pr, "pval", "P-value di permutazione, Russell 2000", "funzioni")
    sl = xr - xs
    dsl = float(sl[gc].mean() - sl[~gc].mean())
    reg("diff_sl", dsl, "pp2", "Differenza piccole meno grandi: gennaio meno altri mesi, punti percentuali", "pandas")

    # Barometro
    ba = fx.resto_anno(rs)
    ba.to_csv(config.RISULTATI / "anni.csv", index=False, float_format="%.5f")
    conc = float(((ba["gennaio"] > 0) == (ba["resto"] > 0)).mean())
    reg("n_anni_baro", len(ba), "int", "Anni completi per il barometro", "dati/")
    reg("baro", conc, "pct0", "Quota di anni in cui il segno di gennaio coincide con quello del resto dell'anno", "pandas")
    base = float((ba["resto"] > 0).mean())
    reg("base_resto", base, "pct0", "Quota di anni con il resto dell'anno positivo", "pandas")
    reg("baro_dopo_pos", float((ba[ba["gennaio"] > 0]["resto"] > 0).mean()), "pct0", "Dopo un gennaio positivo: quota di anni con il resto positivo", "pandas")
    reg("baro_dopo_neg", float((ba[ba["gennaio"] <= 0]["resto"] > 0).mean()), "pct0", "Dopo un gennaio negativo: quota di anni con il resto positivo", "pandas")

    h = [d > 0, p >= config.SOGLIA_P, RIS["diff_d"]["valore"] < RIS["diff_p"]["valore"], dr > ds, RIS["rango_jan"]["valore"] > 3, conc > config.H6_QUOTA]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
