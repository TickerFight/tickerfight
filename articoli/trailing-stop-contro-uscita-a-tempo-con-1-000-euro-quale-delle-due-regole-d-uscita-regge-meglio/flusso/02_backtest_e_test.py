"""Passo 2 - Trailing stop contro uscita a tempo, con le condizioni di chi parte con 1.000 euro.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv              per strumento, regola e scenario: valore finale, rendimento annuo, ordini, costi, tasse, perdita massima
  periodi.csv            per ogni periodo investito delle due regole principali: date, durata, motivo dell'uscita, rendimento lordo
  scimmie_finali.csv     valore finale netto di ogni scimmia (scenario principale), per strumento e regola
  curve.csv              valore giorno per giorno (una seduta su cinque) di buy & hold, uscita di trend, trailing stop e uscita a tempo

Regole: buy & hold; "tr" (investito se la chiusura sta sopra la media a 200 sedute); "ts10" = si entra sul trend e si esce con
trailing stop del 10%; "tt60" = si entra sul trend e si esce dopo 60 sedute; "ts5", "ts15", "tt20", "tt120" = controlli.
Quattro scenari: lordo (nessun costo, nessuna tassa) e tre scenari di commissione, tutti con la tassa del 26%.
Scimmia: stesso numero di periodi investiti e stessa durata totale della regola, piazzati a caso senza sovrapposizioni;
gli stessi costi e le stesse tasse, passati dallo stesso contabile.
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
ID_SCEN_PRINC = f"c{config.SCENARIO_PRINCIPALE}"
NOME_SCEN = {f"c{k}": nome for k, (nome, _, _) in enumerate(config.SCENARI_COSTO)}
NOME_SCEN["lordo"] = "lordo"


REGOLE = {"bh": (None, None), "tr": (None, None)}
for x in (config.TRAIL,) + tuple(config.TRAIL_CONTROLLO):
    REGOLE[f"ts{int(round(x * 100))}"] = (x, None)
for x in (config.TEMPO,) + tuple(config.TEMPO_CONTROLLO):
    REGOLE[f"tt{x}"] = (None, x)
ID_TS = f"ts{int(round(config.TRAIL * 100))}"
ID_TT = f"tt{config.TEMPO}"
IDS_TS = sorted((r for r in REGOLE if r.startswith("ts")), key=lambda r: int(r[2:]))
IDS_TT = sorted((r for r in REGOLE if r.startswith("tt")), key=lambda r: int(r[2:]))


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


def analizza(k_str: int, tk: str, nome: str, valuta: str, meta: dict, fx_df) -> dict | None:
    riga = [r for r in meta["strumenti"] if r["ticker"] == tk][0]
    if riga["stato"] != "ok":
        print(f"{tk}: scartato, {riga['stato']}")
        return None
    t = s.carica_csv(config.file_dati(tk))
    if valuta == "USD":
        if fx_df is None:
            print(f"{tk}: scartato, manca il cambio")
            return None
        df = s.prepara(t, fx_df, config.MEDIA_MOBILE)
    else:
        df = s.prepara(t, None, config.MEDIA_MOBILE)
    if len(df) < config.MEDIA_MOBILE + 50:
        return None
    i0 = s.primo_indice(df)
    anni_test = (df.index[-1] - df.index[i0]).days / 365.25
    if anni_test < config.STORIA_MINIMA_ANNI:
        print(f"{tk}: scartato, solo {anni_test:.1f} anni di test")
        return None
    n = len(df)
    C, FX = df["Close"].to_numpy(float), df["fx"].to_numpy(float)
    anni_idx = df.index.year.to_numpy()

    # --- Tutte le simulazioni (regola x scenario) --------------------------------------------------------------------
    sim = {}
    for rid, (tr_, tp_) in REGOLE.items():
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, rid != "bh", trail=tr_, tempo=tp_)
    prove = []
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "n_uscite_regola": r["n_uscite_regola"], "commissioni": r["commissioni_eur"],
                      "tasse": r["tasse_eur"], "perdita_massima": r["perdita_massima"], "quota_investito": r["quota_giorni_investito"]})

    # --- Periodi investiti delle due regole principali ---------------------------------------------------------------------
    righe = []
    dur, rend = {}, {}
    for rid in (ID_TS, ID_TT):
        ops = sim[(rid, "lordo")]["operazioni"]
        dur[rid], rend[rid] = [], []
        for j in range(0, len(ops) - 1, 2):
            acq, ven = ops[j], ops[j + 1]
            d_ = ven["i"] - acq["i"]
            rr = ven["prezzo_eur"] / acq["prezzo_eur"] - 1
            dur[rid].append(d_)
            rend[rid].append(rr)
            righe.append({"strumento": tk, "regola": rid, "acquisto": acq["data"], "vendita": ven["data"], "sedute": d_,
                          "motivo": ven["motivo"], "rendimento_lordo": rr})
    per_df = pd.DataFrame(righe)
    quota_ts_lunghi = float(np.mean([d_ > config.TEMPO for d_ in dur[ID_TS]])) if dur[ID_TS] else float("nan")
    quota_tt_perdita = float(np.mean([x < 0 for x in rend[ID_TT]])) if rend[ID_TT] else float("nan")
    quota_ts_perdita = float(np.mean([x < 0 for x in rend[ID_TS]])) if rend[ID_TS] else float("nan")

    # --- Le scimmie (rispetto alla regola di trend e alla regola con lo stop del 5%) --------------------------------------
    rng_s = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    scim = {}
    for rid in (ID_TS, ID_TT):
        a, b = s.blocchi(sim[(rid, "lordo")])
        k, D = len(a), int((b - a).sum())
        if k < 2:
            scim[rid] = None
            continue
        finali = {sid: np.empty(config.N_SCIMMIE) for sid in NOME_SCEN if sid != "lordo"}
        for j in range(config.N_SCIMMIE):
            ia, ib = s.scimmia(k, D, N, rng_s)
            for sid, f, p, al in SCEN[1:]:
                finali[sid][j] = s.valuta_blocchi(C, FX, anni_idx, ia + i0, ib + i0, config.CAPITALE, f, p, al)[0]
        scim[rid] = {"k": k, "D": D, "finali": finali}

    # --- Bootstrap a blocchi: trailing stop contro uscita a tempo (rendimento giornaliero netto, scenario principale)
    e_ts = sim[(ID_TS, ID_SCEN_PRINC)]["equity"]
    e_tt = sim[(ID_TT, ID_SCEN_PRINC)]["equity"]
    e_tr = sim[("tr", ID_SCEN_PRINC)]["equity"]
    d = (e_ts[1:] / e_ts[:-1] - 1) - (e_tt[1:] / e_tt[:-1] - 1)
    rng_b = np.random.default_rng([config.SEME, k_str, 2])
    medie = bootstrap_blocchi(d - d.mean(), rng_b)             # distribuzione sotto l'ipotesi nulla (differenza media zero)
    osservata = float(d.mean())
    p_boot = (int((np.abs(medie) >= abs(osservata)).sum()) + 1) / (config.N_BOOTSTRAP + 1)
    medie_ic = bootstrap_blocchi(d, np.random.default_rng([config.SEME, k_str, 3]))
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(medie_ic, [alfa, 1 - alfa])

    camp = np.arange(0, N, 5)
    curva = pd.DataFrame({"strumento": tk, "data": df.index[i0:][camp],
                          "bh": sim[("bh", ID_SCEN_PRINC)]["equity"][camp], "tr": e_tr[camp], "ts": e_ts[camp], "tt": e_tt[camp]})
    return dict(tk=tk, sl=config.slug(tk), nome=nome, valuta=valuta, df=df, i0=i0, sim=sim, prove=prove,
                per=per_df, dur=dur, rend=rend, quota_ts_lunghi=quota_ts_lunghi, quota_tt_perdita=quota_tt_perdita,
                quota_ts_perdita=quota_ts_perdita, scim=scim, p_boot=p_boot, diff_ann=osservata * 252, lo=float(lo) * 252, hi=float(hi) * 252, curva=curva, anni=anni_test)


def main() -> None:
    global META
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    META = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    cambio_ok = any(r["ticker"] == config.TICKER_CAMBIO and r["stato"] == "ok" for r in META["strumenti"])
    fx_df = s.carica_csv(config.file_dati(config.TICKER_CAMBIO)) if cambio_ok else None
    res = []
    for k, (tk, nome, valuta) in enumerate(config.STRUMENTI):
        r = analizza(k, tk, nome, valuta, META, fx_df)
        if r:
            res.append(r)
            sm = r["sim"]
            print(f"{tk}: {r['anni']:.1f} anni; netto ({NOME_SCEN[ID_SCEN_PRINC]}) bh {sm[('bh', ID_SCEN_PRINC)]['valore_finale_eur']:.0f}, "
                  f"trend {sm[('tr', ID_SCEN_PRINC)]['valore_finale_eur']:.0f}, trailing {sm[(ID_TS, ID_SCEN_PRINC)]['valore_finale_eur']:.0f}, "
                  f"a tempo {sm[(ID_TT, ID_SCEN_PRINC)]['valore_finale_eur']:.0f}")
    if len(res) < 2:
        raise SystemExit("Troppo pochi strumenti utilizzabili.")

    RP = (ID_TS, ID_TT)
    ph_boot = holm({r["tk"]: r["p_boot"] for r in res})
    ph_sc = {rid: holm({r["tk"]: (int((r["scim"][rid]["finali"][ID_SCEN_PRINC] >= r["sim"][(rid, ID_SCEN_PRINC)]["valore_finale_eur"]).sum()) + 1)
                        / (config.N_SCIMMIE + 1) for r in res if r["scim"][rid]}) for rid in RP}
    M = ID_SCEN_PRINC
    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome} (dopo le 200 sedute della media)", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        reg(f"{sl}_diff_ann", r["diff_ann"], "pp1", f"Differenza media annualizzata del rendimento netto giornaliero tra trailing stop e uscita a tempo, in punti percentuali, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_diff_lo", r["lo"], "pp1", f"Estremo inferiore dell'intervallo bootstrap a blocchi della differenza annualizzata, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_diff_hi", r["hi"], "pp1", f"Estremo superiore dell'intervallo bootstrap a blocchi della differenza annualizzata, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_p_boot", r["p_boot"], "pval", f"p-value a due code: differenza media giornaliera tra trailing stop e uscita a tempo, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_p_boot_holm", ph_boot[r["tk"]], "pval", f"p-value del bootstrap corretto con il metodo di Holm sugli strumenti, {nome}", "bootstrap a blocchi")
        for rid in (ID_TS, ID_TT):
            d_ = r["dur"][rid]
            reg(f"{sl}_{rid}_periodi", len(d_), "int", f"Periodi investiti ({rid}), {nome}", "periodi.csv")
            reg(f"{sl}_{rid}_durata_mediana", float(np.median(d_)), "int", f"Durata mediana di un periodo investito, in sedute ({rid}), {nome}", "periodi.csv")
            reg(f"{sl}_{rid}_durata_max", float(np.max(d_)), "int", f"Periodo investito più lungo, in sedute ({rid}), {nome}", "periodi.csv")
            reg(f"{sl}_{rid}_quota_perdite", float(np.mean([x < 0 for x in r["rend"][rid]])), "pct0", f"Quota dei periodi investiti chiusi in perdita, al lordo di costi e tasse ({rid}), {nome}", "periodi.csv")
        reg(f"{sl}_ts_quota_oltre_tempo", r["quota_ts_lunghi"], "pct0", f"Quota dei periodi del trailing stop più lunghi di {config.TEMPO} sedute, {nome}", "periodi.csv")
        for rid in REGOLE:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
            x = sm[(rid, M)]
            reg(f"{sl}_{rid}_dd", -x["perdita_massima"], "pct0", f"Perdita massima dal picco ({rid}), {nome}")
            reg(f"{sl}_{rid}_quota", x["quota_giorni_investito"], "pct0", f"Quota di sedute investite ({rid}), {nome}")
            if rid != "bh":
                reg(f"{sl}_{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali, acquisti e vendite ({rid}), {nome}")
                reg(f"{sl}_{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / r["anni"], "num1", f"Ordini all'anno ({rid}), {nome}")
            for sid in NOME_SCEN:
                if sid == "lordo":
                    continue
                reg(f"{sl}_{rid}_{sid}_costo", sm[(rid, sid)]["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_tasse", sm[(rid, sid)]["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
        for rid in RP:
            sc = r["scim"][rid]
            if not sc:
                continue
            fin = sc["finali"]
            for sid in NOME_SCEN:
                if sid == "lordo":
                    continue
                reale = sm[(rid, sid)]["valore_finale_eur"]
                reg(f"{sl}_{rid}_{sid}_sc_mediana", float(np.median(fin[sid])), "int", f"Valore finale mediano delle scimmie ({rid}, scenario {NOME_SCEN[sid]}), {nome}", "scimmie_finali.csv")
                reg(f"{sl}_{rid}_{sid}_p_sc", (int((fin[sid] >= reale).sum()) + 1) / (config.N_SCIMMIE + 1), "pval", f"p-value a una coda: quota di scimmie che fanno almeno quanto la regola ({rid}, scenario {NOME_SCEN[sid]}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_sotto", float((fin[M] < sm[(rid, M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la regola ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_sopra_bh", float((fin[M] >= sm[("bh", M)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che fanno almeno quanto il buy & hold ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_holm", ph_sc[rid][r["tk"]], "pval", f"p-value delle scimmie corretto con Holm sugli strumenti ({rid}, scenario principale), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_periodi", sc["k"], "int", f"Periodi investiti della regola ({rid}), uguali per ogni scimmia, {nome}")

    # --- Numeri complessivi, per le cinque ipotesi --------------------------------------------------------------------
    n_str = len(res)
    def o_(r, rid):
        x = r["sim"][(rid, M)]
        return x["n_acquisti"] + x["n_vendite"]
    reg("n_strumenti", n_str, "int", "Strumenti utilizzabili nel test", "config.py, STRUMENTI e dati/")
    reg("n_scartati", len(config.STRUMENTI) - n_str, "int", "Strumenti scartati (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_dd_ts_minore", sum(r["sim"][(ID_TS, M)]["perdita_massima"] > r["sim"][(ID_TT, M)]["perdita_massima"] for r in res), "int", "Strumenti in cui il trailing stop ha una perdita massima più piccola dell'uscita a tempo")
    reg("n_cagr_ts_sopra", sum(r["sim"][(ID_TS, M)]["cagr"] > r["sim"][(ID_TT, M)]["cagr"] for r in res), "int", "Strumenti in cui il trailing stop rende di più, netto, dell'uscita a tempo (scenario principale)")
    reg("n_ordini_ts_meno", sum(o_(r, ID_TS) < o_(r, ID_TT) for r in res), "int", "Strumenti in cui il trailing stop dà meno ordini dell'uscita a tempo")
    reg("n_boot_signif", sum(ph_boot[r["tk"]] < 0.05 for r in res), "int", "Strumenti in cui la differenza tra le due regole è significativa dopo Holm", "bootstrap a blocchi")
    reg("n_boot_signif_grezzo", sum(r["p_boot"] < 0.05 for r in res), "int", "Strumenti in cui la differenza ha p-value sotto il cinque per cento senza correzione", "bootstrap a blocchi")
    reg("n_ts_batte_scimmie", sum(ph_sc[ID_TS].get(r["tk"], 1.0) < 0.05 for r in res), "int", "Strumenti in cui il trailing stop batte le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_tt_batte_scimmie", sum(ph_sc[ID_TT].get(r["tk"], 1.0) < 0.05 for r in res), "int", "Strumenti in cui l'uscita a tempo batte le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_ts_sotto_bh", sum(r["sim"][(ID_TS, M)]["valore_finale_eur"] < r["sim"][("bh", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui il trailing stop chiude sotto il buy & hold, scenario principale")
    reg("n_tt_sotto_bh", sum(r["sim"][(ID_TT, M)]["valore_finale_eur"] < r["sim"][("bh", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui l'uscita a tempo chiude sotto il buy & hold, scenario principale")
    reg("n_ts_sotto_tr", sum(r["sim"][(ID_TS, M)]["valore_finale_eur"] < r["sim"][("tr", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui il trailing stop chiude sotto l'uscita di trend, scenario principale")
    reg("n_tt_sotto_tr", sum(r["sim"][(ID_TT, M)]["valore_finale_eur"] < r["sim"][("tr", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui l'uscita a tempo chiude sotto l'uscita di trend, scenario principale")
    reg("n_prove", len(res) * len(REGOLE) * len(NOME_SCEN), "int", "Simulazioni complete eseguite: strumenti x regole x scenari (lordo compreso)", "config.py")
    reg("n_regole", len(REGOLE), "int", "Regole provate: buy & hold, uscita di trend, tre trailing stop e tre uscite a tempo", "config.py")
    reg("n_test_ipotesi", 3 * n_str, "int", "Test di ipotesi eseguiti (scimmie sulle due regole e bootstrap) con correzione di Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni strumento e regola", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.LUNGHEZZA_BLOCCO, "int", "Sedute per blocco nel bootstrap", "config.py, LUNGHEZZA_BLOCCO")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine nello scenario principale, in euro", "config.py, SCENARI_COSTO")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale all'importo nel terzo scenario", "config.py, SCENARI_COSTO")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("media_mobile", config.MEDIA_MOBILE, "int", "Sedute della media mobile", "config.py, MEDIA_MOBILE")
    reg("trail", config.TRAIL, "pct0", "Soglia del trailing stop principale", "config.py, TRAIL")
    reg("tempo", config.TEMPO, "int", "Sedute dell'uscita a tempo principale", "config.py, TEMPO")
    for x in config.TRAIL_CONTROLLO:
        reg(f"trail_{int(round(x * 100))}", x, "pct0", "Soglia di controllo del trailing stop", "config.py, TRAIL_CONTROLLO")
    for x in config.TEMPO_CONTROLLO:
        reg(f"tempo_{x}", x, "int", "Sedute di controllo dell'uscita a tempo", "config.py, TEMPO_CONTROLLO")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["df"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")

    # --- File di supporto ---------------------------------------------------------------------------------------------
    pd.DataFrame([x for r in res for x in r["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    pd.concat([r["per"] for r in res]).to_csv(config.RISULTATI / "periodi.csv", index=False, float_format="%.4f")
    pd.concat([r["curva"] for r in res]).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.4f")
    colonne = {}
    for r in res:
        for rid in RP:
            if r["scim"][rid]:
                colonne[f"{r['sl']}_{rid}"] = r["scim"][rid]["finali"][M]
    pd.DataFrame(colonne).to_csv(config.RISULTATI / "scimmie_finali.csv", index=False, float_format="%.4f")
    (config.RISULTATI / "strumenti_usati.json").write_text(json.dumps(
        [{"ticker": r["tk"], "slug": r["sl"], "nome": r["nome"]} for r in res], ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
