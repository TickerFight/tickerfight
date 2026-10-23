"""Passo 2 - Sharpe, Sortino, Calmar: otto regole, tre metriche, quattro prove.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json              ogni numero dell'articolo, con descrizione e origine di calcolo
  strategie_campione.csv     per ogni regola, sull'intero periodo: rendimento, rischio, metriche e posti in classifica
  blocchi.csv                metriche e posti di ogni regola in ogni blocco di dieci anni
  correlazioni_blocchi.csv   per ogni blocco, i tau di Kendall tra le tre metriche; per ogni coppia di blocchi, lo Spearman di ciascuna metrica
  bootstrap_vincitori.csv    per ogni metrica, la quota di serie ricampionate in cui vince la stessa regola dell'intero periodo
  scimmie.csv                le tre metriche di ogni scimmia (regola casuale con lo stesso tempo investito e gli stessi cambi del filtro a 200 giorni)
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
METRICHE = ("sharpe", "sortino", "calmar")
NOME_METRICA = {"sharpe": "Sharpe", "sortino": "Sortino", "calmar": "Calmar"}


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def tutte(R: np.ndarray, anni: float) -> dict[str, np.ndarray]:
    return {"sharpe": fx.sharpe(R, config.SEDUTE_ANNO, config.TASSO_SENZA_RISCHIO),
            "sortino": fx.sortino(R, config.SEDUTE_ANNO, config.OBIETTIVO_SORTINO),
            "calmar": fx.calmar(R, anni)}


def media_nan(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.nanmean(x)) if np.isfinite(x).any() else float("nan")


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    S0 = config.INIZIO_TEST_SEDUTE
    ids = list(config.STRATEGIE)
    K = len(ids)
    rng = np.random.default_rng(config.SEME)

    # --- Posizioni e rendimenti netti di tutte le regole (segnale ritardato di un giorno) ----------------------------------
    pos = {i: fx.posizione_regola(close, config.STRATEGIE[i][1]) for i in ids}
    pos_meta = fx.posizione_regola(close, config.META)
    R_all = {i: fx.rendimenti_netti(close, pos[i], config.COSTO_CAMBIO) for i in ids}
    R = np.vstack([R_all[i].to_numpy()[S0:] for i in ids])
    R_meta = fx.rendimenti_netti(close, pos_meta, config.COSTO_CAMBIO).to_numpy()[S0:]
    T = R.shape[1]
    anni = (date[-1] - date[S0 - 1]).days / 365.25
    if T < 2 * config.SEDUTE_BLOCCO:
        raise SystemExit("Troppo pochi dati per i blocchi.")

    # --- Intero periodo ---------------------------------------------------------------------------------------------------
    M = tutte(R, anni)
    cg, mdd = fx.cagr(R, anni), fx.perdita_massima(R)
    vol = R.std(axis=1, ddof=1) * np.sqrt(config.SEDUTE_ANNO)
    quota = np.array([pos[i].to_numpy()[S0:].mean() for i in ids])
    cambi = np.array([pos[i].diff().abs().fillna(0).to_numpy()[S0:].sum() for i in ids])
    P = {k: fx.posti(M[k]) for k in METRICHE}
    win = {k: fx.vincitore(M[k]) for k in METRICHE}
    Mm = tutte(R_meta[None, :], anni)

    tab = pd.DataFrame({"id": ids, "nome": [config.STRATEGIE[i][0] for i in ids], "cagr": cg, "volatilita": vol, "perdita_massima": mdd,
                        "quota_investito": quota, "cambi": cambi,
                        **{k: M[k] for k in METRICHE}, **{f"posto_{k}": P[k] for k in METRICHE}})
    tab.to_csv(config.RISULTATI / "strategie_campione.csv", index=False, float_format="%.6f")

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_inizio", str(date[S0].date()), "data_lunga", "Prima seduta in cui si misurano tutte le regole", "dati/ e config.py")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("anni_campione", anni, "num1", "Anni dell'intero periodo misurato", "dati/")
    reg("w_breve", config.STRATEGIE["sma50"][1][1], "annonum", "Giorni della media mobile più corta tra le regole sopra la media", "config.py, STRATEGIE")
    reg("w_media", config.STRATEGIE["sma100"][1][1], "annonum", "Giorni della media mobile intermedia tra le regole sopra la media", "config.py, STRATEGIE")
    reg("w_lunga", config.STRATEGIE["sma200"][1][1], "annonum", "Giorni della media mobile più lunga (usata anche dal filtro a lungo termine e dall'incrocio)", "config.py, STRATEGIE")
    reg("mom_mesi", config.STRATEGIE["mom"][1][1] / 21, "annonum", "Mesi di storia usati dal momentum (252 sedute, 21 sedute per mese)", "config.py, STRATEGIE")
    reg("n_regole", K, "int", "Regole confrontate nelle classifiche", "config.py, STRATEGIE")
    reg("costo", config.COSTO_CAMBIO, "pct1", "Costo per ogni cambio di posizione, quota del valore", "config.py, COSTO_CAMBIO")
    reg("tasso_zero", config.TASSO_SENZA_RISCHIO, "pct0", "Tasso senza rischio usato nello Sharpe (la cassa non rende)", "config.py, TASSO_SENZA_RISCHIO")
    reg("sedute_anno", config.SEDUTE_ANNO, "int", "Sedute di borsa per anno, usate per annualizzare Sharpe e Sortino", "config.py, SEDUTE_ANNO")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Serie ricampionate nel bootstrap", "config.py")
    reg("lung_blocco_boot", config.LUNGHEZZA_BLOCCO_BOOT, "int", "Lunghezza in sedute dei blocchi del bootstrap", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie (regole casuali) estratte", "config.py")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("soglia_scimmie", config.SOGLIA_SCIMMIE, "pct0", "Quota di scimmie che il filtro deve battere", "config.py")
    reg("tolleranza_uguali", config.TOLLERANZA_UGUALI, "num2", "Differenza sotto la quale due Sharpe o due Sortino sono considerati uguali", "config.py")
    reg("diff_rel_calmar", config.DIFFERENZA_RELATIVA_CALMAR, "pct0", "Differenza relativa minima con cui il Calmar distingue due regole", "config.py")
    for k, i in enumerate(ids):
        reg(f"cagr_{i}", cg[k], "pct1", f"Rendimento annuo composto netto: {config.STRATEGIE[i][0]}", "strategie_campione.csv")
        reg(f"vol_{i}", vol[k], "pct1", f"Volatilità annua: {config.STRATEGIE[i][0]}", "strategie_campione.csv")
        reg(f"mdd_{i}", -mdd[k], "pct0", f"Perdita massima dal massimo (in valore assoluto): {config.STRATEGIE[i][0]}", "strategie_campione.csv")
        reg(f"quota_{i}", quota[k], "pct0", f"Quota delle sedute investite: {config.STRATEGIE[i][0]}", "strategie_campione.csv")
        reg(f"cambi_{i}", cambi[k], "int", f"Numero di cambi di posizione: {config.STRATEGIE[i][0]}", "strategie_campione.csv")
        for km in METRICHE:
            reg(f"{km}_{i}", M[km][k], "num3" if km == "calmar" else "num2", f"{NOME_METRICA[km]} sull'intero periodo: {config.STRATEGIE[i][0]}", "strategie_campione.csv")
            reg(f"posto_{km}_{i}", P[km][k], "int", f"Posto per {NOME_METRICA[km]} sull'intero periodo: {config.STRATEGIE[i][0]}", "strategie_campione.csv")

    # --- Ipotesi 1: i vincitori ----------------------------------------------------------------------------------------------
    for km in METRICHE:
        reg(f"vinc_{km}", config.STRATEGIE[ids[win[km]]][0], "testo", f"Regola prima in classifica per {NOME_METRICA[km]}, intero periodo", "strategie_campione.csv")
    reg("n_vincitori_diversi", len(set(win.values())), "int", "Regole diverse che vincono per almeno una delle tre metriche, intero periodo", "strategie_campione.csv")
    spread = np.max([P[k] for k in METRICHE], axis=0) - np.min([P[k] for k in METRICHE], axis=0)
    k_sp = int(np.argmax(spread))
    reg("regola_spread", config.STRATEGIE[ids[k_sp]][0], "testo", "Regola con la maggior distanza tra il posto migliore e il peggiore nelle tre classifiche", "strategie_campione.csv")
    reg("spread_posti", float(spread[k_sp]), "int", "Distanza in posti tra il posto migliore e il peggiore di quella regola", "strategie_campione.csv")
    reg("posto_max_spread", float(np.min([P[k][k_sp] for k in METRICHE])), "int", "Il posto migliore di quella regola nelle tre classifiche", "strategie_campione.csv")
    reg("posto_min_spread", float(np.max([P[k][k_sp] for k in METRICHE])), "int", "Il posto peggiore di quella regola nelle tre classifiche", "strategie_campione.csv")
    tau_sr_so, tau_sr_ca, tau_so_ca = (fx.kendall(M["sharpe"], M["sortino"]), fx.kendall(M["sharpe"], M["calmar"]), fx.kendall(M["sortino"], M["calmar"]))
    reg("tau_campione_sh_so", tau_sr_so, "num2", "Tau di Kendall tra le classifiche Sharpe e Sortino, intero periodo", "strategie_campione.csv")
    reg("tau_campione_sh_ca", tau_sr_ca, "num2", "Tau di Kendall tra le classifiche Sharpe e Calmar, intero periodo", "strategie_campione.csv")
    reg("tau_campione_so_ca", tau_so_ca, "num2", "Tau di Kendall tra le classifiche Sortino e Calmar, intero periodo", "strategie_campione.csv")

    # --- Blocchi di dieci anni ---------------------------------------------------------------------------------------------------
    bl = fx.blocchi(T, config.SEDUTE_BLOCCO)
    nb = len(bl)
    Rb = {}
    righe_b, MB, PB = [], {k: np.zeros((nb, K)) for k in METRICHE}, {k: np.zeros((nb, K)) for k in METRICHE}
    n_non_definiti = 0
    for b, (a, e) in enumerate(bl):
        anni_b = (date[S0 + e - 1] - date[S0 + a - 1]).days / 365.25
        mb = tutte(R[:, a:e], anni_b)
        for km in METRICHE:
            MB[km][b] = mb[km]
            PB[km][b] = fx.posti(mb[km])
            n_non_definiti += int(np.isnan(mb[km]).sum())
        for k, i in enumerate(ids):
            righe_b.append({"blocco": b + 1, "inizio": date[S0 + a].date(), "fine": date[S0 + e - 1].date(), "id": i,
                            **{km: mb[km][k] for km in METRICHE}, **{f"posto_{km}": PB[km][b][k] for km in METRICHE}})
    pd.DataFrame(righe_b).to_csv(config.RISULTATI / "blocchi.csv", index=False, float_format="%.6f")
    reg("n_blocchi", nb, "int", "Blocchi di dieci anni non sovrapposti dentro il periodo", "blocchi.csv")
    reg("anni_blocco", config.SEDUTE_BLOCCO / config.SEDUTE_ANNO, "annonum", "Anni di ogni blocco", "config.py, SEDUTE_BLOCCO")
    reg("n_non_definiti", n_non_definiti, "int", "Valori di metrica non definiti nei blocchi (rischio zero o nessuna perdita)", "blocchi.csv")
    vinc_uguali = sum(1 for b in range(nb) if len({fx.vincitore(MB[km][b]) for km in METRICHE}) == 1)
    reg("n_blocchi_stesso_vincitore", vinc_uguali, "int", "Blocchi in cui le tre metriche indicano la stessa regola come prima", "blocchi.csv")
    n_vinc_blocchi = {km: len({fx.vincitore(MB[km][b]) for b in range(nb)}) for km in METRICHE}
    for km in METRICHE:
        reg(f"n_vinc_blocchi_{km}", n_vinc_blocchi[km], "int", f"Regole diverse che vincono almeno un blocco per {NOME_METRICA[km]}", "blocchi.csv")
    # fascia di classifica: il buy & hold è mai primo?
    ib = ids.index(config.ID_BH)
    isf = ids.index(config.ID_FILTRO)
    for km in METRICHE:
        reg(f"n_filtro_batte_bh_{km}", int((MB[km][:, isf] > MB[km][:, ib]).sum()), "int",
            f"Blocchi in cui il filtro a 200 giorni ha un {NOME_METRICA[km]} più alto del buy & hold", "blocchi.csv")
    for km in METRICHE:
        reg(f"n_bh_primo_{km}", int((PB[km][:, ib] == 1).sum()), "int", f"Blocchi in cui il buy & hold è primo per {NOME_METRICA[km]}", "blocchi.csv")

    # --- Ipotesi 2: chi si discosta di più -----------------------------------------------------------------------------------------
    righe_c = []
    taus = {"sh_so": [], "sh_ca": [], "so_ca": []}
    for b in range(nb):
        t = {"sh_so": fx.kendall(MB["sharpe"][b], MB["sortino"][b]), "sh_ca": fx.kendall(MB["sharpe"][b], MB["calmar"][b]),
             "so_ca": fx.kendall(MB["sortino"][b], MB["calmar"][b])}
        for kk, v in t.items():
            taus[kk].append(v)
        righe_c.append({"tipo": "tau_blocco", "blocco": b + 1, "coppia": "", **{f"tau_{kk}": v for kk, v in t.items()}})
    tm = {kk: media_nan(v) for kk, v in taus.items()}
    media_tau = {"sharpe": (tm["sh_so"] + tm["sh_ca"]) / 2, "sortino": (tm["sh_so"] + tm["so_ca"]) / 2, "calmar": (tm["sh_ca"] + tm["so_ca"]) / 2}
    for kk in tm:
        reg(f"tau_blocchi_{kk}", tm[kk], "num2", f"Tau di Kendall medio sui blocchi: coppia {kk.replace('_', '/')}", "correlazioni_blocchi.csv")
    for km in METRICHE:
        reg(f"tau_medio_{km}", media_tau[km], "num2", f"Tau medio di {NOME_METRICA[km]} con le altre due metriche, sui blocchi", "correlazioni_blocchi.csv")
    reg("metrica_piu_diversa", NOME_METRICA[min(media_tau, key=media_tau.get)], "testo", "Metrica con il tau medio più basso", "correlazioni_blocchi.csv")
    reg("tau_min_blocchi", float(np.nanmin(np.concatenate([np.asarray(v, dtype=float) for v in taus.values()]))), "num2", "Il tau più basso tra tutte le coppie di metriche e tutti i blocchi", "correlazioni_blocchi.csv")

    # --- Ipotesi 3: persistenza tra decenni consecutivi ----------------------------------------------------------------------
    pers = {km: [fx.spearman(MB[km][b], MB[km][b + 1]) for b in range(nb - 1)] for km in METRICHE}
    for km in METRICHE:
        for b, v in enumerate(pers[km]):
            righe_c.append({"tipo": "spearman_consecutivi", "blocco": b + 1, "coppia": km, "tau_sh_so": v, "tau_sh_ca": np.nan, "tau_so_ca": np.nan})
    pd.DataFrame(righe_c).to_csv(config.RISULTATI / "correlazioni_blocchi.csv", index=False, float_format="%.6f")
    pm = {km: media_nan(pers[km]) for km in METRICHE}
    reg("n_coppie_blocchi", nb - 1, "int", "Coppie di blocchi consecutivi", "correlazioni_blocchi.csv")
    for km in METRICHE:
        reg(f"pers_{km}", pm[km], "num2", f"Correlazione di rango (Spearman) media tra un decennio e il successivo: {NOME_METRICA[km]}", "correlazioni_blocchi.csv")
        reg(f"pers_neg_{km}", int(np.nansum(np.asarray(pers[km]) < 0)), "int", f"Coppie di decenni con correlazione di rango negativa: {NOME_METRICA[km]}", "correlazioni_blocchi.csv")
    for km in ("sharpe", "sortino"):
        reg(f"n_pers_calmar_sopra_{km}", int(sum(1 for c, o in zip(pers["calmar"], pers[km]) if c > o)), "int",
            f"Coppie di decenni in cui il Calmar è più persistente di {NOME_METRICA[km]}", "correlazioni_blocchi.csv")
    reg("metrica_meno_persistente", NOME_METRICA[min(pm, key=pm.get)], "testo", "Metrica con la persistenza media più bassa", "correlazioni_blocchi.csv")

    # --- Ipotesi 4: bootstrap a blocchi circolari -----------------------------------------------------------------------------------------
    idx = fx.indici_blocchi_circolari(T, config.LUNGHEZZA_BLOCCO_BOOT, config.N_BOOTSTRAP, rng)
    wb = {km: np.zeros(config.N_BOOTSTRAP, dtype=int) for km in METRICHE}
    ic_dati = {km: np.zeros((config.N_BOOTSTRAP, K)) for km in METRICHE}
    for r in range(config.N_BOOTSTRAP):
        mr = tutte(R[:, idx[r]], anni)
        for km in METRICHE:
            wb[km][r] = fx.vincitore(mr[km])
            ic_dati[km][r] = mr[km]
    quote = {km: float((wb[km] == win[km]).mean()) for km in METRICHE}
    tre_uguali = float(np.mean([len({wb[km][r] for km in METRICHE}) == 1 for r in range(config.N_BOOTSTRAP)]))
    pd.DataFrame({"metrica": [NOME_METRICA[k] for k in METRICHE], "vincitore_campione": [ids[win[k]] for k in METRICHE],
                  "quota_stesso_vincitore": [quote[k] for k in METRICHE],
                  "regole_diverse_vincenti": [len(set(wb[k])) for k in METRICHE]}).to_csv(config.RISULTATI / "bootstrap_vincitori.csv", index=False, float_format="%.6f")
    for km in METRICHE:
        reg(f"boot_quota_{km}", quote[km], "pct0", f"Quota di serie ricampionate in cui vince la stessa regola dell'intero periodo: {NOME_METRICA[km]}", "bootstrap_vincitori.csv")
        reg(f"boot_n_vincenti_{km}", len(set(wb[km])), "int", f"Regole diverse che vincono almeno una serie ricampionata: {NOME_METRICA[km]}", "bootstrap_vincitori.csv")
    reg("boot_tre_uguali", tre_uguali, "pct0", "Quota di serie ricampionate in cui le tre metriche indicano la stessa regola come prima", "bootstrap_vincitori.csv")
    reg("metrica_piu_fragile", NOME_METRICA[min(quote, key=quote.get)], "testo", "Metrica con la quota più bassa di vincitore confermato", "bootstrap_vincitori.csv")
    a_ic = (1 - config.LIVELLO_CONFIDENZA) / 2
    iq = ids.index(config.ID_FILTRO)
    for km in METRICHE:
        for nome, k in (("bh", ib), ("filtro", iq)):
            lo, hi = np.quantile(ic_dati[km][:, k], [a_ic, 1 - a_ic])
            f = "num3" if km == "calmar" else "num2"
            reg(f"ic_lo_{km}_{nome}", float(lo), f, f"Estremo inferiore dell'intervallo bootstrap di {NOME_METRICA[km]}: {config.STRATEGIE[config.ID_BH if nome == 'bh' else config.ID_FILTRO][0]}", "bootstrap a blocchi")
            reg(f"ic_hi_{km}_{nome}", float(hi), f, f"Estremo superiore dell'intervallo bootstrap di {NOME_METRICA[km]}: {config.STRATEGIE[config.ID_BH if nome == 'bh' else config.ID_FILTRO][0]}", "bootstrap a blocchi")
        v = M[km][iq]
        lo, hi = np.quantile(ic_dati[km][:, iq], [a_ic, 1 - a_ic])
        reg(f"ic_ampiezza_rel_{km}", float((hi - lo) / abs(v)), "pct0", f"Ampiezza dell'intervallo bootstrap rispetto al valore, {NOME_METRICA[km]} del filtro a 200 giorni", "bootstrap a blocchi")

    # --- Ipotesi 5: buy & hold dimezzato ------------------------------------------------------------------------------------------------------
    d_sh = abs(float(Mm["sharpe"][0]) - float(M["sharpe"][ib]))
    d_so = abs(float(Mm["sortino"][0]) - float(M["sortino"][ib]))
    d_ca_rel = abs(float(Mm["calmar"][0]) - float(M["calmar"][ib])) / abs(float(M["calmar"][ib]))
    reg("meta_sharpe", float(Mm["sharpe"][0]), "num2", "Sharpe del buy & hold dimezzato", "02_backtest_e_test.py con funzioni.py")
    reg("meta_sortino", float(Mm["sortino"][0]), "num2", "Sortino del buy & hold dimezzato", "02_backtest_e_test.py con funzioni.py")
    reg("meta_calmar", float(Mm["calmar"][0]), "num3", "Calmar del buy & hold dimezzato", "02_backtest_e_test.py con funzioni.py")
    reg("meta_cagr", float(fx.cagr(R_meta, anni)), "pct1", "Rendimento annuo del buy & hold dimezzato", "02_backtest_e_test.py con funzioni.py")
    reg("meta_mdd", float(-fx.perdita_massima(R_meta)), "pct0", "Perdita massima del buy & hold dimezzato (in valore assoluto)", "02_backtest_e_test.py con funzioni.py")
    reg("diff_meta_sharpe", d_sh, "num3", "Differenza assoluta di Sharpe tra buy & hold e buy & hold dimezzato", "02_backtest_e_test.py")
    reg("diff_meta_sortino", d_so, "num3", "Differenza assoluta di Sortino tra buy & hold e buy & hold dimezzato", "02_backtest_e_test.py")
    reg("diff_meta_calmar_rel", d_ca_rel, "pct0", "Differenza relativa di Calmar tra buy & hold dimezzato e buy & hold", "02_backtest_e_test.py")

    # --- Ipotesi 6: il filtro a 200 giorni contro le scimmie --------------------------------------------------------------------------------------
    val, lun = fx.sequenze(pos[config.ID_FILTRO].to_numpy()[S0:] > 0)
    ret_mercato = close.pct_change().fillna(0.0).to_numpy()[S0:]
    scim = np.empty((config.N_SCIMMIE, T))
    for s in range(config.N_SCIMMIE):
        p = fx.scimmia(val, lun, rng).astype(float)
        cmb = np.abs(np.diff(p, prepend=p[0]))
        scim[s] = ret_mercato * p - config.COSTO_CAMBIO * cmb
    MS = tutte(scim, anni)
    pd.DataFrame({k: MS[k] for k in METRICHE}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.6f")
    perc = {km: float((MS[km] < M[km][iq]).mean()) for km in METRICHE}
    for km in METRICHE:
        reg(f"scim_perc_{km}", perc[km], "pct1", f"Quota di scimmie che fanno peggio del filtro a 200 giorni: {NOME_METRICA[km]}", "scimmie.csv")
        f = "num3" if km == "calmar" else "num2"
        reg(f"scim_mediana_{km}", float(np.median(MS[km])), f, f"Valore mediano di {NOME_METRICA[km]} tra le scimmie", "scimmie.csv")
        reg(f"scim_max_{km}", float(np.max(MS[km])), f, f"Valore massimo di {NOME_METRICA[km]} tra le scimmie", "scimmie.csv")
    reg("scim_cambi", float((np.abs(np.diff(val.astype(int))) > 0).sum()), "int", "Cambi di posizione di ogni scimmia (uguali a quelli del filtro a 200 giorni)", "scimmie.csv")
    reg("scim_quota", float(lun[val].sum() / lun.sum()), "pct0", "Quota di sedute investite di ogni scimmia (uguale a quella del filtro a 200 giorni)", "scimmie.csv")

    # --- Verdetti calcolati (1 = ipotesi confermata) ---------------------------------------------------------------------------------------------------
    h = {1: len(set(win.values())) >= 2,
         2: min(media_tau, key=media_tau.get) == "calmar",
         3: min(pm, key=pm.get) == "calmar",
         4: quote["calmar"] < quote["sharpe"],
         5: d_sh < config.TOLLERANZA_UGUALI and d_so < config.TOLLERANZA_UGUALI and d_ca_rel >= config.DIFFERENZA_RELATIVA_CALMAR,
         6: all(perc[km] >= config.SOGLIA_SCIMMIE for km in METRICHE)}
    for n, ok in h.items():
        reg(f"h{n}_ok", int(ok), "int", f"1 se l'ipotesi {n} è confermata, 0 se smentita", "02_backtest_e_test.py")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {nb} blocchi; {T} sedute")
    print("vincitori:", {k: ids[win[k]] for k in METRICHE})
    print("ipotesi:", {n: int(ok) for n, ok in h.items()})


if __name__ == "__main__":
    main()
