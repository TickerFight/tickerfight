"""Passo 2 - Momentum mensile tra nove ETF settoriali americani, con e senza filtro del VIX (condizioni di chi parte con 1.000 euro).

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv              per regola e scenario: valore finale, rendimento annuo, ordini, costi, tasse, perdita massima
  scimmie_finali.csv     valore finale netto di ogni scimmia (scenario principale), per regola filtrata
  scimmie_ordini.csv     ordini di ogni scimmia
  curve.csv              valore giorno per giorno (una seduta su cinque)
  mesi_filtro.csv        per ogni fine mese: VIX, e se il filtro principale porta in liquidità

Regole: "bh" = buy & hold dell'ETF sull'S&P 500; "m<L>" = momentum mensile, tre settori migliori delle ultime L sedute;
"f<L>_<soglia>" = lo stesso con liquidità se il VIX di fine mese supera la soglia. Scenari: lordo e tre commissioni (tassa 26%).
Scimmia del filtro: stessa regola di base, stesso numero di mesi in liquidità, ma scelti a caso.
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


def mid(L): return f"m{L}"
def fid(L, th): return f"f{L}_{th}"


R_PRINC = fid(*config.PRINCIPALE)
R_SECOND = fid(*config.SECONDA)
FILTRATE = [fid(L, th) for L in config.LOOKBACKS for th in config.SOGLIE_VIX]
BASI = [mid(L) for L in config.LOOKBACKS]
NOME_REGOLA = {"bh": "buy & hold dell'S&P 500"}
for L in config.LOOKBACKS:
    NOME_REGOLA[mid(L)] = f"momentum {L} sedute senza filtro"
    for th in config.SOGLIE_VIX:
        NOME_REGOLA[fid(L, th)] = f"momentum {L} sedute con filtro VIX {th}"


def base_di(rid): return mid(int(rid[1:].split("_")[0]))


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    stato = {r["ticker"]: r["stato"] for r in meta["strumenti"]}
    tickers = [t for t, _ in config.SETTORI] + [config.BENCHMARK[0]]
    for t in tickers + [config.TICKER_CAMBIO, config.TICKER_VIX]:
        if stato.get(t) != "ok":
            raise SystemExit(f"Dati mancanti per {t}: {stato.get(t)}")
    chiusure = {t: s.carica_csv(config.file_dati(t)) for t in tickers}
    cambio = s.carica_csv(config.file_dati(config.TICKER_CAMBIO))
    vixs = s.carica_csv(config.file_dati(config.TICKER_VIX))["Close"].astype(float)
    date, nomi, C, FX = s.prepara(chiusure, cambio)
    VIX = vixs.reindex(date.union(vixs.index)).ffill().reindex(date).to_numpy(float)
    if np.isnan(VIX).any():
        raise SystemExit("VIX mancante in alcune sedute.")
    n = len(date)
    anni_idx = date.year.to_numpy()
    col_sett = list(range(len(config.SETTORI)))
    col_spy = nomi.index(config.BENCHMARK[0])
    t_min = max(config.LOOKBACKS)

    piani = {}
    for L in config.LOOKBACKS:
        piani[mid(L)] = s.piano_rotazione(C, date, L, config.K_SETTORI, t_min, col_sett)
        for th in config.SOGLIE_VIX:
            piani[fid(L, th)] = s.piano_con_filtro(piani[mid(L)], date, VIX, th)
    i0 = min(min(p) for p in piani.values())
    if any(min(p) != i0 for p in piani.values()):
        raise SystemExit("Le regole non partono tutte nella stessa seduta.")
    piani["bh"] = {i0: (col_spy,)}
    anni_test = (date[-1] - date[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        raise SystemExit(f"Solo {anni_test:.1f} anni di test: troppo pochi.")
    REGOLE = ["bh"] + BASI + FILTRATE
    print(f"{n} sedute comuni dal {date[0].date()} al {date[-1].date()}; test dal {date[i0].date()} ({anni_test:.1f} anni); "
          f"{len(piani[R_PRINC])} ribilanciamenti")

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
        if sid in ("lordo", M):
            print(f"  {rid:10s} {sid:6s} finale {r['valore_finale_eur']:9.1f}  cagr {cg[(rid, sid)]*100:6.2f}%  ordini {r['n_acquisti']+r['n_vendite']:4d}  dd {r['perdita_massima']*100:5.1f}%")

    # --- Mesi in liquidità ------------------------------------------------------------------------------------------
    righe = []
    n_cassa = {}
    for rid in FILTRATE:
        n_cassa[rid] = sum(1 for v in piani[rid].values() if len(v) == 0)
    for i in sorted(piani[R_PRINC]):
        righe.append({"data_ordine": str(date[i].date()), "vix_fine_mese": float(VIX[i - 1]), "liquidita": int(len(piani[R_PRINC][i]) == 0)})
    mesi = pd.DataFrame(righe)
    n_mesi = len(mesi)

    # --- Scimmie del filtro: stessa regola di base, stesso numero di mesi in liquidità, scelti a caso ------------------------
    rng_s = np.random.default_rng([config.SEME, 1])
    scim, scim_ord = {}, {}
    for rid in (R_PRINC, R_SECOND):
        base = piani[base_di(rid)]
        finali = {sid: np.empty(config.N_SCIMMIE) for sid, *_ in SCEN}
        ordini = np.empty(config.N_SCIMMIE)
        for j in range(config.N_SCIMMIE):
            pm = s.scimmia_cassa(base, n_cassa[rid], rng_s)
            for sid, f, p, al in SCEN:
                r_ = s.simula(C, FX, anni_idx, pm, i0, config.CAPITALE, f, p, al, serie=False)
                finali[sid][j] = r_["valore_finale_eur"]
                if sid == M:
                    ordini[j] = r_["n_acquisti"] + r_["n_vendite"]
        scim[rid], scim_ord[rid] = finali, ordini
        print(f"  scimmie {rid}: mediana netta {np.median(finali[M]):.0f}, ordini medi {ordini.mean():.1f}")

    # --- Bootstrap a blocchi: filtro contro la stessa regola senza filtro ----------------------------------------------------
    boot = {}
    for q, rid in enumerate((R_PRINC, R_SECOND)):
        e = sim[(rid, M)]["equity"]
        eb = sim[(base_di(rid), M)]["equity"]
        d = (e[1:] / e[:-1] - 1) - (eb[1:] / eb[:-1] - 1)
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

    # --- Registro dei numeri ---------------------------------------------------------------------------------------------
    reg("n_sedute", n, "int", "Sedute comuni a tutti gli strumenti e al cambio", "dati/")
    reg("data_inizio", str(date[i0].date()), "data_lunga", "Prima seduta del test (primo ordine di tutte le regole)", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    reg("anni", anni_test, "num1", "Anni del test")
    reg("anno_crisi", 2008, "annonum", "Anno della crisi finanziaria usato per il confronto sul valore di mercato", "02_backtest_e_test.py, funzione val_anno")
    reg("n_mesi", n_mesi, "int", "Fine mese in cui le regole decidono (dal primo ordine in poi)", "mesi_filtro.csv")
    reg("vix_mediana", float(np.median([VIX[i - 1] for i in piani[R_PRINC]])), "num1", "Mediana del VIX alle chiusure di fine mese del test", "mesi_filtro.csv")
    reg("vix_max_fine_mese", float(mesi["vix_fine_mese"].max()), "num1", "VIX più alto a una chiusura di fine mese del test", "mesi_filtro.csv")
    reg("data_vix_max", mesi.loc[mesi["vix_fine_mese"].idxmax(), "data_ordine"], "data_lunga", "Data dell'ordine del mese dopo la chiusura con il VIX più alto", "mesi_filtro.csv")
    for L in config.LOOKBACKS:
        for th in config.SOGLIE_VIX:
            rid = fid(L, th)
            reg(f"{rid}_mesi_cassa", n_cassa[rid], "int", f"Mesi passati in liquidità ({NOME_REGOLA[rid]})", "mesi_filtro.csv")
            reg(f"{rid}_quota_cassa", n_cassa[rid] / n_mesi, "pct0", f"Quota dei fine mese con il filtro attivo ({NOME_REGOLA[rid]})", "mesi_filtro.csv")
    for th in config.SOGLIE_VIX:
        reg(f"soglia_{th}", th, "int", "Soglia del VIX", "config.py, SOGLIE_VIX")
    reg("soglia_princ", config.PRINCIPALE[1], "int", "Soglia del VIX della regola principale", "config.py, PRINCIPALE")
    for rid in REGOLE:
        for sid in NOME_SCEN:
            x = sim[(rid, sid)]
            reg(f"{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
            reg(f"{rid}_{sid}_cagr", cg[(rid, sid)], "pct1", f"Rendimento annuo composto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
            reg(f"{rid}_{sid}_dd", -x["perdita_massima"], "pct0", f"Perdita massima dal picco ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
        x = sim[(rid, M)]
        reg(f"{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali, liquidazione finale compresa ({NOME_REGOLA[rid]})")
        reg(f"{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / anni_test, "num1", f"Ordini all'anno ({NOME_REGOLA[rid]})")
        reg(f"{rid}_quota_inv", x["quota_giorni_investito"], "pct0", f"Quota di sedute con una posizione aperta ({NOME_REGOLA[rid]})")
        for sid in NOME_SCEN:
            if sid == "lordo":
                continue
            reg(f"{rid}_{sid}_costo", sim[(rid, sid)]["commissioni_eur"], "int", f"Commissioni pagate in tutto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
            reg(f"{rid}_{sid}_tasse", sim[(rid, sid)]["tasse_eur"], "int", f"Tasse pagate in tutto ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})")
        reg(f"{rid}_attrito", cg[(rid, "lordo")] - cg[(rid, M)], "pp1", f"Punti di rendimento annuo persi dal lordo al netto, scenario principale ({NOME_REGOLA[rid]})")
    # Differenze filtro meno base, per tutte e sei le combinazioni
    n_dd_meglio = 0
    n_netto_sopra_base = 0
    for rid in FILTRATE:
        b = base_di(rid)
        reg(f"{rid}_dd_diff", sim[(rid, "lordo")]["perdita_massima"] - sim[(b, "lordo")]["perdita_massima"], "pp1", f"Perdita massima lorda della regola senza filtro meno quella con filtro, in punti percentuali, positiva se il filtro aiuta ({NOME_REGOLA[rid]})")
        reg(f"{rid}_diff_lordo", cg[(rid, "lordo")] - cg[(b, "lordo")], "pp1", f"Rendimento annuo lordo con filtro meno senza filtro, in punti percentuali ({NOME_REGOLA[rid]})")
        reg(f"{rid}_diff_netto", cg[(rid, M)] - cg[(b, M)], "pp1", f"Rendimento annuo netto (commissione fissa) con filtro meno senza filtro, in punti percentuali ({NOME_REGOLA[rid]})")
        reg(f"{rid}_diff_bh_netto", cg[(rid, M)] - cg[("bh", M)], "pp1", f"Rendimento annuo netto della regola filtrata meno quello del buy & hold, in punti percentuali ({NOME_REGOLA[rid]})")
        reg(f"{rid}_ordini_diff", (sim[(rid, M)]["n_acquisti"] + sim[(rid, M)]["n_vendite"] - sim[(b, M)]["n_acquisti"] - sim[(b, M)]["n_vendite"]) / anni_test, "num1", f"Ordini all'anno in più rispetto alla stessa regola senza filtro ({NOME_REGOLA[rid]})")
        n_dd_meglio += sim[(rid, "lordo")]["perdita_massima"] > sim[(b, "lordo")]["perdita_massima"]
        n_netto_sopra_base += sim[(rid, M)]["valore_finale_eur"] > sim[(b, M)]["valore_finale_eur"]
    reg("n_dd_meglio", n_dd_meglio, "int", "Combinazioni (su sei) in cui il filtro riduce la perdita massima lorda", "prove.csv")
    reg("n_netto_sopra_base", n_netto_sopra_base, "int", "Combinazioni (su sei) in cui la regola filtrata chiude sopra la stessa senza filtro, netto con commissione fissa", "prove.csv")
    reg("n_filtrate_sopra_bh_netto", sum(sim[(r, M)]["valore_finale_eur"] > sim[("bh", M)]["valore_finale_eur"] for r in FILTRATE), "int", "Combinazioni (su sei) filtrate che chiudono sopra il buy & hold, netto con commissione fissa", "prove.csv")
    reg("n_base_sopra_bh_netto", sum(sim[(r, M)]["valore_finale_eur"] > sim[("bh", M)]["valore_finale_eur"] for r in BASI), "int", "Regole senza filtro (su due) che chiudono sopra il buy & hold, netto con commissione fissa", "prove.csv")
    # Anno peggiore del buy & hold: 2008
    def val_anno(rid, anno):
        e = sim[(rid, M)]["equity"]
        idx = np.flatnonzero(anni_idx[i0:] == anno)
        return e[idx[-1]] / e[idx[0]] - 1 if len(idx) else float("nan")
    for rid in ["bh", R_PRINC, base_di(R_PRINC)]:
        reg(f"{rid}_anno2008", val_anno(rid, 2008), "pct0", f"Variazione di valore nel 2008, scenario con commissione fissa ({NOME_REGOLA[rid]})")
    for rid in (R_PRINC, R_SECOND):
        fin = scim[rid]
        b = base_di(rid)
        reg(f"{rid}_sc_ordini_medi", float(scim_ord[rid].mean()), "num1", f"Ordini totali medi delle scimmie ({NOME_REGOLA[rid]})", "scimmie_ordini.csv")
        for sid in NOME_SCEN:
            reale = sim[(rid, sid)]["valore_finale_eur"]
            reg(f"{rid}_{sid}_sc_mediana", float(np.median(fin[sid])), "int", f"Valore finale mediano delle scimmie ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})", "scimmie_finali.csv")
            reg(f"{rid}_{sid}_p_sc", (int((fin[sid] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1), "pval", f"p-value a una coda: quota di scimmie che fanno almeno quanto la regola ({NOME_REGOLA[rid]}, scenario {NOME_SCEN[sid]})", "scimmie_finali.csv")
        reg(f"{rid}_sc_sotto", float((fin[M] < sim[(rid, M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la regola, scenario principale ({NOME_REGOLA[rid]})", "scimmie_finali.csv")
        reg(f"{rid}_sc_sopra_base", float((fin[M] >= sim[(b, M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che fanno almeno quanto la regola senza filtro, scenario principale ({NOME_REGOLA[rid]})", "scimmie_finali.csv")
        reg(f"{rid}_p_sc_holm", ph[f"sc_{rid}"], "pval", f"p-value delle scimmie corretto con Holm ({NOME_REGOLA[rid]}, scenario principale)", "scimmie_finali.csv")
        bt = boot[rid]
        reg(f"{rid}_boot_diff", bt["diff"], "pp1", f"Differenza media annualizzata del rendimento netto giornaliero tra filtrata e non filtrata, punti percentuali ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_boot_lo", bt["lo"], "pp1", f"Estremo inferiore dell'intervallo bootstrap della differenza annualizzata ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_boot_hi", bt["hi"], "pp1", f"Estremo superiore dell'intervallo bootstrap della differenza annualizzata ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p_boot", bt["p"], "pval", f"p-value a due code della differenza media giornaliera tra filtrata e non filtrata ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
        reg(f"{rid}_p_boot_holm", bt["p"] if False else ph[f"bo_{rid}"], "pval", f"p-value del bootstrap corretto con Holm ({NOME_REGOLA[rid]})", "bootstrap a blocchi")
    reg("n_sc_signif", sum(ph[f"sc_{r}"] < 0.05 for r in (R_PRINC, R_SECOND)), "int", "Regole filtrate (su due) che battono le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_boot_signif", sum(ph[f"bo_{r}"] < 0.05 for r in (R_PRINC, R_SECOND)), "int", "Regole filtrate (su due) la cui differenza dalla non filtrata è significativa dopo Holm", "bootstrap a blocchi")
    reg("n_prove", len(REGOLE) * len(NOME_SCEN), "int", "Simulazioni complete eseguite: regole x scenari (lordo compreso)", "config.py")
    reg("n_regole", len(REGOLE) - 1, "int", "Regole di momentum provate, con e senza filtro, buy & hold escluso", "config.py")
    reg("n_regole_filtrate", len(FILTRATE), "int", "Regole con filtro provate (periodo di osservazione x soglia)", "config.py")
    reg("n_test_ipotesi", len(famiglia), "int", "Test di ipotesi eseguiti (scimmie e bootstrap, due regole ciascuno) con correzione di Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni regola", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.LUNGHEZZA_BLOCCO, "int", "Sedute per blocco nel bootstrap", "config.py, LUNGHEZZA_BLOCCO")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine nello scenario principale, in euro", "config.py, SCENARI_COSTO")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale all'importo nel terzo scenario", "config.py, SCENARI_COSTO")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("k_settori", config.K_SETTORI, "int", "Settori tenuti dal momentum", "config.py, K_SETTORI")
    for L in config.LOOKBACKS:
        reg(f"lookback_{L}", L, "int", "Sedute del periodo di osservazione", "config.py, LOOKBACKS")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    pd.DataFrame(prove).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    mesi.to_csv(config.RISULTATI / "mesi_filtro.csv", index=False, float_format="%.2f")
    camp = np.arange(0, n - i0, 5)
    curva = pd.DataFrame({"data": date[i0:][camp]})
    for rid in REGOLE:
        curva[rid] = sim[(rid, M)]["equity"][camp]
    curva.to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.4f")
    pd.DataFrame({rid: scim[rid][M] for rid in scim}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    pd.DataFrame({rid: scim_ord[rid] for rid in scim_ord}).to_csv(config.RISULTATI / "scimmie_ordini.csv", index=False)
    (config.RISULTATI / "regole_usate.json").write_text(json.dumps(
        {"regole": REGOLE, "basi": BASI, "filtrate": FILTRATE, "nomi": NOME_REGOLA, "principale": R_PRINC, "seconda": R_SECOND}, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
