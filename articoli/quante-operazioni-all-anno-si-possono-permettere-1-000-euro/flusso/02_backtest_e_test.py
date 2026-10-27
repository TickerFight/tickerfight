"""Passo 2 - La regola a cicli a sei frequenze, con le condizioni di chi parte con 1.000 euro.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv         per strumento, frequenza e scenario: valore finale, rendimento annuo, ordini, costi, tasse
  scimmie_finali.csv  valore finale netto di ogni scimmia (scenario 2 euro), per strumento e frequenza

Regole: buy & hold ("bh"); "cNN" = regola a cicli con ciclo di NN sedute (NN-1 dentro, 1 fuori).
Quattro scenari: lordo (nessun costo, nessuna tassa) e tre scenari di commissione, tutti con la tassa del 26%.
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
RID = [f"y{L}" for L in config.CICLI]          # y252, y126, ...


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


def agenda(n: int, i0: int, L: int) -> np.ndarray:
    return np.array([(i - i0) % L != L - 1 for i in range(n)])


def analizza(k_str, tk, nome, valuta, meta, fx_df):
    riga = [r for r in meta["strumenti"] if r["ticker"] == tk][0]
    if riga["stato"] != "ok":
        print(f"{tk}: scartato, {riga['stato']}")
        return None
    t = s.carica_csv(config.file_dati(tk))
    if valuta == "USD":
        if fx_df is None:
            return None
        df = s.prepara(t, fx_df, 1)
    else:
        df = s.prepara(t, None, 1)
    i0 = s.primo_indice(df)
    anni_test = (df.index[-1] - df.index[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        print(f"{tk}: scartato, solo {anni_test:.1f} anni")
        return None
    n = len(df)
    C, FX = df["Close"].to_numpy(float), df["fx"].to_numpy(float)
    anni_idx = df.index.year.to_numpy()
    sim, prove = {}, []
    for rid in ["bh"] + RID:
        ob = None if rid == "bh" else agenda(n, i0, int(rid[1:]))
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, rid != "bh", obiettivo=ob)
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
                      "quota_investito": r["quota_giorni_investito"]})
    rng = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    scim = {}
    f1, p1, a1 = [(f, p, al) for sid, f, p, al in SCEN if sid == M][0]
    for rid in RID:
        a, b = s.blocchi(sim[(rid, "lordo")])
        k, D = len(a), int((b - a).sum())
        fin = np.empty(config.N_SCIMMIE)
        for j in range(config.N_SCIMMIE):
            ia, ib = s.scimmia(k, D, N, rng)
            fin[j] = s.valuta_blocchi(C, FX, anni_idx, ia + i0, ib + i0, config.CAPITALE, f1, p1, a1)[0]
        scim[rid] = {"k": k, "finali": fin}
    return dict(tk=tk, sl=config.slug(tk), nome=nome, df=df, i0=i0, sim=sim, prove=prove, scim=scim, anni=anni_test)


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    cambio_ok = any(r["ticker"] == config.TICKER_CAMBIO and r["stato"] == "ok" for r in meta["strumenti"])
    fx_df = s.carica_csv(config.file_dati(config.TICKER_CAMBIO)) if cambio_ok else None
    res = []
    for k, (tk, nome, valuta) in enumerate(config.STRUMENTI):
        r = analizza(k, tk, nome, valuta, meta, fx_df)
        if r:
            res.append(r)
            print(f"{tk}: {r['anni']:.1f} anni; netto 2 euro: bh {r['sim'][('bh', M)]['valore_finale_eur']:.0f}, " +
                  ", ".join(f"{x} {r['sim'][(x, M)]['valore_finale_eur']:.0f}" for x in RID))
    if len(res) < 2:
        raise SystemExit("Troppo pochi strumenti utilizzabili.")

    pgrezzo = {}
    for r in res:
        for rid in RID:
            reale = r["sim"][(rid, M)]["valore_finale_eur"]
            pgrezzo[(r["tk"], rid)] = (int((r["scim"][rid]["finali"] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1)
    ph = holm(pgrezzo)

    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome}", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        ordini_anno = {}
        for rid in ["bh"] + RID:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                if sid != "lordo":
                    reg(f"{sl}_{rid}_{sid}_costo", x["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                    reg(f"{sl}_{rid}_{sid}_tasse", x["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                    reg(f"{sl}_{rid}_{sid}_perdita", sm[("bh", sid)]["cagr"] - x["cagr"], "pp1", f"Rendimento annuo netto del buy & hold meno quello della frequenza {rid}, scenario {NOME_SCEN[sid]}, in punti percentuali, {nome}")
            x = sm[(rid, M)]
            oa = (x["n_acquisti"] + x["n_vendite"]) / r["anni"]
            nom = 2 * config.SEDUTE_ANNO / int(rid[1:]) if rid != "bh" else 2 / r["anni"]
            ordini_anno[rid] = nom
            eq = x["equity"]
            morto = np.flatnonzero(eq <= 1e-9)
            vita = (r["df"].index[r["i0"] + int(morto[0])] - r["df"].index[r["i0"]]).days / 365.25 if len(morto) else r["anni"]
            reg(f"{sl}_{rid}_ordini_nom", nom, "num1", f"Ordini all'anno previsti dalla regola se il capitale non si esaurisce ({rid}), {nome}", "config.py, CICLI")
            reg(f"{sl}_{rid}_anni_vita", vita, "num1", f"Anni dopo i quali il capitale è esaurito (scenario principale, {rid}); se non si esaurisce, gli anni del test, {nome}")
            reg(f"{sl}_{rid}_esaurito", int(len(morto) > 0), "int", f"1 se il capitale si esaurisce nello scenario principale ({rid}), {nome}")
            reg(f"{sl}_{rid}_ordini_anno", oa, "num1", f"Ordini all'anno ({rid}), {nome}")
            reg(f"{sl}_{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali ({rid}), {nome}")
            reg(f"{sl}_{rid}_quota", x["quota_giorni_investito"], "pct1", f"Quota di sedute investite ({rid}), {nome}")
            reg(f"{sl}_{rid}_costo_anno_quota", x["commissioni_eur"] / r["anni"] / config.CAPITALE, "pct1", f"Commissioni pagate in media ogni anno, in quota del capitale iniziale ({rid}, scenario principale), {nome}")
            reg(f"{sl}_{rid}_tasse_anno", x["tasse_eur"] / r["anni"], "num1", f"Tasse pagate in media ogni anno in euro ({rid}, scenario principale), {nome}")
            reg(f"{sl}_{rid}_costo_anno", x["commissioni_eur"] / r["anni"], "num1", f"Commissioni pagate in media ogni anno in euro ({rid}, scenario principale), {nome}")
        for rid in RID:
            fin = r["scim"][rid]["finali"]
            reale = sm[(rid, M)]["valore_finale_eur"]
            reg(f"{sl}_{rid}_sc_mediana", float(np.median(fin)), "int", f"Valore finale mediano delle scimmie ({rid}, scenario principale), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p5", float(np.quantile(fin, 0.05)), "int", f"5° percentile del valore finale delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p95", float(np.quantile(fin, 0.95)), "int", f"95° percentile del valore finale delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_sc", pgrezzo[(r["tk"], rid)], "pval", f"p-value a una coda: quota di scimmie che fanno almeno quanto la regola ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_holm", ph[(r["tk"], rid)], "pval", f"p-value delle scimmie corretto con Holm sui 18 test ({rid}), {nome}", "scimmie_finali.csv")
        # frequenza massima sostenibile (perdita netta con 2 euro non sopra la soglia)
        buone = [rid for rid in RID if sm[("bh", M)]["cagr"] - sm[(rid, M)]["cagr"] <= config.SOGLIA_SOSTENIBILE]
        sost = max((ordini_anno[x] for x in buone), default=0.0)
        r["sost"] = sost
        r["buone"] = buone
        reg(f"{sl}_sost_ordini", sost, "num1", f"Ordini all'anno della frequenza più alta provata con perdita netta (2 euro) sotto la soglia, {nome}; zero se nessuna lo è")
        reg(f"{sl}_pareggio_ordini", sm[("bh", "lordo")]["cagr"] * config.CAPITALE / config.SCENARI_COSTO[config.SCENARIO_PRINCIPALE][1], "num1", f"Ordini all'anno con cui le commissioni fisse (non composte) eguagliano il rendimento annuo lordo del buy & hold su {config.CAPITALE:.0f} euro, {nome}", "rendimento lordo del buy & hold diviso la commissione, per 1.000 euro")

    # --- Tabella teorica (nessun dato di mercato) --------------------------------------------------------------------
    fissa = config.SCENARI_COSTO[config.SCENARIO_PRINCIPALE][1]
    perc = config.SCENARI_COSTO[2][2]
    for n_ord in config.ORDINI_TABELLA:
        reg(f"ana_{n_ord}_ordini", n_ord, "int", "Ordini all'anno nella tabella teorica", "config.py, ORDINI_TABELLA")
        reg(f"ana_{n_ord}_fisso", n_ord * fissa / config.CAPITALE, "pct1", f"Costo annuo di {n_ord} ordini da {fissa:.0f} euro su {config.CAPITALE:.0f} euro, in quota del capitale", "ordini x commissione / capitale")
        reg(f"ana_{n_ord}_perc", n_ord * perc, "pct1", f"Costo annuo di {n_ord} ordini con commissione proporzionale su capitale invariato, in quota del capitale", "ordini x aliquota")
    reg("ana_ordini_soglia", config.SOGLIA_SOSTENIBILE * config.CAPITALE / fissa, "num1", "Ordini all'anno che consumano da soli la soglia di sostenibilità con la commissione fissa", "soglia x capitale / commissione")

    # --- Ipotesi ----------------------------------------------------------------------------------------------------
    nS = len(res)
    reg("n_strumenti", nS, "int", "Strumenti utilizzabili", "config.py e dati/")
    reg("n_scartati", len(config.STRUMENTI) - nS, "int", "Strumenti scartati", "metadati.json")
    reg("n_h1", sum(r["sim"][("y10", M)]["cagr"] < 0 for r in res), "int", "Strumenti in cui il rendimento annuo netto (2 euro) del ciclo da 10 sedute è negativo")
    reg("n_h2", sum(r["sim"][("bh", M)]["cagr"] - r["sim"][("y252", M)]["cagr"] <= config.SOGLIA_SOSTENIBILE for r in res), "int", "Strumenti in cui il ciclo annuale perde meno della soglia rispetto al buy & hold (2 euro)")
    reg("n_h3", sum(r["sost"] < 10 for r in res), "int", "Strumenti in cui gli ordini all'anno sostenibili sono meno di 10")
    reg("n_h4", sum(r["sim"][("y5", "c0")]["cagr"] < r["sim"][("bh", "c0")]["cagr"] for r in res), "int", "Strumenti in cui, con commissione zero e tassa, il ciclo da 5 sedute rende meno del buy & hold")
    reg("n_h5", sum(all(r["sim"][("bh", "c2")]["cagr"] - r["sim"][(x, "c2")]["cagr"] < r["sim"][("bh", "c1")]["cagr"] - r["sim"][(x, "c1")]["cagr"] for x in ("y21", "y10", "y5")) for r in res), "int", "Strumenti in cui la commissione 0,1% perde meno della commissione da 2 euro alle tre frequenze alte (21, 10, 5 sedute)")
    reg("n_h6_signif", sum(v < 0.05 for v in ph.values()), "int", "Test sulle scimmie significativi dopo Holm (su 18)", "scimmie_finali.csv")
    reg("n_h6_grezzo", sum(v < 0.05 for v in pgrezzo.values()), "int", "Test sulle scimmie con p-value sotto 0,05 senza correzione (su 18)", "scimmie_finali.csv")
    for x in ("y10", "y5"):
        reg(f"n_esaurito_{x}", sum(int(r["sim"][(x, M)]["equity"].min() <= 1e-9) for r in res), "int", f"Strumenti in cui il capitale si esaurisce con la frequenza {x}, scenario principale")
    reg("n_prove", nS * (1 + len(RID)) * len(NOME_SCEN), "int", "Simulazioni complete: strumenti x (buy & hold + frequenze) x scenari", "config.py")
    reg("n_test", nS * len(RID), "int", "Test di ipotesi con correzione di Holm", "config.py")
    reg("n_frequenze", len(RID), "int", "Frequenze provate", "config.py, CICLI")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per strumento e frequenza", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py")
    reg("commissione_fissa", fissa, "int", "Commissione fissa per ordine, scenario principale, in euro", "config.py")
    reg("commissione_perc", perc, "pct1", "Commissione proporzionale, terzo scenario", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py")
    reg("soglia", config.SOGLIA_SOSTENIBILE, "pp1", "Soglia di sostenibilità: perdita annua massima rispetto al buy & hold, in punti percentuali", "config.py")
    for L in config.CICLI:
        reg(f"ciclo_{L}", L, "int", "Sedute di un ciclo", "config.py, CICLI")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["df"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")

    pd.DataFrame([x for r in res for x in r["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    colonne = {f"{r['sl']}_{rid}": r["scim"][rid]["finali"] for r in res for rid in RID}
    pd.DataFrame(colonne).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "strumenti_usati.json").write_text(json.dumps(
        [{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
