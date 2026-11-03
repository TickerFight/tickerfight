"""Passo 2 - La stessa regola di trend (SMA 200, segnale a ogni seduta) con commissioni di 0, 1 e 3 euro per ordine, 1.000 euro.

Produce in risultati/: metriche.json, prove.csv, griglia.csv, scimmie_finali.csv, strumenti_usati.json.
Regole: "bh" buy & hold; "t" trend. Quattro scenari: lordo e tre commissioni, questi con la tassa del 26%.
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


def punto_pari(fisse, dif):
    """Commissione (euro) in cui la differenza regola meno buy & hold passa da positiva a negativa, per interpolazione; None se non succede."""
    for a in range(len(fisse) - 1):
        if dif[a] > 0 >= dif[a + 1]:
            return fisse[a] + (fisse[a + 1] - fisse[a]) * dif[a] / (dif[a] - dif[a + 1])
    return None


def analizza(k_str, tk, nome, valuta, meta, fx_df):
    riga = [r for r in meta["strumenti"] if r["ticker"] == tk][0]
    if riga["stato"] != "ok":
        return None
    t = s.carica_csv(config.file_dati(tk))
    if valuta == "USD":
        if fx_df is None:
            return None
        df = s.prepara(t, fx_df, config.MEDIA_MOBILE)
    else:
        df = s.prepara(t, None, config.MEDIA_MOBILE)
    i0 = s.primo_indice(df)
    anni_test = (df.index[-1] - df.index[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        return None
    n = len(df)
    C, FX = df["Close"].to_numpy(float), df["fx"].to_numpy(float)
    anni_idx = df.index.year.to_numpy()
    sim, prove = {}, []
    for rid in ["bh", "t"]:
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, rid != "bh")
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
                      "quota_investito": r["quota_giorni_investito"]})
    griglia = []
    for f in config.GRIGLIA_FISSA:
        a = s.simula(df, i0, config.CAPITALE, f, 0.0, config.ALIQUOTA, True)["valore_finale_eur"]
        b = s.simula(df, i0, config.CAPITALE, f, 0.0, config.ALIQUOTA, False)["valore_finale_eur"]
        griglia.append({"strumento": tk, "commissione": f, "regola": a, "buy_hold": b})
    rng = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    a, b = s.blocchi(sim[("t", "lordo")])
    k, D = len(a), int((b - a).sum())
    scim = {}
    for sid, f1, p1, a1 in SCEN[1:]:
        fin = np.empty(config.N_SCIMMIE)
        for j in range(config.N_SCIMMIE):
            ia, ib = s.scimmia(k, D, N, rng)
            fin[j] = s.valuta_blocchi(C, FX, anni_idx, ia + i0, ib + i0, config.CAPITALE, f1, p1, a1)[0]
        scim[sid] = fin
    return dict(tk=tk, sl=config.slug(tk), nome=nome, df=df, i0=i0, sim=sim, prove=prove, griglia=griglia, scim=scim, k=k, anni=anni_test)


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
            print(f"{tk}: {r['anni']:.1f} anni; finale bh/trend per scenario: " +
                  ", ".join(f"{sid} {r['sim'][('bh', sid)]['valore_finale_eur']:.0f}/{r['sim'][('t', sid)]['valore_finale_eur']:.0f}" for sid in NOME_SCEN))
    if len(res) < 2:
        raise SystemExit("Troppo pochi strumenti utilizzabili.")
    cs = ["c0", "c1", "c2"]
    pg = {}
    for r in res:
        for sid in cs:
            reale = r["sim"][("t", sid)]["valore_finale_eur"]
            pg[(r["tk"], sid)] = (int((r["scim"][sid] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1)
    ph = holm(pg)
    npari = 0
    nvantaggio0 = 0
    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome}", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        for rid in ["bh", "t"]:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                if sid != "lordo":
                    reg(f"{sl}_{rid}_{sid}_costo", x["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                    reg(f"{sl}_{rid}_{sid}_tasse", x["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
        x = sm[("t", M)]
        reg(f"{sl}_t_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali della regola, {nome}")
        reg(f"{sl}_t_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / r["anni"], "num1", f"Ordini all'anno della regola, {nome}")
        reg(f"{sl}_t_quota", x["quota_giorni_investito"], "pct0", f"Quota di sedute investite dalla regola, {nome}")
        reg(f"{sl}_d03", sm[("t", "c0")]["cagr"] - sm[("t", "c2")]["cagr"], "pp2", f"Rendimento annuo netto della regola con 0 euro meno quello con 3 euro, in punti percentuali, {nome}")
        reg(f"{sl}_d01", sm[("t", "c0")]["cagr"] - sm[("t", "c1")]["cagr"], "pp2", f"Rendimento annuo netto della regola con 0 euro meno quello con 1 euro, in punti percentuali, {nome}")
        reg(f"{sl}_dtassa", sm[("t", "lordo")]["cagr"] - sm[("t", "c0")]["cagr"], "pp2", f"Rendimento annuo della regola lordo meno netto a commissione zero (effetto della sola tassa), punti percentuali, {nome}")
        reg(f"{sl}_dtassa_bh", sm[("bh", "lordo")]["cagr"] - sm[("bh", "c0")]["cagr"], "pp2", f"Rendimento annuo del buy & hold lordo meno netto a commissione zero (sola tassa), punti percentuali, {nome}")
        for sid in cs:
            reg(f"{sl}_dbh_{sid}", sm[("t", sid)]["cagr"] - sm[("bh", sid)]["cagr"], "pp2", f"Rendimento annuo netto della regola meno quello del buy & hold, scenario {NOME_SCEN[sid]}, punti percentuali, {nome}")
            reg(f"{sl}_gap_{sid}", sm[("bh", sid)]["cagr"] - sm[("t", sid)]["cagr"], "pp2", f"Rendimento annuo netto del buy & hold meno quello della regola, scenario {NOME_SCEN[sid]}, punti percentuali, {nome}")
            reg(f"{sl}_{sid}_sc_sopra", int((r["scim"][sid] >= sm[("t", sid)]["valore_finale_eur"]).sum()) / config.N_SCIMMIE, "pct1", f"Quota di scimmie che chiude sopra la regola, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
            reg(f"{sl}_ebh_{sid}_ass", sm[("bh", sid)]["valore_finale_eur"] - sm[("t", sid)]["valore_finale_eur"], "int", f"Euro finali del buy & hold meno quelli della regola, scenario {NOME_SCEN[sid]}, {nome}")
            reg(f"{sl}_ebh_{sid}", sm[("t", sid)]["valore_finale_eur"] - sm[("bh", sid)]["valore_finale_eur"], "int", f"Euro finali della regola meno quelli del buy & hold, scenario {NOME_SCEN[sid]}, {nome}")
            fin = r["scim"][sid]
            reg(f"{sl}_{sid}_sc_mediana", float(np.median(fin)), "int", f"Valore finale mediano delle scimmie, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{sid}_sc_p5", float(np.quantile(fin, 0.05)), "int", f"5° percentile del valore finale delle scimmie, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{sid}_sc_p95", float(np.quantile(fin, 0.95)), "int", f"95° percentile del valore finale delle scimmie, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{sid}_p_sc", pg[(r["tk"], sid)], "pval", f"p-value a una coda delle scimmie, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{sid}_p_holm", ph[(r["tk"], sid)], "pval", f"p-value delle scimmie con Holm sui 9 test, scenario {NOME_SCEN[sid]}, {nome}", "scimmie_finali.csv")
        reg(f"{sl}_periodi", r["k"], "int", f"Periodi investiti della regola, {nome}")
        fisse = [g["commissione"] for g in r["griglia"]]
        dif = [g["regola"] - g["buy_hold"] for g in r["griglia"]]
        pari = punto_pari(fisse, dif)
        r["pari"] = pari
        vant0 = dif[0] > 0
        nvantaggio0 += int(vant0)
        npari += int(vant0 and pari is not None and pari < 3.0)
        reg(f"{sl}_vantaggio0", int(vant0), "int", f"1 se a commissione zero la regola chiude sopra il buy & hold netto, 0 altrimenti, {nome}", "griglia.csv")
        if pari is not None:
            reg(f"{sl}_pari", pari, "num2", f"Commissione fissa per ordine (euro) oltre la quale la regola scende sotto il buy & hold netto, per interpolazione, {nome}", "griglia.csv")
        reg(f"{sl}_ha_pari", int(pari is not None), "int", f"1 se sulla griglia 0-10 euro la differenza regola meno buy & hold cambia di segno da positiva a negativa, {nome}", "griglia.csv")
        reg(f"{sl}_gr10_regola", r["griglia"][-1]["regola"], "int", f"Valore finale netto della regola con 10 euro per ordine, {nome}", "griglia.csv")
        reg(f"{sl}_gr10_bh", r["griglia"][-1]["buy_hold"], "int", f"Valore finale netto del buy & hold con 10 euro per ordine, {nome}", "griglia.csv")
    nS = len(res)
    reg("n_strumenti", nS, "int", "Strumenti utilizzabili", "config.py e dati/")
    reg("n_h1", sum((rr["sim"][("t", M)]["n_acquisti"] + rr["sim"][("t", M)]["n_vendite"]) / rr["anni"] >= 4 for rr in res), "int", "Strumenti in cui la regola fa almeno 4 ordini all'anno")
    reg("n_h2", sum(rr["sim"][("t", "c0")]["cagr"] - rr["sim"][("t", "c2")]["cagr"] >= 0.005 for rr in res), "int", "Strumenti in cui passare da 0 a 3 euro toglie almeno mezzo punto di rendimento annuo netto")
    reg("n_h3", sum(rr["sim"][("t", "c0")]["valore_finale_eur"] < rr["sim"][("bh", "c0")]["valore_finale_eur"] for rr in res), "int", "Strumenti in cui con commissione zero la regola chiude sotto il buy & hold netto")
    reg("n_h4", sum(rr["sim"][("t", "c2")]["valore_finale_eur"] < rr["sim"][("bh", "c2")]["valore_finale_eur"] for rr in res), "int", "Strumenti in cui con 3 euro la regola chiude sotto il buy & hold netto")
    reg("n_h5_den", nvantaggio0, "int", "Strumenti in cui a commissione zero la regola batte il buy & hold netto", "griglia.csv")
    reg("n_h5_num", npari, "int", "Tra questi, strumenti in cui il vantaggio sparisce prima dei 3 euro", "griglia.csv")
    reg("n_h6_signif", sum(v < 0.05 for v in ph.values()), "int", "Test sulle scimmie significativi dopo Holm (su 9)", "scimmie_finali.csv")
    reg("n_h6_grezzo", sum(v < 0.05 for v in pg.values()), "int", "Test sulle scimmie con p-value sotto 0,05 senza correzione (su 9)", "scimmie_finali.csv")
    reg("n_sotto_p5", sum(int(rr["sim"][("t", sid)]["valore_finale_eur"] < np.quantile(rr["scim"][sid], 0.05)) for rr in res for sid in cs), "int", "Casi (su 9) in cui la regola chiude sotto il quinto percentile delle scimmie", "scimmie_finali.csv")
    reg("n_prove", nS * 2 * 4 + nS * len(config.GRIGLIA_FISSA) * 2, "int", "Simulazioni complete: scenari principali più griglia delle commissioni", "config.py")
    reg("n_test", nS * 3, "int", "Test di ipotesi con Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per strumento e commissione", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py")
    reg("media_mobile", config.MEDIA_MOBILE, "int", "Sedute della media mobile", "config.py")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(rr["df"].index[-1].date()) for rr in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    pd.DataFrame([x for rr in res for x in rr["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    pd.DataFrame([x for rr in res for x in rr["griglia"]]).to_csv(config.RISULTATI / "griglia.csv", index=False, float_format="%.4f")
    pd.DataFrame({f"{rr['sl']}_{sid}": rr["scim"][sid] for rr in res for sid in cs}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "strumenti_usati.json").write_text(json.dumps([{"ticker": rr["tk"], "slug": rr["sl"], "nome": rr["nome"]} for rr in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
