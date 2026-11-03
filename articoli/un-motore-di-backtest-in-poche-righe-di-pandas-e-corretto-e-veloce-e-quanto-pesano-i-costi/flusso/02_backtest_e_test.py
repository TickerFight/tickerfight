"""Passo 2 - Il motore vettoriale alla prova: righe, correttezza, velocità, costi.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json   ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv       valore (una seduta su cinque) di 50/200 senza costi, 50/200 con costi, buy & hold
  costi.csv       rendimento annuo di ogni regola per ogni livello di costo
  tempi.csv       tempo del motore vettoriale e del ciclo, per regola
"""
import ast
import json
import platform
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore_50_righe as m
from motore_ciclo import backtest_ciclo

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore_50_righe.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def importo(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") + " euro" if x < 1e9 else f"un numero con {int(np.floor(np.log10(x))) + 1} cifre"


def righe_di_codice(percorso) -> int:
    """Righe del file escluse quelle vuote, i commenti a riga intera e le docstring."""
    testo = percorso.read_text(encoding="utf-8")
    albero = ast.parse(testo)
    doc = set()
    for nodo in ast.walk(albero):
        if isinstance(nodo, (ast.Module, ast.FunctionDef)) and ast.get_docstring(nodo, clean=False) is not None:
            primo = nodo.body[0]
            doc.update(range(primo.lineno, primo.end_lineno + 1))
    return sum(1 for n, r in enumerate(testo.splitlines(), 1) if r.strip() and not r.strip().startswith("#") and n not in doc)


def tempo_migliore(f, ripetizioni: int) -> float:
    migliore = float("inf")
    for _ in range(ripetizioni):
        t0 = time.perf_counter()
        f()
        migliore = min(migliore, time.perf_counter() - t0)
    return migliore


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close_pieno = df["Close"].astype(float)
    if (close_pieno <= 0).any() or close_pieno.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    sig_pieno = {"un_giorno": m.segnale_un_giorno(close_pieno), "media_20": m.segnale_sopra_media(close_pieno, config.SMA_BREVE),
                 "medie_50_200": m.segnale_medie(close_pieno, config.SMA_VELOCE, config.SMA_LENTA)}
    i0 = config.INIZIO_TEST_SEDUTE
    close = close_pieno.iloc[i0 - 1:]          # una seduta in più: il rendimento del primo giorno del test ha il suo giorno prima
    date = close.index
    anni = (date[-1] - date[0]).days / 365.25
    sig = {k: v.iloc[i0 - 1:] for k, v in sig_pieno.items()}

    reg("prima_data", str(close_pieno.index[0].date()), "data_lunga", "Prima seduta dei dati scaricati", "dati/gspc_giornaliero.csv")
    reg("data_inizio", str(date[1].date()), "data_lunga", "Prima seduta del test (le precedenti servono per le medie)", "dati/ e config.py, INIZIO_TEST_SEDUTE")
    reg("data_fine", str(date[-1].date()), "data_lunga", "Ultima seduta del test", "dati/gspc_giornaliero.csv")
    reg("sedute_avvio", i0, "int", "Sedute iniziali usate solo per calcolare le medie", "config.py, INIZIO_TEST_SEDUTE")
    reg("n_sedute", len(close) - 1, "int", "Sedute nel periodo del test", "dati/")
    reg("anni_test", anni, "num1", "Anni del test")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, solo per dare un'idea", "config.py, CAPITALE")
    reg("sma_breve", config.SMA_BREVE, "annonum", "Giorni della media breve", "config.py")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py")
    reg("n_regole", len(config.REGOLE), "int", "Regole confrontate", "config.py, REGOLE")
    reg("costo_base", config.COSTO_BASE, "pct1", "Costo per ogni cambio di posizione, in percentuale del capitale", "config.py, COSTO_BASE")

    # Anni citati nel testo (letteratura), registrati con la loro fonte
    reg("anno_bailey", 2014, "annonum", "Anno di Bailey, Borwein, López de Prado e Zhu, Notices of the AMS", "pagina dello studio su scholarworks.wmich.edu")
    reg("anno_brock", 1992, "annonum", "Anno di Brock, Lakonishok e LeBaron, Journal of Finance", "pagina dello studio su ideas.repec.org")
    reg("brock_rivista", "47(5), 1731–1764", "testo", "Volume, numero e pagine di Brock, Lakonishok e LeBaron nel Journal of Finance", "pagina dello studio su ideas.repec.org")
    reg("bailey_rivista", "61(5), 458", "testo", "Volume, numero e pagina di Bailey e altri nelle Notices of the AMS", "pagina dello studio su scholarworks.wmich.edu")
    reg("brock_inizio", 1897, "annonum", "Primo anno dei dati Dow Jones usati da Brock, Lakonishok e LeBaron", "abstract dello studio, ideas.repec.org")
    reg("brock_fine", 1986, "annonum", "Ultimo anno dei dati Dow Jones usati da Brock, Lakonishok e LeBaron", "abstract dello studio, ideas.repec.org")

    # --- Ipotesi 1: righe di codice -----------------------------------------------------------------------------
    righe = righe_di_codice(config.BASE / "flusso" / "motore_50_righe.py")
    righe_ciclo = righe_di_codice(config.BASE / "flusso" / "motore_ciclo.py")
    reg("righe_motore", righe, "int", "Righe di codice del motore vettoriale (escluse vuote, commenti e docstring), compresi segnali e metriche", "motore_50_righe.py")
    reg("righe_ciclo", righe_ciclo, "int", "Righe di codice del motore a ciclo (escluse vuote, commenti e docstring)", "motore_ciclo.py")
    reg("soglia_righe", config.SOGLIA_RIGHE, "int", "Soglia di righe fissata nell'ipotesi", "config.py, SOGLIA_RIGHE")
    reg("h1_ok", int(righe <= config.SOGLIA_RIGHE), "int", "1 se il motore sta nella soglia di righe", "calcolo sopra")

    # --- Buy & hold -------------------------------------------------------------------------------------------
    bh = m.backtest(close, pd.Series(True, index=close.index)).iloc[1:]
    bh_val = bh["valore"]
    reg("cagr_bh", m.cagr(bh_val, anni), "pct1", "Rendimento annuo composto del buy & hold, senza costi né tasse")
    reg("dd_bh", -m.perdita_massima(bh_val), "pct0", "Perdita massima dal picco del buy & hold")
    reg("finale_bh", importo(config.CAPITALE * bh_val.iloc[-1]), "testo", "Valore finale del buy & hold")

    righe_costi, righe_tempi, curva = [], [], None
    diff_max_tutte = 0.0
    n_h3 = 0
    chiusure_l = close.tolist()
    for rid, _ in config.REGOLE:
        s = sig[rid]
        s_l = s.tolist()
        # Ipotesi 2: vettoriale = ciclo, per ogni costo della griglia
        diff = 0.0
        for costo in config.COSTI:
            a = m.backtest(close, s, costo)["valore"].to_numpy()
            b = np.array(backtest_ciclo(chiusure_l, s_l, costo))
            diff = max(diff, float(np.max(np.abs(a / b - 1.0))))
        diff_max_tutte = max(diff_max_tutte, diff)
        reg(f"{rid}_diff", diff, "sci", f"Differenza relativa massima, su tutte le sedute e su tutti i costi della griglia, tra motore vettoriale e ciclo, regola «{rid}»")
        # Ipotesi 3: tempi
        tv = tempo_migliore(lambda: m.backtest(close, s, config.COSTO_BASE), config.RIPETIZIONI_TEMPO)
        tc = tempo_migliore(lambda: backtest_ciclo(chiusure_l, s_l, config.COSTO_BASE), config.RIPETIZIONI_TEMPO)
        righe_tempi.append({"regola": rid, "vettoriale_ms": tv * 1000, "ciclo_ms": tc * 1000})
        reg(f"{rid}_ms_vett", tv * 1000, "num1", f"Millisecondi del motore vettoriale (il più veloce di più esecuzioni), regola «{rid}»")
        reg(f"{rid}_ms_ciclo", tc * 1000, "num1", f"Millisecondi del ciclo (il più veloce di più esecuzioni), regola «{rid}»")
        reg(f"{rid}_rapporto", tc / tv, "num1", f"Quante volte il ciclo è più lento del motore vettoriale, regola «{rid}»")
        n_h3 += int(tc / tv >= config.SOGLIA_VELOCITA)
        # Costi
        base = m.backtest(close, s, 0.0).iloc[1:]
        cagr_costi = []
        for costo in config.COSTI:
            bt = m.backtest(close, s, costo).iloc[1:]
            cagr_costi.append(m.cagr(bt["valore"], anni))
            righe_costi.append({"regola": rid, "costo": costo, "cagr": cagr_costi[-1]})
        k_base = config.COSTI.index(config.COSTO_BASE)
        bt_base = m.backtest(close, s, config.COSTO_BASE).iloc[1:]
        n_cambi = int(base["pos"].diff().abs().fillna(base["pos"].abs()).sum())
        reg(f"{rid}_cagr_lordo", cagr_costi[0], "pct1", f"Rendimento annuo senza costi, regola «{rid}»")
        reg(f"{rid}_cagr_netto", cagr_costi[k_base], "pct1", f"Rendimento annuo con il costo base per cambio, regola «{rid}»")
        reg(f"{rid}_perdita_costi", cagr_costi[0] - cagr_costi[k_base], "pp2", f"Punti di rendimento annuo persi per i costi, regola «{rid}»")
        reg(f"{rid}_cagr_costo_max", cagr_costi[-1], "pct1", f"Rendimento annuo con il costo più alto della griglia, regola «{rid}»")
        reg(f"{rid}_finale_netto", importo(config.CAPITALE * bt_base["valore"].iloc[-1]), "testo", f"Valore finale con il costo base, regola «{rid}»")
        reg(f"{rid}_dd_lordo", -m.perdita_massima(base["valore"]), "pct0", f"Perdita massima senza costi, regola «{rid}»")
        reg(f"{rid}_dd_netto", -m.perdita_massima(bt_base["valore"]), "pct0", f"Perdita massima con il costo base, regola «{rid}»")
        reg(f"{rid}_cambi_anno", n_cambi / anni, "int", f"Cambi di posizione all'anno, regola «{rid}»")
        reg(f"{rid}_quota_investito", float(base["pos"].mean()), "pct0", f"Quota di sedute investite, regola «{rid}»")
        if rid == "medie_50_200":
            camp = np.r_[np.arange(0, len(base), 5), len(base) - 1]
            curva = pd.DataFrame({"data": base.index[camp], "valore_bh": bh_val.iloc[camp].to_numpy(),
                                  "valore_lordo": base["valore"].iloc[camp].to_numpy(), "valore_netto": bt_base["valore"].iloc[camp].to_numpy()})

    reg("diff_max", diff_max_tutte, "sci", "Differenza relativa massima tra motore vettoriale e ciclo su tutte le regole, sedute e costi", "calcolo sopra")
    reg("soglia_diff", config.SOGLIA_DIFFERENZA, "sci", "Soglia di differenza fissata nell'ipotesi", "config.py, SOGLIA_DIFFERENZA")
    reg("h2_ok", int(diff_max_tutte < config.SOGLIA_DIFFERENZA), "int", "1 se i due motori coincidono entro la soglia", "calcolo sopra")
    reg("soglia_velocita", config.SOGLIA_VELOCITA, "int", "Soglia di velocità fissata nell'ipotesi, volte", "config.py, SOGLIA_VELOCITA")
    reg("n_h3", n_h3, "int", "Regole per cui il motore vettoriale è almeno SOGLIA_VELOCITA volte più veloce", "calcolo sopra")
    reg("h3_ok", int(n_h3 == len(config.REGOLE)), "int", "1 se la soglia di velocità vale per tutte le regole", "calcolo sopra")

    pl, pv = RIS["medie_50_200_perdita_costi"]["valore"], RIS["un_giorno_perdita_costi"]["valore"]
    reg("soglia_costo_lenta", config.SOGLIA_COSTO_LENTA, "pp1", "Perdita massima per i costi ammessa per le medie 50/200 nell'ipotesi, punti percentuali", "config.py")
    reg("soglia_costo_veloce", config.SOGLIA_COSTO_VELOCE, "pp1", "Perdita minima per i costi attesa per la regola di un giorno, punti percentuali", "config.py")
    reg("h4_ok", int(pl < config.SOGLIA_COSTO_LENTA and pv > config.SOGLIA_COSTO_VELOCE), "int", "1 se vale l'ipotesi sui costi", "calcolo sopra")
    h5 = int(RIS["medie_50_200_cagr_lordo"]["valore"] < RIS["cagr_bh"]["valore"] and RIS["medie_50_200_dd_lordo"]["valore"] < RIS["dd_bh"]["valore"])
    reg("h5_rendimento_sotto", int(RIS["medie_50_200_cagr_lordo"]["valore"] < RIS["cagr_bh"]["valore"]), "int", "1 se le medie 50/200 rendono meno del buy & hold", "calcolo sopra")
    reg("h5_dd_sotto", int(RIS["medie_50_200_dd_lordo"]["valore"] < RIS["dd_bh"]["valore"]), "int", "1 se le medie 50/200 hanno una perdita massima più bassa del buy & hold", "calcolo sopra")
    reg("h5_ok", h5, "int", "1 se valgono entrambe le parti dell'ipotesi 5", "calcolo sopra")

    pd.DataFrame(righe_costi).to_csv(config.RISULTATI / "costi.csv", index=False, float_format="%.6f")
    pd.DataFrame(righe_tempi).to_csv(config.RISULTATI / "tempi.csv", index=False, float_format="%.4f")
    curva.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.6f")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; righe motore {righe}; differenza massima {diff_max_tutte:.2e}")


if __name__ == "__main__":
    main()
