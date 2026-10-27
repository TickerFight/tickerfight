"""Passo 2 - Large cap contro small cap, coppia per coppia.

Per ogni coppia (S&P 500, indice di aziende più piccole), sulla storia in comune dei prezzi di fine mese:
  - rendimento annuo composto di grandi e piccole e differenza;
  - differenza media mensile con bootstrap per anni;
  - quota di mesi vinti dalle piccole;
  - decennio per decennio: differenza dei rendimenti annui composti;
  - finestre mobili di cinque e dieci anni: quota in cui le piccole battono le grandi;
  - scimmie: ogni mese grandi o piccole a caso.
Scrive risultati/metriche.json (ogni numero dell'articolo) e i csv di supporto.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config

RIS: dict = {}
SORGENTE = "risultati/ (calcolato da 02_backtest_e_test.py)"
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, np.integer):
        valore = int(valore)
    elif isinstance(valore, np.floating):
        valore = float(valore)
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").lower()


def fine_mese(csv) -> pd.Series:
    df = pd.read_csv(csv, index_col=0, parse_dates=True)
    c = df["Close"].dropna()
    c = c[c > 0]
    m = c.groupby(c.index.to_period("M")).last()
    # l'ultimo mese è escluso se ancora in corso
    return m.iloc[:-1]


def cagr(rend: np.ndarray) -> float:
    if len(rend) == 0:
        return float("nan")
    return float(np.exp(np.log1p(rend).sum() / (len(rend) / 12)) - 1)


def finestre(rg: np.ndarray, rp: np.ndarray, w: int) -> np.ndarray:
    cg = np.concatenate([[0.0], np.cumsum(np.log1p(rg))])
    cp = np.concatenate([[0.0], np.cumsum(np.log1p(rp))])
    return (cp[w:] - cp[:-w]) - (cg[w:] - cg[:-w])      # log-differenza per ogni finestra


def analizza(pic, mg: pd.Series, rng):
    tk, nome, _ = pic
    mp = fine_mese(config.file_dati(tk))
    df = pd.concat([mg.rename("g"), mp.rename("p")], axis=1).dropna()
    rg = df["g"].pct_change().dropna()
    rp = df["p"].pct_change().dropna()
    if len(rg) < config.MESI_MINIMI:
        return None
    n = len(rg)
    d = (rp - rg).values
    anni = rg.index.year.values
    ua = np.unique(anni)
    # bootstrap per anni sulla differenza media mensile
    gruppi = [d[anni == a] for a in ua]
    medie = np.empty(config.N_BOOTSTRAP)
    for k in range(config.N_BOOTSTRAP):
        sc = rng.integers(0, len(ua), len(ua))
        medie[k] = np.concatenate([gruppi[i] for i in sc]).mean()
    alpha = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.percentile(medie, [100 * alpha, 100 * (1 - alpha)])
    p_due = float(min(1.0, 2 * min((medie <= 0).mean(), (medie >= 0).mean())))
    # decenni
    dec = {}
    for dd in config.DECENNI:
        mask = (anni >= dd) & (anni < dd + 10)
        if mask.sum() >= config.MESI_DECENNIO_MINIMI:
            dec[dd] = (cagr(rp.values[mask]), cagr(rg.values[mask]), int(mask.sum()))
    mask20 = anni >= 2020
    dec20 = (cagr(rp.values[mask20]), cagr(rg.values[mask20]), int(mask20.sum())) if mask20.sum() >= 12 else None
    # finestre mobili
    quote_fin = {}
    for w in config.FINESTRE:
        if n >= w:
            ld = finestre(rg.values, rp.values, w)
            quote_fin[w] = (float((ld > 0).mean()), int(len(ld)))
    # scimmie: ogni mese grandi o piccole a caso; confronto con piccole sempre
    sc = rng.integers(0, 2, size=(config.N_SCIMMIE, n))
    ls = np.where(sc == 1, np.log1p(rp.values), np.log1p(rg.values)).sum(axis=1)
    fin_p, fin_g = float(np.exp(np.log1p(rp.values).sum())), float(np.exp(np.log1p(rg.values).sum()))
    fin_s = np.exp(ls)
    return {"tk": tk, "sl": slug(tk), "nome": nome, "n": n, "inizio": str(df.index[0]), "fine": str(df.index[-1]),
            "cagr_p": cagr(rp.values), "cagr_g": cagr(rg.values), "media_d": float(d.mean()), "lo": float(lo), "hi": float(hi),
            "p": p_due, "quota_mesi": float((d > 0).mean()), "dec": dec, "dec20": dec20, "fin": quote_fin,
            "fin_p": fin_p, "fin_g": fin_g, "sc_med": float(np.median(fin_s)),
            "sc_sotto_p": float((fin_s < fin_p).mean()), "sc_sotto_g": float((fin_s < fin_g).mean()),
            "serie": pd.DataFrame({"data": df.index.astype(str)[1:], "grandi": rg.values, "piccole": rp.values})}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    ok = {r["ticker"] for r in meta["indici"] if r.get("stato") == "ok"}
    if config.GRANDI[0] not in ok:
        raise SystemExit("Manca l'S&P 500.")
    mg = fine_mese(config.file_dati(config.GRANDI[0]))
    rng = np.random.default_rng(config.SEME)
    res = []
    for pic in config.PICCOLE:
        if pic[0] not in ok:
            print(f"{pic[0]}: non disponibile")
            continue
        r = analizza(pic, mg, rng)
        if r:
            res.append(r)
            print(f"{r['nome']}: {r['n']} mesi dal {r['inizio']}, cagr piccole {r['cagr_p']:.3%} grandi {r['cagr_g']:.3%}")
    if not res:
        raise SystemExit("Nessuna coppia utilizzabile.")
    for r in res:
        sl = r["sl"]
        reg(f"{sl}_nome", r["nome"], "testo", "Nome dell'indice di aziende più piccole", "config.py, PICCOLE")
        reg(f"{sl}_mesi", r["n"], "int", f"Mesi di storia in comune con l'S&P 500, {r['nome']}", "coppie.csv")
        reg(f"{sl}_anni", r["n"] / 12, "num1", f"Anni di storia in comune con l'S&P 500, {r['nome']}", "coppie.csv")
        reg(f"{sl}_inizio", r["inizio"], "testo", f"Primo mese della storia in comune (anno-mese), {r['nome']}", "dati/")
        reg(f"{sl}_cagr_p", r["cagr_p"], "pct1", f"Rendimento annuo composto dell'indice piccolo (prezzi), {r['nome']}")
        reg(f"{sl}_cagr_g", r["cagr_g"], "pct1", f"Rendimento annuo composto dell'S&P 500 sullo stesso periodo, {r['nome']}")
        reg(f"{sl}_cagr_diff", r["cagr_p"] - r["cagr_g"], "pp1", f"Differenza di rendimento annuo composto (piccole meno grandi), in punti percentuali, {r['nome']}")
        reg(f"{sl}_val_p", config.CAPITALE * r["fin_p"], "int", f"Valore finale di 10.000 dollari sull'indice piccolo (prezzi, senza tasse), {r['nome']}")
        reg(f"{sl}_val_g", config.CAPITALE * r["fin_g"], "int", f"Valore finale di 10.000 dollari sull'S&P 500 nello stesso periodo, {r['nome']}")
        reg(f"{sl}_media_d", r["media_d"], "pp2", f"Differenza media mensile (piccole meno grandi), in punti percentuali, {r['nome']}")
        reg(f"{sl}_d_lo", r["lo"], "pp2", f"Estremo inferiore dell'intervallo bootstrap per anni, in punti percentuali, {r['nome']}", "bootstrap per anni")
        reg(f"{sl}_d_hi", r["hi"], "pp2", f"Estremo superiore dell'intervallo bootstrap per anni, in punti percentuali, {r['nome']}", "bootstrap per anni")
        reg(f"{sl}_p_d", r["p"], "pval", f"p-value a due code della differenza media mensile (bootstrap per anni), {r['nome']}", "bootstrap per anni")
        reg(f"{sl}_quota_mesi", r["quota_mesi"], "pct0", f"Quota di mesi in cui le piccole battono le grandi, {r['nome']}", "coppie.csv")
        for w, (q, nf) in r["fin"].items():
            reg(f"{sl}_fin{w // 12}_quota", q, "pct0", f"Quota di finestre mobili di {w // 12} anni in cui le piccole battono le grandi, {r['nome']}", "coppie.csv")
            reg(f"{sl}_fin{w // 12}_n", nf, "int", f"Finestre mobili di {w // 12} anni, {r['nome']}", "coppie.csv")
        for dd, (cp_, cg_, m) in r["dec"].items():
            reg(f"{sl}_dec{dd}_diff", cp_ - cg_, "pp1", f"Differenza di rendimento annuo composto nel decennio che inizia nel {dd} (piccole meno grandi), punti percentuali, {r['nome']}", "coppie.csv")
        if r["dec20"]:
            reg(f"{sl}_dec2020_diff", r["dec20"][0] - r["dec20"][1], "pp1", f"Differenza di rendimento annuo composto dal 2020 (piccole meno grandi), punti percentuali, {r['nome']}", "coppie.csv")
            reg(f"{sl}_dec2020_anni", r["dec20"][2] / 12, "num1", f"Anni dal 2020 nei dati, {r['nome']}", "coppie.csv")
        reg(f"{sl}_sc_mediana", config.CAPITALE * r["sc_med"], "int", f"Valore finale mediano delle scimmie (grandi o piccole a caso ogni mese), {r['nome']}", "scimmie")
        reg(f"{sl}_sc_sotto_p", r["sc_sotto_p"], "pct0", f"Quota di scimmie sotto chi è rimasto sempre sulle piccole, {r['nome']}", "scimmie")
        reg(f"{sl}_sc_sotto_g", r["sc_sotto_g"], "pct0", f"Quota di scimmie sotto chi è rimasto sempre sulle grandi, {r['nome']}", "scimmie")
    n = len(res)
    reg("n_coppie", n, "int", "Coppie utilizzabili", "config.py, PICCOLE e dati/")
    reg("n_scartate", len(config.PICCOLE) - n, "int", "Coppie scartate (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_piccole_vincono_cagr", sum(r["cagr_p"] > r["cagr_g"] for r in res), "int", "Coppie in cui le piccole hanno un rendimento annuo composto più alto delle grandi", "coppie.csv")
    # ipotesi 1
    def ip1(r):
        v = [cp_ - cg_ for cp_, cg_, _ in r["dec"].values()]
        return len(v) >= 2 and max(v) > 0 and min(v) < 0
    val1 = [r for r in res if len(r["dec"]) >= 2]
    reg("n_ip1_valutabili", len(val1), "int", "Coppie con almeno due decenni valutabili", "coppie.csv")
    reg("n_ip1_segno_misto", sum(ip1(r) for r in val1), "int", "Coppie con almeno un decennio positivo e uno negativo per le piccole", "coppie.csv")
    reg("n_ip2_include_zero", sum(r["lo"] <= 0 <= r["hi"] for r in res), "int", "Coppie in cui l'intervallo bootstrap della differenza media include lo zero", "bootstrap per anni")
    v3 = [r for r in res if 120 in r["fin"] and True]
    reg("n_ip3_valutabili", len(v3), "int", "Coppie con almeno una finestra di dieci anni", "coppie.csv")
    reg("n_ip3_dentro", sum(config.SOGLIA_FINESTRE[0] <= r["fin"][120][0] <= config.SOGLIA_FINESTRE[1] for r in v3), "int", "Coppie in cui la quota di finestre decennali vinte dalle piccole sta nell'intervallo dell'ipotesi", "coppie.csv")
    reg("n_ip4_dentro", sum(config.SOGLIA_QUOTA[0] <= r["quota_mesi"] <= config.SOGLIA_QUOTA[1] for r in res), "int", "Coppie in cui la quota di mesi vinti dalle piccole sta nell'intervallo dell'ipotesi", "coppie.csv")
    reg("n_ip3_fuori", len(v3) - sum(config.SOGLIA_FINESTRE[0] <= r["fin"][120][0] <= config.SOGLIA_FINESTRE[1] for r in v3), "int", "Coppie in cui la quota di finestre decennali vinte dalle piccole sta fuori dall'intervallo dell'ipotesi", "coppie.csv")
    reg("lit_sp600_lancio", 1994, "annonum", "Anno di lancio dell'S&P SmallCap 600, secondo S&P Dow Jones Indices", "S&P Dow Jones Indices, Celebrating 30 years of the S&P SmallCap 600")
    reg("soglia_fin_lo", config.SOGLIA_FINESTRE[0], "pct0", "Estremo inferiore dell'ipotesi sulle finestre", "config.py")
    reg("soglia_fin_hi", config.SOGLIA_FINESTRE[1], "pct0", "Estremo superiore dell'ipotesi sulle finestre", "config.py")
    reg("soglia_mesi_lo", config.SOGLIA_QUOTA[0], "pct0", "Estremo inferiore dell'ipotesi sui mesi", "config.py")
    reg("soglia_mesi_hi", config.SOGLIA_QUOTA[1], "pct0", "Estremo superiore dell'ipotesi sui mesi", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale dell'esempio, in dollari", "config.py")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per coppia", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("anno_ass", 2018, "annonum", "Anno dell'articolo di Asness e coautori", "Asness et al., Journal of Financial Economics")
    reg("lit_ass_industrie", 30, "int", "Industrie in cui, secondo l'abstract, i risultati di Asness e coautori reggono", "Asness et al. (2018), abstract")
    reg("lit_ass_paesi", 24, "int", "Mercati azionari internazionali in cui, secondo l'abstract, i risultati reggono", "Asness et al. (2018), abstract")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    u = pd.Period(max(r["fine"] for r in res), freq="M")
    reg("data_ultima", f"{MESI_IT[u.month - 1]} {u.year}", "testo", "Ultimo mese completo nei dati", "dati/")

    righe = []
    for r in res:
        righe.append({"coppia": r["nome"], "mesi": r["n"], "inizio": r["inizio"], "cagr_piccole": r["cagr_p"], "cagr_grandi": r["cagr_g"],
                      "quota_mesi": r["quota_mesi"], **{f"dec{k}": v[0] - v[1] for k, v in r["dec"].items()},
                      **({"dec2020": r["dec20"][0] - r["dec20"][1]} if r["dec20"] else {}),
                      **{f"fin{w // 12}": v[0] for w, v in r["fin"].items()}})
    pd.DataFrame(righe).to_csv(config.RISULTATI / "coppie.csv", index=False, float_format="%.6f")
    for r in res:
        r["serie"].to_csv(config.RISULTATI / f"serie_{r['sl']}.csv", index=False, float_format="%.6f")
    (config.RISULTATI / "coppie_usate.json").write_text(json.dumps([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
