"""Passo 2 - Un backtest minimo: segnale, esecuzione, rendimenti, e come leggerlo.

Legge SOLO dati/spy_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv         valore giorno per giorno (una seduta su cinque): regola, regola con esecuzione ritardata, buy & hold
  epoche.csv        regola e buy & hold nelle tre epoche
  finestre.csv      differenza di rendimento annuo (regola meno buy & hold) per ogni finestra mobile di dieci anni
  casuali.csv       rendimento annuo e perdita massima di ogni calendario casuale

La regola: investiti in una seduta se la chiusura di ieri era sopra la media a 200 giorni di ieri, altrimenti in cassa.
Il segnale si calcola sulla chiusura non corretta; i rendimenti vengono dalla chiusura corretta per i dividendi.
Nessuna commissione, nessuna tassa.
"""
import json
import platform
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
import motore_vettoriale as m

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con motore_vettoriale.py"


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def importo(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".") + " euro"


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close, adj = df["Close"].astype(float), df["AdjClose"].astype(float)
    if (close <= 0).any() or close.isna().any() or (adj <= 0).any() or adj.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    rend_pieno = m.rendimenti(adj)
    sig = m.segnale_sopra_media(close, config.SMA)
    i0 = config.INIZIO_TEST_SEDUTE
    date = close.index
    sl = slice(i0, None)
    rend = rend_pieno.iloc[sl]
    anni = (date[-1] - date[i0 - 1]).days / 365.25

    pos = m.posizione(sig, config.RITARDO_ONESTO).iloc[sl]
    pos_es = m.posizione(sig, config.RITARDO_ESECUZIONE).iloc[sl]
    bh = pd.Series(True, index=rend.index)
    v_r, v_e, v_b = m.valore(rend, pos), m.valore(rend, pos_es), m.valore(rend, bh)

    reg("data_prima", str(date[0].date()), "data_lunga", "Prima seduta dei dati scaricati", "dati/spy_giornaliero.csv")
    reg("data_inizio", str(date[i0].date()), "data_lunga", "Prima seduta del test (le precedenti servono per la media)", "dati/ e config.py, INIZIO_TEST_SEDUTE")
    reg("data_fine", str(date[-1].date()), "data_lunga", "Ultima seduta del test", "dati/spy_giornaliero.csv")
    reg("sedute_avvio", config.INIZIO_TEST_SEDUTE, "int", "Sedute iniziali usate solo per calcolare la media, prima dell'inizio del test", "config.py, INIZIO_TEST_SEDUTE")
    reg("n_sedute", len(rend), "int", "Sedute nel periodo del test", "dati/")
    reg("anni_test", anni, "num1", "Anni del test")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, valori lordi", "config.py, CAPITALE")
    reg("sma", config.SMA, "annonum", "Giorni della media mobile", "config.py, SMA")
    reg("ritardo_esecuzione", config.RITARDO_ESECUZIONE, "annonum", "Ritardo (sedute) del segnale nella variante con esecuzione alla chiusura successiva", "config.py, RITARDO_ESECUZIONE")

    c_r, c_b, c_e = m.cagr(v_r, anni), m.cagr(v_b, anni), m.cagr(v_e, anni)
    d_r, d_b, d_e = m.perdita_massima(v_r), m.perdita_massima(v_b), m.perdita_massima(v_e)
    reg("cagr_regola", c_r, "pct1", "Rendimento annuo composto della regola (segnale di ieri, posizione di oggi), senza costi né tasse")
    reg("cagr_bh", c_b, "pct1", "Rendimento annuo composto del buy & hold sullo SPY (dividendi reinvestiti), senza costi né tasse")
    reg("cagr_diff", c_r - c_b, "pp2", "Rendimento annuo della regola meno quello del buy & hold, punti percentuali")
    reg("cagr_diff_assoluta", abs(c_r - c_b), "pp2", "Valore assoluto della differenza di rendimento annuo, punti percentuali")
    reg("cagr_esecuzione", c_e, "pct1", "Rendimento annuo della regola se l'ordine viene eseguito alla chiusura successiva (un giorno in più di ritardo)")
    reg("cagr_esecuzione_diff", c_e - c_r, "pp2", "Rendimento annuo con esecuzione ritardata meno quello con esecuzione ideale, punti percentuali")
    reg("dd_regola", -d_r, "pct0", "Perdita massima dal picco della regola")
    reg("dd_bh", -d_b, "pct0", "Perdita massima dal picco del buy & hold")
    reg("dd_esecuzione", -d_e, "pct0", "Perdita massima dal picco della regola con esecuzione ritardata")
    reg("vol_regola", m.volatilita_annua(rend, pos), "pct0", "Volatilità annua dei rendimenti giornalieri della regola (cassa a rendimento zero)")
    reg("vol_bh", m.volatilita_annua(rend, bh), "pct0", "Volatilità annua dei rendimenti giornalieri del buy & hold")
    reg("finale_regola", importo(config.CAPITALE * v_r.iloc[-1]), "testo", "Valore finale della regola partendo dal capitale iniziale")
    reg("finale_bh", importo(config.CAPITALE * v_b.iloc[-1]), "testo", "Valore finale del buy & hold partendo dal capitale iniziale")
    reg("quota_investito", float(pos.mean()), "pct0", "Quota di sedute in cui la regola è investita")
    n_cambi = int(pos.astype(int).diff().abs().sum())
    reg("n_cambi", n_cambi, "int", "Cambi di posizione (acquisti e vendite) della regola nel periodo")
    reg("cambi_anno", n_cambi / anni, "num1", "Cambi di posizione all'anno")
    reg("costo_decimo", n_cambi / anni * config.COSTO_DECIMO, "pp2", "Costo annuo in punti percentuali se ogni cambio di posizione costasse un decimo di punto percentuale")
    reg("costo_decimo_pp", config.COSTO_DECIMO, "pp1", "Costo ipotizzato per ogni cambio di posizione, punti percentuali", "config.py, COSTO_DECIMO")
    # giorni cattivi
    peggior = rend.nsmallest(10).index
    reg("peggiori_10_fuori", int((~pos[peggior]).sum()), "int", "Quanti dei dieci peggiori giorni del test la regola aveva già evitato (era in cassa)")
    migliori = rend.nlargest(10).index
    reg("migliori_10_fuori", int((~pos[migliori]).sum()), "int", "Quanti dei dieci migliori giorni del test la regola si è persa (era in cassa)")
    reg("h1_ok", int(c_r < c_b), "int", "1 se la regola rende meno del buy & hold", "calcolo sopra")
    reg("h2_ok", int(d_r > d_b), "int", "1 se la perdita massima della regola è meno profonda di quella del buy & hold", "calcolo sopra")

    # --- epoche -------------------------------------------------------------------------------------------------
    righe_ep, n_vince = [], 0
    for k, (nome, a, b) in enumerate(config.SOTTOPERIODI, 1):
        idx = rend.index
        msk = np.ones(len(idx), bool)
        if a: msk &= idx >= pd.Timestamp(a)
        if b: msk &= idx <= pd.Timestamp(b)
        r_p, p_p = rend[msk], pos[msk]
        an = (r_p.index[-1] - r_p.index[0]).days / 365.25
        vr, vb = m.valore(r_p, p_p), m.valore(r_p, pd.Series(True, index=r_p.index))
        cr, cb, dr, db = m.cagr(vr, an), m.cagr(vb, an), m.perdita_massima(vr), m.perdita_massima(vb)
        n_vince += int(cr > cb)
        righe_ep.append({"periodo": nome, "cagr_regola": cr, "cagr_bh": cb, "dd_regola": dr, "dd_bh": db})
        reg(f"ep{k}_nome", nome, "testo", "Nome dell'epoca", "config.py, SOTTOPERIODI")
        reg(f"ep{k}_cagr_regola", cr, "pct1", f"Rendimento annuo della regola, {nome}")
        reg(f"ep{k}_cagr_bh", cb, "pct1", f"Rendimento annuo del buy & hold, {nome}")
        reg(f"ep{k}_diff", cr - cb, "pp2", f"Rendimento annuo della regola meno buy & hold, punti percentuali, {nome}")
        reg(f"ep{k}_dd_regola", -dr, "pct0", f"Perdita massima della regola, {nome}")
        reg(f"ep{k}_dd_bh", -db, "pct0", f"Perdita massima del buy & hold, {nome}")
    reg("n_epoche", len(config.SOTTOPERIODI), "int", "Epoche confrontate", "config.py, SOTTOPERIODI")
    reg("n_epoche_vince", n_vince, "int", "Epoche in cui la regola rende più del buy & hold", "epoche.csv")
    pd.DataFrame(righe_ep).to_csv(config.RISULTATI / "epoche.csv", index=False, float_format="%.6f")

    # --- finestre mobili di dieci anni -----------------------------------------------------------------------------
    lr = np.log1p(rend.to_numpy() * pos.to_numpy(float))
    lb = np.log1p(rend.to_numpy())
    cr_, cb_ = np.r_[0.0, np.cumsum(lr)], np.r_[0.0, np.cumsum(lb)]
    W = config.FINESTRA_SEDUTE
    righe_fi = []
    for s in range(0, len(rend) - W + 1, config.PASSO_FINESTRA):
        e = s + W
        an_w = (rend.index[e - 1] - rend.index[s]).days / 365.25
        a_r = float(np.exp((cr_[e] - cr_[s]) / an_w) - 1)
        a_b = float(np.exp((cb_[e] - cb_[s]) / an_w) - 1)
        righe_fi.append({"inizio": rend.index[s], "fine": rend.index[e - 1], "cagr_regola": a_r, "cagr_bh": a_b, "diff": a_r - a_b})
    fi = pd.DataFrame(righe_fi)
    fi.to_csv(config.RISULTATI / "finestre.csv", index=False, float_format="%.6f")
    quota = float((fi["diff"] > 0).mean())
    reg("fin_n", len(fi), "int", "Finestre mobili di dieci anni considerate (una nuova ogni mese di borsa)", "finestre.csv")
    reg("fin_anni", round(W / 252), "annonum", "Durata in anni di ciascuna finestra mobile", "config.py, FINESTRA_SEDUTE")
    reg("fin_quota_vince", quota, "pct0", "Quota di finestre in cui la regola rende più del buy & hold", "finestre.csv")
    imax, imin = fi["diff"].idxmax(), fi["diff"].idxmin()
    reg("fin_diff_max", float(fi.loc[imax, "diff"]), "pp2", "Miglior differenza (regola meno buy & hold) tra le finestre, punti percentuali", "finestre.csv")
    reg("fin_diff_max_inizio", str(fi.loc[imax, "inizio"].date()), "anno", "Anno di inizio della finestra con la miglior differenza", "finestre.csv")
    reg("fin_diff_min", float(fi.loc[imin, "diff"]), "pp2", "Peggior differenza (regola meno buy & hold) tra le finestre, punti percentuali", "finestre.csv")
    reg("fin_diff_min_inizio", str(fi.loc[imin, "inizio"].date()), "anno", "Anno di inizio della finestra con la peggior differenza", "finestre.csv")
    vinte = fi[fi["diff"] > 0]
    if len(vinte):
        reg("fin_vinte_inizio_da", str(vinte["inizio"].min().date()), "anno", "Anno di inizio della prima finestra (in ordine di data) in cui la regola batte il buy & hold", "finestre.csv")
        reg("fin_vinte_inizio_a", str(vinte["inizio"].max().date()), "anno", "Anno di inizio dell'ultima finestra (in ordine di data) in cui la regola batte il buy & hold", "finestre.csv")
        reg("fin_vinte_fine_da", str(vinte["fine"].min().date()), "anno", "Anno di fine della prima finestra in cui la regola batte il buy & hold", "finestre.csv")
        reg("fin_vinte_fine_a", str(vinte["fine"].max().date()), "anno", "Anno di fine dell'ultima finestra in cui la regola batte il buy & hold", "finestre.csv")
    reg("fin_diff_mediana", float(fi["diff"].median()), "pp2", "Differenza mediana (regola meno buy & hold) tra le finestre, punti percentuali", "finestre.csv")
    reg("h3_ok", int(0 < n_vince < len(config.SOTTOPERIODI) and 0.20 <= quota <= 0.80), "int", "1 se la regola vince in almeno un'epoca e perde in almeno un'altra e la quota di finestre vinte sta tra 20% e 80%", "calcolo sopra")

    # --- calendari casuali ------------------------------------------------------------------------------------------
    rng = np.random.default_rng(config.SEME)
    bl = m.blocchi(pos.to_numpy())
    r_np = rend.to_numpy()
    ca, cd = [], []
    for _ in range(config.N_CASUALI):
        p = m.calendario_casuale(bl, rng)
        v = np.cumprod(1.0 + r_np * p)
        ca.append(v[-1] ** (1.0 / anni) - 1.0)
        cd.append(float((v / np.maximum.accumulate(v) - 1.0).min()))
    ca, cd = np.array(ca), np.array(cd)
    pd.DataFrame({"cagr": ca, "perdita_massima": cd}).to_csv(config.RISULTATI / "casuali.csv", index=False, float_format="%.6f")
    sotto_cagr = float((ca < c_r).mean())
    meglio_dd = float((cd < d_r).mean())          # calendari con perdita massima più profonda della regola
    reg("n_casuali", config.N_CASUALI, "int", "Calendari casuali generati", "config.py, N_CASUALI")
    reg("n_blocchi", len(bl), "int", "Blocchi consecutivi (dentro o fuori) della regola, rimescolati nei calendari casuali", "calcolo sopra")
    reg("cas_quota_sotto_cagr", sotto_cagr, "pct1", "Quota di calendari casuali con un rendimento annuo più basso di quello della regola")
    reg("cas_quota_meglio_dd", meglio_dd, "pct1", "Quota di calendari casuali con una perdita massima più profonda di quella della regola")
    reg("cas_cagr_mediana", float(np.median(ca)), "pct1", "Rendimento annuo mediano dei calendari casuali")
    reg("cas_cagr_p5", float(np.percentile(ca, 5)), "pct1", "5° percentile del rendimento annuo dei calendari casuali")
    reg("cas_cagr_p95", float(np.percentile(ca, config.PERCENTILE_ALTO)), "pct1", "95° percentile del rendimento annuo dei calendari casuali")
    reg("cas_dd_mediana", -float(np.median(cd)), "pct0", "Perdita massima mediana dei calendari casuali")
    reg("cas_dd_p5", -float(np.percentile(cd, 5)), "pct0", "Perdita massima del 5° percentile più profondo dei calendari casuali")
    reg("cas_dd_p95", -float(np.percentile(cd, 95)), "pct0", "Perdita massima del 95° percentile (la più lieve tra le più profonde) dei calendari casuali")
    reg("cas_soglia_alta", config.PERCENTILE_ALTO, "annonum", "Percentile alto usato come soglia", "config.py, PERCENTILE_ALTO")
    reg("h4_ok", int(meglio_dd >= 0.95), "int", "1 se la perdita massima della regola è meno profonda di almeno il 95% dei calendari casuali", "calcolo sopra")
    reg("h5_ok", int(sotto_cagr < 0.95), "int", "1 se il rendimento annuo della regola NON supera il 95° percentile dei calendari casuali", "calcolo sopra")

    # --- curve ---------------------------------------------------------------------------------------------------------
    camp = np.r_[np.arange(0, len(rend), 5), len(rend) - 1]
    pd.DataFrame({"data": rend.index[camp], "valore_bh": v_b.iloc[camp].to_numpy(), "valore_regola": v_r.iloc[camp].to_numpy(),
                  "valore_esecuzione": v_e.iloc[camp].to_numpy(), "investito": pos.iloc[camp].astype(int).to_numpy()}
                 ).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")
    print(f"regola {c_r:.1%} (perdita max {d_r:.0%}), buy & hold {c_b:.1%} ({d_b:.0%}); esecuzione ritardata {c_e:.1%}")
    print(f"epoche vinte {n_vince}/{len(config.SOTTOPERIODI)}; finestre vinte {quota:.0%}; "
          f"casuali sotto la regola: rendimento {sotto_cagr:.0%}, perdita massima più profonda {meglio_dd:.0%}")


if __name__ == "__main__":
    main()
