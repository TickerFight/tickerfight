"""Passo 2 - Regola di trend con e senza stop loss, con le condizioni di chi parte con 1.000 euro.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine di calcolo
  prove.csv              per strumento, regola e scenario: valore finale, rendimento annuo, ordini, costi, tasse, perdita massima
  stop_eventi.csv        per ogni stop scattato: data di vendita, prezzo, data e prezzo del rientro
  scimmie_finali.csv     valore finale netto di ogni scimmia (scenario principale), per strumento e regola
  curve.csv              valore giorno per giorno (una seduta su cinque) di buy & hold, trend e trend con stop

Regole: buy & hold (compra il primo giorno e tiene); "trend" (investito se la chiusura sta sopra la media a 200 sedute);
"s5" = trend con stop loss al 5%; "s3", "s8", "s10" = controlli con altre soglie. Quattro scenari: lordo (nessun costo,
nessuna tassa) e tre scenari di commissione, tutti con la tassa del 26%.
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


def id_regola(soglia: float) -> str:
    return f"s{int(round(soglia * 100))}"


REGOLE = {"bh": None, "tr": None, id_regola(config.STOP): config.STOP}
for x in config.SOGLIE_CONTROLLO:
    REGOLE[id_regola(x)] = x
ID_STOP = id_regola(config.STOP)


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
    for rid, stop in REGOLE.items():
        for sid, f, p, al in SCEN:
            sim[(rid, sid)] = s.simula(df, i0, config.CAPITALE, f, p, al, rid != "bh", stop=stop)
    prove = []
    for (rid, sid), r in sim.items():
        prove.append({"strumento": tk, "regola": rid, "scenario": sid, "finale": r["valore_finale_eur"], "cagr": r["cagr"],
                      "ordini": r["n_acquisti"] + r["n_vendite"], "n_stop": r["n_stop"], "commissioni": r["commissioni_eur"],
                      "tasse": r["tasse_eur"], "perdita_massima": r["perdita_massima"], "quota_investito": r["quota_giorni_investito"]})

    # --- Stop scattati: che cosa è successo dopo ---------------------------------------------------------------------
    eventi = []
    ops = sim[(ID_STOP, "lordo")]["operazioni"]
    for j, o in enumerate(ops):
        if o["motivo"] != "stop loss":
            continue
        succ = [x for x in ops[j + 1:] if x["lato"] == "acquisto"]
        ev = {"strumento": tk, "data_stop": o["data"], "prezzo_stop": o["prezzo"], "data_rientro": None, "prezzo_rientro": None}
        if succ:
            ev["data_rientro"], ev["prezzo_rientro"] = succ[0]["data"], succ[0]["prezzo"]
        eventi.append(ev)
    ev_df = pd.DataFrame(eventi)
    con_rientro = ev_df.dropna(subset=["prezzo_rientro"]) if len(ev_df) else ev_df
    quota_piu_caro = float((con_rientro["prezzo_rientro"] > con_rientro["prezzo_stop"]).mean()) if len(con_rientro) else float("nan")

    # --- Dove sta il livello dello stop rispetto alla media a 200 sedute, nei giorni di acquisto della regola di trend ------
    acq_tr = np.array([o["i"] for o in sim[("tr", "lordo")]["operazioni"] if o["lato"] == "acquisto"], dtype=int)
    sma = df["sma"].to_numpy(float)
    livello_stop = C[acq_tr] * (1.0 - config.STOP)
    quota_stop_sotto_media = float((livello_stop < sma[acq_tr]).mean())
    distanza_mediana = float(np.median(C[acq_tr] / sma[acq_tr] - 1.0))

    # --- Le scimmie (rispetto alla regola di trend e alla regola con lo stop del 5%) --------------------------------------
    rng_s = np.random.default_rng([config.SEME, k_str, 1])
    N = n - i0
    scim = {}
    for rid in ("tr", ID_STOP):
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

    # --- Bootstrap a blocchi: regola con stop contro regola senza stop (rendimento giornaliero netto, scenario principale)
    e_stop = sim[(ID_STOP, ID_SCEN_PRINC)]["equity"]
    e_tr = sim[("tr", ID_SCEN_PRINC)]["equity"]
    d = (e_stop[1:] / e_stop[:-1] - 1) - (e_tr[1:] / e_tr[:-1] - 1)
    rng_b = np.random.default_rng([config.SEME, k_str, 2])
    medie = bootstrap_blocchi(d - d.mean(), rng_b)             # distribuzione sotto l'ipotesi nulla (differenza media zero)
    osservata = float(d.mean())
    p_boot = (int((np.abs(medie) >= abs(osservata)).sum()) + 1) / (config.N_BOOTSTRAP + 1)
    medie_ic = bootstrap_blocchi(d, np.random.default_rng([config.SEME, k_str, 3]))
    alfa = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = np.quantile(medie_ic, [alfa, 1 - alfa])

    camp = np.arange(0, N, 5)
    curva = pd.DataFrame({"strumento": tk, "data": df.index[i0:][camp],
                          "bh": sim[("bh", ID_SCEN_PRINC)]["equity"][camp], "tr": e_tr[camp], "stop": e_stop[camp]})
    return dict(tk=tk, sl=config.slug(tk), nome=nome, valuta=valuta, df=df, i0=i0, sim=sim, prove=prove, ev=ev_df,
                n_stop=len(ev_df), n_rientri=len(con_rientro), quota_piu_caro=quota_piu_caro, scim=scim,
                quota_stop_sotto_media=quota_stop_sotto_media, distanza_mediana=distanza_mediana, p_boot=p_boot, diff_ann=osservata * 252, lo=float(lo) * 252, hi=float(hi) * 252, curva=curva, anni=anni_test)


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
                  f"trend {sm[('tr', ID_SCEN_PRINC)]['valore_finale_eur']:.0f}, con stop {sm[(ID_STOP, ID_SCEN_PRINC)]['valore_finale_eur']:.0f}; "
                  f"stop scattati {r['n_stop']}")
    if len(res) < 2:
        raise SystemExit("Troppo pochi strumenti utilizzabili.")

    ph_boot = holm({r["tk"]: r["p_boot"] for r in res})
    ph_sc = {rid: holm({r["tk"]: (int((r["scim"][rid]["finali"][ID_SCEN_PRINC] >= r["sim"][(rid, ID_SCEN_PRINC)]["valore_finale_eur"]).sum()) + 1)
                        / (config.N_SCIMMIE + 1) for r in res if r["scim"][rid]}) for rid in ("tr", ID_STOP)}
    for r in res:
        sl, nome, sm = r["sl"], r["nome"], r["sim"]
        reg(f"{sl}_nome", nome, "testo", "Nome dello strumento", "config.py, STRUMENTI")
        reg(f"{sl}_data_inizio", str(r["df"].index[r["i0"]].date()), "data_lunga", f"Prima seduta del test su {nome} (dopo le 200 sedute della media)", "dati/")
        reg(f"{sl}_anni", r["anni"], "num1", f"Anni del test su {nome}")
        reg(f"{sl}_n_stop", r["n_stop"], "int", f"Stop loss scattati con la soglia del 5%, {nome}", "stop_eventi.csv")
        reg(f"{sl}_quota_stop_sotto_media", r["quota_stop_sotto_media"], "pct0", f"Quota degli acquisti della regola di trend in cui il livello dello stop (95% del prezzo) sta sotto la media a 200 sedute del giorno, {nome}", "02_backtest_e_test.py, operazioni della regola di trend")
        reg(f"{sl}_distanza_mediana", r["distanza_mediana"], "pct1", f"Distanza mediana della chiusura dalla media a 200 sedute nei giorni di acquisto della regola di trend, {nome}", "02_backtest_e_test.py, operazioni della regola di trend")
        reg(f"{sl}_n_rientri", r["n_rientri"], "int", f"Stop seguiti da un rientro nei dati, {nome}", "stop_eventi.csv")
        if r["n_rientri"] > 0:
            reg(f"{sl}_quota_rientro_piu_caro", r["quota_piu_caro"], "pct0", f"Quota degli stop dopo i quali si è rientrati a un prezzo più alto di quello di vendita, {nome}", "stop_eventi.csv")
        reg(f"{sl}_diff_ann", r["diff_ann"], "pp1", f"Differenza media annualizzata del rendimento netto giornaliero tra regola con stop e regola senza stop, in punti percentuali, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_diff_lo", r["lo"], "pp1", f"Estremo inferiore dell'intervallo bootstrap a blocchi della differenza annualizzata, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_diff_hi", r["hi"], "pp1", f"Estremo superiore dell'intervallo bootstrap a blocchi della differenza annualizzata, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_p_boot", r["p_boot"], "pval", f"p-value a due code: differenza media giornaliera tra regola con stop e regola senza stop, {nome}", "bootstrap a blocchi")
        reg(f"{sl}_p_boot_holm", ph_boot[r["tk"]], "pval", f"p-value del bootstrap corretto con il metodo di Holm sugli strumenti, {nome}", "bootstrap a blocchi")
        for rid in REGOLE:
            for sid in NOME_SCEN:
                x = sm[(rid, sid)]
                reg(f"{sl}_{rid}_{sid}_finale", x["valore_finale_eur"], "int", f"Valore finale di {config.CAPITALE:.0f} euro ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_cagr", x["cagr"], "pct1", f"Rendimento annuo composto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
            x = sm[(rid, ID_SCEN_PRINC)]
            reg(f"{sl}_{rid}_dd", -x["perdita_massima"], "pct0", f"Perdita massima dal picco ({rid}), {nome}")
            reg(f"{sl}_{rid}_quota", x["quota_giorni_investito"], "pct0", f"Quota di sedute investite ({rid}), {nome}")
            if rid != "bh":
                reg(f"{sl}_{rid}_ordini", x["n_acquisti"] + x["n_vendite"], "int", f"Ordini totali, acquisti e vendite ({rid}), {nome}")
                reg(f"{sl}_{rid}_n_stop", x["n_stop"], "int", f"Stop loss scattati ({rid}), {nome}")
                reg(f"{sl}_{rid}_ordini_anno", (x["n_acquisti"] + x["n_vendite"]) / r["anni"], "num1", f"Ordini all'anno ({rid}), {nome}")
            for sid in NOME_SCEN:
                if sid == "lordo":
                    continue
                reg(f"{sl}_{rid}_{sid}_costo", sm[(rid, sid)]["commissioni_eur"], "int", f"Commissioni pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
                reg(f"{sl}_{rid}_{sid}_tasse", sm[(rid, sid)]["tasse_eur"], "int", f"Tasse pagate in tutto ({rid}, scenario {NOME_SCEN[sid]}), {nome}")
        for rid in ("tr", ID_STOP):
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
            reg(f"{sl}_{rid}_sc_sotto", float((fin[ID_SCEN_PRINC] < sm[(rid, ID_SCEN_PRINC)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che chiudono sotto la regola ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_sopra_bh", float((fin[ID_SCEN_PRINC] >= sm[("bh", ID_SCEN_PRINC)]["valore_finale_eur"]).mean()), "pct0", f"Quota di scimmie che fanno almeno quanto il buy & hold ({rid}), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_p_holm", ph_sc[rid][r["tk"]], "pval", f"p-value delle scimmie corretto con Holm sugli strumenti ({rid}, scenario principale), {nome}", "scimmie_finali.csv")
            reg(f"{sl}_{rid}_sc_periodi", sc["k"], "int", f"Periodi investiti della regola ({rid}), uguali per ogni scimmia, {nome}")

    # --- Numeri complessivi, per le sei ipotesi ----------------------------------------------------------------------
    M = ID_SCEN_PRINC
    n_str = len(res)
    reg("n_strumenti", n_str, "int", "Strumenti utilizzabili nel test", "config.py, STRUMENTI e dati/")
    reg("n_scartati", len(config.STRUMENTI) - n_str, "int", "Strumenti scartati (nessun dato o storia troppo corta)", "metadati.json")
    reg("n_dd_minore", sum(r["sim"][(ID_STOP, M)]["perdita_massima"] > r["sim"][("tr", M)]["perdita_massima"] for r in res), "int", "Strumenti in cui lo stop riduce la perdita massima della regola di trend")
    reg("n_cagr_stop_sotto", sum(r["sim"][(ID_STOP, M)]["cagr"] < r["sim"][("tr", M)]["cagr"] for r in res), "int", "Strumenti in cui la regola con lo stop rende meno, netto, di quella senza stop (scenario principale)")
    reg("n_ordini_piu", sum(r["sim"][(ID_STOP, M)]["n_acquisti"] + r["sim"][(ID_STOP, M)]["n_vendite"] > r["sim"][("tr", M)]["n_acquisti"] + r["sim"][("tr", M)]["n_vendite"] for r in res), "int", "Strumenti in cui lo stop aumenta il numero di ordini")
    reg("n_boot_signif", sum(ph_boot[r["tk"]] < 0.05 for r in res), "int", "Strumenti in cui la differenza tra regola con stop e senza stop è significativa dopo Holm", "bootstrap a blocchi")
    reg("n_boot_signif_grezzo", sum(r["p_boot"] < 0.05 for r in res), "int", "Strumenti in cui la differenza ha p-value sotto il cinque per cento senza correzione", "bootstrap a blocchi")
    reg("n_stop_batte_scimmie", sum(ph_sc[ID_STOP].get(r["tk"], 1.0) < 0.05 for r in res), "int", "Strumenti in cui la regola con lo stop batte le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_trend_batte_scimmie", sum(ph_sc["tr"].get(r["tk"], 1.0) < 0.05 for r in res), "int", "Strumenti in cui la regola di trend senza stop batte le scimmie dopo Holm", "scimmie_finali.csv")
    reg("n_stop_sotto_bh", sum(r["sim"][(ID_STOP, M)]["valore_finale_eur"] < r["sim"][("bh", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui la regola con lo stop chiude sotto il buy & hold, scenario principale")
    reg("n_trend_sotto_bh", sum(r["sim"][("tr", M)]["valore_finale_eur"] < r["sim"][("bh", M)]["valore_finale_eur"] for r in res), "int", "Strumenti in cui la regola di trend senza stop chiude sotto il buy & hold, scenario principale")
    reg("n_stop_totale", sum(r["n_stop"] for r in res), "int", "Stop scattati in tutti gli strumenti", "stop_eventi.csv")
    pieni = [r["ev"] for r in res if len(r["ev"])]
    tutti = pd.concat(pieni) if pieni else pd.DataFrame(columns=["strumento", "data_stop", "prezzo_stop", "data_rientro", "prezzo_rientro"])
    cr = tutti.dropna(subset=["prezzo_rientro"])
    reg("n_rientri_totale", len(cr), "int", "Stop (tutti gli strumenti) seguiti da un rientro nei dati", "stop_eventi.csv")
    if len(cr):
        reg("quota_rientro_piu_caro_tutti", float((cr["prezzo_rientro"] > cr["prezzo_stop"]).mean()), "pct0", "Quota degli stop (tutti gli strumenti) dopo i quali si è rientrati a un prezzo più alto di quello di vendita", "stop_eventi.csv")
    reg("n_prove", len(res) * len(REGOLE) * len(NOME_SCEN), "int", "Simulazioni complete eseguite: strumenti x regole x scenari (lordo compreso)", "config.py")
    reg("n_regole", len(REGOLE), "int", "Regole provate: buy & hold, trend, trend con stop al 5% e con tre soglie di controllo", "config.py")
    reg("n_test_ipotesi", 3 * n_str, "int", "Test di ipotesi eseguiti (scimmie e bootstrap) con correzione di Holm", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate per ogni strumento e regola", "config.py, N_SCIMMIE")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.LUNGHEZZA_BLOCCO, "int", "Sedute per blocco nel bootstrap", "config.py, LUNGHEZZA_BLOCCO")
    reg("seme", config.SEME, "annonum", "Seme dei sorteggi", "config.py, SEME")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale in euro", "config.py, CAPITALE")
    reg("commissione_fissa", config.SCENARI_COSTO[1][1], "int", "Commissione fissa per ordine nello scenario principale, in euro", "config.py, SCENARI_COSTO")
    reg("commissione_perc", config.SCENARI_COSTO[2][2], "pct1", "Commissione proporzionale all'importo nel terzo scenario", "config.py, SCENARI_COSTO")
    reg("aliquota", config.ALIQUOTA, "pct0", "Aliquota sulle plusvalenze", "config.py, ALIQUOTA")
    reg("media_mobile", config.MEDIA_MOBILE, "int", "Sedute della media mobile", "config.py, MEDIA_MOBILE")
    reg("stop", config.STOP, "pct0", "Soglia dello stop loss", "config.py, STOP")
    for x in config.SOGLIE_CONTROLLO:
        reg(f"stop_{id_regola(x)}", x, "pct0", "Soglia di controllo dello stop loss", "config.py, SOGLIE_CONTROLLO")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("data_scarico", META["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("data_ultima", max(str(r["df"].index[-1].date()) for r in res), "data_lunga", "Ultima seduta presente nei dati", "dati/")

    # --- File di supporto ---------------------------------------------------------------------------------------------
    pd.DataFrame([x for r in res for x in r["prove"]]).to_csv(config.RISULTATI / "prove.csv", index=False, float_format="%.6f")
    tutti.to_csv(config.RISULTATI / "stop_eventi.csv", index=False, float_format="%.4f")
    pd.concat([r["curva"] for r in res]).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.4f")
    colonne = {}
    for r in res:
        for rid in ("tr", ID_STOP):
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
