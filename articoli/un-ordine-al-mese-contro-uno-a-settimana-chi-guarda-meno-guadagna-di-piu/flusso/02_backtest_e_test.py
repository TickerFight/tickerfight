"""Passo 2 - La stessa regola di trend (SMA 200) valutata ogni seduta, ogni settimana, ogni mese, con 1.000 euro.

Produce in risultati/: metriche.json, prove.csv, scimmie_finali.csv, strumenti_usati.json.
Regole: "bh" buy & hold; "g", "s", "m" = trend decisa ogni seduta / ultima seduta della settimana / ultima del mese.
Quattro scenari: lordo e tre commissioni, questi con la tassa del 26%.
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
RID = [x for x, _ in config.FREQUENZE]


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


def decisioni(idx: pd.DatetimeIndex, freq: str) -> np.ndarray:
    """True nelle sedute in cui si guarda il segnale: tutte, l'ultima di ogni settimana, l'ultima di ogni mese."""
    n = len(idx)
    if freq == "g":
        return np.ones(n, bool)
    chiave = idx.to_period("W") if freq == "s" else idx.to_period("M")
    k = np.asarray(chiave.astype(str))
    dec = np.zeros(n, bool)
    dec[:-1] = k[1:] != k[:-1]
    dec[-1] = True
    return dec


def obiettivo(seg: np.ndarray, dec: np.ndarray, i0: int) -> np.ndarray:
    """Posizione voluta alla seduta i: il segnale dell'ultima seduta di decisione precedente a i (alla prima seduta, quello di i-1)."""
    n = len(seg)
    ob = np.zeros(n, bool)
    corrente = bool(seg[i0 - 1])
    for i in range(i0, n):
        if dec[i - 1] and i - 1 >= i0:
            corrente = bool(seg[i - 1])
        ob[i] = corrente
    return ob


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
    SEG = df["segnale"].to_numpy(bool)
    anni_idx = df.index.year.to_numpy()
    sim, prove = {}, []
    for rid in ["bh"] + RID:
        ob = None if rid == "bh" else obiettivo(SEG, decisioni(df.index, rid), i0)
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, rid != "bh", obiettivo=ob)
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
                      "quota_investito": r["quota_giorni_investito"]})
    rng = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    f1, p1, a1 = [(f, p, al) for sid, f, p, al in SCEN if sid == M][0]
    scim = {}
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
    pg = {}
    for r in res:
        for rid in RID:
            reale = r["sim"][(rid, M)]["valore_finale_eur"]
            pg[(r["tk"], rid)] = (int((r["scim"][rid]["finali"] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1)
    ph = holm(pg)
    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome}", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        for rid in ["bh"] + RID:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                if sid != "lordo":
                    reg(f"{sl}_{rid}_{sid}_costo", x["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                    reg(f"{sl}_{rid}_{sid}_tasse", x["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
            x = sm[(rid, M)]
            reg(f"{sl}_{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali ({rid}), {nome}")
            reg(f"{sl}_{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / r["anni"], "num1", f"Ordini all'anno ({rid}), {nome}")
            reg(f"{sl}_{rid}_quota", x["quota_giorni_investito"], "pct0", f"Quota di sedute investite ({rid}), {nome}")
        for sid in NOME_SCEN:
            reg(f"{sl}_dsm_{sid}", sm[("s", sid)]["cagr"] - sm[("m", sid)]["cagr"], "pp1", f"Rendimento annuo della frequenza settimanale meno quello della mensile, scenario {NOME_SCEN[sid]}, in punti percentuali, {nome}")
        reg(f"{sl}_rapporto_ordini", (sm[("s", M)]["n_acquisti"] + sm[("s", M)]["n_vendite"]) / (sm[("m", M)]["n_acquisti"] + sm[("m", M)]["n_vendite"]), "num1", f"Quante volte gli ordini della frequenza settimanale superano quelli della mensile, {nome}")
        for rid in RID:
            fin = r["scim"][rid]["finali"]
            reg(f"{sl}_{rid}_sc_mediana", float(np.median(fin)), "int", f"Valore finale mediano delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p5", float(np.quantile(fin, 0.05)), "int", f"5° percentile del valore finale delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p95", float(np.quantile(fin, 0.95)), "int", f"95° percentile del valore finale delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_sc", pg[(r["tk"], rid)], "pval", f"p-value a una coda delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_holm", ph[(r["tk"], rid)], "pval", f"p-value delle scimmie con Holm sui 9 test ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_periodi", r["scim"][rid]["k"], "int", f"Periodi investiti della regola ({rid}), {nome}")
    nS = len(res)
    fz = lambda rr, a, b, sid: rr["sim"][(a, sid)]["cagr"] - rr["sim"][(b, sid)]["cagr"]
    reg("n_strumenti", nS, "int", "Strumenti utilizzabili", "config.py e dati/")
    reg("n_h1", sum(rr["sim"][("s", M)]["n_acquisti"] + rr["sim"][("s", M)]["n_vendite"] >= 2 * (rr["sim"][("m", M)]["n_acquisti"] + rr["sim"][("m", M)]["n_vendite"]) for rr in res), "int", "Strumenti in cui la frequenza settimanale fa almeno il doppio degli ordini della mensile")
    reg("n_h2", sum(abs(fz(rr, "s", "m", "lordo")) < 0.01 for rr in res), "int", "Strumenti in cui la differenza lorda di rendimento annuo tra settimanale e mensile è sotto un punto")
    reg("n_h3", sum(fz(rr, "m", "s", M) > 0 for rr in res), "int", "Strumenti in cui la mensile rende più della settimanale, netto 2 euro")
    reg("n_h4", sum(abs(fz(rr, "s", "m", "c2")) < abs(fz(rr, "s", "m", "c1")) for rr in res), "int", "Strumenti in cui la differenza settimanale-mensile con 0,1% è più piccola in valore assoluto di quella con 2 euro")
    reg("n_h5", sum(all(rr["sim"][(x, M)]["valore_finale_eur"] < rr["sim"][("bh", M)]["valore_finale_eur"] for x in RID) for rr in res), "int", "Strumenti in cui nessuna delle tre frequenze batte il buy & hold netto (2 euro)")
    reg("n_h5_g", sum(rr["sim"][("g", M)]["valore_finale_eur"] < rr["sim"][("bh", M)]["valore_finale_eur"] for rr in res), "int", "Strumenti in cui la regola giornaliera chiude sotto il buy & hold netto (2 euro)")
    reg("n_h5_s", sum(rr["sim"][("s", M)]["valore_finale_eur"] < rr["sim"][("bh", M)]["valore_finale_eur"] for rr in res), "int", "Strumenti in cui la regola settimanale chiude sotto il buy & hold netto (2 euro)")
    reg("n_h5_m", sum(rr["sim"][("m", M)]["valore_finale_eur"] < rr["sim"][("bh", M)]["valore_finale_eur"] for rr in res), "int", "Strumenti in cui la regola mensile chiude sotto il buy & hold netto (2 euro)")
    reg("n_h6_signif", sum(v < 0.05 for v in ph.values()), "int", "Test sulle scimmie significativi dopo Holm (su 9)", "scimmie_finali.csv")
    reg("n_h6_grezzo", sum(v < 0.05 for v in pg.values()), "int", "Test sulle scimmie con p-value sotto 0,05 senza correzione (su 9)", "scimmie_finali.csv")
    reg("n_sotto_p5", sum(int(rr["sim"][(x, M)]["valore_finale_eur"] < np.quantile(rr["scim"][x]["finali"], 0.05)) for rr in res for x in RID), "int", "Casi (su 9) in cui la regola chiude sotto il quinto percentile delle scimmie", "scimmie_finali.csv")
    reg("n_prove", nS * 4 * 4, "int", "Simulazioni complete: strumenti x (buy & hold + tre frequenze) x scenari", "config.py")
    reg("n_test", nS * 3, "int", "Test di ipotesi con Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per strumento e frequenza", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine, scenario principale", "config.py")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale, terzo scenario", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py")
    reg("media_mobile", config.MEDIA_MOBILE, "int", "Sedute della media mobile", "config.py")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(rr["df"].index[-1].date()) for rr in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    pd.DataFrame([x for rr in res for x in rr["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    pd.DataFrame({f"{rr['sl']}_{rid}": rr["scim"][rid]["finali"] for rr in res for rid in RID}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "strumenti_usati.json").write_text(json.dumps([{"ticker": rr["tk"], "slug": rr["sl"], "nome": rr["nome"]} for rr in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
