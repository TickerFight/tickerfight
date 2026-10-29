"""Passo 2 - Dogs of the Dow: i dieci titoli a più alto rendimento da dividendo contro l'universo, lo SPY e la sorte.

Legge SOLO i file in dati/ e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv         valore di 1 dollaro per Dogs, universo e SPY (una seduta su cinque)
  annuali.csv       rendimento di ogni anno intero per Dogs, universo, SPY (e varianti)
  scelte.csv        i titoli scelti a fine di ogni anno e il loro rendimento da dividendo
  bootstrap.csv     differenze di Sharpe ricampionate (Dogs - universo)
  scimmie.csv       valore finale di 1 dollaro per ogni scimmia
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


def leggi(file) -> pd.DataFrame:
    df = pd.read_csv(file, parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[~df.index.duplicated(keep="last")]


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    adj, close, div = leggi(config.FILE_ADJ), leggi(config.FILE_CLOSE), leggi(config.FILE_DIV)
    idx = adj[config.INDICE].dropna().index
    adj, close = adj.reindex(idx), close.reindex(idx)
    titoli = [t for t in config.UNIVERSO if t in adj.columns]
    ultima = idx[-1]
    fine_anno = pd.Series(idx, index=idx).groupby(idx.year).last()          # ultimo giorno di Borsa di ogni anno
    anni_f = [a for a in range(config.PRIMO_ANNO_FORMAZIONE, ultima.year) if a in fine_anno.index]
    rng = np.random.default_rng(config.SEME)

    righe = {k: [] for k in ("d10", "d5", "bassi", "uni", "spy")}
    date_g, annuali, scelte = [], [], []
    rend_ann = np.zeros((len(anni_f), len(titoli)))
    disp = np.zeros((len(anni_f), len(titoli)), dtype=bool)
    prec_d10 = None
    ricambi, yd_dogs, yd_uni, n_disp = [], [], [], []
    for j, F in enumerate(anni_f):
        Y = F + 1
        s = fine_anno[F]
        e = fine_anno[Y] if Y < ultima.year else ultima
        anno_f = adj.index[(adj.index.year == F) & (adj.index <= s)]
        storia = adj.loc[anno_f, titoli].notna().sum().to_numpy()
        ok = (storia >= config.MIN_STORIA_GG) & adj.loc[s, titoli].notna().to_numpy() & adj.loc[e, titoli].notna().to_numpy()
        dv = div.reindex(columns=titoli).loc[(div.index.year == F) & (div.index <= s)].sum().to_numpy()
        yld = m.rendimento_da_dividendo(dv, close.loc[s, titoli].to_numpy())
        yld = np.where(ok, yld, 0.0)
        sel = {"d10": m.scegli_alti(yld, ok, config.K_DOGS), "d5": m.scegli_alti(yld, ok, config.K_PICCOLI),
               "bassi": m.scegli_alti(yld, ok, config.K_DOGS, bassi=True), "uni": np.flatnonzero(ok)}
        P = adj.loc[s:e, titoli].to_numpy()
        for k, pos in sel.items():
            righe[k].append(m.rendimenti_giornalieri_pesi_uguali(P[:, pos]))
        righe["spy"].append(m.rendimenti_giornalieri_pesi_uguali(adj.loc[s:e, [config.INDICE]].to_numpy()))
        date_g.append(adj.loc[s:e].index[1:])
        rend_ann[j] = np.where(ok, P[-1] / P[0] - 1.0, 0.0)
        disp[j] = ok
        n_disp.append(int(ok.sum()))
        yd_dogs.append(float(yld[sel["d10"]].mean()))
        yd_uni.append(float(yld[ok].mean()))
        if prec_d10 is not None:
            ricambi.append(len(set(sel["d10"]) - prec_d10) / config.K_DOGS)
        prec_d10 = set(sel["d10"])
        scelte.append({"anno_acquisto": F, "anno_detenzione": Y, "titoli": " ".join(titoli[i] for i in sel["d10"]),
                       "rend_div_medio": float(yld[sel["d10"]].mean())})
        annuali.append({"anno": Y, "completo": int(Y < ultima.year), **{k: float(np.prod(1 + righe[k][-1]) - 1) for k in righe}})
    date = date_g[0].append(date_g[1:]) if len(date_g) > 1 else date_g[0]
    R = {k: np.concatenate(v) for k, v in righe.items()}
    T = len(date)
    anni = (date[-1] - date[0]).days / 365.25
    if anni < config.ANNI_MINIMI:
        raise SystemExit(f"Periodo di {anni:.1f} anni: troppo corto.")
    A = pd.DataFrame(annuali)
    comp = A[A["completo"] == 1]

    reg("data_inizio", str(date[0].date()), "data_lunga", "Primo giorno del periodo con i Dogs in portafoglio", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta nei dati", "dati/")
    reg("anni", anni, "num1", "Anni del periodo", "dati/")
    reg("n_sedute", T, "int", "Rendimenti giornalieri nel periodo", "dati/")
    reg("n_anni_interi", len(comp), "int", "Anni interi nel periodo (l'ultimo, parziale, è escluso dai confronti anno per anno)", "dati/")
    reg("anno_primo", int(A["anno"].iloc[0]), "annonum", "Primo anno di detenzione", "dati/")
    reg("anno_ultimo_intero", int(comp["anno"].iloc[-1]), "annonum", "Ultimo anno intero di detenzione", "dati/")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale per tradurre i rendimenti in dollari", "config.py, CAPITALE")
    reg("k_dogs", config.K_DOGS, "int", "Titoli dei Dogs", "config.py, K_DOGS")
    reg("k_piccoli", config.K_PICCOLI, "int", "Titoli della variante a cinque", "config.py, K_PICCOLI")
    reg("n_universo", len(titoli), "int", "Titoli nell'universo fissato in anticipo", "config.py, UNIVERSO")
    reg("n_disp_min", min(n_disp), "int", "Titoli disponibili nel primo anno (con storia completa)", "dati/")
    reg("n_disp_max", max(n_disp), "int", "Titoli disponibili nell'ultimo anno", "dati/")
    reg("h4_min", config.H4_MIN, "pct0", "Ipotesi 4: quota minima di anni con i Dogs davanti", "config.py")
    reg("h4_max", config.H4_MAX, "pct0", "Ipotesi 4: quota massima di anni con i Dogs davanti", "config.py")
    reg("n_scimmie", config.N_SCIMMIE, "int", "Scimmie simulate", "config.py, N_SCIMMIE")
    reg("n_boot", config.N_BOOTSTRAP, "int", "Ricampionamenti bootstrap", "config.py, N_BOOTSTRAP")
    reg("blocco", config.BLOCCO_BOOTSTRAP, "int", "Giorni per blocco del bootstrap", "config.py, BLOCCO_BOOTSTRAP")
    reg("livello_ic", config.LIVELLO_CONFIDENZA, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("soglia", 0.05, "pct0", "Livello di significatività dei test", "convenzione")
    reg("rend_div_dogs", float(np.mean(yd_dogs)), "pct1", "Rendimento da dividendo medio dei Dogs al momento dell'acquisto", "scelte.csv")
    reg("rend_div_uni", float(np.mean(yd_uni)), "pct1", "Rendimento da dividendo medio dell'universo al momento dell'acquisto", "scelte.csv")
    reg("ricambio", float(np.mean(ricambi)), "pct0", "Quota media di titoli dei Dogs sostituita da un anno all'altro", "scelte.csv")

    stat = {}
    for k in R:
        r = R[k]
        e = m.equity(r)
        stat[k] = dict(cagr=m.cagr(r, GA), vol=m.vol(r, GA), sharpe=m.sharpe(r, GA), dd=m.max_dd(r), finale=config.CAPITALE * float(e[-1]), tot=float(e[-1] - 1))
        reg(f"{k}_cagr", stat[k]["cagr"], "pct1", f"Rendimento annuo composto ({k}, dividendi reinvestiti)", "motore.cagr")
        reg(f"{k}_vol", stat[k]["vol"], "pct1", f"Volatilità annua ({k})", "motore.vol")
        reg(f"{k}_sharpe", stat[k]["sharpe"], "num2", f"Rapporto di Sharpe ({k}, tasso privo di rischio zero)", "motore.sharpe")
        reg(f"{k}_dd", -stat[k]["dd"], "pct0", f"Perdita massima dal picco ({k})", "motore.max_dd")
        reg(f"{k}_finale", stat[k]["finale"], "int", f"Valore finale del capitale iniziale ({k})", "motore.equity")
    reg("diff_cagr_uni", stat["d10"]["cagr"] - stat["uni"]["cagr"], "pp1", "Rendimento annuo composto dei Dogs meno quello dell'universo, in punti", "motore.cagr")
    reg("diff_cagr_spy", stat["d10"]["cagr"] - stat["spy"]["cagr"], "pp1", "Rendimento annuo composto dei Dogs meno quello dello SPY, in punti", "motore.cagr")
    reg("diff_dd_uni", stat["d10"]["dd"] - stat["uni"]["dd"], "pp1", "Perdita massima dei Dogs meno quella dell'universo (positivo = Dogs meno profonda), in punti", "motore.max_dd")
    reg("diff_vol_uni", stat["d10"]["vol"] - stat["uni"]["vol"], "pp1", "Volatilità dei Dogs meno quella dell'universo, in punti", "motore.vol")
    reg("corr_uni", float(np.corrcoef(R["d10"], R["uni"])[0, 1]), "num2", "Correlazione dei rendimenti giornalieri tra Dogs e universo", "numpy.corrcoef")

    # --- Anno per anno ------------------------------------------------------------------------------------------
    batte_uni = comp["d10"] > comp["uni"]
    batte_spy = comp["d10"] > comp["spy"]
    ecc = (comp["d10"] - comp["uni"]).to_numpy()
    reg("quota_batte_uni", float(batte_uni.mean()), "pct0", "Quota di anni interi in cui i Dogs rendono più dell'universo", "annuali.csv")
    reg("n_batte_uni", int(batte_uni.sum()), "int", "Anni interi in cui i Dogs rendono più dell'universo", "annuali.csv")
    reg("quota_batte_spy", float(batte_spy.mean()), "pct0", "Quota di anni interi in cui i Dogs rendono più dello SPY", "annuali.csv")
    reg("n_batte_spy", int(batte_spy.sum()), "int", "Anni interi in cui i Dogs rendono più dello SPY", "annuali.csv")
    ib, iw = int(np.argmax(ecc)), int(np.argmin(ecc))
    reg("anno_meglio", int(comp["anno"].iloc[ib]), "annonum", "Anno intero con il miglior eccesso dei Dogs sull'universo", "annuali.csv")
    reg("ecc_meglio", float(ecc[ib]), "pp1", "Eccesso di rendimento dei Dogs sull'universo nel miglior anno, in punti", "annuali.csv")
    reg("anno_peggio", int(comp["anno"].iloc[iw]), "annonum", "Anno intero con il peggior eccesso dei Dogs sull'universo", "annuali.csv")
    reg("ecc_peggio", float(ecc[iw]), "pp1", "Eccesso di rendimento dei Dogs sull'universo nel peggior anno, in punti", "annuali.csv")
    reg("ecc_medio", float(ecc.mean()), "pp1", "Eccesso medio annuo dei Dogs sull'universo (anni interi), in punti", "annuali.csv")
    # due metà del periodo
    meta = comp["anno"].iloc[len(comp) // 2]
    for nome, sub in (("a", comp[comp["anno"] < meta]), ("b", comp[comp["anno"] >= meta])):
        reg(f"meta_{nome}_diff", float(np.prod(1 + sub["d10"]) ** (1 / len(sub)) - np.prod(1 + sub["uni"]) ** (1 / len(sub))), "pp1",
            f"Rendimento annuo composto dei Dogs meno quello dell'universo nella metà {nome} degli anni interi, in punti", "annuali.csv")
        reg(f"meta_{nome}_n", len(sub), "int", f"Anni nella metà {nome}", "annuali.csv")
    reg("meta_anno", int(meta), "annonum", "Primo anno della seconda metà", "annuali.csv")

    # --- Bootstrap della differenza di Sharpe -----------------------------------------------------------------------
    boot = m.bootstrap_diff_sharpe(R["d10"], R["uni"], config.N_BOOTSTRAP, config.BLOCCO_BOOTSTRAP, GA, rng)
    lo, hi = np.quantile(boot, [(1 - config.LIVELLO_CONFIDENZA) / 2, 1 - (1 - config.LIVELLO_CONFIDENZA) / 2])
    reg("diff_sharpe", stat["d10"]["sharpe"] - stat["uni"]["sharpe"], "num2", "Sharpe dei Dogs meno Sharpe dell'universo", "motore.sharpe")
    reg("diff_sharpe_lo", float(lo), "num2", "Estremo inferiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    reg("diff_sharpe_hi", float(hi), "num2", "Estremo superiore dell'intervallo bootstrap a blocchi della differenza di Sharpe", "bootstrap a blocchi")
    pd.DataFrame({"diff_sharpe": boot}).to_csv(config.RISULTATI / "bootstrap.csv", index=False, float_format="%.5f")

    # --- Scimmie ---------------------------------------------------------------------------------------------------
    fin = m.scimmie_annuali(rend_ann, disp, config.K_DOGS, config.N_SCIMMIE, rng)
    pd.DataFrame({"finale": fin}).to_csv(config.RISULTATI / "scimmie.csv", index=False, float_format="%.5f")
    cap = config.CAPITALE
    fd, fu, fs = stat["d10"]["finale"] / cap, stat["uni"]["finale"] / cap, stat["spy"]["finale"] / cap
    reg("sc_mediana", cap * float(np.median(fin)), "int", "Valore finale mediano delle scimmie (dieci titoli a caso ogni anno)", "scimmie.csv")
    reg("sc_p5", cap * float(np.percentile(fin, 5)), "int", "Quinto percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_p95", cap * float(np.percentile(fin, 95)), "int", "Novantacinquesimo percentile del valore finale delle scimmie", "scimmie.csv")
    reg("sc_sotto_dogs", float((fin < fd).mean()), "pct0", "Quota di scimmie che chiudono sotto i Dogs", "scimmie.csv")
    reg("sc_batte_uni", float((fin > fu).mean()), "pct0", "Quota di scimmie che chiudono sopra l'universo", "scimmie.csv")
    reg("sc_batte_spy", float((fin > fs).mean()), "pct0", "Quota di scimmie che chiudono sopra lo SPY", "scimmie.csv")

    # --- File di supporto ---------------------------------------------------------------------------------------------
    camp = np.arange(0, T, 5)
    cum = {k: np.cumprod(1 + R[k]) for k in ("d10", "uni", "spy")}
    pd.DataFrame({"data": date[camp].strftime("%Y-%m-%d"), **{k: cum[k][camp] for k in cum}}).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.5f")
    A.to_csv(config.RISULTATI / "annuali.csv", index=False, float_format="%.5f")
    pd.DataFrame(scelte).to_csv(config.RISULTATI / "scelte.csv", index=False, float_format="%.5f")

    # --- Verdetti sulle ipotesi -----------------------------------------------------------------------------------
    h = [stat["d10"]["cagr"] < stat["uni"]["cagr"],
         stat["d10"]["dd"] > stat["uni"]["dd"],
         stat["d10"]["cagr"] < stat["spy"]["cagr"],
         config.H4_MIN <= float(batte_uni.mean()) <= config.H4_MAX,
         float(np.percentile(fin, 5)) <= fd <= float(np.percentile(fin, 95)),
         bool(lo <= 0 <= hi)]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su sei)", "confronto con config.py")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pandas": pd.__version__,
           "numpy": np.__version__, "ipotesi": config.IPOTESI, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")


if __name__ == "__main__":
    main()
