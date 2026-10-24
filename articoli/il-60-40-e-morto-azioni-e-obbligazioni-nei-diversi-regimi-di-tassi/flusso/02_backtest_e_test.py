"""Passo 2 - Il 60/40 nei regimi di tassi: serie mensili, statistiche, correlazioni, finestre a 10 anni, bootstrap e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json          ogni numero dell'articolo, con descrizione e origine
  mensili.csv            per ogni mese: rendimenti di azioni, obbligazioni sintetiche, 60/40, liquidità, tasso a 10 anni, regime
  finestre_10anni.csv    per ogni mese di partenza: rendimento annuo dei 10 anni successivi (60/40, azioni, obbligazioni)
  per_regime.csv         statistiche per regime di tassi
  anni_solari.csv        rendimento di ogni anno solare
  scimmie_sharpe.csv     Sharpe dei portafogli a peso azionario casuale

Nessun look-ahead: il regime di un mese usa il rendimento a 10 anni di fine mese precedente; il ribilanciamento è a gennaio.
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
    if isinstance(valore, (np.floating, np.integer, np.bool_)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def leggi(ticker: str) -> pd.Series:
    return pd.read_csv(config.file_dati(ticker), index_col=0, parse_dates=True)["Close"]


def tasso_pct(s: pd.Series) -> pd.Series:
    """Rendimento in % a fine mese; se la scala fosse in decimi di punto (valori mediani > 25) si divide per 10."""
    m = fx.fine_mese(s)
    return m / 10.0 if m.median() > 25 else m


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    meta = json.loads(config.FILE_METADATI.read_text(encoding="utf-8"))
    rng = np.random.default_rng(config.SEME)
    scarico = pd.Timestamp(meta["scaricato_il_utc"][:10]).to_period("M")

    az_m = fx.fine_mese(leggi("VFINX"))
    fondo_m = fx.fine_mese(leggi("VBMFX"))
    y = tasso_pct(leggi("^TNX"))
    irx = tasso_pct(leggi("^IRX"))
    ultimo = min(az_m.index[-1], y.index[-1], irx.index[-1], scarico - 1)     # solo mesi completi

    mesi = pd.period_range(config.INIZIO_CAMPIONE, ultimo, freq="M")
    ra = az_m.pct_change().reindex(mesi)
    y_prec = y.shift(1).reindex(mesi)
    y_ora = y.reindex(mesi)
    rb = pd.Series([fx.rendimento_obbligazione(a / 100, b / 100, config.SCADENZA_OBBL) for a, b in zip(y_prec, y_ora)], index=mesi)
    cassa = (irx.shift(1) / 100 / 12).reindex(mesi)
    if ra.isna().any() or rb.isna().any() or cassa.isna().any():
        raise SystemExit("Valori mancanti nelle serie mensili")
    n = len(mesi)
    A, B, C = ra.values, rb.values, cassa.values
    W = config.PESO_AZIONI
    M = fx.portafoglio(A, B, mesi, W)[0]
    reg_m = fx.regime(y_prec.values, config.SOGLIA_BASSI, config.SOGLIA_ALTI)

    pd.DataFrame({"mese": mesi.astype(str), "azioni": A, "obbligazioni": B, "mix": M, "cassa": C,
                  "tasso10_prec": y_prec.values, "regime": reg_m}).to_csv(config.RISULTATI / "mensili.csv", index=False, float_format="%.6f")

    reg("campione_inizio", mesi[0].year, "annonum", "Anno del primo mese del campione", "config.py, INIZIO_CAMPIONE")
    reg("campione_fine_anno", mesi[-1].year, "annonum", "Anno dell'ultimo mese completo del campione", "dati/")
    reg("campione_fine_mese", f"{mesi[-1].year}-{mesi[-1].month:02d}-{mesi[-1].days_in_month:02d}",
        "data_lunga", "Ultimo mese completo del campione (fine mese)", "dati/")
    reg("n_mesi", n, "int", "Mesi del campione", "numero di mesi")
    reg("n_anni", n / 12, "num1", "Anni del campione", "mesi / 12")
    reg("peso_azioni", W, "pct0", "Peso delle azioni", "config.py, PESO_AZIONI")
    reg("peso_obbl", 1 - W, "pct0", "Peso delle obbligazioni", "config.py, PESO_AZIONI")
    reg("soglia_bassi", config.SOGLIA_BASSI, "int", "Soglia dei tassi bassi (rendimento a 10 anni, in %)", "config.py, SOGLIA_BASSI")
    reg("soglia_alti", config.SOGLIA_ALTI, "int", "Soglia dei tassi alti (rendimento a 10 anni, in %)", "config.py, SOGLIA_ALTI")
    reg("scadenza", config.SCADENZA_OBBL, "int", "Scadenza dell'obbligazione sintetica, anni", "config.py, SCADENZA_OBBL")
    reg("data_scarico", meta["scaricato_il_utc"][:10], "data", "Data del download dei dati", "dati/metadati.json")
    reg("y_min", float(np.nanmin(y_ora.values)), "num2", "Rendimento a 10 anni minimo nel campione (%)", "dati/TNX.csv, fine mese")
    reg("y_max", float(np.nanmax(y_ora.values)), "num2", "Rendimento a 10 anni massimo nel campione (%)", "dati/TNX.csv, fine mese")

    # --- statistiche complessive ------------------------------------------------------------------------------------
    serie = {"az": A, "mix": M, "ob": B}
    nomi = {"az": "100% azioni", "mix": "60/40", "ob": "100% obbligazioni a 10 anni"}
    for k, r in serie.items():
        reg(f"{k}_cagr", fx.cagr(r), "pct1", f"Rendimento annuo composto, {nomi[k]}")
        reg(f"{k}_vol", fx.volatilita(r), "pct1", f"Volatilità annua, {nomi[k]}")
        reg(f"{k}_sharpe", float(fx.sharpe(r, C)), "num2", f"Sharpe ratio annualizzato (eccesso sui Bot a 13 settimane), {nomi[k]}")
        reg(f"{k}_dd", fx.perdita_massima(r), "pct1", f"Perdita massima dal picco (mensile), {nomi[k]}")
    reg("cassa_cagr", fx.cagr(C), "pct1", "Rendimento annuo composto dei Bot a 13 settimane", "dati/IRX.csv")
    reg("valore_az", float(np.prod(1 + A)), "num1", "Valore finale di 1 dollaro in azioni", SORGENTE)
    reg("valore_mix", float(np.prod(1 + M)), "num1", "Valore finale di 1 dollaro nel 60/40", SORGENTE)
    reg("valore_ob", float(np.prod(1 + B)), "num1", "Valore finale di 1 dollaro in obbligazioni", SORGENTE)

    # --- anni solari ------------------------------------------------------------------------------------------------
    ann = pd.DataFrame({k: fx.rendimenti_anno_solare(r, mesi) for k, r in serie.items()})
    anni_pieni = [a for a in ann.index if sum(1 for m in mesi if m.year == a) == 12]
    ann = ann.loc[anni_pieni]
    ann.to_csv(config.RISULTATI / "anni_solari.csv", index_label="anno", float_format="%.5f")
    pa = int(ann["mix"].idxmin())
    reg("mix_peggior_anno", pa, "annonum", "Anno solare peggiore del 60/40", "anni_solari.csv")
    reg("mix_peggior_rend", float(ann["mix"].min()), "pct1", "Rendimento dell'anno solare peggiore del 60/40", "anni_solari.csv")
    reg("anno_crisi", 2008, "annonum", "Anno della crisi finanziaria, usato come confronto", "scelto a priori nelle ipotesi")
    reg("anno_rialzi", 2022, "annonum", "Anno dei rialzi dei tassi, ipotesi 1", "config.py, SOGLIE")
    for a in (2008, 2022):
        for k in ("az", "mix", "ob"):
            reg(f"{k}_{a}", float(ann.loc[a, k]), "pct1", f"Rendimento {nomi[k]} nel {a}", "anni_solari.csv")
    reg("mix_anni_neg", int((ann["mix"] < 0).sum()), "int", "Anni solari negativi del 60/40", "anni_solari.csv")
    reg("n_anni_pieni", len(ann), "int", "Anni solari completi nel campione", "anni_solari.csv")
    reg("az_anni_neg", int((ann["az"] < 0).sum()), "int", "Anni solari negativi delle azioni", "anni_solari.csv")
    both = int(((ann["az"] < 0) & (ann["ob"] < 0)).sum())
    reg("anni_entrambi_neg", both, "int", "Anni solari in cui azioni e obbligazioni sono andate entrambe in perdita", "anni_solari.csv")
    anni_ent = ", ".join(str(a) for a in ann.index[(ann["az"] < 0) & (ann["ob"] < 0)])
    reg("anni_entrambi_elenco", anni_ent if anni_ent else "nessuno", "testo", "Elenco degli anni con azioni e obbligazioni entrambe in perdita", "anni_solari.csv")

    # --- regimi ---------------------------------------------------------------------------------------------------
    righe = []
    for rg in ("bassi", "medi", "alti"):
        sel = reg_m == rg
        k_n = int(sel.sum())
        reg(f"n_{rg}", k_n, "int", f"Mesi con tassi {rg}")
        reg(f"quota_{rg}", k_n / n, "pct0", f"Quota dei mesi con tassi {rg}")
        riga = {"regime": rg, "mesi": k_n}
        if k_n >= 12:
            c = float(np.corrcoef(A[sel], B[sel])[0, 1])
            reg(f"corr_{rg}", c, "num2", f"Correlazione mensile azioni/obbligazioni con tassi {rg}")
            riga["corr"] = c
            for k, r in serie.items():
                v = float(np.prod(1 + r[sel]) ** (12 / k_n) - 1)
                reg(f"reg_{rg}_{k}", v, "pct1", f"Rendimento annuo composto ({nomi[k]}) nei mesi con tassi {rg}")
                riga[k] = v
        righe.append(riga)
    pd.DataFrame(righe).to_csv(config.RISULTATI / "per_regime.csv", index=False, float_format="%.5f")
    reg("corr_tutto", float(np.corrcoef(A, B)[0, 1]), "num2", "Correlazione mensile azioni/obbligazioni, intero campione")
    reg("corr_diff", RIS["corr_alti"]["valore"] - RIS["corr_bassi"]["valore"], "num2", "Correlazione con tassi alti meno correlazione con tassi bassi")

    # --- correlazione mobile e anni delle citazioni ---------------------------------------------------------------------
    FIN = 36
    rc = pd.Series(A).rolling(FIN).corr(pd.Series(B)).replace([np.inf, -np.inf], np.nan).dropna()
    reg("finestra_corr", FIN, "int", "Mesi della finestra mobile della correlazione", "costante dello script (FIN)")
    reg("corr_mob_min", float(rc.min()), "num2", "Correlazione mobile minima azioni/obbligazioni")
    reg("corr_mob_min_anno", mesi[int(rc.idxmin())].year, "annonum", "Anno in cui la correlazione mobile ha toccato il minimo")
    reg("corr_mob_max", float(rc.max()), "num2", "Correlazione mobile massima azioni/obbligazioni")
    reg("corr_mob_max_anno", mesi[int(rc.idxmax())].year, "annonum", "Anno in cui la correlazione mobile ha toccato il massimo")
    reg("corr_mob_ultima", float(rc.iloc[-1]), "num2", "Ultima correlazione mobile del campione")
    reg("corr_mob_quota_neg", float((rc < 0).mean()), "pct0", "Quota dei mesi con correlazione mobile negativa")
    reg("cit_campbell", 2017, "annonum", "Anno di pubblicazione di Campbell, Sunderam e Viceira (Critical Finance Review)", "abstract letto su nber.org/papers/w14701")
    reg("cit_baele", 2010, "annonum", "Anno di pubblicazione di Baele, Bekaert e Inghelbrecht (Review of Financial Studies)", "abstract letto su nber.org/papers/w15260")

    # --- finestre a 10 anni ---------------------------------------------------------------------------------------
    H = config.ORIZZONTE_ANNI * 12
    fw = {k: fx.finestre_mobili(r, H) for k, r in serie.items()}
    nf = len(fw["mix"])
    y_part = y_ora.values[:nf]                       # rendimento a 10 anni a fine del mese t, noto alla partenza
    reg_f = fx.regime(y_part, config.SOGLIA_BASSI, config.SOGLIA_ALTI)
    pd.DataFrame({"mese_partenza": mesi[:nf].astype(str), "tasso10": y_part, "regime": reg_f,
                  "mix": fw["mix"], "az": fw["az"], "ob": fw["ob"]}).to_csv(config.RISULTATI / "finestre_10anni.csv", index=False, float_format="%.5f")
    reg("fw_anni", config.ORIZZONTE_ANNI, "int", "Anni di ciascuna finestra", "config.py, ORIZZONTE_ANNI")
    reg("fw_n", nf, "int", "Mesi di partenza con una finestra completa", "numero di finestre")
    for rg in ("bassi", "alti", "medi"):
        sel = reg_f == rg
        reg(f"fw_n_{rg}", int(sel.sum()), "int", f"Finestre che partono con tassi {rg}")
        if sel.sum() > 0:
            reg(f"fw_med_{rg}", float(np.median(fw["mix"][sel])), "pct1", f"Mediana del rendimento annuo del 60/40 nei 10 anni dopo una partenza con tassi {rg}")
            reg(f"fw_med_az_{rg}", float(np.median(fw["az"][sel])), "pct1", f"Mediana del rendimento annuo delle azioni nei 10 anni dopo una partenza con tassi {rg}")
            reg(f"fw_med_ob_{rg}", float(np.median(fw["ob"][sel])), "pct1", f"Mediana del rendimento annuo delle obbligazioni nei 10 anni dopo una partenza con tassi {rg}")
    reg("fw_diff", RIS["fw_med_alti"]["valore"] - RIS["fw_med_bassi"]["valore"], "pp1",
        "Mediana 60/40 dopo tassi alti meno mediana dopo tassi bassi (punti percentuali annui)")
    reg("fw_corr_tasso", float(np.corrcoef(y_part, fw["mix"])[0, 1]), "num2", "Correlazione tra il rendimento a 10 anni alla partenza e il rendimento annuo del 60/40 nei 10 anni dopo")
    reg("fw_corr_tasso_ob", float(np.corrcoef(y_part, fw["ob"])[0, 1]), "num2", "Come sopra, per le sole obbligazioni")
    reg("fw_ultima_partenza", f"{mesi[nf-1].year}-{mesi[nf-1].month:02d}-{mesi[nf-1].days_in_month:02d}", "data_lunga", "Ultimo mese di partenza con finestra completa")

    # --- bootstrap della differenza di Sharpe ---------------------------------------------------------------------------
    eA, eM = A - C, M - C
    punto = float(fx.sharpe(M, C) - fx.sharpe(A, C))
    dif = []
    for _ in range(config.N_BOOTSTRAP):
        ix = fx.indici_blocchi(n, config.BLOCCO_MESI, rng)
        dif.append(float(fx.sharpe(M[ix], C[ix]) - fx.sharpe(A[ix], C[ix])))
    a = (1 - config.LIVELLO_CONFIDENZA) / 2
    lo, hi = float(np.quantile(dif, a)), float(np.quantile(dif, 1 - a))
    reg("boot_diff", punto, "num2", "Sharpe del 60/40 meno Sharpe delle azioni")
    reg("boot_lo", lo, "num2", "Estremo inferiore dell'intervallo di confidenza della differenza di Sharpe")
    reg("boot_hi", hi, "num2", "Estremo superiore dell'intervallo di confidenza della differenza di Sharpe")
    reg("boot_zero_dentro", int(lo <= 0 <= hi), "int", "1 se l'intervallo comprende lo zero")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_MESI, "int", "Lunghezza dei blocchi del bootstrap, mesi", "config.py, BLOCCO_MESI")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello dell'intervallo di confidenza", "config.py, LIVELLO_CONFIDENZA")

    # --- scimmie: peso azionario casuale per ogni anno -------------------------------------------------------------
    anni_u = list(dict.fromkeys(m.year for m in mesi))
    Wc = rng.uniform(0.0, 1.0, size=(config.N_SCIMMIE, len(anni_u)))
    P = fx.portafoglio(A, B, mesi, Wc)
    sh = np.asarray(fx.sharpe(P, C[None, :], asse=1))
    pd.DataFrame({"sharpe": sh}).to_csv(config.RISULTATI / "scimmie_sharpe.csv", index=False, float_format="%.5f")
    s_mix, s_az = float(fx.sharpe(M, C)), float(fx.sharpe(A, C))
    reg("n_scimmie", config.N_SCIMMIE, "int", "Portafogli a peso azionario casuale", "config.py, N_SCIMMIE")
    reg("scim_perc_mix", float((sh <= s_mix).mean()), "pct1", "Quota di scimmie con Sharpe non superiore a quello del 60/40")
    reg("scim_perc_az", float((sh <= s_az).mean()), "pct1", "Quota di scimmie con Sharpe non superiore a quello delle sole azioni")
    reg("scim_med", float(np.median(sh)), "num2", "Sharpe mediano delle scimmie")
    reg("scim_p05", float(np.quantile(sh, 0.05)), "num2", "Sharpe del 5° percentile delle scimmie")
    reg("scim_p95", float(np.quantile(sh, 0.95)), "num2", "Sharpe del 95° percentile delle scimmie")

    # --- controllo del proxy obbligazionario -------------------------------------------------------------------------
    rf = fondo_m.pct_change()
    comune = mesi.intersection(rf.dropna().index)
    comune = comune[comune >= pd.Period("1987-01", "M")]
    x, z = rb.reindex(comune).values, rf.reindex(comune).values
    reg("proxy_n", len(comune), "int", "Mesi in comune tra serie sintetica e fondo obbligazionario", "dati/VBMFX.csv")
    reg("proxy_corr", float(np.corrcoef(x, z)[0, 1]), "num2", "Correlazione mensile tra obbligazioni sintetiche a 10 anni e fondo VBMFX", "dati/VBMFX.csv")
    reg("proxy_cagr_sint", fx.cagr(x), "pct1", "Rendimento annuo composto della serie sintetica nel periodo in comune")
    reg("proxy_cagr_fondo", fx.cagr(z), "pct1", "Rendimento annuo composto del fondo VBMFX nel periodo in comune", "dati/VBMFX.csv")
    reg("proxy_inizio", comune[0].year, "annonum", "Anno di inizio del confronto con il fondo", "dati/VBMFX.csv")

    # --- verdetti delle ipotesi (flag 1/0) -------------------------------------------------------------------------------
    S = config.SOGLIE
    reg("ip1_ok", int(pa == S["ip1_anno"]), "int", "Ipotesi 1 verificata (anno peggiore = 2022)", "confronto con config.SOGLIE")
    reg("ip2_ok", int(RIS["corr_diff"]["valore"] >= S["ip2_diff"]), "int", "Ipotesi 2 verificata", "confronto con config.SOGLIE")
    reg("ip3_sharpe_ok", int(RIS["mix_sharpe"]["valore"] > RIS["az_sharpe"]["valore"]), "int", "Ipotesi 3, parte Sharpe")
    reg("ip3_dd_ok", int(abs(RIS["mix_dd"]["valore"]) < abs(RIS["az_dd"]["valore"])), "int", "Ipotesi 3, parte perdita massima")
    reg("ip4_ok", int(RIS["fw_diff"]["valore"] >= S["ip4_pp"]), "int", "Ipotesi 4 verificata", "confronto con config.SOGLIE")
    reg("ip5_ok", RIS["boot_zero_dentro"]["valore"], "int", "Ipotesi 5 verificata (intervallo comprende lo zero)")
    reg("ip6_ok", int(S["ip6_lo"] <= RIS["scim_perc_mix"]["valore"] <= S["ip6_hi"]), "int", "Ipotesi 6 verificata")
    reg("ip7_ok", int(RIS["proxy_corr"]["valore"] >= S["ip7_corr"]), "int", "Ipotesi 7 verificata")
    reg("s_ip1_anno", S["ip1_anno"], "annonum", "Soglia ipotesi 1: anno", "config.py, SOGLIE")
    reg("s_ip2_diff", S["ip2_diff"], "num2", "Soglia ipotesi 2: differenza di correlazione", "config.py, SOGLIE")
    reg("s_ip4_pp", S["ip4_pp"], "pp1", "Soglia ipotesi 4: punti percentuali annui", "config.py, SOGLIE")
    reg("s_ip6_lo", S["ip6_lo"], "pct0", "Soglia ipotesi 6: percentile inferiore", "config.py, SOGLIE")
    reg("s_ip6_hi", S["ip6_hi"], "pct0", "Soglia ipotesi 6: percentile superiore", "config.py, SOGLIE")
    reg("s_ip7_corr", S["ip7_corr"], "num2", "Soglia ipotesi 7: correlazione minima", "config.py, SOGLIE")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri su {n} mesi")


if __name__ == "__main__":
    main()
