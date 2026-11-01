"""Passo 2 - Azioni contro obbligazioni (VFINX contro VBMFX): rendimento, rischio, finestre mobili a 5, 10 e 20 anni, fasi di crisi e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv           valore di 1 dollaro nei due fondi (una seduta su cinque)
  finestre_rif.csv    rendimento annuo delle finestre mobili di dieci anni a fine mese, per fondo
  quote_orizzonti.csv per ogni orizzonte: quota di finestre vinte dalle azioni e rendimenti peggiori/migliori
  bootstrap.csv       differenze di Sharpe ricampionate (azioni - obbligazioni)
  scimmie.csv         valore finale di 1 dollaro per ogni scimmia
Scimmia: ogni mese sceglie a caso uno dei due fondi e prende il rendimento di quel mese (senza costi).
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
MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
           "novembre", "dicembre"]


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


def sotto_acqua(equity: np.ndarray, date: pd.DatetimeIndex) -> dict:
    """Massima perdita dal picco: date di picco, minimo e (se avvenuto) recupero."""
    picco = np.maximum.accumulate(equity)
    dd = equity / picco - 1
    t = int(np.argmin(dd))
    p = int(np.argmax(equity[: t + 1]))
    rec = np.flatnonzero(equity[t:] >= equity[p])
    return {"dd": float(dd[t]), "picco": date[p], "minimo": date[t], "recupero": date[t + int(rec[0])] if len(rec) else None}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    sigle = [s for _, _, s in config.ETF]
    prezzi = pd.concat({s: carica(t) for t, _, s in config.ETF}, axis=1).dropna()
    anni = (prezzi.index[-1] - prezzi.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Storia comune di {anni:.1f} anni: troppo corta.")
    R = prezzi.pct_change().dropna()
    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    fini = m.fine_mese(R.index)
    rng = np.random.default_rng(config.SEME)
    ci = {s: i for i, s in enumerate(sigle)}
    A, B = "AZIONI", "OBBLIG"

    reg("data_inizio", str(prezzi.index[0].date()), "data_lunga", "Prima seduta in comune dei due fondi", "dati/")
    reg("data_ultima", str(prezzi.index[-1].date()), "data_lunga", "Ultima seduta nei dati", "dati/")
    reg("anni", anni, "num1", "Anni di storia comune", "dati/")
    reg("n_sedute", len(R), "int", "Rendimenti giornalieri in comune", "dati/")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per tradurre i rendimenti in dollari", "config.py, CAPITALE")
    reg("h2_min", config.H2_MIN, "pct0", "Ipotesi 2: quota minima di finestre di venti anni con le azioni davanti", "config.py")
    reg("h4_soglia", config.H4_SOGLIA, "pct0", "Ipotesi 4: soglia della perdita massima delle obbligazioni", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate", "config.py, N_SCIMMIE")
    reg("n_boot", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py, BLOCCO_BOOTSTRAP")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    for k, a in enumerate(config.FINESTRE_ANNI):
        reg(f"orizz{k}", a, "annonum", f"Orizzonte numero {k + 1} delle finestre mobili, in anni", "config.py, FINESTRE_ANNI")
    reg("anno_bodie", 1995, "annonum", "Anno dell'articolo di Bodie citato nel testo", "Financial Analysts Journal, vol. 51 n. 3")
    reg("anno_pastor", 2012, "annonum", "Anno dell'articolo di Pástor e Stambaugh citato nel testo", "The Journal of Finance")

    # --- Periodo comune -----------------------------------------------------------------------------------------
    stat = {}
    for s in sigle:
        r = R[s].to_numpy()
        e = m.equity(r)
        stat[s] = dict(cagr=m.cagr(r, GA), vol=m.vol(r, GA), sharpe=m.sharpe(r, GA), dd=m.max_dd(r),
                       finale=config.CAPITALE * float(e[-1]), tot=float(e[-1] - 1),
                       ua=sotto_acqua(np.r_[1.0, e], R.index.insert(0, prezzi.index[0])))
        k = s.lower()
        nome = "le azioni" if s == A else "le obbligazioni"
        reg(f"{k}_cagr", stat[s]["cagr"], "pct1", f"Rendimento annuo composto di {nome} (dividendi e cedole reinvestiti)", "motore.cagr")
        reg(f"{k}_vol", stat[s]["vol"], "pct1", f"Volatilità annua di {nome}", "motore.vol")
        reg(f"{k}_sharpe", stat[s]["sharpe"], "num2", f"Rapporto di Sharpe di {nome} (tasso privo di rischio zero)", "motore.sharpe")
        reg(f"{k}_dd", -stat[s]["dd"], "pct0", f"Perdita massima dal picco di {nome}", "motore.max_dd")
        reg(f"{k}_finale", stat[s]["finale"], "int", f"Valore finale del capitale iniziale in {nome}", "motore.equity")
        ua = stat[s]["ua"]
        reg(f"{k}_dd_picco", f"{MESI_IT[ua['picco'].month - 1]} {ua['picco'].year}", "testo", f"Mese del picco prima della perdita massima di {nome}", "dati/")
        reg(f"{k}_dd_minimo", f"{MESI_IT[ua['minimo'].month - 1]} {ua['minimo'].year}", "testo", f"Mese del minimo della perdita massima di {nome}", "dati/")
        if ua["recupero"] is not None:
            reg(f"{k}_dd_recupero_anni", (ua["recupero"] - ua["picco"]).days / 365.25, "num1", f"Anni dal picco al pieno recupero della perdita massima di {nome}", "dati/")
            reg(f"{k}_dd_recupero", f"{MESI_IT[ua['recupero'].month - 1]} {ua['recupero'].year}", "testo", f"Mese del pieno recupero della perdita massima di {nome}", "dati/")
        else:
            reg(f"{k}_dd_non_recuperato", 1, "int", f"1 se {nome} non ha ancora recuperato la perdita massima", "dati/")
    reg("diff_cagr", stat[A]["cagr"] - stat[B]["cagr"], "pp1", "Rendimento annuo composto delle azioni meno quello delle obbligazioni, in punti percentuali", "motore.cagr")
    reg("rapporto_finale", stat[A]["finale"] / stat[B]["finale"], "num1", "Valore finale delle azioni diviso quello delle obbligazioni", "motore.equity")
    reg("corr", float(np.corrcoef(R[A], R[B])[0, 1]), "num2", "Correlazione dei rendimenti giornalieri tra azioni e obbligazioni", "numpy.corrcoef")

    # --- Bootstrap della differenza di Sharpe ---------------------------------------------------------------------
    boot = m.bootstrap_diff_sharpe(R[A].to_numpy(), R[B].to_numpy(), config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
    lo, hi = np.quantile(boot, [(1 - config.LIVELLO_CONFIDENZA) / 2, 1 - (1 - config.LIVELLO_CONFIDENZA) / 2])
    d0 = stat[A]["sharpe"] - stat[B]["sharpe"]
    reg("diff_sharpe", d0, "num2", "Sharpe delle azioni meno Sharpe delle obbligazioni", "motore.sharpe")
    reg("diff_sharpe_lo", float(lo), "num2", "Estremo inferiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    reg("diff_sharpe_hi", float(hi), "num2", "Estremo superiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    pd.DataFrame({"diff_sharpe": boot}).to_csv(config.RISULTATI / "bootstrap.csv", index=False, float_format="%.5f")

    # --- Finestre mobili --------------------------------------------------------------------------------------------
    righe_q = []
    quote_az = []
    for k, anni_fin in enumerate(config.FINESTRE_ANNI):
        pos, rend = m.rendimento_finestre(cum, fini, anni_fin * GA)
        if len(pos) < 24:
            raise SystemExit(f"Poche finestre a {anni_fin} anni: {len(pos)}")
        quote = m.quote_vincitrici(rend)
        ann = (1.0 + rend) ** (1.0 / anni_fin) - 1.0
        qa = float(quote[ci[A]])
        quote_az.append(qa)
        reg(f"fin{k}_n", len(pos), "int", f"Finestre mobili di {anni_fin} anni (a fine mese)", "motore.rendimento_finestre")
        reg(f"fin{k}_quota_az", qa, "pct0", f"Quota di finestre di {anni_fin} anni in cui le azioni rendono più delle obbligazioni", "motore.quote_vincitrici")
        reg(f"fin{k}_quota_ob", float(quote[ci[B]]), "pct0", f"Quota di finestre di {anni_fin} anni in cui le obbligazioni rendono più delle azioni", "motore.quote_vincitrici")
        pa, ma = float(ann[:, ci[A]].min()), float(ann[:, ci[A]].max())
        pb, mb = float(ann[:, ci[B]].min()), float(ann[:, ci[B]].max())
        reg(f"fin{k}_peggio_az", pa, "pct1", f"Peggior rendimento annuo delle azioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{k}_miglio_az", ma, "pct1", f"Miglior rendimento annuo delle azioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{k}_peggio_ob", pb, "pct1", f"Peggior rendimento annuo delle obbligazioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{k}_miglio_ob", mb, "pct1", f"Miglior rendimento annuo delle obbligazioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{k}_neg_az", float((ann[:, ci[A]] < 0).mean()), "pct0", f"Quota di finestre di {anni_fin} anni con rendimento negativo per le azioni", "motore.rendimento_finestre")
        reg(f"fin{k}_neg_ob", float((ann[:, ci[B]] < 0).mean()), "pct0", f"Quota di finestre di {anni_fin} anni con rendimento negativo per le obbligazioni", "motore.rendimento_finestre")
        reg(f"fin{k}_mediana_az", float(np.median(ann[:, ci[A]])), "pct1", f"Rendimento annuo mediano delle azioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{k}_mediana_ob", float(np.median(ann[:, ci[B]])), "pct1", f"Rendimento annuo mediano delle obbligazioni su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        righe_q.append({"anni": anni_fin, "finestre": len(pos), "quota_azioni": qa, "peggio_azioni": pa, "migliore_azioni": ma,
                        "peggio_obblig": pb, "migliore_obblig": mb})
        if anni_fin == config.FINESTRA_RIF:
            out = pd.DataFrame(ann, columns=sigle)
            out.insert(0, "data", R.index[pos].strftime("%Y-%m-%d"))
            out.to_csv(config.RISULTATI / "finestre_rif.csv", index=False, float_format="%.5f")
    pd.DataFrame(righe_q).to_csv(config.RISULTATI / "quote_orizzonti.csv", index=False, float_format="%.5f")
    reg("fin_rif_anni", config.FINESTRA_RIF, "annonum", "Anni della finestra mostrata nel grafico", "config.py, FINESTRA_RIF")

    # --- Fasi di crisi -----------------------------------------------------------------------------------------------
    crisi_ok = []
    for k, (nome, a, b) in enumerate(config.CRISI):
        sub = prezzi.loc[a:b]
        if len(sub) < 10:
            raise SystemExit(f"Fase «{nome}» senza dati sufficienti")
        ra = float(sub[A].iloc[-1] / sub[A].iloc[0] - 1)
        rb = float(sub[B].iloc[-1] / sub[B].iloc[0] - 1)
        reg(f"crisi{k}_nome", nome, "testo", "Nome della fase", "config.py, CRISI")
        reg(f"crisi{k}_az", ra, "pct1", f"Rendimento delle azioni nella fase «{nome}»", "dati/")
        reg(f"crisi{k}_ob", rb, "pct1", f"Rendimento delle obbligazioni nella fase «{nome}»", "dati/")
        crisi_ok.append((ra, rb))
    n_ob_meglio = sum(int(rb > ra) for ra, rb in crisi_ok[: config.N_CROLLI_AZIONARI])
    reg("n_crolli", config.N_CROLLI_AZIONARI, "int", "Crolli azionari fissati in anticipo", "config.py, N_CROLLI_AZIONARI")
    reg("n_ob_meglio", n_ob_meglio, "int", "Crolli azionari in cui le obbligazioni rendono più delle azioni", "dati/")
    ra22, rb22 = crisi_ok[config.N_CROLLI_AZIONARI]
    ambedue_neg = bool(ra22 < 0 and rb22 < 0)

    # --- Scimmie ---------------------------------------------------------------------------------------------------
    mensili = m.rendimenti_mensili(R.to_numpy(), fini)
    fin = m.scimmie_valore_finale(mensili, config.N_SCIMMIE, rng)
    bh = np.prod(1.0 + mensili, axis=0)
    pd.DataFrame({"finale": fin}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.5f")
    reg("sc_mediana", config.CAPITALE * float(np.median(fin)), "int", "Valore finale mediano delle scimmie (scelta casuale tra i due fondi ogni mese)", "scimmie.csv")
    reg("sc_p5", config.CAPITALE * float(np.percentile(fin, 5)), "int", "Quinto percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_p95", config.CAPITALE * float(np.percentile(fin, 95)), "int", "Novantacinquesimo percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_batte_ob", float((fin > bh[ci[B]]).mean()), "pct0", "Quota di scimmie che chiudono sopra le sole obbligazioni", "scimmie.csv")
    reg("sc_batte_az", float((fin > bh[ci[A]]).mean()), "pct0", "Quota di scimmie che chiudono sopra le sole azioni", "scimmie.csv")

    camp = np.arange(0, len(R), 5)
    pd.DataFrame({"data": R.index[camp].strftime("%Y-%m-%d"), "azioni": cum[camp, ci[A]], "obblig": cum[camp, ci[B]]}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.5f")

    # --- Verdetti sulle ipotesi -----------------------------------------------------------------------------------
    h = [quote_az[0] < quote_az[1] < quote_az[2],
         quote_az[2] >= config.H2_MIN,
         RIS["fin0_peggio_az"]["valore"] < 0 and RIS["fin2_peggio_az"]["valore"] > 0,
         -stat[B]["dd"] > config.H4_SOGLIA,
         bool(lo <= 0 <= hi),
         n_ob_meglio == config.N_CROLLI_AZIONARI and ambedue_neg]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")
    reg("h6_crolli", int(n_ob_meglio == config.N_CROLLI_AZIONARI), "int", "Ipotesi 6, prima parte: 1 se le obbligazioni battono le azioni in tutti i crolli", "dati/")
    reg("h6_2022", int(ambedue_neg), "int", "Ipotesi 6, seconda parte: 1 se nel 2022 azioni e obbligazioni perdono tutte e due", "dati/")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pandas": pd.__version__,
           "numpy": np.__version__, "ipotesi": config.IPOTESI, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
