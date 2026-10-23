"""Passo 2 - 500 euro su ciascuno di 50 titoli dell'S&P 500: regola 50/200 contro buy & hold, in euro.

Legge SOLO i file in dati/ (scaricati dal passo 1) e produce in risultati/:
  metriche.json              ogni numero dell'articolo, con descrizione e origine di calcolo
  classifica.csv             una riga per titolo: valori finali netti, differenza, perdita massima, operazioni
  operazioni_regola.csv      registro di tutte le operazioni della regola, per titolo
  curva_portafoglio.csv      valore giorno per giorno dei 50 x 500 euro con la regola e con il buy & hold

Regole del metodo:
  - l'ipotesi, la scelta dei titoli e i parametri sono dichiarati in config.py prima di guardare i risultati;
  - il segnale di fine seduta t decide l'ordine di t+1 (nessun look-ahead);
  - ogni titolo parte con 500 euro, commissione fissa per ordine e tassa del 26% in euro, come nell'articolo su Apple;
  - ogni numero dell'articolo passa da reg(): niente cifre scritte a mano nel testo.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import simulazione as s

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con simulazione.py"
SCEN = {"lordo": (0.0, 0.0), "comm": (config.COMMISSIONE, 0.0), "netto": (config.COMMISSIONE, config.ALIQUOTA)}


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    sel = pd.read_csv(config.DATI / "selezione.csv")
    comp = pd.read_csv(config.FILE_COMPOSIZIONE)
    info = comp.set_index("ticker_yahoo")
    cambio = s.carica_csv(config.FILE_CAMBIO)
    tickers = meta["titoli"]

    righe, operazioni, curve_mm, curve_bh = [], [], {}, {}
    date_inizio, date_fine = set(), set()
    for t in tickers:
        df = s.prepara(s.carica_csv(config.DATI_TITOLI / f"{t}.csv"), cambio, config.SMA_VELOCE, config.SMA_LENTA)
        fine = df.index[-1]
        i0 = s.indice_data(df, fine - pd.DateOffset(years=config.ANNI_TEST))
        if i0 < config.SMA_LENTA + 1:
            raise SystemExit(f"{t}: storia insufficiente per la media lenta.")
        if df["fx"].iloc[i0 - 1:].isna().any():
            raise SystemExit(f"{t}: cambio mancante nel periodo del test.")
        date_inizio.add(df.index[i0])
        date_fine.add(fine)
        R = {}
        for modo in (config.MODO_PRINCIPALE, config.MODO_CONTROLLO):
            for sc, (c, a) in SCEN.items():
                for nome, strat in (("mm", True), ("bh", False)):
                    R[(modo, sc, nome)] = s.simula(df, i0, config.CAPITALE, c, a, modo, strat)
        P = config.MODO_PRINCIPALE
        mm, bh = R[(P, "netto", "mm")], R[(P, "netto", "bh")]
        righe.append({
            "ticker": t, "nome": info.loc[t, "nome"], "settore": info.loc[t, "settore"],
            "finale_mm_lordo": R[(P, "lordo", "mm")]["valore_finale_eur"], "finale_bh_lordo": R[(P, "lordo", "bh")]["valore_finale_eur"],
            "finale_mm_netto": mm["valore_finale_eur"], "finale_bh_netto": bh["valore_finale_eur"],
            "differenza": mm["valore_finale_eur"] - bh["valore_finale_eur"],
            "differenza_chiusura": R[(config.MODO_CONTROLLO, "netto", "mm")]["valore_finale_eur"]
            - R[(config.MODO_CONTROLLO, "netto", "bh")]["valore_finale_eur"],
            "rend_mm_netto": mm["rendimento_totale"], "rend_bh_netto": bh["rendimento_totale"],
            "cagr_mm_netto": mm["cagr"], "cagr_bh_netto": bh["cagr"],
            "maxdd_mm": -mm["perdita_massima"], "maxdd_bh": -bh["perdita_massima"],
            "quota_investito": mm["quota_giorni_investito"], "n_ordini_mm": mm["n_acquisti"] + mm["n_vendite"],
            "tasse_mm": mm["tasse_eur"], "tasse_bh": bh["tasse_eur"],
            "commissioni_mm": mm["commissioni_eur"], "commissioni_bh": bh["commissioni_eur"],
        })
        for o in mm["operazioni"]:
            operazioni.append({"ticker": t, **o})
        d = df.index[i0:]
        curve_mm[t] = pd.Series(mm["equity"], index=d)
        curve_bh[t] = pd.Series(bh["equity"], index=d)

    if max(date_fine) - min(date_fine) > pd.Timedelta(days=5) or max(date_inizio) - min(date_inizio) > pd.Timedelta(days=5):
        raise SystemExit("I titoli non coprono lo stesso periodo di test.")
    tab = pd.DataFrame(righe).sort_values("differenza", ascending=False).reset_index(drop=True)
    tab.insert(0, "posizione", np.arange(1, len(tab) + 1))
    tab.to_csv(config.RISULTATI / "classifica.csv", index=False, float_format="%.6f")
    pd.DataFrame(operazioni).to_csv(config.RISULTATI / "operazioni_regola.csv", index=False, float_format="%.6f")
    pf_mm = pd.DataFrame(curve_mm).sum(axis=1, min_count=len(tickers))
    pf_bh = pd.DataFrame(curve_bh).sum(axis=1, min_count=len(tickers))
    ok = pf_mm.notna() & pf_bh.notna()
    pf = pd.DataFrame({"data": pf_mm.index[ok], "valore_regola_netto": pf_mm[ok].to_numpy(), "valore_bh_netto": pf_bh[ok].to_numpy()})
    pf.to_csv(config.RISULTATI / "curva_portafoglio.csv", index=False, float_format="%.6f")

    n = len(tab)
    origine_dati = f"dati/ ({meta['fonte']}, {n} titoli e {config.TICKER_CAMBIO}, scaricati il {meta['scaricato_il_utc'][:10]})"
    cl = "classifica.csv"

    # --- Parametri e dati ---------------------------------------------------------------------------------
    reg("n_titoli", n, "int", "Numero di titoli del campione", "config.py, N_TITOLI (controllato su classifica.csv)")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per ogni titolo, in euro", "config.py, CAPITALE")
    reg("capitale_totale", config.CAPITALE * n, "int", "Capitale iniziale complessivo dei 50 titoli, in euro", "config.py: CAPITALE per numero di titoli")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ogni ordine, in euro", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py, SMA_VELOCE")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py, SMA_LENTA")
    reg("anni_test", config.ANNI_TEST, "annonum", "Anni del test", "config.py, ANNI_TEST")
    reg("seme", config.SEME, "annonum", "Seme del sorteggio dei titoli", "config.py, SEME")
    reg("data_inizio", str(min(date_inizio).date()), "data_lunga", "Prima seduta del test", origine_dati)
    reg("data_fine", str(max(date_fine).date()), "data_lunga", "Ultima seduta del test (ultimo dato scaricato)", origine_dati)
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("n_componenti", meta["componenti_nell_elenco"], "int", "Componenti dell'S&P 500 nell'elenco usato per il sorteggio", "dati/metadati.json")
    reg("n_provati", meta["titoli_provati"], "int", "Titoli provati nel sorteggio per ottenerne 50 validi", "dati/metadati.json")
    reg("n_scartati", meta["titoli_scartati"], "int", "Titoli scartati per dati assenti o storia troppo corta", "dati/metadati.json")

    # --- Risultati sul campione ---------------------------------------------------------------------------
    vince = tab["differenza"] > 0
    reg("n_vince", int(vince.sum()), "int", "Titoli su cui la regola chiude sopra il buy & hold, dopo costi e tasse", f"{cl}: differenza > 0")
    reg("n_perde", int((~vince).sum()), "int", "Titoli su cui il buy & hold chiude sopra o alla pari", f"{cl}: differenza <= 0")
    reg("quota_vince", float(vince.mean()), "pct0", "Quota dei titoli su cui vince la regola", f"{cl}: differenza > 0, su 50")
    reg("mediana_diff", float(tab["differenza"].median()), "num2", "Differenza mediana in euro, regola meno buy & hold, netto", f"{cl}: mediana di differenza")
    reg("media_diff", float(tab["differenza"].mean()), "num2", "Differenza media in euro, regola meno buy & hold, netto", f"{cl}: media di differenza")
    reg("mediana_finale_mm", float(tab["finale_mm_netto"].median()), "num2", "Valore finale netto mediano della regola, in euro", f"{cl}: mediana di finale_mm_netto")
    reg("mediana_finale_bh", float(tab["finale_bh_netto"].median()), "num2", "Valore finale netto mediano del buy & hold, in euro", f"{cl}: mediana di finale_bh_netto")
    reg("mediana_rend_mm", float(tab["rend_mm_netto"].median()), "pct0", "Rendimento totale netto mediano della regola", f"{cl}: mediana di rend_mm_netto")
    reg("mediana_rend_bh", float(tab["rend_bh_netto"].median()), "pct0", "Rendimento totale netto mediano del buy & hold", f"{cl}: mediana di rend_bh_netto")
    reg("diff_min", float(tab["differenza"].min()), "num2", "Differenza peggiore per la regola, in euro", f"{cl}: minimo di differenza")
    reg("diff_max", float(tab["differenza"].max()), "num2", "Differenza migliore per la regola, in euro", f"{cl}: massimo di differenza")

    fin_mm, fin_bh = float(tab["finale_mm_netto"].sum()), float(tab["finale_bh_netto"].sum())
    reg("finale_pf_mm", fin_mm, "num2", "Valore finale in euro del portafoglio dei 50 titoli con la regola, netto", f"{cl}: somma di finale_mm_netto")
    reg("finale_pf_bh", fin_bh, "num2", "Valore finale in euro del portafoglio dei 50 titoli con il buy & hold, netto", f"{cl}: somma di finale_bh_netto")
    reg("diff_pf_abs", abs(fin_mm - fin_bh), "num2", "Distanza finale in euro tra i due portafogli, netto", "differenza assoluta tra le due somme")
    reg("rend_pf_mm", fin_mm / (config.CAPITALE * n) - 1, "pct0", "Rendimento totale netto del portafoglio con la regola", "finale_pf_mm / capitale_totale - 1")
    reg("rend_pf_bh", fin_bh / (config.CAPITALE * n) - 1, "pct0", "Rendimento totale netto del portafoglio con il buy & hold", "finale_pf_bh / capitale_totale - 1")
    for nome, col in (("mm", "valore_regola_netto"), ("bh", "valore_bh_netto")):
        v = pf[col].to_numpy()
        reg(f"maxdd_pf_{nome}", float(-(v / np.maximum.accumulate(v) - 1).min()), "pct0",
            f"Perdita massima dal picco del portafoglio dei 50 titoli: {'regola' if nome == 'mm' else 'buy & hold'}",
            "curva_portafoglio.csv: minimo di valore/picco - 1")

    # --- Chi vince e quando -------------------------------------------------------------------------------
    scesi = tab["finale_bh_netto"] < config.CAPITALE
    reg("n_bh_perdita", int(scesi.sum()), "int", "Titoli su cui il buy & hold chiude sotto i 500 euro iniziali", f"{cl}: finale_bh_netto < capitale")
    reg("n_vince_tra_perdita", int((vince & scesi).sum()), "int", "Di questi, quelli su cui la regola chiude sopra il buy & hold", f"{cl}: differenza > 0 tra i titoli in perdita")
    reg("n_bh_guadagno", int((~scesi).sum()), "int", "Titoli su cui il buy & hold chiude sopra i 500 euro iniziali", f"{cl}: finale_bh_netto >= capitale")
    reg("n_vince_tra_guadagno", int((vince & ~scesi).sum()), "int", "Di questi, quelli su cui la regola chiude sopra il buy & hold", f"{cl}: differenza > 0 tra i titoli in guadagno")
    reg("corr_rango", float(tab[["rend_bh_netto", "differenza"]].rank().corr().iloc[0, 1]), "num2",
        "Correlazione di rango (Spearman) tra rendimento netto del buy & hold e differenza regola meno buy & hold",
        f"{cl}: correlazione tra i ranghi di rend_bh_netto e differenza")
    meglio_dd = tab["maxdd_mm"] < tab["maxdd_bh"]
    reg("n_dd_meglio", int(meglio_dd.sum()), "int", "Titoli su cui la regola ha una perdita massima minore del buy & hold", f"{cl}: maxdd_mm < maxdd_bh")
    reg("mediana_maxdd_mm", float(tab["maxdd_mm"].median()), "pct0", "Perdita massima mediana della regola", f"{cl}: mediana di maxdd_mm")
    reg("mediana_maxdd_bh", float(tab["maxdd_bh"].median()), "pct0", "Perdita massima mediana del buy & hold", f"{cl}: mediana di maxdd_bh")
    reg("mediana_ordini", float(tab["n_ordini_mm"].median()), "num1", "Ordini mediani della regola per titolo (acquisti e vendite, compresa la vendita finale)", f"{cl}: mediana di n_ordini_mm")
    reg("mediana_quota_investito", float(tab["quota_investito"].median()), "pct0", "Quota mediana di sedute in cui la regola è investita", f"{cl}: mediana di quota_investito")
    reg("tasse_tot_mm", float(tab["tasse_mm"].sum()), "num2", "Tasse totali pagate in euro dalla regola sui 50 titoli", f"{cl}: somma di tasse_mm")
    reg("tasse_tot_bh", float(tab["tasse_bh"].sum()), "num2", "Tasse totali pagate in euro dal buy & hold sui 50 titoli", f"{cl}: somma di tasse_bh")
    reg("comm_tot_mm", float(tab["commissioni_mm"].sum()), "num2", "Commissioni totali pagate in euro dalla regola sui 50 titoli", f"{cl}: somma di commissioni_mm")
    reg("comm_tot_bh", float(tab["commissioni_bh"].sum()), "num2", "Commissioni totali pagate in euro dal buy & hold sui 50 titoli", f"{cl}: somma di commissioni_bh")
    reg("n_lordo_vince", int((tab["finale_mm_lordo"] > tab["finale_bh_lordo"]).sum()), "int",
        "Titoli su cui la regola chiude sopra il buy & hold anche senza costi né tasse", f"{cl}: finale_mm_lordo > finale_bh_lordo")
    vince_c = tab["differenza_chiusura"] > 0
    reg("n_vince_chiusura", int(vince_c.sum()), "int", "Controllo: titoli su cui vince la regola con ordini alla chiusura", f"{cl}: differenza_chiusura > 0")
    reg("mediana_diff_chiusura", float(tab["differenza_chiusura"].median()), "num2", "Controllo: differenza mediana con ordini alla chiusura, in euro", f"{cl}: mediana di differenza_chiusura")

    # --- Classifica: testa e coda -------------------------------------------------------------------------
    for k in range(1, config.N_CLASSIFICA + 1):
        for pref, r in (("mig", tab.iloc[k - 1]), ("peg", tab.iloc[-k])):
            src = f"{cl}, {'posizione ' + str(int(r['posizione']))}"
            reg(f"{pref}{k}_ticker", r["ticker"], "testo", "Simbolo del titolo", src)
            reg(f"{pref}{k}_nome", r["nome"], "testo", "Nome del titolo", src)
            reg(f"{pref}{k}_mm", float(r["finale_mm_netto"]), "num2", "Valore finale netto con la regola, in euro", src)
            reg(f"{pref}{k}_bh", float(r["finale_bh_netto"]), "num2", "Valore finale netto con il buy & hold, in euro", src)
            reg(f"{pref}{k}_diff", float(r["differenza"]), "num2", "Differenza regola meno buy & hold, in euro", src)
            reg(f"{pref}{k}_rend_bh", float(r["rend_bh_netto"]), "pct0", "Rendimento totale netto del buy & hold sul titolo", src)

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    print(f"Periodo {min(date_inizio).date()} -> {max(date_fine).date()}, {n} titoli")
    print(f"la regola vince su {int(vince.sum())} titoli su {n}; differenza mediana {tab['differenza'].median():.2f} euro")
    print(f"portafoglio: regola {fin_mm:.2f}  buy&hold {fin_bh:.2f}")


if __name__ == "__main__":
    main()
