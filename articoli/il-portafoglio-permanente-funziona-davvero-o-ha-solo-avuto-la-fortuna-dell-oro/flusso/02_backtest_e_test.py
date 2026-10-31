"""Passo 2 - Il Portafoglio Permanente: serie mensili, statistiche, anni solari, sotto-periodi, bootstrap, scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine
  mensili.csv         rendimenti mensili di asset e portafogli
  anni_solari.csv     rendimento di ogni anno solare
  scimmie.csv         Sharpe e perdita massima dei portafogli a pesi casuali

Nessun look-ahead: i pesi sono fissi e decisi in config.py; il ribilanciamento è a gennaio; la liquidità del mese usa il tasso di fine mese precedente.
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
NOMI = {"pp": "Portafoglio Permanente", "az": "100% azioni", "m6040": "60/40", "ob": "100% obbligazioni lunghe",
        "oro": "100% oro", "senza_oro": "senza oro", "senza_cassa": "senza liquidità"}


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer, np.bool_)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def leggi(ticker: str) -> pd.Series:
    return pd.read_csv(config.file_dati(ticker), index_col=0, parse_dates=True)["Close"]


def tasso_pct(s: pd.Series) -> pd.Series:
    m = fx.fine_mese(s)
    return m / 10.0 if m.median() > 25 else m


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    scarico = pd.Timestamp(meta["scaricato_il_utc"][:10]).to_period("M")

    az_m, ob_m, oro_m = (fx.fine_mese(leggi(t)) for t in ("VFINX", "VUSTX", "GC=F"))
    agg_m, gld_m = fx.fine_mese(leggi("VBMFX")), fx.fine_mese(leggi("GLD"))
    irx = tasso_pct(leggi("^IRX"))
    ultimo = min(az_m.index[-1], ob_m.index[-1], oro_m.index[-1], irx.index[-1], scarico - 1)
    mesi = pd.period_range(config.INIZIO_CAMPIONE, ultimo, freq="M")
    A, O, G = (s.pct_change().reindex(mesi).values for s in (az_m, ob_m, oro_m))
    AGG = agg_m.pct_change().reindex(mesi).values
    C = (irx.shift(1) / 100 / 12).reindex(mesi).values
    R = np.column_stack([A, O, G, C])
    if np.isnan(R).any() or np.isnan(AGG).any():
        raise SystemExit("Valori mancanti nelle serie mensili")
    n = len(mesi)

    P = {k: fx.portafoglio(R, mesi, w)[0] for k, w in config.PESI.items()}
    m6040 = fx.portafoglio(np.column_stack([A, AGG]), mesi, [config.PESO_AZIONI_6040, 1 - config.PESO_AZIONI_6040])[0]
    serie = {"pp": P["pp"], "az": A, "m6040": m6040, "ob": O, "oro": G,
             "senza_oro": P["senza_oro"], "senza_cassa": P["senza_cassa"]}
    pd.DataFrame({"mese": mesi.astype(str), "azioni": A, "obbligazioni": O, "oro": G, "cassa": C, "pp": P["pp"], "m6040": m6040,
                  "senza_oro": P["senza_oro"], "senza_cassa": P["senza_cassa"]}).to_csv(config.RISULTATI / "mensili.csv", index=False, float_format="%.6f")

    reg("campione_inizio", mesi[0].year, "annonum", "Anno del primo mese del campione", "config.py, INIZIO_CAMPIONE")
    reg("campione_fine_mese", f"{mesi[-1].year}-{mesi[-1].month:02d}-{mesi[-1].days_in_month:02d}", "data_lunga", "Ultimo mese completo del campione", "dati/")
    reg("n_mesi", n, "int", "Mesi del campione", "numero di mesi")
    reg("n_anni", n / 12, "num1", "Anni del campione", "mesi / 12")
    reg("peso_pp", config.PESI["pp"][0], "pct0", "Peso di ciascuno dei quattro asset nel Portafoglio Permanente", "config.py, PESI")
    reg("peso_6040_az", config.PESO_AZIONI_6040, "pct0", "Peso delle azioni nel 60/40", "config.py")
    reg("peso_6040_ob", 1 - config.PESO_AZIONI_6040, "pct0", "Peso delle obbligazioni nel 60/40", "config.py")
    reg("peso_terzo", 1 / 3, "pct0", "Peso di ciascuno dei tre asset nelle versioni senza oro e senza liquidità", "config.py, PESI")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")

    # --- statistiche complessive ------------------------------------------------------------------------------------
    for k, r in serie.items():
        reg(f"{k}_cagr", fx.cagr(r), "pct1", f"Rendimento annuo composto, {NOMI[k]}")
        reg(f"{k}_vol", fx.volatilita(r), "pct1", f"Volatilità annua, {NOMI[k]}")
        reg(f"{k}_sharpe", float(fx.sharpe(r, C)), "num2", f"Sharpe ratio annualizzato (eccesso sui Bot a 13 settimane), {NOMI[k]}")
        reg(f"{k}_dd", fx.perdita_massima(r), "pct1", f"Perdita massima dal picco (mensile), {NOMI[k]}")
        reg(f"{k}_valore", float(np.prod(1 + r)), "num2", f"Valore finale di 1 dollaro, {NOMI[k]}")
    for k in ("pp", "az", "m6040"):
        reg(f"{k}_sott_acqua", fx.mesi_sott_acqua(serie[k]), "int", f"Periodo più lungo (mesi) sotto il massimo precedente, {NOMI[k]}")
        reg(f"{k}_sott_acqua_anni", fx.mesi_sott_acqua(serie[k]) / 12, "num1", f"Come sopra, in anni, {NOMI[k]}")
    reg("cassa_cagr", fx.cagr(C), "pct1", "Rendimento annuo composto dei Bot a 13 settimane", "dati/IRX.csv")

    # --- anni solari ------------------------------------------------------------------------------------------------
    ann = pd.DataFrame({k: fx.rendimenti_anno_solare(r, mesi) for k, r in serie.items()})
    anni_pieni = [a for a in ann.index if sum(1 for m in mesi if m.year == a) == 12]
    ann = ann.loc[anni_pieni]
    ann.to_csv(config.RISULTATI / "anni_solari.csv", index_label="anno", float_format="%.5f")
    pa = int(ann["pp"].idxmin())
    reg("pp_peggior_anno", pa, "annonum", "Anno solare peggiore del Portafoglio Permanente", "anni_solari.csv")
    reg("pp_peggior_rend", float(ann["pp"].min()), "pct1", "Rendimento dell'anno solare peggiore del PP", "anni_solari.csv")
    reg("anno_crisi", 2008, "annonum", "Anno della crisi finanziaria, scelto a priori nelle ipotesi", "ipotesi 4")
    reg("anno_rialzi", 2022, "annonum", "Anno dei rialzi dei tassi, scelto a priori nelle ipotesi", "config.py, SOGLIE")
    for a in (2008, 2022):
        for k in ("pp", "az", "m6040", "ob", "oro"):
            reg(f"{k}_{a}", float(ann.loc[a, k]), "pct1", f"Rendimento {NOMI[k]} nel {a}", "anni_solari.csv")
    reg("pp_anni_neg", int((ann["pp"] < 0).sum()), "int", "Anni solari negativi del PP", "anni_solari.csv")
    reg("az_anni_neg", int((ann["az"] < 0).sum()), "int", "Anni solari negativi delle azioni", "anni_solari.csv")
    reg("m6040_anni_neg", int((ann["m6040"] < 0).sum()), "int", "Anni solari negativi del 60/40", "anni_solari.csv")
    reg("n_anni_pieni", len(ann), "int", "Anni solari completi nel campione", "anni_solari.csv")
    reg("pp_meglio_az_anni", int((ann["pp"] > ann["az"]).sum()), "int", "Anni solari in cui il PP ha reso più delle azioni", "anni_solari.csv")

    # --- correlazioni tra gli asset -----------------------------------------------------------------------------------
    for (a, b, na) in ((A, O, "az_ob"), (A, G, "az_oro"), (O, G, "ob_oro")):
        reg(f"corr_{na}", float(np.corrcoef(a, b)[0, 1]), "num2", f"Correlazione mensile {na.replace('_', '/')}")

    # --- sotto-periodi -------------------------------------------------------------------------------------------------
    sp = pd.Period(config.DIVISIONE_PERIODO, "M")
    i1 = np.array([m < sp for m in mesi])
    i2 = ~i1
    reg("sp_divisione", sp.year, "annonum", "Anno d'inizio del secondo sotto-periodo", "config.py, DIVISIONE_PERIODO")
    reg("sp_fine1_anno", (sp - 1).year, "annonum", "Anno finale del primo sotto-periodo", "config.py, DIVISIONE_PERIODO")
    for nome, sel in (("p1", i1), ("p2", i2)):
        reg(f"{nome}_mesi", int(sel.sum()), "int", f"Mesi del sotto-periodo {nome}")
        for k in ("pp", "az", "m6040", "oro"):
            reg(f"{nome}_{k}_cagr", fx.cagr(serie[k][sel]), "pct1", f"Rendimento annuo composto, {NOMI[k]}, sotto-periodo {nome}")
        for k in ("pp", "az", "m6040"):
            reg(f"{nome}_{k}_sharpe", float(fx.sharpe(serie[k][sel], C[sel])), "num2", f"Sharpe, {NOMI[k]}, sotto-periodo {nome}")
        reg(f"{nome}_pp_dd", fx.perdita_massima(serie["pp"][sel]), "pct1", f"Perdita massima del PP, sotto-periodo {nome}")
        reg(f"{nome}_az_dd", fx.perdita_massima(serie["az"][sel]), "pct1", f"Perdita massima delle azioni, sotto-periodo {nome}")
        reg(f"{nome}_diff_6040", RIS[f"{nome}_pp_sharpe"]["valore"] - RIS[f"{nome}_m6040_sharpe"]["valore"], "num2",
            f"Sharpe del PP meno Sharpe del 60/40, sotto-periodo {nome}")

    # --- bootstrap della differenza di Sharpe ---------------------------------------------------------------------------
    dif = []
    for _ in range(config.N_BOOTSTRAP):
        ix = fx.indici_blocchi(n, config.BLOCCO_MESI, rng)
        dif.append(float(fx.sharpe(serie["pp"][ix], C[ix]) - fx.sharpe(A[ix], C[ix])))
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = float(np.quantile(dif, a)), float(np.quantile(dif, 1 - a))
    reg("boot_diff", RIS["pp_sharpe"]["valore"] - RIS["az_sharpe"]["valore"], "num2", "Sharpe del PP meno Sharpe delle azioni")
    reg("boot_lo", lo, "num2", "Estremo inferiore dell'intervallo di confidenza della differenza di Sharpe")
    reg("boot_hi", hi, "num2", "Estremo superiore dell'intervallo di confidenza della differenza di Sharpe")
    reg("boot_zero_dentro", int(lo <= 0 <= hi), "int", "1 se l'intervallo comprende lo zero")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_MESI, "int", "Lunghezza dei blocchi del bootstrap, mesi", "config.py, BLOCCO_MESI")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello dell'intervallo di confidenza", "config.py, LIVELLO_CONFIDENZA")

    # --- scimmie: pesi casuali (Dirichlet uniforme) estratti di nuovo ogni gennaio ------------------------------------------
    anni_u = list(dict.fromkeys(m.year for m in mesi))
    Wc = rng.dirichlet(np.ones(4), size=(config.N_SCIMMIE, len(anni_u)))
    PM = fx.portafoglio(R, mesi, Wc)
    sh = np.asarray(fx.sharpe(PM, C[None, :], asse=1))
    dd = np.array([fx.perdita_massima(x) for x in PM])
    pd.DataFrame({"sharpe": sh, "perdita_massima": dd}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.5f")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Portafogli a pesi casuali", "config.py, N_SCIMMIE")
    reg("scim_perc_pp", float((sh <= RIS["pp_sharpe"]["valore"]).mean()), "pct1", "Quota di scimmie con Sharpe non superiore a quello del PP")
    reg("scim_perc_az", float((sh <= RIS["az_sharpe"]["valore"]).mean()), "pct1", "Quota di scimmie con Sharpe non superiore a quello delle azioni")
    reg("scim_dd_meglio", float((dd > RIS["pp_dd"]["valore"]).mean()), "pct1", "Quota di scimmie con perdita massima più piccola di quella del PP")
    reg("scim_med", float(np.median(sh)), "num2", "Sharpe mediano delle scimmie")
    reg("scim_p05", float(np.quantile(sh, 0.05)), "num2", "Sharpe del 5° percentile delle scimmie")
    reg("scim_p95", float(np.quantile(sh, 0.95)), "num2", "Sharpe del 95° percentile delle scimmie")
    reg("scim_dd_med", float(np.median(dd)), "pct1", "Perdita massima mediana delle scimmie")

    # --- controllo: oro (future) contro GLD -------------------------------------------------------------------------------
    rg = gld_m.pct_change()
    comune = mesi.intersection(rg.dropna().index)
    comune = comune[comune >= pd.Period(config.INIZIO_CONTROLLO_ORO, "M")]
    x, z = pd.Series(G, index=mesi).reindex(comune).values, rg.reindex(comune).values
    reg("proxy_n", len(comune), "int", "Mesi in comune tra oro (future) e GLD", "dati/GLD.csv")
    reg("proxy_corr", float(np.corrcoef(x, z)[0, 1]), "num2", "Correlazione mensile tra oro (future) e GLD", "dati/GLD.csv")
    reg("proxy_cagr_fut", fx.cagr(x), "pct1", "Rendimento annuo composto dell'oro (future) nel periodo in comune")
    reg("proxy_cagr_gld", fx.cagr(z), "pct1", "Rendimento annuo composto del GLD nel periodo in comune", "dati/GLD.csv")
    reg("proxy_inizio", comune[0].year, "annonum", "Anno di inizio del confronto con GLD", "config.py, INIZIO_CONTROLLO_ORO")

    # --- verdetti (flag 1/0) ----------------------------------------------------------------------------------------------
    S = config.SOGLIE
    V = lambda k: RIS[k]["valore"]
    reg("ip1_ok", int(abs(V("pp_dd")) < abs(V("az_dd")) and abs(V("pp_dd")) < abs(V("m6040_dd"))), "int", "Ipotesi 1 verificata")
    reg("ip2_ok", int(V("pp_sharpe") > V("az_sharpe")), "int", "Ipotesi 2 verificata")
    reg("ip3_ok", int(V("pp_cagr") < V("az_cagr")), "int", "Ipotesi 3 verificata")
    reg("ip4_ok", int(pa == S["ip3_anno"]), "int", "Ipotesi 4 verificata")
    reg("ip5_ok", int(V("pp_sharpe") > V("senza_oro_sharpe")), "int", "Ipotesi 5 verificata")
    reg("ip6_ok", int(abs(V("senza_cassa_dd")) > abs(V("pp_dd"))), "int", "Ipotesi 6 verificata")
    reg("ip7_ok", V("boot_zero_dentro"), "int", "Ipotesi 7 verificata (l'intervallo comprende lo zero)")
    reg("ip8_ok", int(V("scim_perc_pp") > S["ip7_perc"]), "int", "Ipotesi 8 verificata")
    reg("ip9_ok", int(V("p1_diff_6040") > V("p2_diff_6040")), "int", "Ipotesi 9 verificata")
    reg("ip10_ok", int(V("proxy_corr") >= S["ip9_corr"]), "int", "Ipotesi 10 verificata")
    reg("s_ip4_anno", S["ip3_anno"], "annonum", "Soglia ipotesi 4: anno", "config.py, SOGLIE")
    reg("s_ip8_perc", S["ip7_perc"], "pct0", "Soglia ipotesi 8: quota di scimmie battute", "config.py, SOGLIE")
    reg("s_ip10_corr", S["ip9_corr"], "num2", "Soglia ipotesi 10: correlazione minima", "config.py, SOGLIE")
    reg("cit_baur", 2010, "annonum", "Anno di Baur e Lucey (The Financial Review)", "abstract letto su opus.lib.uts.edu.au")
    reg("cit_erb", 2013, "annonum", "Anno di Erb e Harvey (Financial Analysts Journal)", "abstract letto su ideas.repec.org")
    reg("cit_demiguel", 2009, "annonum", "Anno di DeMiguel, Garlappi e Uppal (Review of Financial Studies)", "abstract letto su ideas.repec.org")

    reg("cit_dm_modelli", 14, "int", "Numero di modelli di ottimizzazione messi a confronto da DeMiguel, Garlappi e Uppal", "abstract letto su ideas.repec.org")
    reg("cit_dm_dataset", 7, "int", "Numero di insiemi di dati usati da DeMiguel, Garlappi e Uppal", "abstract letto su ideas.repec.org")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {n} mesi")


if __name__ == "__main__":
    main()
