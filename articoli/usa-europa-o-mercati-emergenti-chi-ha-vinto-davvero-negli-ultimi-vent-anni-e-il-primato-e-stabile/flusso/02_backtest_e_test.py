"""Passo 2 - USA contro Europa contro emergenti: rendimento, rischio, finestre mobili, correlazioni, persistenza e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv            valore di 1 dollaro nelle tre aree (una seduta su cinque)
  finestre_5anni.csv   rendimento annuo delle finestre mobili di cinque anni a fine mese, per area
  vol_corr.csv         volatilità e correlazioni a un anno mobile (una seduta su cinque)
  scimmie.csv          valore finale di 1 dollaro per ogni scimmia
  bootstrap.csv        differenze di Sharpe ricampionate (USA - Europa, USA - emergenti)
  varianti.csv         controlli di robustezza (altri ETF, altre finestre)
Scimmia: ogni mese sceglie a caso una delle tre aree e prende il rendimento di quel mese (senza costi).
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore as m

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore.py"
GA = config.GIORNI_ANNO


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def carica(ticker: str) -> pd.Series:
    df = pd.read_csv(config.file_dati(ticker), parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    c = df[config.COLONNA_PREZZO].astype(float)
    if (c <= 0).any() or c.isna().any():
        raise SystemExit(f"{ticker}: prezzi mancanti o non positivi.")
    return c


def rendimenti_comuni(gruppo) -> pd.DataFrame:
    """Rendimenti giornalieri sul periodo in cui esistono tutti gli ETF del gruppo (colonne = aree)."""
    serie = {area: carica(t) for t, _, area in gruppo}
    prezzi = pd.concat(serie, axis=1).dropna()
    anni = (prezzi.index[-1] - prezzi.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Storia comune di {anni:.1f} anni: troppo corta.")
    return prezzi.pct_change().dropna()


def analisi_finestre(R: pd.DataFrame, anni_fin: int):
    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    fini = m.fine_mese(R.index)
    lung = anni_fin * GA
    pos, rend = m.rendimento_finestre(cum, fini, lung)
    quote = m.quote_vincitrici(rend)
    ann = (1.0 + rend) ** (1.0 / anni_fin) - 1.0
    return cum, fini, pos, ann, quote


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(config.SEME)
    R = rendimenti_comuni(config.ETF)
    aree = list(R.columns)               # USA, Europa, Emergenti
    sl = {"USA": "usa", "Europa": "eur", "Emergenti": "em"}
    tk = {a: t for t, _, a in config.ETF}
    nome = {a: n for t, n, a in config.ETF}
    anni = (R.index[-1] - R.index[0]).days / 365.25
    reg("prima_data", str(R.index[0].date()), "data_lunga", "Prima seduta con rendimento disponibile per tutti e tre gli ETF", "dati/*.csv")
    reg("data_ultima", str(R.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/*.csv")
    reg("anni", anni, "num1", "Anni del periodo comune", "dati/*.csv")
    reg("n_sedute", len(R), "int", "Sedute di borsa del periodo comune", "dati/*.csv")

    # --- 1. Rendimento e rischio sull'intero periodo ------------------------------------------------------
    B = {}
    for a in aree:
        r = R[a].to_numpy()
        B[a] = {"cagr": m.cagr(r, GA), "vol": m.vol(r, GA), "dd": m.max_dd(r), "sh": m.sharpe(r, GA),
                "fin": config.CAPITALE * m.equity(r)[-1]}
        s = sl[a]
        reg(f"{s}_ticker", tk[a], "testo", f"Ticker dell'ETF per l'area {a}", "config.py, ETF")
        reg(f"{s}_nome", nome[a], "testo", f"Nome dell'ETF per l'area {a}", "config.py, ETF")
        reg(f"{s}_cagr", B[a]["cagr"], "pct1", f"Rendimento annuo composto, dividendi reinvestiti ({a})")
        reg(f"{s}_vol", B[a]["vol"], "pct1", f"Volatilità annua realizzata ({a})")
        reg(f"{s}_dd", B[a]["dd"], "pct1", f"Perdita massima dal picco ({a})")
        reg(f"{s}_sh", B[a]["sh"], "num2", f"Indice di Sharpe con cassa a rendimento zero ({a})")
        reg(f"{s}_finale", B[a]["fin"], "int", f"Valore finale di {config.CAPITALE:.0f} dollari investiti all'inizio ({a})")
    bs = {}
    for altra in ("Europa", "Emergenti"):
        d = m.bootstrap_diff_sharpe(R["USA"], R[altra], config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
        lo, hi = np.percentile(d, [(1 - config.LIVELLO_CONFIDENZA) / 2 * 100, (1 + config.LIVELLO_CONFIDENZA) / 2 * 100])
        bs[altra] = (float(lo), float(hi), d)
        s = sl[altra]
        dif = B["USA"]["sh"] - B[altra]["sh"]
        reg(f"dsh_{s}", dif, "num2", f"Differenza di Sharpe USA meno {altra}")
        reg(f"dsh_{s}_lo", lo, "num2", f"Estremo inferiore dell'intervallo al 95% della differenza di Sharpe USA meno {altra} (bootstrap a blocchi)")
        reg(f"dsh_{s}_hi", hi, "num2", f"Estremo superiore dell'intervallo al 95% della differenza di Sharpe USA meno {altra} (bootstrap a blocchi)")
    pd.DataFrame({"usa_meno_eur": bs["Europa"][2], "usa_meno_em": bs["Emergenti"][2]}).to_csv(
        config.RISULTATI / "bootstrap.csv", index=False, float_format="%.5f")
    reg("ip1_cagr", int(B["USA"]["cagr"] > B["Europa"]["cagr"] and B["USA"]["cagr"] > B["Emergenti"]["cagr"]), "int",
        "1 se gli Stati Uniti hanno il rendimento annuo più alto di entrambe le altre aree, 0 altrimenti")
    reg("ip1_ic_eur_sopra", int(bs["Europa"][0] > 0), "int", "1 se l'intervallo della differenza di Sharpe USA-Europa sta tutto sopra lo zero")
    reg("ip1_ic_em_zero", int(bs["Emergenti"][0] <= 0 <= bs["Emergenti"][1]), "int", "1 se l'intervallo della differenza di Sharpe USA-emergenti contiene lo zero")

    # --- 2. Volatilità a un anno mobile e perdita massima ---------------------------------------------------
    vm = pd.DataFrame({a: m.volatilita_mobile(R[a], config.GIORNI_VOL, GA) for a in aree}).dropna()
    reg("quota_vol_em", float((vm["Emergenti"] > vm["USA"]).mean()), "pct0", "Quota di giorni in cui la volatilità a un anno degli emergenti supera quella degli Stati Uniti")
    reg("quota_vol_eur", float((vm["Europa"] > vm["USA"]).mean()), "pct0", "Quota di giorni in cui la volatilità a un anno dell'Europa supera quella degli Stati Uniti")
    reg("vol_em_min", float((vm["Emergenti"]).min()), "pct0", "Volatilità a un anno più bassa degli emergenti")
    reg("ip2_ok", int((vm["Emergenti"] > vm["USA"]).mean() > 0.90 and B["Emergenti"]["dd"] < B["USA"]["dd"]), "int",
        "1 se gli emergenti hanno volatilità più alta in oltre il 90% dei giorni e perdita massima più profonda")
    reg("ip2_dd_em_peggio", int(B["Emergenti"]["dd"] < B["USA"]["dd"]), "int", "1 se la perdita massima degli emergenti è più profonda di quella degli Stati Uniti")
    reg("ip2_vol_ok", int((vm["Emergenti"] > vm["USA"]).mean() > 0.90), "int", "1 se gli emergenti hanno volatilità più alta in oltre il 90% dei giorni")

    # --- 3. Finestre mobili ----------------------------------------------------------------------------------
    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    var_righe = []
    for anni_fin in config.FINESTRE_ANNI:
        _, fini, pos, ann, quote = analisi_finestre(R, anni_fin)
        if len(pos) == 0:
            continue
        k = f"w{anni_fin}"
        reg(f"{k}_n", len(pos), "int", f"Numero di finestre mobili di {anni_fin} anni (una a fine mese)")
        for j, a in enumerate(aree):
            reg(f"{k}_quota_{sl[a]}", float(quote[j]), "pct0", f"Quota di finestre di {anni_fin} anni in cui l'area {a} ha il rendimento più alto")
            reg(f"{k}_med_{sl[a]}", float(np.median(ann[:, j])), "pct1", f"Rendimento annuo mediano nelle finestre di {anni_fin} anni ({a})")
            var_righe.append({"tipo": f"finestre {anni_fin} anni", "area": a, "quota_prima": quote[j], "mediana_annua": float(np.median(ann[:, j]))})
        if anni_fin == config.FINESTRA_RIF:
            idx = R.index[pos]
            pd.DataFrame(ann, index=idx, columns=aree).rename_axis("data").to_csv(config.RISULTATI / "finestre_5anni.csv", float_format="%.5f")
            reg("w5_max_quota", float(quote.max()), "pct0", "Quota massima di finestre di cinque anni vinta da una singola area")
            reg("w5_min_quota", float(quote.min()), "pct0", "Quota minima di finestre di cinque anni vinta da un'area")
            reg("ip3_ok", int(quote.max() <= config.QUOTA_MAX_VINCITRICE and quote.min() >= config.QUOTA_MIN_VINCITRICE), "int",
                "1 se nessuna area vince oltre il 70% delle finestre di cinque anni e ciascuna almeno il 10%")
            reg("w5_prima_data", str(idx[0].date()), "data_lunga", "Fine della prima finestra di cinque anni")
            for j, a in enumerate(aree):
                reg(f"w5_pos_{sl[a]}", float((ann[:, j] > 0).mean()), "pct0", f"Quota di finestre di cinque anni con rendimento positivo ({a})")
            reg("w5_usa_su_eur", float((ann[:, 0] > ann[:, 1]).mean()), "pct0", "Quota di finestre di cinque anni in cui gli Stati Uniti battono l'Europa")
            reg("w5_usa_su_em", float((ann[:, 0] > ann[:, 2]).mean()), "pct0", "Quota di finestre di cinque anni in cui gli Stati Uniti battono gli emergenti")
            # ultima finestra
            for j, a in enumerate(aree):
                reg(f"w5_ult_{sl[a]}", float(ann[-1, j]), "pct1", f"Rendimento annuo dell'ultima finestra di cinque anni ({a})")

    # --- 4. Correlazioni -----------------------------------------------------------------------------------
    coppie = [("USA", "Europa", "ue"), ("USA", "Emergenti", "um"), ("Europa", "Emergenti", "em")]
    cm = pd.DataFrame({k: m.correlazione_mobile(R[a], R[b], config.GIORNI_VOL) for a, b, k in coppie}).dropna()
    for a, b, k in coppie:
        reg(f"corr_{k}_pieno", float(R[a].corr(R[b])), "num2", f"Correlazione giornaliera {a}-{b} sull'intero periodo")
        reg(f"corr_{k}_med", float(cm[k].median()), "num2", f"Mediana della correlazione a un anno mobile {a}-{b}")
        reg(f"corr_{k}_min", float(cm[k].min()), "num2", f"Minimo della correlazione a un anno mobile {a}-{b}")
        reg(f"corr_{k}_max", float(cm[k].max()), "num2", f"Massimo della correlazione a un anno mobile {a}-{b}")
    reg("ip4_med_ok", int(cm["ue"].median() > config.SOGLIA_CORR), "int", "1 se la mediana della correlazione a un anno USA-Europa supera 0,7")
    casi = 0
    for kk, (et, ini, fin) in enumerate(config.CRISI):
        w = R.loc[ini:fin]
        reg(f"crisi{kk}_nome", et, "testo", "Nome della finestra di crisi", "config.py, CRISI")
        reg(f"crisi{kk}_ini", ini, "data", f"Inizio della finestra «{et}» (fissata prima dei risultati)", "config.py, CRISI")
        reg(f"crisi{kk}_fin", fin, "data", f"Fine della finestra «{et}» (fissata prima dei risultati)", "config.py, CRISI")
        reg(f"crisi{kk}_n", len(w), "int", f"Sedute della finestra «{et}»")
        for a, b, k in coppie[:2]:
            c = float(w[a].corr(w[b]))
            reg(f"crisi{kk}_corr_{k}", c, "num2", f"Correlazione giornaliera {a}-{b} nella finestra «{et}»")
            casi += int(c > R[a].corr(R[b]))
        for a in aree:
            reg(f"crisi{kk}_rend_{sl[a]}", float(np.prod(1 + w[a]) - 1), "pct1", f"Rendimento nella finestra «{et}» ({a})")
    reg("ip4_crisi_casi", casi, "int", "Casi (su quattro) in cui la correlazione nella crisi supera quella dell'intero periodo (USA-Europa e USA-emergenti, due crisi)")
    reg("ip4_ok", int(cm["ue"].median() > config.SOGLIA_CORR and casi >= 3), "int", "1 se l'ipotesi quattro è confermata in entrambe le sue parti")
    reg("soglia_vol_quota", 0.90, "pct0", "Quota di giorni dell'ipotesi due (volatilità degli emergenti più alta)", "config.py, IPOTESI")
    reg("soglia_p", 0.05, "pct0", "Soglia di significatività usata nelle ipotesi cinque e sei", "config.py, IPOTESI")
    reg("crisi_casi_min", 3, "int", "Casi minimi (su quattro) richiesti dall'ipotesi quattro", "config.py, IPOTESI")
    reg("soglia_corr", config.SOGLIA_CORR, "num1", "Soglia di correlazione dell'ipotesi quattro", "config.py, SOGLIA_CORR")

    # --- 5. Persistenza del vincitore ------------------------------------------------------------------------
    fini = m.fine_mese(R.index)
    lung = config.FINESTRA_RIF * GA
    passato, futuro = m.persistenza(cum, fini, lung)
    if len(passato) > 12:
        oss, p = m.p_permutazione(passato, futuro, config.N_PERMUTAZIONI, rng)
        reg("pers_n", len(passato), "int", "Mesi con cinque anni di storia prima e cinque anni dopo (sovrapposti)")
        reg("pers_quota", oss, "pct0", "Quota di mesi in cui l'area vincitrice dei cinque anni precedenti vince anche i cinque successivi")
        reg("pers_p", p, "pval", "p-value del test di permutazione (quota di permutazioni con almeno altrettante coincidenze)")
        reg("pers_caso", 1 / len(aree), "pct0", "Quota attesa dal caso con tre aree equiprobabili", "1/3")
        reg("pers_prima", str(R.index[fini[fini >= lung][0]].date()), "data_lunga", "Primo mese di prova del test di persistenza", "dati/*.csv")
        reg("ip5_ok", int(p > 0.05), "int", "1 se il p-value di persistenza è sopra il 5%")
        # quanti vincitori distinti nel futuro (indice dell'indipendenza effettiva)
        reg("pers_futuro_distinti", len(set(futuro.tolist())), "int", "Aree diverse che risultano vincitrici nei cinque anni successivi")
    else:
        reg("pers_n", len(passato), "int", "Mesi utili per il test di persistenza (troppo pochi)")
        reg("ip5_ok", 0, "int", "1 se il p-value di persistenza è sopra il 5% (test non eseguibile: 0)")

    # --- 6. Scimmie -----------------------------------------------------------------------------------------
    mens = m.rendimenti_mensili(R.to_numpy(), fini)
    fin_sc = m.scimmie_valore_finale(mens, config.N_SCIMMIE, rng)
    bh_usa = float(m.equity(R["USA"].to_numpy())[-1])
    reg("n_scimmie", config.N_SCIMMIE, "int", "Numero di scimmie", "config.py, N_SCIMMIE")
    reg("scim_p_usa", float((fin_sc >= bh_usa).mean()), "pct1", "Quota di scimmie con valore finale uguale o superiore al buy & hold sugli Stati Uniti")
    for a in aree:
        bh = float(m.equity(R[a].to_numpy())[-1])
        reg(f"scim_p_{sl[a]}", float((fin_sc >= bh).mean()), "pct1", f"Quota di scimmie con valore finale uguale o superiore al buy & hold ({a})")
    reg("scim_med_cagr", float(np.median(fin_sc ** (1 / anni) - 1)), "pct1", "Rendimento annuo composto mediano delle scimmie")
    reg("scim_med_fin", float(config.CAPITALE * np.median(fin_sc)), "int", f"Valore finale mediano di {config.CAPITALE:.0f} dollari per le scimmie")
    reg("ip6_ok", int((fin_sc >= bh_usa).mean() < 0.05), "int", "1 se meno del 5% delle scimmie batte il buy & hold sugli Stati Uniti")
    pd.DataFrame({"valore_finale": fin_sc}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.5f")
    reg("bh_usa_finale_rel", bh_usa, "num2", "Valore finale di 1 dollaro nel buy & hold sugli Stati Uniti")

    # --- 7. Robustezza: altri ETF ---------------------------------------------------------------------------
    try:
        R2 = rendimenti_comuni(config.ETF_ALT)
        anni2 = (R2.index[-1] - R2.index[0]).days / 365.25
        reg("alt_prima_data", str(R2.index[0].date()), "data_lunga", "Prima seduta del controllo con VTI, VGK e VWO", "dati/*.csv")
        reg("alt_anni", anni2, "num1", "Anni del periodo comune del controllo con VTI, VGK e VWO")
        for a in R2.columns:
            reg(f"alt_{sl[a]}_cagr", m.cagr(R2[a].to_numpy(), GA), "pct1", f"Rendimento annuo composto nel controllo ({a})")
            reg(f"alt_{sl[a]}_vol", m.vol(R2[a].to_numpy(), GA), "pct1", f"Volatilità annua nel controllo ({a})")
        _, _, pos2, ann2, quote2 = analisi_finestre(R2, config.FINESTRA_RIF)
        for j, a in enumerate(R2.columns):
            reg(f"alt_quota_{sl[a]}", float(quote2[j]), "pct0", f"Quota di finestre di cinque anni vinte nel controllo ({a})")
            var_righe.append({"tipo": "ETF alternativi, finestre 5 anni", "area": a, "quota_prima": quote2[j], "mediana_annua": float(np.median(ann2[:, j]))})
        reg("alt_ordine_uguale", int(np.argsort(-np.array([m.cagr(R2[a].to_numpy(), GA) for a in R2.columns])).tolist()
                                    == np.argsort(-np.array([B[a]["cagr"] for a in aree])).tolist()), "int",
            "1 se nel controllo l'ordine dei rendimenti annui delle tre aree è lo stesso dell'analisi principale")
        reg("alt_ok", 1, "int", "1 se il controllo con altri ETF è stato eseguito")
    except SystemExit as e:
        reg("alt_ok", 0, "int", f"1 se il controllo con altri ETF è stato eseguito (non eseguibile: {e})")

    # --- parametri e fonti ---------------------------------------------------------------------------------
    reg("giorni_anno", GA, "int", "Giorni di borsa in un anno per annualizzare", "config.py, GIORNI_ANNO")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale di riferimento in dollari", "config.py, CAPITALE")
    reg("giorni_vol", config.GIORNI_VOL, "int", "Giorni di borsa della finestra a un anno per volatilità e correlazione", "config.py, GIORNI_VOL")
    reg("n_bootstrap", config.N_BOOTSTRAP, "int", "Ricampionamenti del bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py, BLOCCO_BOOTSTRAP")
    reg("n_permutazioni", config.N_PERMUTAZIONI, "int", "Permutazioni del test di persistenza", "config.py, N_PERMUTAZIONI")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello di confidenza", "config.py, LIVELLO_CONFIDENZA")
    reg("quota_max", config.QUOTA_MAX_VINCITRICE, "pct0", "Quota massima di finestre per una singola area, ipotesi tre", "config.py")
    reg("quota_min", config.QUOTA_MIN_VINCITRICE, "pct0", "Quota minima di finestre per ciascuna area, ipotesi tre", "config.py")
    for i, f in enumerate(config.FINESTRE_ANNI):
        reg(f"finestra{i}", f, "int", "Anni di una finestra mobile", "config.py, FINESTRE_ANNI")
    reg("finestra_rif", config.FINESTRA_RIF, "int", "Anni della finestra mobile di riferimento", "config.py, FINESTRA_RIF")
    reg("lit_ls_anno", 1995, "annonum", "Anno di Longin e Solnik, Journal of International Money and Finance", "riferimento bibliografico")
    reg("lit_bu_anno", 1996, "annonum", "Anno di Bekaert e Urias, Journal of Finance (volume 51)", "riferimento bibliografico")
    reg("lit_ls_paesi", 7, "int", "Paesi studiati da Longin e Solnik, secondo l'abstract", "abstract dell'articolo")
    reg("lit_ls_anno_ini", 1960, "annonum", "Primo anno del periodo studiato da Longin e Solnik", "titolo dell'articolo")
    reg("lit_ls_anno_fin", 1990, "annonum", "Ultimo anno del periodo studiato da Longin e Solnik", "titolo dell'articolo")
    reg("lit_bu_paesi", 6, "int", "Paesi per i quali Bekaert e Urias stimano le barriere agli investimenti, secondo l'abstract", "abstract dell'articolo")
    reg("run_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"), "testo", "Data di esecuzione dell'analisi", "02_backtest_e_test.py")

    # --- file -----------------------------------------------------------------------------------------------
    c = pd.DataFrame(cum, index=R.index, columns=aree).iloc[::5]
    c.rename_axis("data").to_csv(config.RISULTATI / "curve.csv", float_format="%.6f")
    pd.concat([vm.add_prefix("vol_"), cm.add_prefix("corr_")], axis=1).dropna().iloc[::5].rename_axis("data").to_csv(
        config.RISULTATI / "vol_corr.csv", float_format="%.5f")
    pd.DataFrame(var_righe).to_csv(config.RISULTATI / "varianti.csv", index=False, float_format="%.5f")
    json.dump({"valori": RIS}, open(config.RISULTATI / "metriche.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Scritti {len(RIS)} numeri in metriche.json")


if __name__ == "__main__":
    main()
