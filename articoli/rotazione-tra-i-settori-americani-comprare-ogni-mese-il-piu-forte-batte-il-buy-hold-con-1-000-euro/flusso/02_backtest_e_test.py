"""Passo 2 - Rotazione mensile tra nove ETF settoriali americani, con le condizioni di chi parte con 1.000 euro.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv              per regola e scenario: valore finale, rendimento annuo, ordini, costi, tasse, perdita massima
  scimmie_finali.csv     valore finale netto di ogni scimmia (scenario principale), per regola
  curve.csv              valore giorno per giorno (una seduta su cinque) di buy & hold, nove settori e rotazioni
  scelte.csv             il settore scelto a ogni ribilanciamento dalla rotazione principale

Regole: "bh" = buy & hold dell'ETF sull'S&P 500; "eq" = i nove settori comprati in parti uguali e tenuti; "r<L>_<K>" =
rotazione mensile verso i K settori con il rendimento più alto delle ultime L sedute. Quattro scenari: lordo (nessun costo,
nessuna tassa) e tre scenari di commissione, tutti con la tassa del 26%.
Scimmia: stessi giorni di ordine e stesso numero di ordini della regola, settori scelti a caso; gli stessi costi e le
stesse tasse, passati dallo stesso contabile.
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
SCEN = [("lordo", 0.0, 0.0, 0.0)] + [(f"c{k}", f, p, config.ALIQUOTA) for k, (_, f, p) in enumerate(config.SCENARI_COSTO)]
M = f"c{config.SCENARIO_PRINCIPALE}"
NOME_SCEN = {f"c{k}": nome for k, (nome, _, _) in enumerate(config.SCENARI_COSTO)}
NOME_SCEN["lordo"] = "lordo"


def rid_rot(L: int, k: int) -> str:
    return f"r{L}_{k}"


R_PRINC = rid_rot(*config.PRINCIPALE)
R_SECOND = rid_rot(*config.SECONDARIA_SCIMMIE)
VARIANTI = [rid_rot(L, k) for k in config.N_SETTORI for L in config.LOOKBACKS]
NOME_REGOLA = {"bh": "buy & hold dell'S&P 500", "eq": "nove settori tenuti"}
for L in config.LOOKBACKS:
    for k in config.N_SETTORI:
        NOME_REGOLA[rid_rot(L, k)] = f"rotazione, {L} sedute, {k} {'settore' if k == 1 else 'settori'}"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out


def bootstrap_blocchi(d: np.ndarray, rng) -> np.ndarray:
    """Medie di B ricampionamenti a blocchi circolari della serie d (lunghezza del blocco: config.LUNGHEZZA_BLOCCO)."""
    N, L = len(d), config.LUNGHEZZA_BLOCCO
    nb = int(np.ceil(N / L))
    medie = np.empty(config.N_BOOTSTRAP)
    passo = 250
    for a in range(0, config.N_BOOTSTRAP, passo):
        m = min(passo, config.N_BOOTSTRAP - a)
        inizi = rng.integers(0, N, size=(m, nb))
        idx = (inizi[:, :, None] + np.arange(L)[None, None, :]) % N
        medie[a:a + m] = d[idx.reshape(m, -1)[:, :N]].mean(axis=1)
    return medie


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    stato = {r["ticker"]: r["stato"] for r in meta["strumenti"]}
    tickers = [t for t, _ in config.SETTORI] + [config.BENCHMARK[0]]
    for t in tickers + [config.TICKER_CAMBIO]:
        if stato.get(t) != "ok":
            raise SystemExit(f"Dati mancanti per {t}: {stato.get(t)}")
    chiusure = {t: s.carica_csv(config.file_dati(t)) for t in tickers}
    cambio = s.carica_csv(config.file_dati(config.TICKER_CAMBIO))
    date, nomi, C, FX = s.prepara(chiusure, cambio)
    n = len(date)
    anni_idx = date.year.to_numpy()
    col_sett = list(range(len(config.SETTORI)))
    col_spy = nomi.index(config.BENCHMARK[0])
    t_min = max(config.LOOKBACKS)

    piani = {}
    for L in config.LOOKBACKS:
        for k in config.N_SETTORI:
            piani[rid_rot(L, k)] = s.piano_rotazione(C, date, L, k, t_min, col_sett)
    i0 = min(min(p) for p in piani.values())
    if any(min(p) != i0 for p in piani.values()):
        raise SystemExit("Le regole non partono tutte nella stessa seduta.")
    piani["bh"] = {i0: (col_spy,)}
    piani["eq"] = {i0: tuple(col_sett)}
    anni_test = (date[-1] - date[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        raise SystemExit(f"Solo {anni_test:.1f} anni di test: troppo pochi.")
    REGOLE = ["bh", "eq"] + VARIANTI
    print(f"{n} sedute comuni dal {date[0].date()} al {date[-1].date()}; test dal {date[i0].date()} ({anni_test:.1f} anni); "
          f"{len(piani[R_PRINC])} ribilanciamenti")

    # --- Tutte le simulazioni (regola x scenario) --------------------------------------------------------------------
    sim = {}
    for rid in REGOLE:
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(C, FX, anni_idx, piani[rid], i0, config.CAPITALE, f, p, al, serie=True)
    cg = {k: s.cagr(v["valore_finale_eur"], config.CAPITALE, date, i0) for k, v in sim.items()}
    prove = []
    for (rid, sid), r in sim.items():
        prove.append({"regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": cg[(rid, sid)],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
                      "perdita_massima": r["perdita_massima"]})
    for (rid, sid), r in sim.items():
        print(f"  {rid:8s} {sid:6s} finale {r['valore_finale_eur']:9.1f}  cagr {cg[(rid, sid)]*100:6.2f}%  ordini {r['n_acquisti']+r['n_vendite']:4d}")

    # --- Scelte della rotazione principale ---------------------------------------------------------------------------------
    scelte = []
    prev: set = set()
    for i in sorted(piani[R_PRINC]):
        t = piani[R_PRINC][i]
        scelte.append({"data_ordine": str(date[i].date()), "settore": nomi[t[0]], "cambia": int(set(t) != prev)})
        prev = set(t)
    sc_df = pd.DataFrame(scelte)
    quota_cambio = float(sc_df["cambia"].iloc[1:].mean())
    conteggio = sc_df["settore"].value_counts()
    nome_sett = dict(config.SETTORI)

    # --- Le scimmie (rispetto alle due regole con L = 126) -------------------------------------------------------------------
    rng_s = np.random.default_rng([config.SEME, 1])
    scim = {}
    for rid in (R_PRINC, R_SECOND):
        finali = {sid: np.empty(config.N_SCIMMIE) for sid, *_ in SCEN}
        for j in range(config.N_SCIMMIE):
            pm = s.scimmia_piano(piani[rid], col_sett, rng_s)
            for sid, f, p, al in SCEN:
                finali[sid][j] = s.simula(C, FX, anni_idx, pm, i0, config.CAPITALE, f, p, al, serie=False)["valore_finale_eur"]
        scim[rid] = finali
        print(f"  scimmie {rid}: mediana netta {np.median(finali[M]):.0f}")

    # --- Bootstrap a blocchi: rotazione contro buy & hold (rendimento giornaliero netto, scenario principale) ---------------
    boot = {}
    e_bh = sim[("bh", M)]["equity"]
    for q, rid in enumerate((R_PRINC, R_SECOND)):
        e = sim[(rid, M)]["equity"]
        d = (e[1:] / e[:-1] - 1) - (e_bh[1:] / e_bh[:-1] - 1)
        medie = bootstrap_blocchi(d - d.mean(), np.random.default_rng([config.SEME, 2, q]))
        osserv = float(d.mean())
        p_boot = (int((np.abs(medie) >= abs(osserv)).sum()) + 1) / (config.N_BOOTSTRAP + 1)
        medie_ic = bootstrap_blocchi(d, np.random.default_rng([config.SEME, 3, q]))
        alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
        lo, hi = np.quantile(medie_ic, [alfa, 1 - alfa])
        boot[rid] = dict(p=p_boot, diff=osserv * 252, lo=float(lo) * 252, hi=float(hi) * 252)

    p_sc = {rid: (int((scim[rid][M] >= sim[(rid, M)]["valore_finale_eur"]).sum()) + 1) / (config.N_SCIMMIE + 1) for rid in scim}
    famiglia = {f"sc_{rid}": p_sc[rid] for rid in scim} | {f"bo_{rid}": boot[rid]["p"] for rid in boot}
    ph = holm(famiglia)

    # --- Registro dei numeri ---------------------------------------------------------------------------------------------------
    reg("n_sedute", n, "int", "Sedute comuni a tutti gli strumenti e al cambio", "dati/")
    reg("data_inizio", str(date[i0].date()), "data_lunga", "Prima seduta del test (primo ordine di tutte le regole)", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    reg("data_prima_serie", str(date[0].date()), "data_lunga", "Prima seduta con tutti i dati disponibili (cambio incluso)", "dati/")
    reg("anni", anni_test, "num1", "Anni del test")
    reg("n_ribilanciamenti", len(piani[R_PRINC]), "int", "Fine mese in cui la rotazione principale decide (dal primo ordine in poi)", "scelte.csv")
    reg("quota_mesi_cambio", quota_cambio, "pct0", "Quota dei ribilanciamenti in cui la rotazione principale cambia settore", "scelte.csv")
    top = conteggio.index[0]
    reg("settore_top_nome", nome_sett[top], "testo", "Settore scelto più spesso dalla rotazione principale", "scelte.csv")
    reg("settore_top_ticker", top, "testo", "Ticker del settore scelto più spesso", "scelte.csv")
    reg("settore_top_quota", float(conteggio.iloc[0] / len(sc_df)), "pct0", "Quota dei ribilanciamenti in cui la rotazione principale sceglie il settore più frequente", "scelte.csv")
    reg("n_settori_usati", int(len(conteggio)), "int", "Settori diversi scelti almeno una volta dalla rotazione principale", "scelte.csv")
    for rid in REGOLE:
        for sid in NOME_SCEN:
            x = sim[(rid, sid)]
            reg(f"{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
            reg(f"{rid}_{sid}_cagr", cg[(rid, sid)], "pct1", f"Rendimento annuo composto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
        x = sim[(rid, M)]
        reg(f"{rid}_dd", -x["perdita_massima"], "pct0", f"Perdita massima dal picco ({NOME_REGOLA[rid]}, scenario principale)")
        reg(f"{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali, acquisti e vendite, liquidazione finale compresa ({NOME_REGOLA[rid]})")
        reg(f"{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / anni_test, "num1", f"Ordini all'anno ({NOME_REGOLA[rid]})")
        for sid in NOME_SCEN:
            if sid == "lordo":
                continue
            reg(f"{rid}_{sid}_costo", sim[(rid, sid)]["commissioni_eur"], "int", f"Commissioni pagate in tutto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
            reg(f"{rid}_{sid}_tasse", sim[(rid, sid)]["tasse_eur"], "int", f"Tasse pagate in tutto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
        reg(f"{rid}_attrito", cg[(rid, "lordo")] - cg[(rid, M)], "pp1", f"Punti di rendimento annuo persi dal lordo al netto, scenario principale ({NOME_REGOLA[rid]})")
        # prima e seconda metà del periodo (equity netta dello scenario principale)
        e = x["equity"]
        mezzo = len(e) // 2
        a1 = (len(e[:mezzo]) / 252.0)
        a2 = (len(e[mezzo:]) / 252.0)
        reg(f"{rid}_cagr_meta1", (e[mezzo - 1] / e[0]) ** (1 / a1) - 1, "pct1", f"Rendimento annuo della prima metà del periodo, valore di mercato senza liquidazione ({NOME_REGOLA[rid]}, scenario principale)")
        reg(f"{rid}_cagr_meta2", (e[-1] / e[mezzo]) ** (1 / a2) - 1, "pct1", f"Rendimento annuo della seconda metà del periodo, valore di mercato senza liquidazione ({NOME_REGOLA[rid]}, scenario principale)")
    reg("data_meta", str(date[i0 + len(sim[("bh", M)]["equity"]) // 2].date()), "data_lunga", "Seduta che divide a metà il periodo di test", "dati/")
    for rid in (R_PRINC, R_SECOND):
        fin = scim[rid]
        for sid in NOME_SCEN:
            reale = sim[(rid, sid)]["valore_finale_eur"]
            reg(f"{rid}_{sid}_sc_mediana", float(np.median(fin[sid])), "int", f"Valore finale mediano delle scimmie ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})", "scimmie_finali.csv")
            reg(f"{rid}_{sid}_p_sc", (int((fin[sid] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1), "pval", f"p-value a una coda: quota di scimmie che fanno almeno quanto la regola ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})", "scimmie_finali.csv")
        reg(f"{rid}_sc_sotto", float((fin[M] < sim[(rid, M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la regola, scenario principale ({NOME_REGOLA[rid]})", "scimmie_finali.csv")
        reg(f"{rid}_sc_sopra_bh", float((fin[M] >= sim[("bh", M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che fanno almeno quanto il buy & hold, scenario principale ({NOME_REGOLA[rid]})", "scimmie_finali.csv")
        reg(f"{rid}_p_sc_holm", ph[f"sc_{rid}"], "pval", f"p-value delle scimmie corretto con Holm ({NOME_REGOLA[rid]}, scenario principale)", "scimmie_finali.csv")
        b = boot[rid]
        reg(f"{rid}_diff_ann", b["diff"], "pp1", f"Differenza media annualizzata del rendimento netto giornaliero tra la rotazione e il buy & hold, in punti percentuali ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_diff_lo", b["lo"], "pp1", f"Estremo inferiore dell'intervallo bootstrap a blocchi della differenza annualizzata ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_diff_hi", b["hi"], "pp1", f"Estremo superiore dell'intervallo bootstrap a blocchi della differenza annualizzata ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p_boot", b["p"], "pval", f"p-value a due code della differenza media giornaliera tra rotazione e buy & hold ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p_boot_holm", ph[f"bo_{rid}"], "pval", f"p-value del bootstrap corretto con Holm ({NOME_REGOLA[rid]})", "bootstrap a blocchi")

    # --- Numeri complessivi, per le sei ipotesi ----------------------------------------------------------------------
    reg("diff_lordo_princ", cg[(R_PRINC, "lordo")] - cg[("bh", "lordo")], "pp1", "Rendimento annuo lordo della rotazione principale meno quello del buy & hold, in punti percentuali")
    reg("diff_netto_princ", cg[(R_PRINC, M)] - cg[("bh", M)], "pp1", "Rendimento annuo netto della rotazione principale meno quello del buy & hold, scenario principale, in punti percentuali")
    reg("diff_netto_eq", cg[(R_PRINC, M)] - cg[("eq", M)], "pp1", "Rendimento annuo netto della rotazione principale meno quello dei nove settori tenuti, scenario principale, in punti percentuali")
    reg("n_var_sopra_bh_lordo", sum(cg[(v, "lordo")] > cg[("bh", "lordo")] for v in VARIANTI), "int", "Combinazioni (su sei) con rendimento annuo lordo sopra il buy & hold")
    reg("n_var_sotto_bh_netto", sum(sim[(v, M)]["valore_finale_eur"] < sim[("bh", M)]["valore_finale_eur"] for v in VARIANTI), "int", "Combinazioni (su sei) che chiudono sotto il buy & hold al netto, scenario principale")
    reg("n_var_sotto_bh_c0", sum(sim[(v, "c0")]["valore_finale_eur"] < sim[("bh", "c0")]["valore_finale_eur"] for v in VARIANTI), "int", "Combinazioni (su sei) che chiudono sotto il buy & hold al netto con commissione zero (resta la sola tassa)")
    reg("n_var_sotto_bh_c2", sum(sim[(v, "c2")]["valore_finale_eur"] < sim[("bh", "c2")]["valore_finale_eur"] for v in VARIANTI), "int", "Combinazioni (su sei) che chiudono sotto il buy & hold al netto con commissione proporzionale")
    reg("n_var_sotto_eq_netto", sum(sim[(v, M)]["valore_finale_eur"] < sim[("eq", M)]["valore_finale_eur"] for v in VARIANTI), "int", "Combinazioni (su sei) che chiudono sotto i nove settori tenuti, scenario principale")
    reg("n_ordini_piu_k3", sum(sim[(rid_rot(L, 3), M)]["n_acquisti"] + sim[(rid_rot(L, 3), M)]["n_vendite"] > sim[(rid_rot(L, 1), M)]["n_acquisti"] + sim[(rid_rot(L, 1), M)]["n_vendite"] for L in config.LOOKBACKS), "int", "Periodi di osservazione (su tre) in cui la rotazione a tre settori fa più ordini di quella a un settore")
    reg("n_boot_signif", sum(ph[f"bo_{r}"] < 0.05 for r in (R_PRINC, R_SECOND)), "int", "Regole (su due) la cui differenza dal buy & hold è significativa dopo Holm", "bootstrap a blocchi")
    reg("n_sc_signif", sum(ph[f"sc_{r}"] < 0.05 for r in (R_PRINC, R_SECOND)), "int", "Regole (su due) che battono le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_prove", len(REGOLE) * len(NOME_SCEN), "int", "Simulazioni complete eseguite: regole x scenari (lordo compreso)", "config.py")
    reg("n_regole_rotazione", len(VARIANTI), "int", "Regole di rotazione provate (periodo di osservazione x numero di settori)", "config.py")
    reg("n_test_ipotesi", len(famiglia), "int", "Test di ipotesi eseguiti (scimmie e bootstrap, due regole ciascuno) con correzione di Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni regola", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.LUNGHEZZA_BLOCCO, "int", "Sedute per blocco nel bootstrap", "config.py, LUNGHEZZA_BLOCCO")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine nello scenario principale, in euro", "config.py, SCENARI_COSTO")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale all'importo nel terzo scenario", "config.py, SCENARI_COSTO")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    for L in config.LOOKBACKS:
        reg(f"lookback_{L}", L, "int", "Sedute del periodo di osservazione", "config.py, LOOKBACKS")
    reg("lookback_princ", config.PRINCIPALE[0], "int", "Sedute del periodo di osservazione della rotazione principale", "config.py, PRINCIPALE")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    # --- File di supporto ---------------------------------------------------------------------------------------------
    pd.DataFrame(prove).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    sc_df.to_csv(config.RISULTATI / "scelte.csv", index=False)
    camp = np.arange(0, n - i0, 5)
    curva = pd.DataFrame({"data": date[i0:][camp]})
    for rid in REGOLE:
        curva[rid] = sim[(rid, M)]["equity"][camp]
    curva.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.4f")
    pd.DataFrame({rid: scim[rid][M] for rid in scim}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "regole_usate.json").write_text(json.dumps(
        {"regole": REGOLE, "varianti": VARIANTI, "nomi": NOME_REGOLA, "principale": R_PRINC, "seconda": R_SECOND}, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
