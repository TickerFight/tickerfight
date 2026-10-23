"""Passo 2 - Il costo nascosto: otto regole, sei livelli di costo, ribilanciamento e scimmie.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json              ogni numero dell'articolo, con descrizione e origine di calcolo
  costi_regole.csv           per ogni regola e livello di costo: rendimento annuo, Sharpe, cambi all'anno, posto per Sharpe
  ribilanciamento.csv        per ogni frequenza di ribilanciamento e livello di costo: rendimento annuo e Sharpe del 50/50
  scimmie.csv                per ogni probabilità di cambio e livello di costo: rendimento annuo mediano e quota di scimmie in perdita
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
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    S0 = config.INIZIO_TEST_SEDUTE
    ids = list(config.STRATEGIE)
    K, C = len(ids), len(config.COSTI)
    rng = np.random.default_rng(config.SEME)
    ret = close.pct_change().fillna(0.0)
    T = len(close) - S0
    anni = (date[-1] - date[S0 - 1]).days / 365.25
    nome = {i: config.STRATEGIE[i][0] for i in ids}

    # --- Posizioni (segnale di ieri decide oggi) e rendimenti netti a ogni livello di costo ------------------------------------
    pos = {i: fx.posizione_regola(close, config.STRATEGIE[i][1]).iloc[S0:] for i in ids}
    ret_s = ret.iloc[S0:]
    cambi = {i: float((pos[i].diff().abs().fillna(0.0).sum() + abs(pos[i].iloc[0]))) for i in ids}
    cambi_anno = {i: cambi[i] / anni for i in ids}
    CG = np.zeros((K, C))
    SH = np.zeros((K, C))
    for k, i in enumerate(ids):
        for c, costo in enumerate(config.COSTI):
            R = fx.rendimenti_netti(ret_s, pos[i], costo).to_numpy()
            CG[k, c] = fx.cagr(R, anni)
            SH[k, c] = fx.sharpe(R, config.SEDUTE_ANNO)
    PS = np.vstack([fx.posti(SH[:, c]) for c in range(C)]).T       # posti per Sharpe, per ogni costo
    righe = []
    for k, i in enumerate(ids):
        for c, costo in enumerate(config.COSTI):
            righe.append({"id": i, "nome": nome[i], "costo": costo, "cagr": CG[k, c], "sharpe": SH[k, c],
                          "posto_sharpe": PS[k, c], "cambi_anno": cambi_anno[i]})
    pd.DataFrame(righe).to_csv(config.RISULTATI / "costi_regole.csv", index=False, float_format="%.6f")

    ib, isf, isv = ids.index(config.ID_BH), ids.index(config.ID_FILTRO), ids.index(config.ID_VELOCE)
    c0, cm = 0, C - 1
    cp = list(config.COSTI).index(config.COSTO_PROVA)

    # --- Parametri e dati ---------------------------------------------------------------------------------------------------------
    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_inizio", str(date[S0].date()), "data_lunga", "Prima seduta in cui si misurano tutte le regole", "dati/ e config.py")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("anni_campione", anni, "num1", "Anni dell'intero periodo misurato", "dati/")
    reg("w_breve", config.STRATEGIE["sma50"][1][1], "annonum", "Giorni della media mobile più corta", "config.py, STRATEGIE")
    reg("w_media", config.STRATEGIE["sma100"][1][1], "annonum", "Giorni della media mobile intermedia", "config.py, STRATEGIE")
    reg("w_lunga", config.STRATEGIE["sma200"][1][1], "annonum", "Giorni della media mobile più lunga", "config.py, STRATEGIE")
    reg("mom_mesi", config.STRATEGIE["mom"][1][1] / 21, "annonum", "Mesi di storia usati dal momentum (252 sedute, 21 per mese)", "config.py, STRATEGIE")
    reg("n_regole", K, "int", "Regole confrontate", "config.py, STRATEGIE")
    reg("n_costi", C, "int", "Livelli di costo provati", "config.py, COSTI")
    for c, costo in enumerate(config.COSTI):
        reg(f"costo_{c}", costo, "pct2", f"Livello di costo numero {c + 1} della griglia, quota del valore scambiato", "config.py, COSTI")
    reg("costo_max", config.COSTO_MAX, "pct1", "Costo più alto della griglia", "config.py, COSTI")
    reg("costo_prova", config.COSTO_PROVA, "pct1", "Costo tipico citato nel testo", "config.py, COSTO_PROVA")
    reg("sedute_anno", config.SEDUTE_ANNO, "int", "Sedute di borsa per anno", "config.py")
    reg("quota_azioni", config.QUOTA_AZIONI, "pct0", "Quota in azioni del portafoglio ribilanciato", "config.py, QUOTA_AZIONI")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie estratte per ogni probabilità di cambio", "config.py")
    reg("cambi_min_anno", config.CAMBI_MIN_ANNO, "annonum", "Cambi all'anno minimi per entrare nella prova di proporzionalità", "config.py")
    reg("banda_lo", config.BANDA_PROPORZIONALITA[0], "num1", "Estremo basso della banda di proporzionalità", "config.py")
    reg("banda_hi", config.BANDA_PROPORZIONALITA[1], "num1", "Estremo alto della banda di proporzionalità", "config.py")
    reg("soglia_bh_pp", config.SOGLIA_BH, "pp2", "Perdita massima ammessa per il buy & hold, in punti percentuali di rendimento annuo", "config.py")
    reg("soglia_prob_scimmie", config.SOGLIA_PROB_SCIMMIE, "pct0", "Probabilità giornaliera di cambio da cui si valuta l'ipotesi sulle scimmie", "config.py")
    reg("soglia_ribil_pp", config.SOGLIA_RIBIL, "pp2", "Perdita massima ammessa con ribilanciamento annuale, in punti percentuali", "config.py, ipotesi 5")

    # --- Rendimenti, Sharpe e cambi per regola ---------------------------------------------------------------------------------------
    for k, i in enumerate(ids):
        reg(f"cambi_anno_{i}", cambi_anno[i], "num1", f"Cambi di posizione all'anno: {nome[i]}", "posizioni sul periodo misurato")
        reg(f"cagr_{i}_lordo", CG[k, c0], "pct1", f"Rendimento annuo composto senza costi: {nome[i]}", "costi_regole.csv")
        reg(f"cagr_{i}_prova", CG[k, cp], "pct1", f"Rendimento annuo composto con costo {config.COSTO_PROVA:.1%}: {nome[i]}", "costi_regole.csv")
        reg(f"cagr_{i}_max", CG[k, cm], "pct1", f"Rendimento annuo composto con costo {config.COSTO_MAX:.1%}: {nome[i]}", "costi_regole.csv")
        reg(f"perdita_{i}", CG[k, c0] - CG[k, cm], "pp2", f"Perdita di rendimento annuo (punti percentuali) tra costo zero e costo massimo: {nome[i]}", "costi_regole.csv")
        reg(f"sharpe_{i}_lordo", SH[k, c0], "num2", f"Sharpe senza costi: {nome[i]}", "costi_regole.csv")
        reg(f"sharpe_{i}_prova", SH[k, cp], "num2", f"Sharpe con costo {config.COSTO_PROVA:.1%}: {nome[i]}", "costi_regole.csv")
        reg(f"sharpe_{i}_max", SH[k, cm], "num2", f"Sharpe con costo {config.COSTO_MAX:.1%}: {nome[i]}", "costi_regole.csv")
        reg(f"posto_{i}_lordo", PS[k, c0], "int", f"Posto per Sharpe senza costi: {nome[i]}", "costi_regole.csv")
        reg(f"posto_{i}_max", PS[k, cm], "int", f"Posto per Sharpe con costo massimo: {nome[i]}", "costi_regole.csv")

    # --- Ipotesi 1: proporzionalità ------------------------------------------------------------------------------------------------------
    elig = [i for i in ids if cambi_anno[i] >= config.CAMBI_MIN_ANNO]
    rapp = {i: (CG[ids.index(i), c0] - CG[ids.index(i), cm]) / (cambi_anno[i] * config.COSTO_MAX) for i in elig}
    for i in elig:
        reg(f"rapporto_{i}", rapp[i], "num2", f"Perdita osservata divisa per (cambi all'anno x costo massimo): {nome[i]}", "costi_regole.csv")
    in_banda = [i for i in elig if config.BANDA_PROPORZIONALITA[0] <= rapp[i] <= config.BANDA_PROPORZIONALITA[1]]
    reg("n_eleggibili", len(elig), "int", "Regole con almeno un cambio all'anno", "posizioni")
    reg("n_in_banda", len(in_banda), "int", "Regole eleggibili con rapporto dentro la banda di proporzionalità", "costi_regole.csv")
    reg("rapporto_min", min(rapp.values()), "num2", "Rapporto più basso tra le regole eleggibili", "costi_regole.csv")
    reg("rapporto_max", max(rapp.values()), "num2", "Rapporto più alto tra le regole eleggibili", "costi_regole.csv")
    k_max_cambi = max(ids, key=lambda i: cambi_anno[i])
    reg("regola_piu_attiva", nome[k_max_cambi], "testo", "Regola con più cambi all'anno", "posizioni")
    reg("perdita_piu_attiva", CG[ids.index(k_max_cambi), c0] - CG[ids.index(k_max_cambi), cm], "pp2",
        "Perdita di rendimento annuo (punti percentuali) della regola più attiva, costo zero contro costo massimo", "costi_regole.csv")

    # --- Ipotesi 2: buy & hold ---------------------------------------------------------------------------------------------------------
    perdita_bh = CG[ib, c0] - CG[ib, cm]
    reg("perdita_bh_fine", perdita_bh, "pp3", "Perdita di rendimento annuo del buy & hold (punti percentuali, tre decimali) tra costo zero e costo massimo", "costi_regole.csv")

    # --- Ipotesi 3 e 4: Sharpe contro buy & hold --------------------------------------------------------------------------------------------
    altre = [k for k in range(K) if k != ib]
    n_sh = {c: int(sum(SH[k, c] > SH[ib, c] for k in altre)) for c in range(C)}
    n_cg = {c: int(sum(CG[k, c] > CG[ib, c] for k in altre)) for c in range(C)}
    for c, tag in ((c0, "lordo"), (cp, "prova"), (cm, "max")):
        reg(f"n_sharpe_sopra_bh_{tag}", n_sh[c], "int", f"Regole (escluso il buy & hold) con Sharpe più alto del buy & hold, costo livello {tag}", "costi_regole.csv")
        reg(f"n_cagr_sopra_bh_{tag}", n_cg[c], "int", f"Regole (escluso il buy & hold) con rendimento annuo più alto del buy & hold, costo livello {tag}", "costi_regole.csv")
    reg("n_altre_regole", len(altre), "int", "Regole diverse dal buy & hold", "config.py")
    n_neg = int((CG[:, cm] < 0).sum())
    reg("n_cagr_negativo_max", n_neg, "int", "Regole con rendimento annuo negativo al costo massimo", "costi_regole.csv")
    reg("tau_classifica", fx.kendall(SH[:, c0], SH[:, cm]), "num2", "Tau di Kendall tra la classifica per Sharpe senza costi e quella con costo massimo", "costi_regole.csv")
    reg("n_cambiano_posto", int((PS[:, c0] != PS[:, cm]).sum()), "int", "Regole che cambiano posto nella classifica per Sharpe tra costo zero e costo massimo", "costi_regole.csv")
    vinc0, vincm = ids[int(np.nanargmax(SH[:, c0]))], ids[int(np.nanargmax(SH[:, cm]))]
    reg("vinc_lordo", nome[vinc0], "testo", "Regola prima per Sharpe senza costi", "costi_regole.csv")
    reg("vinc_max", nome[vincm], "testo", "Regola prima per Sharpe con costo massimo", "costi_regole.csv")
    reg("filtro_meno_bh_max", SH[isf, cm] - SH[ib, cm], "num2", "Sharpe del filtro a 200 giorni meno Sharpe del buy & hold, costo massimo", "costi_regole.csv")

    # --- Ipotesi 5: ribilanciamento -----------------------------------------------------------------------------------------------------------
    righe_r = []
    RB = {}
    ret_a = ret_s.to_numpy()
    for nome_f, ogni in config.RIBILANCIAMENTI.items():
        for c, costo in enumerate(config.COSTI):
            R = fx.mix_ribilanciato(ret_a, config.QUOTA_AZIONI, ogni, costo)
            RB[(nome_f, c)] = (float(fx.cagr(R, anni)), float(fx.sharpe(R, config.SEDUTE_ANNO)))
            righe_r.append({"frequenza": nome_f, "ogni_sedute": ogni, "costo": costo, "cagr": RB[(nome_f, c)][0], "sharpe": RB[(nome_f, c)][1]})
    pd.DataFrame(righe_r).to_csv(config.RISULTATI / "ribilanciamento.csv", index=False, float_format="%.6f")
    perdite_rb = {}
    for nome_f, ogni in config.RIBILANCIAMENTI.items():
        perdite_rb[nome_f] = RB[(nome_f, c0)][0] - RB[(nome_f, cm)][0]
        reg(f"ribil_ogni_{nome_f}", ogni, "int", f"Sedute tra un ribilanciamento e l'altro: {nome_f}", "config.py, RIBILANCIAMENTI")
        reg(f"ribil_n_{nome_f}", len(ret_a) // ogni, "int", f"Ribilanciamenti eseguiti nel periodo: {nome_f}", "ribilanciamento.csv")
        reg(f"ribil_lordo_{nome_f}", RB[(nome_f, c0)][0], "pct2", f"Rendimento annuo del 50/50 senza costi: {nome_f}", "ribilanciamento.csv")
        reg(f"ribil_prova_{nome_f}", RB[(nome_f, cp)][0], "pct2", f"Rendimento annuo del 50/50 con costo {config.COSTO_PROVA:.1%}: {nome_f}", "ribilanciamento.csv")
        reg(f"ribil_max_{nome_f}", RB[(nome_f, cm)][0], "pct2", f"Rendimento annuo del 50/50 con costo massimo: {nome_f}", "ribilanciamento.csv")
        reg(f"ribil_perdita_{nome_f}", perdite_rb[nome_f], "pp2", f"Perdita di rendimento annuo (punti percentuali) tra costo zero e costo massimo: 50/50 {nome_f}", "ribilanciamento.csv")
        reg(f"ribil_perdita_prova_{nome_f}", RB[(nome_f, c0)][0] - RB[(nome_f, cp)][0], "pp2", f"Perdita di rendimento annuo (punti percentuali) tra costo zero e costo tipico: 50/50 {nome_f}", "ribilanciamento.csv")
    gnames = list(config.RIBILANCIAMENTI)
    reg("ribil_vantaggio_lordo_giorn_ann", RB[("giornaliero", c0)][0] - RB[("annuale", c0)][0], "pp2",
        "Rendimento annuo senza costi del 50/50 giornaliero meno quello annuale, in punti percentuali (positivo = il ribilanciamento frequente rende di più prima dei costi)", "ribilanciamento.csv")

    # --- Ipotesi 6: scimmie ---------------------------------------------------------------------------------------------------------------------
    righe_s = []
    SC = {}
    for j, p in enumerate(config.PROB_CAMBIO):
        pos_s = fx.posizioni_scimmie(config.N_SCIMMIE, T, p, rng)
        cambi_s = float((np.abs(np.diff(pos_s, axis=1, prepend=np.zeros((config.N_SCIMMIE, 1)))).sum(axis=1)).mean() / anni)
        reg(f"scim_prob_{j}", p, "pct0", f"Probabilità giornaliera di cambiare stato, gruppo di scimmie numero {j + 1}", "config.py, PROB_CAMBIO")
        reg(f"scim_cambi_anno_{j}", cambi_s, "num1", f"Cambi all'anno medi delle scimmie del gruppo {j + 1}", "scimmie.csv")
        for c, costo in enumerate(config.COSTI):
            R = fx.rendimenti_scimmie(ret_a, pos_s, costo)
            cg = fx.cagr(R, anni)
            SC[(j, c)] = (float(np.median(cg)), float((cg < 0).mean()))
            righe_s.append({"prob_cambio": p, "costo": costo, "cagr_mediano": SC[(j, c)][0], "quota_in_perdita": SC[(j, c)][1], "cambi_anno": cambi_s})
        reg(f"scim_med_lordo_{j}", SC[(j, c0)][0], "pct1", f"Rendimento annuo mediano senza costi, scimmie del gruppo {j + 1}", "scimmie.csv")
        reg(f"scim_med_prova_{j}", SC[(j, cp)][0], "pct1", f"Rendimento annuo mediano con costo {config.COSTO_PROVA:.1%}, scimmie del gruppo {j + 1}", "scimmie.csv")
        reg(f"scim_med_max_{j}", SC[(j, cm)][0], "pct1", f"Rendimento annuo mediano con costo massimo, scimmie del gruppo {j + 1}", "scimmie.csv")
        reg(f"scim_perdita_max_{j}", SC[(j, cm)][1], "pct0", f"Quota di scimmie in perdita (rendimento annuo negativo) con costo massimo, gruppo {j + 1}", "scimmie.csv")
    pd.DataFrame(righe_s).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.6f")
    reg("n_gruppi_scimmie", len(config.PROB_CAMBIO), "int", "Gruppi di scimmie (probabilità di cambio diverse)", "config.py")
    reg("bh_lordo_confronto", CG[ib, c0], "pct1", "Rendimento annuo del buy & hold senza costi (riferimento per le scimmie)", "costi_regole.csv")

    gruppi_h6 = [j for j, p in enumerate(config.PROB_CAMBIO) if p >= config.SOGLIA_PROB_SCIMMIE]
    reg("n_gruppi_h6", len(gruppi_h6), "int", "Gruppi di scimmie con probabilità di cambio alta (ipotesi 6)", "config.py")
    reg("n_gruppi_h6_ok", int(sum(1 for j in gruppi_h6 if SC[(j, c0)][0] > 0 and SC[(j, cm)][0] < 0)), "int",
        "Gruppi ad alta probabilità di cambio con mediana positiva a costo zero e negativa a costo massimo", "scimmie.csv")

    # --- Verdetti calcolati (1 = ipotesi confermata) ---------------------------------------------------------------------------------------------
    h = {1: len(in_banda) == len(elig),
         2: perdita_bh < config.SOGLIA_BH,
         3: n_sh[cm] < n_sh[c0],
         4: SH[isf, cm] > SH[ib, cm],
         5: perdite_rb["giornaliero"] > perdite_rb["mensile"] > perdite_rb["annuale"] and perdite_rb["annuale"] < config.SOGLIA_RIBIL,
         6: RIS["n_gruppi_h6_ok"]["valore"] == len(gruppi_h6)}
    for n, ok in h.items():
        reg(f"h{n}_ok", int(ok), "int", f"1 se l'ipotesi {n} è confermata, 0 se smentita", "02_backtest_e_test.py")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {T} sedute")
    print("ipotesi:", {n: int(ok) for n, ok in h.items()})


if __name__ == "__main__":
    main()
