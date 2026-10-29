"""Passo 2 - Tech contro il resto: rendimento, rischio, finestre mobili, fasi di crisi, persistenza e scimmie.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv            valore di 1 dollaro in tecnologia e nel resto (una seduta su cinque)
  finestre_5anni.csv   rendimento annuo delle finestre mobili di cinque anni a fine mese, per portafoglio
  bootstrap.csv        differenze di Sharpe ricampionate (tecnologia - resto)
  scimmie.csv          valore finale di 1 dollaro per ogni scimmia
Scimmia: ogni mese sceglie a caso tra tecnologia e resto e prende il rendimento di quel mese (senza costi).
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
    out = {"dd": float(dd[t]), "picco": date[p], "minimo": date[t], "recupero": date[t + int(rec[0])] if len(rec) else None}
    return out


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    sigle = ["XLK", "RESTO"]
    tutti = pd.concat({t: carica(t) for t, _, _ in config.ETF}, axis=1).dropna()
    anni = (tutti.index[-1] - tutti.index[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Storia comune di {anni:.1f} anni: troppo corta.")
    ret = tutti.pct_change().dropna()
    # il resto: media a pesi uguali, ribilanciata ogni giorno, degli altri otto settori
    R = pd.DataFrame({"XLK": ret["XLK"], "RESTO": ret.drop(columns="XLK").mean(axis=1)})
    prezzi = (1.0 + R).cumprod()
    cum = np.cumprod(1.0 + R.to_numpy(), axis=0)
    fini = m.fine_mese(R.index)
    rng = np.random.default_rng(config.SEME)
    ci = {s: i for i, s in enumerate(sigle)}
    A, B = "XLK", "RESTO"

    reg("data_inizio", str(tutti.index[0].date()), "data_lunga", "Prima seduta in comune dei nove ETF", "dati/")
    reg("data_ultima", str(tutti.index[-1].date()), "data_lunga", "Ultima seduta nei dati", "dati/")
    reg("anni", anni, "num1", "Anni di storia comune dei nove ETF", "dati/")
    reg("n_sedute", len(R), "int", "Rendimenti giornalieri in comune", "dati/")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per tradurre i rendimenti in dollari", "config.py, CAPITALE")
    reg("soglia_dd", config.H2_DD_PUNTI, "pp1", "Ipotesi 2: scarto minimo di perdita massima (tecnologia meno resto) in punti percentuali", "config.py")
    reg("h4_min", config.H4_MIN, "pct0", "Ipotesi 4: quota minima di finestre di cinque anni con la tecnologia davanti", "config.py")
    reg("h4_max", config.H4_MAX, "pct0", "Ipotesi 4: quota massima di finestre di cinque anni con la tecnologia davanti", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate", "config.py, N_SCIMMIE")
    reg("n_perm", config.N_PERMUTAZIONI, "int", "Permutazioni del test di persistenza", "config.py, N_PERMUTAZIONI")
    reg("n_boot", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py, BLOCCO_BOOTSTRAP")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("soglia", 0.05, "pct0", "Livello di significatività dei test", "convenzione")

    # --- Periodo comune -----------------------------------------------------------------------------------------
    stat = {}
    for s in sigle:
        r = R[s].to_numpy()
        e = m.equity(r)
        stat[s] = dict(cagr=m.cagr(r, GA), vol=m.vol(r, GA), sharpe=m.sharpe(r, GA), dd=m.max_dd(r),
                       finale=config.CAPITALE * float(e[-1]), tot=float(e[-1] - 1), ua=sotto_acqua(np.r_[1.0, e], R.index.insert(0, tutti.index[0])))
        k = s.lower()
        reg(f"{k}_cagr", stat[s]["cagr"], "pct1", f"Rendimento annuo composto di prezzo di {s} (solo prezzo)", "motore.cagr")
        reg(f"{k}_vol", stat[s]["vol"], "pct1", f"Volatilità annua di {s}", "motore.vol")
        reg(f"{k}_sharpe", stat[s]["sharpe"], "num2", f"Rapporto di Sharpe di {s} (tasso privo di rischio zero)", "motore.sharpe")
        reg(f"{k}_dd", -stat[s]["dd"], "pct0", f"Perdita massima dal picco di {s}", "motore.max_dd")
        reg(f"{k}_finale", stat[s]["finale"], "int", f"Valore finale del capitale iniziale in {s}", "motore.equity")
        reg(f"{k}_tot", stat[s]["tot"], "pct0", f"Rendimento totale di {s} nel periodo", "motore.equity")
        ua = stat[s]["ua"]
        reg(f"{k}_dd_picco", f"{MESI_IT[ua['picco'].month - 1]} {ua['picco'].year}", "testo", f"Mese del picco prima della perdita massima di {s}", "dati/")
        reg(f"{k}_dd_minimo", f"{MESI_IT[ua['minimo'].month - 1]} {ua['minimo'].year}", "testo", f"Mese del minimo della perdita massima di {s}", "dati/")
        if ua["recupero"] is not None:
            reg(f"{k}_dd_recupero_anni", (ua["recupero"] - ua["picco"]).days / 365.25, "num1", f"Anni dal picco al pieno recupero della perdita massima di {s}", "dati/")
            reg(f"{k}_dd_recupero", f"{MESI_IT[ua['recupero'].month - 1]} {ua['recupero'].year}", "testo", f"Mese del pieno recupero della perdita massima di {s}", "dati/")
        else:
            reg(f"{k}_dd_non_recuperato", 1, "int", f"1 se {s} non ha ancora recuperato la perdita massima", "dati/")
    reg("diff_cagr", stat[A]["cagr"] - stat[B]["cagr"], "pp1", "Rendimento annuo composto della tecnologia meno quello del resto, in punti percentuali", "motore.cagr")
    reg("diff_dd", stat[B]["dd"] - stat[A]["dd"], "pp1", "Perdita massima della tecnologia meno quella del resto, in punti percentuali", "motore.max_dd")
    reg("diff_vol", stat[A]["vol"] - stat[B]["vol"], "pp1", "Volatilità della tecnologia meno quella del resto, in punti percentuali", "motore.vol")
    reg("rapporto_finale", stat[A]["finale"] / stat[B]["finale"], "num2", "Valore finale della tecnologia diviso quello del resto", "motore.equity")
    reg("corr", float(np.corrcoef(R[A], R[B])[0, 1]), "num2", "Correlazione dei rendimenti giornalieri tra tecnologia e resto", "numpy.corrcoef")

    # --- Bootstrap della differenza di Sharpe ---------------------------------------------------------------------
    boot = m.bootstrap_diff_sharpe(R[A].to_numpy(), R[B].to_numpy(), config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
    lo, hi = np.quantile(boot, [(1 - config.LIVELLO_CONFIDENZA) / 2, 1 - (1 - config.LIVELLO_CONFIDENZA) / 2])
    d0 = stat[A]["sharpe"] - stat[B]["sharpe"]
    reg("diff_sharpe", d0, "num2", "Sharpe della tecnologia meno Sharpe del resto", "motore.sharpe")
    reg("diff_sharpe_lo", float(lo), "num2", "Estremo inferiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    reg("diff_sharpe_hi", float(hi), "num2", "Estremo superiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    pd.DataFrame({"diff_sharpe": boot}).to_csv(config.RISULTATI / "bootstrap.csv", index=False, float_format="%.5f")

    # --- Finestre mobili --------------------------------------------------------------------------------------------
    for anni_fin in config.FINESTRE_ANNI:
        pos, rend = m.rendimento_finestre(cum, fini, anni_fin * GA)
        quote = m.quote_vincitrici(rend)
        ann = (1.0 + rend) ** (1.0 / anni_fin) - 1.0
        reg(f"fin{anni_fin}_n", len(pos), "int", f"Finestre mobili di {anni_fin} anni (a fine mese)", "motore.rendimento_finestre")
        reg(f"fin{anni_fin}_quota_xlk", float(quote[ci[A]]), "pct0", f"Quota di finestre di {anni_fin} anni in cui la tecnologia rende più del resto", "motore.quote_vincitrici")
        reg(f"fin{anni_fin}_quota_resto", float(quote[ci[B]]), "pct0", f"Quota di finestre di {anni_fin} anni in cui il resto rende più della tecnologia", "motore.quote_vincitrici")
        reg(f"fin{anni_fin}_peggio_xlk", float(ann[:, ci[A]].min()), "pct0", f"Peggior rendimento annuo della tecnologia su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{anni_fin}_miglio_xlk", float(ann[:, ci[A]].max()), "pct0", f"Miglior rendimento annuo della tecnologia su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{anni_fin}_peggio_resto", float(ann[:, ci[B]].min()), "pct0", f"Peggior rendimento annuo del resto su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        reg(f"fin{anni_fin}_miglio_resto", float(ann[:, ci[B]].max()), "pct0", f"Miglior rendimento annuo del resto su finestre di {anni_fin} anni", "motore.rendimento_finestre")
        if anni_fin == config.FINESTRA_RIF:
            out = pd.DataFrame(ann, columns=sigle)
            out.insert(0, "data", R.index[pos].strftime("%Y-%m-%d"))
            out.to_csv(config.RISULTATI / "finestre_5anni.csv", index=False, float_format="%.5f")
            ultima_xlk = bool(ann[-1, ci[A]] > ann[-1, ci[B]])
            reg("fin_rif_ultima_xlk", int(ultima_xlk), "int", "1 se nell'ultima finestra di riferimento la tecnologia rende più del resto", "motore.rendimento_finestre")
    reg("fin_rif_anni", config.FINESTRA_RIF, "annonum", "Anni della finestra di riferimento", "config.py, FINESTRA_RIF")

    # --- Fasi di crisi -----------------------------------------------------------------------------------------------
    n_peggio = 0
    for k, (nome, a, b) in enumerate(config.CRISI):
        sub = prezzi.loc[a:b]
        if len(sub) < 20:
            continue
        ra = float(sub[A].iloc[-1] / sub[A].iloc[0] - 1)
        rb = float(sub[B].iloc[-1] / sub[B].iloc[0] - 1)
        reg(f"crisi{k}_nome", nome, "testo", "Nome della fase di crisi", "config.py, CRISI")
        reg(f"crisi{k}_xlk", ra, "pct0", f"Rendimento della tecnologia nella fase «{nome}»", "dati/")
        reg(f"crisi{k}_resto", rb, "pct0", f"Rendimento del resto nella fase «{nome}»", "dati/")
        reg(f"crisi{k}_xlk_peggio", int(ra < rb), "int", f"1 se la tecnologia perde più del resto nella fase «{nome}»", "dati/")
        n_peggio += int(ra < rb)
    reg("n_crisi_xlk_peggio", n_peggio, "int", "Fasi di crisi in cui la tecnologia rende meno del resto", "dati/")
    reg("n_crisi", len(config.CRISI), "int", "Fasi di crisi fissate in anticipo", "config.py, CRISI")

    # --- Persistenza ----------------------------------------------------------------------------------------------
    passato, futuro = m.persistenza(cum, fini, config.FINESTRA_RIF * GA)
    oss, p_perm = m.p_permutazione(passato, futuro, config.N_PERMUTAZIONI, rng)
    reg("pers_n", len(passato), "int", "Mesi usati nel test di persistenza", "motore.persistenza")
    reg("pers_quota", oss, "pct0", "Quota di mesi in cui il vincitore dei cinque anni precedenti vince anche nei cinque successivi", "motore.p_permutazione")
    reg("pers_p", p_perm, "pval", "P-value del test di permutazione per la persistenza del vincitore", "motore.p_permutazione")
    reg("pers_atteso", 0.5, "pct0", "Quota attesa per puro caso con due alternative", "calcolo")

    # --- Scimmie ---------------------------------------------------------------------------------------------------
    mensili = m.rendimenti_mensili(R.to_numpy(), fini)
    fin = m.scimmie_valore_finale(mensili, config.N_SCIMMIE, rng)
    bh = np.prod(1.0 + mensili, axis=0)
    pd.DataFrame({"finale": fin}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.5f")
    reg("sc_mediana", config.CAPITALE * float(np.median(fin)), "int", "Valore finale mediano delle scimmie (scelta casuale tra tecnologia e resto ogni mese)", "scimmie.csv")
    reg("sc_p5", config.CAPITALE * float(np.percentile(fin, 5)), "int", "Quinto percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_p95", config.CAPITALE * float(np.percentile(fin, 95)), "int", "Novantacinquesimo percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_batte_resto", float((fin > bh[ci[B]]).mean()), "pct0", "Quota di scimmie che chiudono sopra il resto", "scimmie.csv")
    reg("sc_batte_xlk", float((fin > bh[ci[A]]).mean()), "pct0", "Quota di scimmie che chiudono sopra la tecnologia", "scimmie.csv")
    reg("sc_tra", int(min(stat[A]["finale"], stat[B]["finale"]) <= config.CAPITALE * float(np.median(fin)) <= max(stat[A]["finale"], stat[B]["finale"])), "int", "1 se il valore finale mediano delle scimmie sta tra quello del resto e quello della tecnologia", "scimmie.csv")

    camp = np.arange(0, len(R), 5)
    pd.DataFrame({"data": R.index[camp].strftime("%Y-%m-%d"), "resto": cum[camp, ci[B]], "xlk": cum[camp, ci[A]]}).to_csv(
        config.RISULTATI / "curve.csv", index=False, float_format="%.5f")

    # --- Verdetti sulle ipotesi -----------------------------------------------------------------------------------
    quota5 = float(m.quote_vincitrici(m.rendimento_finestre(cum, fini, config.FINESTRA_RIF * GA)[1])[ci[A]])
    h = [stat[A]["cagr"] > stat[B]["cagr"],
         stat[A]["vol"] > stat[B]["vol"] and (stat[B]["dd"] - stat[A]["dd"]) >= config.H2_DD_PUNTI,
         bool(lo <= 0 <= hi),
         config.H4_MIN <= quota5 <= config.H4_MAX,
         p_perm > 0.05,
         RIS["crisi0_xlk_peggio"]["valore"] == 1 and RIS["crisi2_xlk_peggio"]["valore"] == 1,
         RIS["sc_tra"]["valore"] == 1]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su sette)", "confronto con config.py")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pandas": pd.__version__,
           "numpy": np.__version__, "ipotesi": config.IPOTESI, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
