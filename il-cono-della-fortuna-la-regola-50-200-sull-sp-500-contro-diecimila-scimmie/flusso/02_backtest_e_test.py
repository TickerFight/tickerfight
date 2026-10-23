"""Passo 2 - Il cono della fortuna: la regola 50/200 sull'S&P 500 contro migliaia di scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv              prezzo, medie, posizione e valore del portafoglio giorno per giorno (regola e buy & hold)
  operazioni_regola.csv  registro di tutte le operazioni della regola
  cono_fasce.csv         percentili dei percorsi casuali nel tempo, con il valore della regola e il suo percentile
  cono_densita.csv       densità dei percorsi casuali: una riga per data, una colonna per fascia di valore
  percorsi_finali.csv    valore finale e perdita massima di ogni percorso casuale

La scimmia: stessa quota di giorni investiti, stesso numero di acquisti e di vendite e stessa durata di ogni
periodo di permanenza sul mercato della regola; cambia solo dove i periodi cadono nel tempo. Passa dallo stesso motore
di simulazione (commissioni, cambio, tassa e minusvalenze compresi).
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


def reg(chiave, valore, formato, descrizione, origine):
    """Registra un numero con la sua giustificazione (finisce nelle note dell'articolo)."""
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def periodi(w: np.ndarray) -> list[int]:
    """Lunghezze dei periodi consecutivi di True."""
    x = np.r_[False, w, False].astype(int)
    d = np.diff(x)
    return list((np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).tolist())


def scimmia(durate: list[int], lunghezza: int, rng) -> np.ndarray:
    """Segnale casuale: gli stessi periodi (in ordine casuale), con pause di durata casuale (>= 1 tra due periodi)."""
    m = len(durate)
    giorni_fuori = lunghezza - sum(durate)
    liberi = giorni_fuori - (m - 1)
    tagli = np.sort(rng.choice(liberi + m, size=m, replace=False))
    bordi = np.r_[-1, tagli, liberi + m]
    pause = np.diff(bordi) - 1                      # m + 1 pause: la prima e l'ultima possono essere zero
    pause[1:-1] += 1                                # le pause interne sono almeno di un giorno
    ordine = rng.permutation(m)
    w = np.zeros(lunghezza, dtype=bool)
    pos = int(pause[0])
    for k, j in enumerate(ordine):
        w[pos:pos + durate[j]] = True
        pos += durate[j] + int(pause[k + 1])
    return w


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    titolo = s.carica_csv(config.FILE_DATI)
    cambio = s.carica_csv(config.FILE_CAMBIO)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    df = s.prepara(titolo, cambio, config.SMA_VELOCE, config.SMA_LENTA)
    n = len(df)
    fine = df.index[-1]
    i0 = s.indice_data(df, fine - pd.DateOffset(years=config.ANNI_TEST))
    if i0 < config.SMA_LENTA + 1:
        raise SystemExit("Storia insufficiente per calcolare la media lenta prima dell'inizio del test.")
    if df["fx"].iloc[i0 - 1:].isna().any():
        raise SystemExit("Cambio mancante in una seduta nel periodo del test.")
    L = n - i0
    date = df.index[i0:]
    P = config.MODO_PRINCIPALE

    mm = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, P, True)
    bh = s.simula(df, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, P, False)
    pd.DataFrame(mm["operazioni"]).to_csv(config.RISULTATI / "operazioni_regola.csv", index=False, float_format="%.6f")
    f = df.iloc[i0:]
    pd.DataFrame({"data": date, "chiusura_usd": f["Close"].to_numpy(), "sma_veloce": f["sma_v"].to_numpy(),
                  "sma_lenta": f["sma_l"].to_numpy(), "regola_in_posizione": mm["in_posizione"],
                  "valore_regola": mm["equity"], "valore_bh": bh["equity"]}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    # --- La scimmia ----------------------------------------------------------------------------------------
    seg = df["segnale"].to_numpy(bool)
    w = seg[i0 - 1:n - 1]                       # i segnali che decidono gli ordini delle sedute i0 ... n-1
    durate = periodi(w)
    if len(durate) < 3:
        raise SystemExit("La regola ha troppi pochi periodi investiti per un confronto con il caso.")
    rng = np.random.default_rng(config.SEME)
    df2 = df.copy()
    base = seg.copy()
    # la bar del giorno bh minimo: serve il valore dei percorsi casuali proprio quel giorno
    dd_bh = bh["equity"] / np.maximum.accumulate(bh["equity"]) - 1
    i_min_bh = int(np.argmin(dd_bh))
    campione = sorted(set(range(0, L, config.PASSO_CAMPIONE)) | {L - 1, i_min_bh})
    eq = np.empty((config.N_PERCORSI, len(campione)), dtype=np.float32)
    finali = np.empty(config.N_PERCORSI)
    dd = np.empty(config.N_PERCORSI)
    for k in range(config.N_PERCORSI):
        sig = base.copy()
        sig[i0 - 1:n - 1] = scimmia(durate, len(w), rng)
        df2["segnale"] = sig
        r = s.simula(df2, i0, config.CAPITALE, config.COMMISSIONE, config.ALIQUOTA, P, True)
        if r["n_acquisti"] != mm["n_acquisti"] or r["n_vendite"] != mm["n_vendite"] or abs(r["quota_giorni_investito"] - mm["quota_giorni_investito"]) > 1e-9:
            raise SystemExit("La scimmia non ha la stessa dieta della regola: controllare scimmia().")
        eq[k] = r["equity"][campione]
        finali[k] = r["valore_finale_eur"]
        dd[k] = -r["perdita_massima"]
    pd.DataFrame({"finale": finali, "perdita_massima": dd}).to_csv(config.RISULTATI / "percorsi_finali.csv", index=False, float_format="%.6f")

    date_c = date[campione]
    rule_c = mm["equity"][campione]
    bh_c = bh["equity"][campione]
    liv = [5, 25, 50, 75, 95]
    pc = np.percentile(eq, liv, axis=0)
    perc_regola = (eq < rule_c[None, :]).mean(axis=0)
    fasce = pd.DataFrame({"data": date_c, **{f"p{q}": pc[i] for i, q in enumerate(liv)},
                          "regola": rule_c, "buy_hold": bh_c, "percentile_regola": perc_regola})
    fasce.to_csv(config.RISULTATI / "cono_fasce.csv", index=False, float_format="%.4f")
    lo, hi = float(eq.min()), float(eq.max())
    bordi = np.linspace(lo, hi, config.BIN_VALORE + 1)
    dens = np.stack([np.histogram(eq[:, j], bins=bordi)[0] for j in range(eq.shape[1])]) / config.N_PERCORSI
    centri = (bordi[:-1] + bordi[1:]) / 2
    dd_df = pd.DataFrame(dens, columns=[f"{c:.2f}" for c in centri])
    dd_df.insert(0, "data", date_c)
    dd_df.to_csv(config.RISULTATI / "cono_densita.csv", index=False, float_format="%.6f")

    # --- Numeri dell'articolo ---------------------------------------------------------------------------------
    origine_dati = f"dati/ ({meta['fonte']}, {config.TICKER} e {config.TICKER_CAMBIO}, scaricati il {meta['scaricato_il_utc'][:10]})"
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione", config.COMMISSIONE, "num2", "Commissione fissa per ogni ordine, in euro", "config.py, COMMISSIONE")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("sma_veloce", config.SMA_VELOCE, "annonum", "Giorni della media veloce", "config.py, SMA_VELOCE")
    reg("sma_lenta", config.SMA_LENTA, "annonum", "Giorni della media lenta", "config.py, SMA_LENTA")
    reg("anni_test", config.ANNI_TEST, "annonum", "Anni del test", "config.py, ANNI_TEST")
    reg("n_percorsi", config.N_PERCORSI, "int", "Percorsi casuali simulati", "config.py, N_PERCORSI")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("data_inizio", str(date[0].date()), "data_lunga", "Prima seduta del test", origine_dati)
    reg("data_fine", str(fine.date()), "data_lunga", "Ultima seduta del test (ultimo dato scaricato)", origine_dati)
    reg("n_sedute", L, "int", "Sedute di borsa nel periodo del test", origine_dati)
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("finale_mm", mm["valore_finale_eur"], "num2", "Valore finale netto della regola, in euro (si vende tutto alla fine)", f"{SORGENTE}, simula()")
    reg("finale_bh", bh["valore_finale_eur"], "num2", "Valore finale netto del buy & hold, in euro", f"{SORGENTE}, simula()")
    reg("rend_mm", mm["rendimento_totale"], "pct0", "Rendimento totale netto della regola", f"{SORGENTE}, simula()")
    reg("rend_bh", bh["rendimento_totale"], "pct0", "Rendimento totale netto del buy & hold", f"{SORGENTE}, simula()")
    reg("cagr_mm", mm["cagr"], "pct1", "Rendimento annuo composto netto della regola", f"{SORGENTE}, simula()")
    reg("cagr_bh", bh["cagr"], "pct1", "Rendimento annuo composto netto del buy & hold", f"{SORGENTE}, simula()")
    reg("maxdd_mm", -mm["perdita_massima"], "pct0", "Perdita massima dal picco della regola", f"{SORGENTE}, simula()")
    reg("maxdd_bh", -bh["perdita_massima"], "pct0", "Perdita massima dal picco del buy & hold", f"{SORGENTE}, simula()")
    reg("n_acquisti", mm["n_acquisti"], "int", "Acquisti della regola nel periodo", f"{SORGENTE}, simula()")
    reg("n_ordini", mm["n_acquisti"] + mm["n_vendite"], "int", "Ordini della regola (acquisti e vendite, compresa l'eventuale vendita finale)", f"{SORGENTE}, simula()")
    reg("quota_investito", mm["quota_giorni_investito"], "pct0", "Quota di sedute con la regola investita", f"{SORGENTE}, simula()")
    reg("durata_media", float(np.mean(durate)), "int", "Durata media, in sedute, di un periodo investito della regola", "operazioni della regola")
    reg("durata_max", int(max(durate)), "int", "Durata, in sedute, del periodo investito più lungo della regola", "operazioni della regola")
    reg("tasse_mm", mm["tasse_eur"], "num2", "Tasse pagate dalla regola, in euro", f"{SORGENTE}, simula()")
    reg("comm_mm", mm["commissioni_eur"], "num2", "Commissioni pagate dalla regola, in euro", f"{SORGENTE}, simula()")

    cas_med = float(np.median(finali))
    reg("cas_mediana", cas_med, "num2", "Valore finale mediano dei percorsi casuali, in euro", "percorsi_finali.csv")
    reg("cas_p5", float(np.percentile(finali, 5)), "num2", "5° percentile del valore finale dei percorsi casuali, in euro", "percorsi_finali.csv")
    reg("cas_p95", float(np.percentile(finali, 95)), "num2", "95° percentile del valore finale dei percorsi casuali, in euro", "percorsi_finali.csv")
    reg("cas_min", float(finali.min()), "num2", "Valore finale peggiore tra i percorsi casuali, in euro", "percorsi_finali.csv")
    reg("cas_max", float(finali.max()), "num2", "Valore finale migliore tra i percorsi casuali, in euro", "percorsi_finali.csv")
    reg("perc_mm", float((finali < mm["valore_finale_eur"]).mean()), "pct0", "Quota di percorsi casuali che chiudono sotto la regola", "percorsi_finali.csv")
    reg("p_mm", (int((finali >= mm["valore_finale_eur"]).sum()) + 1) / (config.N_PERCORSI + 1), "pval",
        "Quota di percorsi casuali che fanno almeno quanto la regola (p-value a una coda)", "percorsi_finali.csv")
    reg("quota_cas_sopra_mm", float((finali >= mm["valore_finale_eur"]).mean()), "pct0", "Quota di percorsi casuali che fanno almeno quanto la regola", "percorsi_finali.csv")
    reg("quota_cas_sopra_bh", float((finali >= bh["valore_finale_eur"]).mean()), "pct1", "Quota di percorsi casuali che fanno almeno quanto il buy & hold", "percorsi_finali.csv")
    reg("bh_sopra_mediana", bh["valore_finale_eur"] - cas_med, "num2", "Buy & hold meno valore mediano dei percorsi casuali, in euro", "finale_bh - cas_mediana")
    reg("mm_sopra_mediana", mm["valore_finale_eur"] - cas_med, "num2", "Regola meno valore mediano dei percorsi casuali, in euro", "finale_mm - cas_mediana")
    reg("cas_dd_mediana", float(np.median(dd)), "pct0", "Perdita massima mediana dei percorsi casuali", "percorsi_finali.csv")
    reg("cas_dd_p5", float(np.percentile(dd, 5)), "pct0", "5° percentile della perdita massima dei percorsi casuali (i meno colpiti)", "percorsi_finali.csv")
    reg("cas_dd_p95", float(np.percentile(dd, 95)), "pct0", "95° percentile della perdita massima dei percorsi casuali (i più colpiti)", "percorsi_finali.csv")
    # Molti percorsi hanno la stessa perdita massima della regola (il crollo del 2020 li trova tutti investiti): si
    # arrotonda a sei decimali per non assegnare a caso gli «uguali» a causa del rumore dell'aritmetica.
    ddr, soglia_dd = np.round(dd, 6), round(float(-mm["perdita_massima"]), 6)
    reg("dd_perc_mm", float((ddr > soglia_dd).mean()), "pct0", "Quota di percorsi casuali con una perdita massima più grande di quella della regola", "percorsi_finali.csv")
    reg("dd_uguale_mm", float((ddr == soglia_dd).mean()), "pct0", "Quota di percorsi casuali con la stessa perdita massima della regola (arrotondata a sei decimali)", "percorsi_finali.csv")
    reg("dd_minore_mm", float((ddr < soglia_dd).mean()), "pct0", "Quota di percorsi casuali con una perdita massima più piccola di quella della regola", "percorsi_finali.csv")
    reg("p_dd", (int((ddr <= soglia_dd).sum()) + 1) / (config.N_PERCORSI + 1), "pval",
        "Quota di percorsi casuali con una perdita massima minore o uguale a quella della regola (p-value a una coda)", "percorsi_finali.csv")

    # La regola dentro il cono, nel tempo
    j_min, j_max = int(np.argmin(perc_regola)), int(np.argmax(perc_regola))
    j_bh = campione.index(i_min_bh)
    reg("perc_min", float(perc_regola[j_min]), "pct0", "Punto più basso del percentile della regola tra i percorsi casuali", "cono_fasce.csv")
    reg("data_perc_min", str(date_c[j_min].date()), "data_lunga", "Data del punto più basso del percentile della regola", "cono_fasce.csv")
    reg("perc_max", float(perc_regola[j_max]), "pct0", "Punto più alto del percentile della regola tra i percorsi casuali", "cono_fasce.csv")
    reg("data_perc_max", str(date_c[j_max].date()), "data_lunga", "Data del punto più alto del percentile della regola", "cono_fasce.csv")
    reg("perc_medio", float(perc_regola.mean()), "pct0", "Percentile medio della regola nel tempo (media sulle date campionate)", "cono_fasce.csv")
    reg("quota_tempo_sopra_mediana", float((rule_c > pc[2]).mean()), "pct0", "Quota di date in cui la regola sta sopra la mediana dei percorsi casuali", "cono_fasce.csv")
    reg("data_minimo_bh", str(date_c[j_bh].date()), "data_lunga", "Giorno del punto più basso del buy & hold (massima perdita dal picco)", "curve.csv")
    reg("perc_al_minimo_bh", float(perc_regola[j_bh]), "pct0", "Percentile della regola tra i percorsi casuali nel giorno del punto più basso del buy & hold", "cono_fasce.csv")
    reg("mm_al_minimo_bh", float(rule_c[j_bh]), "num2", "Valore della regola nel giorno del punto più basso del buy & hold, in euro", "cono_fasce.csv")
    reg("mediana_al_minimo_bh", float(pc[2][j_bh]), "num2", "Valore mediano dei percorsi casuali nello stesso giorno, in euro", "cono_fasce.csv")
    reg("bh_al_minimo_bh", float(bh_c[j_bh]), "num2", "Valore del buy & hold nello stesso giorno, in euro", "cono_fasce.csv")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri in risultati/metriche.json")
    print(f"Periodo {date[0].date()} -> {fine.date()}, {L} sedute; regola: {mm['n_acquisti']} acquisti, investita {mm['quota_giorni_investito']:.0%}")
    print(f"regola {mm['valore_finale_eur']:.2f}  bh {bh['valore_finale_eur']:.2f}  casuali mediana {cas_med:.2f} [{np.percentile(finali,5):.0f}, {np.percentile(finali,95):.0f}]")
    print(f"percentile regola {np.mean(finali < mm['valore_finale_eur']):.0%}; p={RIS['p_mm']['valore']:.4f}; dd regola {-mm['perdita_massima']:.0%}, casuali mediana {np.median(dd):.0%}")
    print(f"minimo bh il {date_c[j_bh].date()}: percentile regola {perc_regola[j_bh]:.0%}")


if __name__ == "__main__":
    main()
