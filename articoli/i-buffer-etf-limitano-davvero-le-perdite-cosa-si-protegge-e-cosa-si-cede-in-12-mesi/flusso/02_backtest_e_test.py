"""Passo 2 - Buffer ETF contro S&P 500: finestre di 12 mesi per ogni fondo, test delle ipotesi.

Legge SOLO dati/serie_giornaliere.csv e produce in risultati/:
  metriche.json   ogni numero dell'articolo, con descrizione e origine
  finestre.csv    una riga per fondo e anno di partenza: date, rendimento del fondo, dell'S&P 500 TR, della liquidità e del portafoglio 80/20
  classi.csv      differenza media (fondo meno indice) per classe di rendimento dell'indice
Il periodo di un fondo va dal primo giorno di borsa del suo mese di partenza al primo giorno di borsa dello stesso mese dell'anno dopo.
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


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    g = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    w = fx.finestre(g, config.FONDI, config.MESI_PERIODO)
    if len(w) < 20:
        raise SystemExit(f"Solo {len(w)} finestre complete: troppo poche.")
    w["r_mix"] = fx.mix(w["r_spy"].to_numpy(), w["r_cash"].to_numpy(), config.QUOTA_AZIONI_MIX)
    w["diff"] = w["r_fondo"] - w["r_spy"]
    w.to_csv(config.RISULTATI / "finestre.csv", index=False, float_format="%.6f")
    N = len(w)
    giu = w[w["r_spy"] < 0]
    forte = w[w["r_spy"] > config.SOGLIA_FORTE]
    medio = w[(w["r_spy"] >= 0) & (w["r_spy"] <= config.SOGLIA_FORTE)]
    anni_p = sorted(w["anno_partenza"].unique())
    fondi_ok = sorted(w["fondo"].unique())

    reg("prima_data", str(w["inizio"].min().date()) if hasattr(w["inizio"].min(), "date") else str(w["inizio"].min())[:10], "data_lunga", "Primo giorno di partenza di una finestra completa", "finestre.csv")
    reg("data_ultima", str(pd.Timestamp(w["fine"].max()).date()), "data_lunga", "Ultimo giorno di fine di una finestra completa", "finestre.csv")
    reg("n_fondi", len(fondi_ok), "int", "Buffer ETF con almeno un periodo completo di 12 mesi", "finestre.csv")
    reg("n_finestre", N, "int", "Periodi completi di 12 mesi (un fondo e un anno di partenza)", "finestre.csv")
    reg("n_anni_partenza", len(anni_p), "int", "Anni di partenza distinti dei periodi", "finestre.csv")
    reg("anno_primo", int(anni_p[0]), "annonum", "Primo anno di partenza", "finestre.csv")
    reg("anno_ultimo", int(anni_p[-1]), "annonum", "Ultimo anno di partenza", "finestre.csv")
    reg("rend_medio_fondo", float(w["r_fondo"].mean()), "pct1", "Rendimento medio dei fondi sui periodi di 12 mesi", "finestre.csv")
    reg("rend_medio_spy", float(w["r_spy"].mean()), "pct1", "Rendimento medio dell'S&P 500 TR sulle stesse finestre", "finestre.csv")
    reg("diff_media", float(w["diff"].mean()), "pp1", "Rendimento medio del fondo meno quello dell'indice (punti percentuali)", "finestre.csv")
    reg("fondo_min", float(w["r_fondo"].min()), "pct1", "Rendimento peggiore di un fondo su un periodo", "finestre.csv")
    reg("spy_min", float(w["r_spy"].min()), "pct1", "Rendimento peggiore dell'S&P 500 TR su un periodo", "finestre.csv")
    reg("fondo_max", float(w["r_fondo"].max()), "pct1", "Rendimento migliore di un fondo su un periodo", "finestre.csv")
    reg("spy_max", float(w["r_spy"].max()), "pct1", "Rendimento migliore dell'S&P 500 TR su un periodo", "finestre.csv")
    reg("h4_ok", int(w["diff"].mean() < 0), "int", "1 se l'ipotesi 4 è rispettata (i fondi rendono in media meno dell'indice)", "finestre.csv")

    # Ipotesi 1 e 2: periodi di ribasso
    reg("n_giu", len(giu), "int", "Periodi in cui l'S&P 500 TR perde", "finestre.csv")
    if len(giu):
        q1 = float((giu["r_fondo"] > giu["r_spy"]).mean())
        rid = float((giu["r_fondo"] - giu["r_spy"]).mean())
        reg("giu_quota_meglio", q1, "pct0", "Quota dei periodi di ribasso in cui il fondo perde meno dell'indice", "finestre.csv")
        reg("giu_riduzione", rid, "pp1", "Riduzione media della perdita (fondo meno indice) nei periodi di ribasso, punti percentuali", "finestre.csv")
        reg("giu_spy_medio", float(giu["r_spy"].mean()), "pct1", "Rendimento medio dell'S&P 500 TR nei periodi di ribasso", "finestre.csv")
        reg("giu_fondo_medio", float(giu["r_fondo"].mean()), "pct1", "Rendimento medio dei fondi nei periodi di ribasso", "finestre.csv")
        reg("giu_n_meglio", int((giu["r_fondo"] > giu["r_spy"]).sum()), "int", "Periodi di ribasso in cui il fondo perde meno dell'indice", "finestre.csv")
        reg("giu_anni", ", ".join(str(int(a)) for a in sorted(giu["anno_partenza"].unique())), "testo", "Anni di partenza dei periodi di ribasso", "finestre.csv")
        reg("giu_fondo_peggio", float(giu["r_fondo"].min()), "pct1", "Perdita peggiore di un fondo nei periodi di ribasso", "finestre.csv")
        reg("giu_spy_peggio", float(giu["r_spy"].min()), "pct1", "Perdita peggiore dell'indice nei periodi di ribasso", "finestre.csv")
        reg("giu_fondo_positivi", int((giu["r_fondo"] > 0).sum()), "int", "Periodi di ribasso dell'indice chiusi in positivo dal fondo", "finestre.csv")
        reg("h1_ok", int(q1 >= config.H1_QUOTA_MIN), "int", "1 se l'ipotesi 1 è rispettata", "finestre.csv")
        reg("h2_ok", int(rid >= config.H2_RIDUZIONE_MIN), "int", "1 se l'ipotesi 2 è rispettata", "finestre.csv")
    else:
        raise SystemExit("Nessun periodo di ribasso dell'indice: ipotesi 1 e 2 non verificabili.")
    reg("h1_min", config.H1_QUOTA_MIN, "pct0", "Soglia dell'ipotesi 1", "config.py")
    reg("h2_min", config.H2_RIDUZIONE_MIN, "pp1", "Soglia dell'ipotesi 2 (punti percentuali)", "config.py")

    # Ipotesi 3: forti rialzi
    reg("soglia_forte", config.SOGLIA_FORTE, "pct0", "Rendimento dell'indice oltre il quale il periodo è «di forte rialzo»", "config.py")
    reg("n_forte", len(forte), "int", "Periodi di forte rialzo dell'indice", "finestre.csv")
    reg("n_medio", len(medio), "int", "Periodi con l'indice tra 0 e la soglia di forte rialzo", "finestre.csv")
    if len(forte):
        q3 = float((forte["r_fondo"] < forte["r_spy"]).mean())
        reg("forte_quota_meno", q3, "pct0", "Quota dei periodi di forte rialzo in cui il fondo rende meno dell'indice", "finestre.csv")
        reg("forte_diff", float((forte["r_fondo"] - forte["r_spy"]).mean()), "pp1", "Differenza media (fondo meno indice) nei forti rialzi, punti percentuali", "finestre.csv")
        reg("forte_spy_medio", float(forte["r_spy"].mean()), "pct1", "Rendimento medio dell'indice nei forti rialzi", "finestre.csv")
        reg("forte_fondo_medio", float(forte["r_fondo"].mean()), "pct1", "Rendimento medio dei fondi nei forti rialzi", "finestre.csv")
        reg("h3_ok", int(q3 >= config.H3_QUOTA_MIN), "int", "1 se l'ipotesi 3 è rispettata", "finestre.csv")
    else:
        raise SystemExit("Nessun periodo di forte rialzo: ipotesi 3 non verificabile.")
    reg("h3_min", config.H3_QUOTA_MIN, "pct0", "Soglia dell'ipotesi 3", "config.py")
    if len(medio):
        reg("medio_diff", float((medio["r_fondo"] - medio["r_spy"]).mean()), "pp1", "Differenza media (fondo meno indice) nei periodi di rialzo moderato, punti percentuali", "finestre.csv")
        reg("medio_spy_medio", float(medio["r_spy"].mean()), "pct1", "Rendimento medio dell'indice nei periodi di rialzo moderato", "finestre.csv")
        reg("medio_fondo_medio", float(medio["r_fondo"].mean()), "pct1", "Rendimento medio dei fondi nei periodi di rialzo moderato", "finestre.csv")
    classi = pd.DataFrame({
        "classe": ["indice in ribasso", "indice tra 0 e soglia", "indice oltre soglia"],
        "n": [len(giu), len(medio), len(forte)],
        "diff_media": [float((x["r_fondo"] - x["r_spy"]).mean()) if len(x) else np.nan for x in (giu, medio, forte)]})
    classi.to_csv(config.RISULTATI / "classi.csv", index=False, float_format="%.6f")

    # Ipotesi 5: portafoglio 80/20
    quota_meglio_mix = float((w["r_fondo"] > w["r_mix"]).mean())
    reg("quota_mix", config.QUOTA_AZIONI_MIX, "pct0", "Quota di S&P 500 nel portafoglio semplice di confronto (il resto in liquidità)", "config.py")
    reg("rend_medio_mix", float(w["r_mix"].mean()), "pct1", "Rendimento medio del portafoglio 80/20 sui periodi", "finestre.csv")
    reg("mix_min", float(w["r_mix"].min()), "pct1", "Rendimento peggiore del portafoglio 80/20 su un periodo", "finestre.csv")
    reg("fondo_batte_mix", quota_meglio_mix, "pct0", "Quota dei periodi in cui il fondo rende più del portafoglio 80/20", "finestre.csv")
    reg("mix_batte_fondo", 1 - quota_meglio_mix, "pct0", "Quota dei periodi in cui il portafoglio 80/20 rende almeno quanto il fondo", "finestre.csv")
    reg("quota_cash", 1 - config.QUOTA_AZIONI_MIX, "pct0", "Quota di liquidità nel portafoglio semplice di confronto", "config.py")
    reg("mesi_periodo", config.MESI_PERIODO, "int", "Mesi di un periodo (outcome period) dei buffer ETF", "config.py")
    reg("anno_hill", 2006, "annonum", "Anno di pubblicazione di Hill, Balasubramanian, Gregory e Tierens", "Financial Analysts Journal, vol. 62")
    reg("anno_in", 2015, "annonum", "Anno di pubblicazione di Israelov e Nielsen", "Financial Analysts Journal, vol. 71")
    reg("h5_min", config.H5_QUOTA_MIN, "pct0", "Soglia dell'ipotesi 5", "config.py")
    reg("h5_ok", int((1 - quota_meglio_mix) >= config.H5_QUOTA_MIN), "int", "1 se l'ipotesi 5 è rispettata (il portafoglio 80/20 rende almeno quanto il fondo in metà o più dei periodi)", "finestre.csv")
    giu_mix = giu["r_mix"]
    reg("giu_mix_medio", float(giu_mix.mean()), "pct1", "Rendimento medio del portafoglio 80/20 nei periodi di ribasso dell'indice", "finestre.csv")
    reg("giu_fondo_meglio_mix", float((giu["r_fondo"] > giu["r_mix"]).mean()), "pct0", "Quota dei periodi di ribasso in cui il fondo rende più del portafoglio 80/20", "finestre.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {N} finestre ({len(fondi_ok)} fondi, anni {anni_p[0]}-{anni_p[-1]})")
    print(f"H1 {q1:.0%} su {len(giu)}; H2 {rid:+.2%}; H3 {q3:.0%} su {len(forte)}; H4 diff {w['diff'].mean():+.2%}; H5 mix>=fondo {1-quota_meglio_mix:.0%}")


if __name__ == "__main__":
    main()
