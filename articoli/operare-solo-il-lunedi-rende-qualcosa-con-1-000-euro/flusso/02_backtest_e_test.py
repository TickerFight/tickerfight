"""Passo 2 - Posizione solo in un giorno della settimana, con 1.000 euro.

Produce in risultati/: metriche.json, prove.csv, scimmie_finali.csv, strumenti_usati.json.
Regole: "bh" buy & hold; "d0".."d4" = investito solo nella seduta del lunedì..venerdì (acquisto alla chiusura della seduta
precedente, vendita alla chiusura di quella del giorno). Quattro scenari: lordo e tre commissioni (con tassa 26%).
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
RID = [x for x, _, _ in config.GIORNI]
NOME_G = {x: n for x, n, _ in config.GIORNI}


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


def obiettivo(idx: pd.DatetimeIndex, giorno: int) -> np.ndarray:
    """True alla chiusura della seduta che precede una seduta del giorno scelto: si compra lì e si vende alla chiusura dopo."""
    wd = idx.dayofweek.to_numpy()
    ob = np.zeros(len(idx), bool)
    ob[:-1] = wd[1:] == giorno
    return ob


def analizza(k_str, tk, nome, valuta, meta, fx_df):
    riga = [r for r in meta["strumenti"] if r["ticker"] == tk][0]
    if riga["stato"] != "ok":
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
        return None
    n = len(df)
    C, FX = df["Close"].to_numpy(float), df["fx"].to_numpy(float)
    anni_idx = df.index.year.to_numpy()
    wd = df.index.dayofweek.to_numpy()
    rend = np.r_[np.nan, (C[1:] / FX[1:]) / (C[:-1] / FX[:-1]) - 1]       # rendimento in euro da chiusura a chiusura
    sim, prove = {}, []
    for rid, _, g in config.GIORNI:
        ob = obiettivo(df.index, g)
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, True, obiettivo=ob)
    for sid, f, p, al in SCEN:
        sim[("bh", sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, False)
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "commissioni": r["commissioni_eur"], "tasse": r["tasse_eur"],
                      "quota_investito": r["quota_giorni_investito"]})
    rng = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    scim = {}
    for rid in RID:
        a, b = s.blocchi(sim[(rid, "lordo")])
        k, D = len(a), int((b - a).sum())
        fin = np.empty(config.N_SCIMMIE)
        for j in range(config.N_SCIMMIE):
            ia, ib = s.scimmia(k, D, N, rng)
            fin[j] = s.valuta_blocchi(C, FX, anni_idx, ia + i0, ib + i0, config.CAPITALE, 0.0, 0.0, 0.0)[0]
        scim[rid] = {"k": k, "finali": fin}
    medie = {rid: float(np.nanmean(rend[i0:][wd[i0:] == g])) for rid, _, g in config.GIORNI}
    media_tutti = float(np.nanmean(rend[i0:]))
    return dict(tk=tk, sl=config.slug(tk), nome=nome, df=df, i0=i0, sim=sim, prove=prove, scim=scim, anni=anni_test,
                medie=medie, media_tutti=media_tutti)


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
            print(f"{tk}: {r['anni']:.1f} anni; lordo bh {r['sim'][('bh','lordo')]['valore_finale_eur']:.0f}, " +
                  ", ".join(f"{x} {r['sim'][(x, 'lordo')]['valore_finale_eur']:.0f}" for x in RID))
    if len(res) < 2:
        raise SystemExit("Troppo pochi strumenti utilizzabili.")
    pg = {}
    for r in res:
        for rid in RID:
            reale = r["sim"][(rid, "lordo")]["valore_finale_eur"]
            pg[(r["tk"], rid)] = (int((r["scim"][rid]["finali"] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1)
    ph = holm(pg)
    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome}", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        reg(f"{sl}_media_tutti", r["media_tutti"], "pct2", f"Rendimento medio di una seduta qualunque (tutti i giorni), {nome}")
        for rid in ["bh"] + RID:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                if sid != "lordo":
                    reg(f"{sl}_{rid}_{sid}_costo", x["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                    reg(f"{sl}_{rid}_{sid}_tasse", x["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
            x = sm[(rid, M)]
            xl = sm[(rid, "lordo")]
            reg(f"{sl}_{rid}_ordini_anno", (xl["n_acquisti"] + xl["n_vendite"]) / r["anni"], "num1", f"Ordini all'anno, senza costi che fermino la regola ({rid}), {nome}")
            reg(f"{sl}_{rid}_quota", sm[(rid, "lordo")]["quota_giorni_investito"], "pct0", f"Quota di sedute investite ({rid}), {nome}")
            eq = x["equity"]
            morto = np.flatnonzero(eq <= 2 * config.SCENARI_COSTO[1][1]) if rid != "bh" else []
            vita = (r["df"].index[r["i0"] + int(morto[0])] - r["df"].index[r["i0"]]).days / 365.25 if len(morto) else r["anni"]
            reg(f"{sl}_{rid}_anni_vita", vita, "num1", f"Anni dopo i quali il capitale scende sotto quattro euro, cioè non basta più a pagare i costi di un ciclo (2 euro, {rid}); se non succede, gli anni del test, {nome}")
            reg(f"{sl}_{rid}_esaurito", int(len(morto) > 0), "int", f"1 se il capitale scende sotto quattro euro con 2 euro a ordine ({rid}), {nome}")
        for rid in RID:
            fin = r["scim"][rid]["finali"]
            reg(f"{sl}_{rid}_media", r["medie"][rid], "pct2", f"Rendimento medio delle sedute di {NOME_G[rid]} (da chiusura a chiusura), {nome}")
            reg(f"{sl}_{rid}_sc_mediana", float(np.median(fin)), "int", f"Valore finale lordo mediano delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p5", float(np.quantile(fin, 0.05)), "int", f"5° percentile del valore finale lordo delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_p95", float(np.quantile(fin, 0.95)), "int", f"95° percentile del valore finale lordo delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_sc", pg[(r["tk"], rid)], "pval", f"p-value a una coda delle scimmie ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_holm", ph[(r["tk"], rid)], "pval", f"p-value delle scimmie con Holm sui 15 test ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_periodi", r["scim"][rid]["k"], "int", f"Sedute investite ({rid}), {nome}")
        mig = max(RID, key=lambda x: sm[(x, "lordo")]["valore_finale_eur"])
        r["mig"] = mig
        reg(f"{sl}_migliore", NOME_G[mig], "testo", f"Giorno con il valore finale lordo più alto, {nome}")
    nS = len(res)
    reg("n_strumenti", nS, "int", "Strumenti utilizzabili", "config.py e dati/")
    reg("n_h1", sum(ph[(r["tk"], "d0")] >= 0.05 for r in res), "int", "Strumenti in cui il lunedì non batte le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_h2_signif", sum(v < 0.05 for v in ph.values()), "int", "Test sulle scimmie significativi dopo Holm (su 15, tutti i giorni)", "scimmie_finali.csv")
    reg("n_h2_grezzo", sum(v < 0.05 for v in pg.values()), "int", "Test sulle scimmie con p-value sotto 0,05 senza correzione (su 15)", "scimmie_finali.csv")
    reg("n_h3_lunedi", sum(r["sim"][("d0", M)]["valore_finale_eur"] <= 2 * config.SCENARI_COSTO[1][1] for r in res), "int", "Strumenti in cui il capitale scende sotto quattro euro con la regola del lunedì e 2 euro a ordine")
    reg("n_h3_tutti", sum(int(r["sim"][(x, M)]["valore_finale_eur"] <= 2 * config.SCENARI_COSTO[1][1]) for r in res for x in RID), "int", "Casi (su 15) in cui il capitale scende sotto quattro euro con 2 euro a ordine")
    reg("n_h4", sum(r["sim"][("d0", "c2")]["cagr"] < 0 for r in res), "int", "Strumenti in cui la regola del lunedì con commissione 0,1% ha rendimento annuo negativo")
    reg("n_h5_batte", sum(int(r["sim"][(x, "c0")]["valore_finale_eur"] > r["sim"][("bh", "c0")]["valore_finale_eur"]) for r in res for x in RID), "int", "Casi (su 15) in cui un giorno batte il buy & hold netto con commissione zero e tassa")
    reg("n_h6_giorni_diversi", len({r["mig"] for r in res}), "int", "Giorni migliori diversi tra gli strumenti")
    reg("n_prove", nS * 6 * 4, "int", "Simulazioni complete: strumenti x (buy & hold + cinque giorni) x scenari", "config.py")
    reg("n_test", nS * 5, "int", "Test di ipotesi con Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie per strumento e giorno", "config.py")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine, scenario principale", "config.py")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale, terzo scenario", "config.py")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["df"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")
    pd.DataFrame([x for r in res for x in r["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    pd.DataFrame({f"{r['sl']}_{rid}": r["scim"][rid]["finali"] for r in res for rid in RID}).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "strumenti_usati.json").write_text(json.dumps([{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
