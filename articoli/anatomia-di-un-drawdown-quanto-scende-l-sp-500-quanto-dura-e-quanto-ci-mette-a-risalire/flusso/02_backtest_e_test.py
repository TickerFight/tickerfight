"""Passo 2 - Anatomia di un drawdown: episodi dell'S&P 500 dal 1927 e confronto con serie rimescolate a caso.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine di calcolo
  episodi.csv          tutti gli episodi con profondità >= soglia minima (picco, minimo, recupero, durate)
  drawdown_serie.csv   il drawdown a ogni seduta
  rimescolate.csv      per ogni serie rimescolata: drawdown massimo, quota di sedute sott'acqua, numero di episodi
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore_drawdown as md

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore_drawdown.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def mesi(giorni):
    return giorni / config.GIORNI_MESE


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    c = close.to_numpy()
    n = len(c)
    anni = (date[-1] - date[0]).days / 365.25

    dd = md.serie_drawdown(c)
    pd.DataFrame({"Date": date, "drawdown": dd}).to_csv(config.RISULTATI / "drawdown_serie.csv", index=False, float_format="%.6f")

    # --- Dati ---------------------------------------------------------------------------------------------------
    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta della serie", "dati/gspc_giornaliero.csv")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta della serie", "dati/gspc_giornaliero.csv")
    reg("anno_inizio", str(date[0].date()), "anno", "Anno della prima seduta", "dati/gspc_giornaliero.csv")
    reg("n_sedute", n, "int", "Numero di sedute nella serie", "dati/gspc_giornaliero.csv")
    reg("n_anni", anni, "num1", "Anni coperti dalla serie (giorni di calendario / 365,25)", "date prima e ultima seduta")

    # --- Tempo passato sott'acqua -------------------------------------------------------------------------------
    reg("quota_sotto", float((dd < 0).mean()), "pct1", "Quota di sedute in cui la chiusura è sotto il massimo storico precedente", "serie drawdown")
    reg("quota_sul_massimo", float((dd == 0).mean()), "pct1", "Quota di sedute in cui la chiusura è un nuovo massimo storico (o lo eguaglia)", "serie drawdown")
    reg("n_massimi", int((dd == 0).sum()), "int", "Numero di sedute in cui la chiusura è un massimo storico", "serie drawdown")
    for s in (0.10, 0.20):
        reg(f"quota_sotto_{int(s*100)}", float((dd <= -s).mean()), "pct1", f"Quota di sedute con drawdown di almeno il {int(s*100)}%", "serie drawdown")
    reg("dd_attuale", float(-dd[-1]), "pct1", "Profondità del drawdown all'ultima seduta (0 = sul massimo)", "serie drawdown")

    # --- Episodi ------------------------------------------------------------------------------------------------
    ep = md.episodi(c, config.SOGLIA_MINIMA)
    righe = []
    for e in ep:
        ip, im, ir = e["i_picco"], e["i_minimo"], e["i_recupero"]
        discesa = (date[im] - date[ip]).days
        recupero = (date[ir] - date[im]).days if ir is not None else np.nan
        righe.append({"picco": date[ip].date(), "minimo": date[im].date(), "recupero": date[ir].date() if ir is not None else "",
                      "profondita": e["profondita"], "giorni_discesa": discesa, "giorni_recupero": recupero,
                      "giorni_totali": discesa + recupero if ir is not None else np.nan,
                      "sedute_discesa": im - ip, "aperto": ir is None})
    E = pd.DataFrame(righe)
    E.to_csv(config.RISULTATI / "episodi.csv", index=False, float_format="%.6f")

    for s in config.SOGLIE:
        k = int(round(s * 100))
        nk = int((E["profondita"] >= s).sum())
        reg(f"n_ep_{k:02d}", nk, "int", f"Numero di drawdown di almeno il {k}% (episodi, compreso l'eventuale aperto)", "episodi.csv")
    n10 = int((E["profondita"] >= 0.10).sum())
    reg("ep10_per_anno", n10 / anni, "num2", "Drawdown di almeno il 10% per anno (episodi / anni della serie)", "episodi.csv, anni della serie")
    reg("anni_tra_ep10", anni / n10, "num1", "Anni in media tra l'inizio di un drawdown di almeno il 10% e il successivo (anni della serie / episodi)", "episodi.csv, anni della serie")

    ch = E[~E["aperto"]]
    ch10 = ch[ch["profondita"] >= config.SOGLIA_RECUPERO_ANALISI]
    ch5 = ch
    reg("n_ep10_chiusi", len(ch10), "int", "Drawdown di almeno il 10% già recuperati", "episodi.csv")
    reg("n_ep05_chiusi", len(ch5), "int", "Drawdown di almeno il 5% già recuperati", "episodi.csv")
    reg("mediana_discesa_mesi", mesi(ch10["giorni_discesa"].median()), "num1", "Mediana dei mesi dal massimo al minimo, drawdown >= 10% recuperati", "episodi.csv")
    reg("mediana_recupero_mesi", mesi(ch10["giorni_recupero"].median()), "num1", "Mediana dei mesi dal minimo al nuovo massimo, drawdown >= 10% recuperati", "episodi.csv")
    reg("mediana_totale_mesi", mesi(ch10["giorni_totali"].median()), "num1", "Mediana dei mesi dal massimo al nuovo massimo, drawdown >= 10% recuperati", "episodi.csv")
    reg("media_totale_mesi", mesi(ch10["giorni_totali"].mean()), "num1", "Media dei mesi dal massimo al nuovo massimo, drawdown >= 10% recuperati", "episodi.csv")
    nrec = int((ch10["giorni_recupero"] > ch10["giorni_discesa"]).sum())
    reg("n_recupero_piu_lungo", nrec, "int", "Drawdown >= 10% recuperati in cui il recupero dura più della discesa", "episodi.csv")
    reg("quota_recupero_piu_lungo", nrec / len(ch10), "pct0", "Quota dei drawdown >= 10% recuperati in cui il recupero dura più della discesa", "episodi.csv")
    reg("mediana_prof_ep10", float(ch10["profondita"].median()), "pct1", "Profondità mediana dei drawdown >= 10% recuperati", "episodi.csv")
    ratio = (ch10["giorni_recupero"] / ch10["giorni_discesa"].clip(lower=1)).median()
    reg("rapporto_mediano", float(ratio), "num1", "Mediana del rapporto durata del recupero / durata della discesa, drawdown >= 10% recuperati", "episodi.csv")
    rho = md.rango_spearman(ch5["profondita"].to_numpy(), ch5["giorni_totali"].to_numpy())
    reg("rho_prof_durata", rho, "num2", "Correlazione di rango (Spearman) tra profondità e durata totale, drawdown >= 5% recuperati", "episodi.csv")
    # per fasce di profondità
    for lo, hi, k in ((0.05, 0.10, "05_10"), (0.10, 0.20, "10_20"), (0.20, 1.01, "20_piu")):
        sub = ch5[(ch5["profondita"] >= lo) & (ch5["profondita"] < hi)]
        reg(f"fascia_{k}_n", len(sub), "int", f"Drawdown recuperati con profondità tra {lo:.0%} e {min(hi,1):.0%}", "episodi.csv")
        reg(f"fascia_{k}_mediana_mesi", mesi(sub["giorni_totali"].median()), "num1", f"Mediana dei mesi totali (massimo -> nuovo massimo) nella fascia {k}", "episodi.csv")

    # --- Il più profondo ----------------------------------------------------------------------------------------
    pegg = E.sort_values("profondita", ascending=False).reset_index(drop=True)
    p = pegg.iloc[0]
    reg("dd_max", float(p["profondita"]), "pct1", "Drawdown massimo della serie", "episodi.csv")
    reg("dd_max_picco", str(p["picco"]), "data_lunga", "Data del massimo prima del drawdown più profondo", "episodi.csv")
    reg("dd_max_minimo", str(p["minimo"]), "data_lunga", "Data del minimo del drawdown più profondo", "episodi.csv")
    reg("dd_max_recupero", str(p["recupero"]), "data_lunga", "Data del nuovo massimo dopo il drawdown più profondo", "episodi.csv")
    reg("dd_max_discesa_mesi", mesi(p["giorni_discesa"]), "num1", "Mesi dal massimo al minimo nel drawdown più profondo", "episodi.csv")
    reg("dd_max_recupero_anni", p["giorni_recupero"] / 365.25, "num1", "Anni dal minimo al nuovo massimo nel drawdown più profondo", "episodi.csv")
    reg("dd_max_totale_anni", p["giorni_totali"] / 365.25, "num1", "Anni dal massimo al nuovo massimo nel drawdown più profondo", "episodi.csv")
    # i cinque peggiori
    for k in range(5):
        r = pegg.iloc[k]
        pre = f"top{k+1}_"
        reg(pre + "picco", str(r["picco"]), "data_lunga", f"Data del massimo prima del {k+1}° drawdown più profondo", "episodi.csv")
        reg(pre + "prof", float(r["profondita"]), "pct1", f"Profondità del {k+1}° drawdown più profondo", "episodi.csv")
        reg(pre + "discesa", mesi(r["giorni_discesa"]), "num1", f"Mesi di discesa del {k+1}° drawdown più profondo", "episodi.csv")
        if r["aperto"]:
            reg(pre + "recupero", "ancora in corso", "testo", f"Recupero del {k+1}° drawdown più profondo (testo)", "episodi.csv")
        else:
            reg(pre + "recupero", f"{mesi(r['giorni_recupero']):.1f}".replace(".", ",") + " mesi", "testo", f"Mesi di recupero del {k+1}° drawdown più profondo", "episodi.csv")
    # a -x% serve +y%
    for s in (0.20, 0.50):
        reg(f"serve_{int(s*100)}", 1 / (1 - s) - 1, "pct0", f"Guadagno necessario per tornare al massimo dopo una perdita del {int(s*100)}%", "formula 1/(1-perdita) - 1")
        reg(f"perdita_{int(s*100)}", s, "pct0", f"Perdita di esempio per il calcolo del guadagno necessario ({int(s*100)}%)", "config / esempio")
    # episodio in corso
    ap = E[E["aperto"]]
    if len(ap):
        a = ap.iloc[0]
        reg("aperto_si", 1, "int", "1 se alla fine della serie c'è un episodio >= 5% ancora aperto", "episodi.csv")
        reg("aperto_prof", float(a["profondita"]), "pct1", "Profondità massima dell'episodio ancora aperto", "episodi.csv")
        reg("aperto_picco", str(a["picco"]), "data_lunga", "Data del massimo dell'episodio ancora aperto", "episodi.csv")
    else:
        reg("aperto_si", 0, "int", "1 se alla fine della serie c'è un episodio >= 5% ancora aperto", "episodi.csv")

    # --- Confronto con il caso ----------------------------------------------------------------------------------
    rend = c[1:] / c[:-1] - 1
    rng = np.random.default_rng(config.SEME)
    righe_r = []
    for k in range(config.N_RIMESCOLAMENTI):
        x = np.concatenate([[1.0], np.cumprod(1 + rng.permutation(rend))])
        d = md.serie_drawdown(x)
        e2 = md.episodi(x, 0.10)
        righe_r.append({"dd_max": float(-d.min()), "quota_sotto": float((d < 0).mean()),
                        "n_ep10": len(e2), "n_ep20": sum(1 for z in e2 if z["profondita"] >= 0.20)})
    R = pd.DataFrame(righe_r)
    R.to_csv(config.RISULTATI / "rimescolate.csv", index=False, float_format="%.6f")
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    reg("n_rimesc", config.N_RIMESCOLAMENTI, "int", "Numero di serie rimescolate a caso", "config.py")
    reg("rim_dd_mediano", float(R["dd_max"].median()), "pct1", "Drawdown massimo mediano delle serie rimescolate", "rimescolate.csv")
    q95 = float(R["dd_max"].quantile(config.LIVELLO_CONFIDENZA))
    reg("rim_dd_p95", q95, "pct1", "95° percentile del drawdown massimo delle serie rimescolate", "rimescolate.csv")
    reg("rim_dd_p05", float(R["dd_max"].quantile(1 - config.LIVELLO_CONFIDENZA)), "pct1", "5° percentile del drawdown massimo delle serie rimescolate", "rimescolate.csv")
    reg("rim_quota_piu_profonde", float((R["dd_max"] >= p["profondita"]).mean()), "pct1", "Quota di serie rimescolate con drawdown massimo almeno pari a quello reale", "rimescolate.csv")
    reg("rim_quota_sotto", float(R["quota_sotto"].median()), "pct1", "Quota mediana di sedute sott'acqua nelle serie rimescolate", "rimescolate.csv")
    reg("rim_n_ep10", float(R["n_ep10"].median()), "num1", "Numero mediano di drawdown >= 10% nelle serie rimescolate", "rimescolate.csv")
    reg("rim_n_ep20", float(R["n_ep20"].median()), "num1", "Numero mediano di drawdown >= 20% nelle serie rimescolate", "rimescolate.csv")
    reg("n_ep_20_reale", int((E["profondita"] >= 0.20).sum()), "int", "Numero di drawdown >= 20% nella serie reale", "episodi.csv")
    reg("n_ep_10_reale", n10, "int", "Numero di drawdown >= 10% nella serie reale", "episodi.csv")

    # --- Costanti dichiarate in config.py, citate nel testo ------------------------------------------------------
    for s in config.SOGLIE:
        reg(f"s{int(round(s*100)):02d}", s, "pct0", f"Soglia di profondità dichiarata in config.py ({s:.0%})", "config.py, SOGLIE")
    reg("rho_soglia", 0.5, "num1", "Soglia di correlazione di rango dell'ipotesi 4", "config.py, IPOTESI")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello dell'intervallo usato per il 95° percentile", "config.py")
    reg("anno_gz", 1993, "annonum", "Anno di pubblicazione di Grossman e Zhou", "abstract letto su IDEAS/RePEc (Mathematical Finance)")
    reg("anno_ma", 2004, "annonum", "Anno di pubblicazione di Magdon-Ismail e Atiya", "pagina della rivista Risk (risk.net)")
    reg("rif_gz", "3(3), 241-276", "testo", "Volume, numero e pagine di Grossman e Zhou su Mathematical Finance", "abstract letto su IDEAS/RePEc")
    reg("sedute_anno", config.SEDUTE_ANNO, "int", "Sedute di borsa in un anno (convenzione)", "config.py")

    # --- Ipotesi: esito (calcolato) ---------------------------------------------------------------------------------
    reg("ip1_ok", int((dd < 0).mean() > 2 / 3), "int", "Ipotesi 1 verificata (1 = sì)", "confronto con la soglia di config.IPOTESI")
    reg("ip2_ok", int(n10 / anni >= 0.5), "int", "Ipotesi 2 verificata (1 = sì)", "confronto con la soglia di config.IPOTESI")
    reg("ip3_ok", int(nrec / len(ch10) > 0.5), "int", "Ipotesi 3 verificata (1 = sì)", "confronto con la soglia di config.IPOTESI")
    reg("ip4_ok", int(rho > 0.5), "int", "Ipotesi 4 verificata (1 = sì)", "confronto con la soglia di config.IPOTESI")
    reg("ip5_ok", int(p["profondita"] > q95), "int", "Ipotesi 5 verificata (1 = sì)", "confronto con la soglia di config.IPOTESI")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {len(E)} episodi >= {config.SOGLIA_MINIMA:.0%}")
    print({k: RIS[k]["valore"] for k in RIS if k.startswith("ip") and k.endswith("_ok")})


if __name__ == "__main__":
    main()
