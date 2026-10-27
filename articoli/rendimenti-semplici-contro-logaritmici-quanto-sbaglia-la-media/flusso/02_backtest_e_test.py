"""Passo 2 - Rendimenti semplici contro logaritmici: quanto vale la differenza, e da dove viene.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json    ogni numero dell'articolo, con descrizione e origine di calcolo
  curve.csv        valore di 500 euro in buy & hold e valore "promesso" dalla media aritmetica annua (una seduta su 21)
  decenni.csv      per ogni decennio: media aritmetica, rendimento composto, divario, mezza varianza
  frequenze.csv    il divario calcolato con rendimenti giornalieri, mensili e annuali
  giorni.csv       differenza tra rendimento semplice e logaritmico giorno per giorno (campione + peggiori sedute)

Nessuna strategia da testare: il confronto è tra la media dei rendimenti semplici, il rendimento annuo composto del buy & hold
(che è quello che l'investitore ha davvero ottenuto) e il valore della media dei logaritmi.
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
    """Un importo in euro; se è assurdamente grande si dice solo quante cifre ha."""
    if x < 1e9:
        return f"{x:,.0f}".replace(",", ".") + " euro"
    return f"un numero con {int(np.floor(np.log10(x))) + 1} cifre"


def finestra(close: pd.Series):
    """Dal primo 31 dicembre all'ultimo anno solare completo: restituisce la serie delle chiusure e il numero di anni."""
    anni_dati = close.index.year
    ultimo_anno_dati = int(anni_dati[-1])
    fine_anno = close.groupby(anni_dati).apply(lambda s: s.index[-1])
    complete = [a for a in fine_anno.index if a < ultimo_anno_dati]
    a0, a1 = int(complete[0]), int(complete[-1])
    c = close.loc[fine_anno[a0]:fine_anno[a1]]
    return c, a1 - a0


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    c, anni = finestra(close)
    r, l = m.rend_sempl(c), m.rend_log(c)
    n = len(r)
    spa = n / anni
    tot = float(c.iloc[-1] / c.iloc[0])
    cagr = tot ** (1.0 / anni) - 1.0
    assert abs(cagr - m.cagr_da_rend(r, anni)) < 1e-9

    A, L, V = m.media_annua(r, spa), m.media_annua(l, spa), m.varianza_annua(r, spa)
    gap, gap_log, mezza = A - cagr, A - L, V / 2.0
    err = gap_log - mezza

    reg("prima_data", str(c.index[0].date()), "data_lunga", "Chiusura da cui parte il calcolo (ultima seduta del primo anno solare)", "dati/gspc_giornaliero.csv")
    reg("data_fine", str(c.index[-1].date()), "data_lunga", "Ultima seduta del calcolo (fine dell'ultimo anno solare completo)", "dati/gspc_giornaliero.csv")
    reg("anni_test", anni, "int", "Anni solari interi della finestra", "dati/gspc_giornaliero.csv")
    reg("n_sedute", n, "int", "Rendimenti giornalieri nella finestra", "dati/")
    reg("sedute_anno", spa, "int", "Sedute in un anno, in media (rendimenti giornalieri diviso anni)", "n_sedute / anni_test")
    reg("capitale", config.CAPITALE, "int", "Capitale iniziale, solo per dare un'idea (valori lordi)", "config.py, CAPITALE")

    reg("anno_hudson", 2015, "annonum", "Anno di pubblicazione di Hudson e Gregoriou, International Review of Financial Analysis", "abstract letto su IDEAS/RePEc")
    reg("anno_jacquier", 2003, "annonum", "Anno di pubblicazione di Jacquier, Kane e Marcus, Financial Analysts Journal", "abstract letto su IDEAS/RePEc")
    reg("anno_cooper", 1996, "annonum", "Anno di pubblicazione di Cooper, European Financial Management", "abstract letto su IDEAS/RePEc")

    # --- esempio da manuale -----------------------------------------------------------------------------------
    su, giu = config.ESEMPIO_SU, config.ESEMPIO_GIU
    reg("es_su", su, "pct0", "Rendimento del primo anno dell'esempio", "config.py, ESEMPIO_SU")
    reg("es_giu", giu, "pct0", "Rendimento del secondo anno dell'esempio", "config.py, ESEMPIO_GIU")
    reg("es_dopo_su", config.CAPITALE * (1 + su), "int", "Capitale dopo il primo anno dell'esempio", "capitale x (1 + rendimento)")
    reg("es_finale", config.CAPITALE * (1 + su) * (1 + giu), "int", "Capitale dopo i due anni dell'esempio", "capitale x (1 + su) x (1 + giù)")
    reg("es_totale", (1 + su) * (1 + giu) - 1, "pct0", "Rendimento complessivo dei due anni dell'esempio", "(1 + su) x (1 + giù) - 1")
    reg("es_media_arit", (su + giu) / 2, "pct0", "Media aritmetica dei due rendimenti dell'esempio", "(su + giù) / 2")
    reg("es_log_su", float(np.log(1 + su)), "pct2", "Rendimento logaritmico del primo anno dell'esempio", "ln(1 + su)")
    reg("es_log_giu", float(np.log(1 + giu)), "pct2", "Rendimento logaritmico del secondo anno dell'esempio", "ln(1 + giù)")
    reg("es_log_media", float((np.log(1 + su) + np.log(1 + giu)) / 2), "pct2", "Media dei due rendimenti logaritmici dell'esempio", "(ln(1 + su) + ln(1 + giù)) / 2")

    # --- l'intero periodo, rendimenti giornalieri ---------------------------------------------------------------
    reg("media_semplice", A, "pct2", "Media dei rendimenti semplici giornalieri per il numero di sedute in un anno")
    reg("media_log", L, "pct2", "Media dei rendimenti logaritmici giornalieri per il numero di sedute in un anno")
    reg("cagr", cagr, "pct2", "Rendimento annuo composto del buy & hold sul S&P 500 (indice di prezzo), senza costi né tasse")
    reg("cagr_da_log", float(np.expm1(L)), "pct2", "e elevato alla media logaritmica annua, meno uno: coincide con il rendimento composto")
    reg("cagr_meno_log", cagr - L, "pp2", "Rendimento annuo composto meno media logaritmica annua, punti percentuali l'anno (circa metà del quadrato della media logaritmica)")
    reg("volatilita", float(np.sqrt(V)), "pct1", "Volatilità annua: deviazione standard dei rendimenti giornalieri per la radice delle sedute in un anno")
    reg("mezza_varianza", mezza, "pct2", "Varianza annua dei rendimenti diviso due")
    reg("gap", gap, "pp2", "Divario tra media dei rendimenti semplici e rendimento annuo composto, punti percentuali l'anno")
    reg("gap_log", gap_log, "pp2", "Divario tra media dei rendimenti semplici e media dei rendimenti logaritmici, punti percentuali l'anno")
    reg("errore_mezza_var", err, "pp2", "Divario tra media semplice e media logaritmica meno la mezza varianza, punti percentuali l'anno")
    reg("h1_ok", int(config.GAP_MIN <= gap <= config.GAP_MAX), "int", "1 se il divario sta nell'intervallo dell'ipotesi 1", "config.py, GAP_MIN e GAP_MAX")
    reg("gap_min", config.GAP_MIN, "pp1", "Estremo basso dell'intervallo dell'ipotesi 1, punti percentuali", "config.py")
    reg("gap_max", config.GAP_MAX, "pp1", "Estremo alto dell'intervallo dell'ipotesi 1, punti percentuali", "config.py")
    reg("soglia_errore", config.ERRORE_MEZZA_VARIANZA, "pp1", "Errore massimo tollerato per la mezza varianza, punti percentuali", "config.py")

    # --- somme e prodotti ---------------------------------------------------------------------------------------------
    reg("totale_reale_pct", (tot - 1.0) * 100.0, "int", "Rendimento totale del buy & hold nel periodo, in percentuale")
    reg("somma_semplici_pct", float(r.sum()) * 100.0, "int", "Somma dei rendimenti semplici giornalieri, in percentuale")
    reg("somma_log_ok", int(abs(float(l.sum()) - np.log(tot)) < 1e-9), "int", "1 se la somma dei logaritmi giornalieri coincide con il logaritmo del rendimento totale (tolleranza 1e-9)")
    reg("prodotto_ok", int(abs(float((1 + r).prod()) - tot) < 1e-6 * tot), "int", "1 se il prodotto dei fattori (1 + rendimento) coincide con il rapporto tra ultima e prima chiusura")
    finale_reale = config.CAPITALE * tot
    proiez = config.CAPITALE * (1 + A) ** anni
    reg("finale_reale", importo(finale_reale), "testo", "Valore finale del buy & hold partendo dal capitale iniziale")
    reg("finale_proiezione", importo(proiez), "testo", "Valore che si otterrebbe componendo la media dei rendimenti semplici annua per gli stessi anni")
    reg("rapporto_proiezione", proiez / finale_reale, "num1", "Valore promesso dalla media semplice diviso valore reale del buy & hold")

    # --- decenni ----------------------------------------------------------------------------------------------------
    rd = []
    for dec in sorted(set(r.index.year // 10 * 10)):
        sub = r[(r.index.year // 10 * 10) == dec]
        nanni = len(set(sub.index.year))
        if nanni < config.DECENNIO_MIN_ANNI:
            continue
        sp = len(sub) / nanni
        ls = np.log1p(sub)
        a_d, l_d, v_d = m.media_annua(sub, sp), m.media_annua(ls, sp), m.varianza_annua(sub, sp)
        cg = m.cagr_da_rend(sub, nanni)
        rd.append({"decennio": dec, "etichetta": f"{sub.index.year.min()}-{sub.index.year.max()}", "anni": nanni,
                   "media_semplice": a_d, "cagr": cg, "gap": a_d - cg, "gap_log": a_d - l_d,
                   "volatilita": float(np.sqrt(v_d)), "mezza_varianza": v_d / 2, "errore": (a_d - l_d) - v_d / 2})
    dd = pd.DataFrame(rd)
    corr = float(np.corrcoef(dd["gap"], dd["mezza_varianza"])[0, 1])
    iv, ic = dd["volatilita"].idxmax(), dd["volatilita"].idxmin()
    n_err_ok = int((dd["errore"].abs() < config.ERRORE_MEZZA_VARIANZA).sum())
    reg("n_dec_gap_neg", int((dd["gap"] < 0).sum()), "int", "Decenni in cui la media semplice è inferiore al rendimento composto (divario negativo)", "decenni.csv")
    reg("n_decenni", len(dd), "int", "Decenni con abbastanza anni nella finestra", "decenni.csv")
    reg("decenni_min_anni", config.DECENNIO_MIN_ANNI, "int", "Anni minimi perché un decennio entri nel confronto", "config.py, DECENNIO_MIN_ANNI")
    reg("n_decenni_err_ok", n_err_ok, "int", "Decenni in cui l'errore della mezza varianza è sotto la soglia", "decenni.csv")
    reg("h2_ok", int(abs(err) < config.ERRORE_MEZZA_VARIANZA and n_err_ok == len(dd)), "int", "1 se l'errore è sotto soglia sull'intero periodo e in ogni decennio")
    reg("errore_max_dec", float(dd["errore"].abs().max()), "pp2", "Errore assoluto massimo della mezza varianza tra i decenni, punti percentuali l'anno", "decenni.csv")
    reg("corr_dec", corr, "num2", "Correlazione tra divario e mezza varianza nei decenni", "decenni.csv")
    reg("soglia_corr", config.SOGLIA_CORRELAZIONE, "num2", "Soglia di correlazione dell'ipotesi 3", "config.py")
    reg("dec_vol_nome", dd.loc[iv, "etichetta"], "testo", "Decennio con la volatilità più alta", "decenni.csv")
    reg("dec_vol_vol", dd.loc[iv, "volatilita"], "pct1", "Volatilità annua del decennio più volatile", "decenni.csv")
    reg("dec_vol_gap", dd.loc[iv, "gap"], "pp2", "Divario nel decennio più volatile, punti percentuali l'anno", "decenni.csv")
    reg("dec_calmo_nome", dd.loc[ic, "etichetta"], "testo", "Decennio con la volatilità più bassa", "decenni.csv")
    reg("dec_calmo_vol", dd.loc[ic, "volatilita"], "pct1", "Volatilità annua del decennio più calmo", "decenni.csv")
    reg("dec_calmo_gap", dd.loc[ic, "gap"], "pp2", "Divario nel decennio più calmo, punti percentuali l'anno", "decenni.csv")
    reg("h3_ok", int(corr > config.SOGLIA_CORRELAZIONE and dd.loc[iv, "gap"] > dd.loc[ic, "gap"]), "int", "1 se correlazione sopra soglia e divario del decennio più volatile maggiore di quello del più calmo")
    dd.to_csv(config.RISULTATI / "decenni.csv", index=False, float_format="%.6f")

    # --- giorno per giorno --------------------------------------------------------------------------------------------
    diff = r - l
    quota = float((diff < config.SOGLIA_GIORNO).mean())
    ip = r.idxmin()
    reg("soglia_giorno", config.SOGLIA_GIORNO, "pp2", "Differenza giornaliera sotto cui semplice e logaritmico si confondono, punti percentuali", "config.py, SOGLIA_GIORNO")
    reg("quota_sotto_soglia", quota, "pct1", "Quota di sedute con differenza sotto la soglia")
    reg("soglia_quota", config.SOGLIA_QUOTA_GIORNI, "pct0", "Quota minima dell'ipotesi 4", "config.py")
    reg("soglia_peggior", config.SOGLIA_PEGGIOR_GIORNO, "pp1", "Differenza minima nella peggior seduta, ipotesi 4, punti percentuali", "config.py")
    reg("peggior_data", str(ip.date()), "data_lunga", "Seduta con il peggior rendimento semplice della finestra", "dati/")
    reg("peggior_semplice", float(r[ip]), "pct1", "Rendimento semplice della peggior seduta")
    reg("peggior_log", float(l[ip]), "pct1", "Rendimento logaritmico della peggior seduta")
    reg("peggior_diff", float(diff[ip]), "pp2", "Differenza tra rendimento semplice e logaritmico nella peggior seduta, punti percentuali")
    reg("diff_media", float(diff.mean()), "pp3", "Differenza media giornaliera tra rendimento semplice e logaritmico, punti percentuali")
    reg("n_oltre_decimo", int((diff > 0.001).sum()), "int", "Sedute con differenza sopra un decimo di punto percentuale")
    reg("h4_ok", int(quota >= config.SOGLIA_QUOTA_GIORNI and diff[ip] > config.SOGLIA_PEGGIOR_GIORNO), "int", "1 se l'ipotesi 4 è confermata")
    campione = diff.iloc[::7]
    peggiori = diff.nlargest(10)
    gg = pd.DataFrame({"data": pd.concat([campione, peggiori]).index.unique()})
    gg["semplice"] = r.loc[gg["data"]].to_numpy()
    gg["logaritmico"] = l.loc[gg["data"]].to_numpy()
    gg.sort_values("data").to_csv(config.RISULTATI / "giorni.csv", index=False, float_format="%.8f")

    # --- frequenze --------------------------------------------------------------------------------------------------
    cm = c.groupby([c.index.year, c.index.month]).last()
    rm, lm = cm.pct_change().dropna(), np.log(cm / cm.shift(1)).dropna()
    ca = c.groupby(c.index.year).last()
    ra, la = ca.pct_change().dropna(), np.log(ca / ca.shift(1)).dropna()
    A_m, L_m, V_m = m.media_annua(rm, config.MESI_ANNO), m.media_annua(lm, config.MESI_ANNO), m.varianza_annua(rm, config.MESI_ANNO)
    A_y, L_y, V_y = float(ra.mean()), float(la.mean()), float(ra.var(ddof=1))
    g_d, g_m, g_y = gap, A_m - cagr, A_y - cagr
    spread = max(g_d, g_m, g_y) - min(g_d, g_m, g_y)
    reg("n_mesi", len(rm), "int", "Rendimenti mensili nella finestra", "chiusure di fine mese")
    reg("n_anni_rend", len(ra), "int", "Rendimenti annuali (anni solari) nella finestra", "chiusure di fine anno")
    reg("gap_giorn", g_d, "pp2", "Divario con rendimenti giornalieri, punti percentuali l'anno")
    reg("gap_mens", g_m, "pp2", "Divario con rendimenti mensili (media mensile per 12), punti percentuali l'anno")
    reg("gap_ann", g_y, "pp2", "Divario con rendimenti annuali, punti percentuali l'anno")
    reg("mezza_giorn", mezza, "pp2", "Mezza varianza con rendimenti giornalieri, punti percentuali l'anno")
    reg("mezza_mens", V_m / 2, "pp2", "Mezza varianza con rendimenti mensili, punti percentuali l'anno")
    reg("mezza_ann", V_y / 2, "pp2", "Mezza varianza con rendimenti annuali, punti percentuali l'anno")
    reg("media_ann", A_y, "pct2", "Media dei rendimenti annuali dei singoli anni solari")
    reg("spread_freq", spread, "pp2", "Differenza tra il divario più alto e quello più basso fra le tre frequenze, punti percentuali l'anno")
    reg("soglia_freq", config.SOGLIA_FREQUENZE, "pp1", "Soglia dell'ipotesi 5, punti percentuali", "config.py")
    reg("h5_ok", int(spread < config.SOGLIA_FREQUENZE), "int", "1 se l'ipotesi 5 è confermata")
    pd.DataFrame([
        {"frequenza": "giornaliera", "gap": g_d, "mezza_varianza": mezza, "media_semplice": A, "media_log": L},
        {"frequenza": "mensile", "gap": g_m, "mezza_varianza": V_m / 2, "media_semplice": A_m, "media_log": L_m},
        {"frequenza": "annuale", "gap": g_y, "mezza_varianza": V_y / 2, "media_semplice": A_y, "media_log": L_y},
    ]).to_csv(config.RISULTATI / "frequenze.csv", index=False, float_format="%.6f")

    # --- curva: valore reale contro valore promesso dalla media semplice -------------------------------------------
    k = np.r_[np.arange(0, n + 1, 21), n]
    k = np.unique(k)
    t = k / n * anni
    pd.DataFrame({"data": c.index[k], "anni": t, "valore_reale": config.CAPITALE * (c.to_numpy()[k] / c.iloc[0]),
                  "valore_promesso": config.CAPITALE * (1 + A) ** t}).to_csv(config.RISULTATI / "curve.csv", index=False, float_format="%.6f")

    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri")
    print(f"media semplice {A:.2%}, media log {L:.2%}, composto {cagr:.2%}, divario {gap:.2%}, mezza varianza {mezza:.2%}")
    print(f"ipotesi: H1 {RIS['h1_ok']['valore']} H2 {RIS['h2_ok']['valore']} H3 {RIS['h3_ok']['valore']} "
          f"H4 {RIS['h4_ok']['valore']} H5 {RIS['h5_ok']['valore']}")


if __name__ == "__main__":
    main()
