"""Passo 2 - ARIMA sui rendimenti mensili dell'S&P 500: dentro il campione e fuori dal campione.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json       ogni numero dell'articolo, con descrizione e origine
  bic_ordini.csv      BIC di ogni ordine (p, q) sull'intero periodo
  previsioni.csv      per ogni mese fuori campione: valore reale, previsione ARIMA, previsione media storica
  bootstrap_r2.csv    R quadro fuori campione di ogni ricampionamento
"""
import json
import platform
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.stattools import adfuller

import config
import funzioni as fx

RIS: dict = {}
SORGENTE = "02_backtest_e_test.py con funzioni.py"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]


def reg(chiave, valore, formato, descrizione, origine=SORGENTE):
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def nome_mese(per: pd.Period) -> str:
    return f"{MESI[per.month - 1]} {per.year}"


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    rm = fx.rendimenti_mensili(close)
    y = rm.to_numpy()
    T = len(y)
    rng = np.random.default_rng(config.SEME)

    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("mese_primo", nome_mese(rm.index[0]), "testo", "Primo mese con un rendimento mensile", "dati/")
    reg("mese_ultimo", nome_mese(rm.index[-1]), "testo", "Ultimo mese completo usato", "dati/")
    reg("n_mesi", T, "int", "Rendimenti mensili usati (mesi completi)", "dati/")
    reg("anni_totali", T / 12, "num1", "Anni coperti dai rendimenti mensili", "dati/")
    reg("media_mese", float(y.mean()), "pct2", "Rendimento logaritmico medio mensile", "dati/")
    reg("vol_mese", float(y.std(ddof=1)), "pct1", "Deviazione standard dei rendimenti mensili", "dati/")
    reg("quota_positivi", float((y > 0).mean()), "pct0", "Quota di mesi con rendimento positivo", "dati/")
    reg("p_max", config.P_MAX, "int", "Ordine massimo AR provato", "config.py, P_MAX")
    reg("q_max", config.Q_MAX, "int", "Ordine massimo MA provato", "config.py, Q_MAX")
    reg("n_modelli", (config.P_MAX + 1) * (config.Q_MAX + 1), "int", "Modelli provati (coppie p, q)", "config.py")
    reg("mesi_iniziali", config.MESI_INIZIALI, "int", "Mesi usati solo per la prima stima", "config.py, MESI_INIZIALI")
    reg("anni_iniziali", config.MESI_INIZIALI / 12, "int", "Anni usati solo per la prima stima", "config.py")
    reg("ogni_mesi", config.OGNI_MESI, "int", "Mesi tra una ristima del modello e la successiva", "config.py, OGNI_MESI")
    reg("lag_test", config.LAG_TEST, "int", "Ritardi del test di Ljung-Box e di Newey-West", "config.py, LAG_TEST")
    reg("soglia", config.SOGLIA, "pct0", "Livello di significatività dei test", "config.py")
    reg("soglia_forte", config.SOGLIA_FORTE, "pct0", "Livello di significatività forte", "config.py")
    reg("h2_r2", config.H2_R2_MAX, "pct0", "Ipotesi 2: quota massima di varianza spiegata in campione", "config.py")
    reg("h3_r2", config.H3_R2_OOS_MAX, "pct0", "Ipotesi 3: R quadro fuori campione massimo", "config.py")
    reg("n_boot", config.N_BOOT, "int", "Ricampionamenti bootstrap", "config.py")
    reg("blocco_medio", config.BLOCCO_MEDIO, "int", "Lunghezza media dei blocchi del bootstrap, in mesi", "config.py")
    reg("livello_ic", config.LIVELLO_IC, "pct0", "Livello degli intervalli di confidenza", "config.py")

    # --- Stazionarietà: perché d = 0 sui rendimenti e d = 1 sui prezzi ---------------------------------------------
    lp = np.log(close.groupby([close.index.year, close.index.month]).last().to_numpy())
    p_liv = adfuller(lp, maxlag=config.LAG_ADF, autolag=None, regression="ct", result_object=False)[1]
    p_rend = adfuller(y, maxlag=config.LAG_ADF, autolag=None, regression="c", result_object=False)[1]
    reg("adf_p_prezzi", float(p_liv), "pval", "P-value del test ADF sul logaritmo dei prezzi mensili (con tendenza)", "statsmodels.adfuller")
    reg("adf_p_rend", float(p_rend), "pval", "P-value del test ADF sui rendimenti mensili", "statsmodels.adfuller")

    # --- Dentro il campione ------------------------------------------------------------------------------------------
    ordine, ris, tab = fx.scegli_ordine(y, config.P_MAX, config.Q_MAX, "bic")
    ordine_aic, _, _ = fx.scegli_ordine(y, config.P_MAX, config.Q_MAX, "aic")
    pd.DataFrame([{"p": p, "q": q, "bic": b, "delta_bic": b - min(tab.values())} for (p, q), b in sorted(tab.items())]).to_csv(
        config.RISULTATI / "bic_ordini.csv", index=False, float_format="%.4f")
    p, q = ordine
    reg("ord_p", p, "int", "Ordine AR scelto dal BIC sull'intero periodo", "scegli_ordine")
    reg("ord_q", q, "int", "Ordine MA scelto dal BIC sull'intero periodo", "scegli_ordine")
    reg("ord_somma", p + q, "int", "Parametri di memoria (p + q) scelti dal BIC", "scegli_ordine")
    reg("aic_p", ordine_aic[0], "int", "Ordine AR scelto dall'AIC", "scegli_ordine")
    reg("aic_q", ordine_aic[1], "int", "Ordine MA scelto dall'AIC", "scegli_ordine")
    bic0 = tab[(0, 0)]
    reg("delta_bic_zero", bic0 - min(tab.values()), "num1", "BIC del modello senza memoria (0, 0) meno il BIC del migliore", "bic_ordini.csv")
    res = np.asarray(ris.resid)
    r2_in = 1 - float(np.var(res)) / float(np.var(y))
    reg("r2_in", r2_in, "pct2", "Quota di varianza spiegata dal modello scelto, dentro il campione (1 meno varianza dei residui su varianza dei rendimenti)", "statsmodels")
    names = list(ris.param_names)
    for nome, chiave in (("ar.L1", "phi1"), ("ma.L1", "theta1")):
        reg(chiave, float(ris.params[names.index(nome)]) if nome in names else 0.0, "num3", f"Coefficiente {nome} del modello scelto (zero se assente)", "statsmodels")
        reg(chiave + "_z", float(ris.tvalues[names.index(nome)]) if nome in names else 0.0, "num1", f"Statistica z di {nome} (zero se assente)", "statsmodels")
    lb, lbp = fx.ljung_box_serie(res, config.LAG_TEST)
    lb2, lb2p = fx.ljung_box_serie(res ** 2, config.LAG_TEST)
    lby2, lby2p = fx.ljung_box_serie(y ** 2, config.LAG_TEST)
    reg("lb_res_p", lbp, "pval", "P-value di Ljung-Box sui residui (12 ritardi)", "statsmodels")
    reg("lb_res2_stat", lb2, "num1", "Statistica di Ljung-Box sui quadrati dei residui (12 ritardi)", "statsmodels")
    reg("lb_res2_p", lb2p, "pval", "P-value di Ljung-Box sui quadrati dei residui (12 ritardi)", "statsmodels")
    reg("lb_y2_p", lby2p, "pval", "P-value di Ljung-Box sui quadrati dei rendimenti (12 ritardi)", "statsmodels")
    reg("acf1_mensile", float(np.corrcoef(y[1:], y[:-1])[0, 1]), "num3", "Autocorrelazione dei rendimenti mensili al ritardo 1", "numpy.corrcoef")

    # --- Fuori dal campione ------------------------------------------------------------------------------------------
    f_mod, f_med, reale, ordini = fx.previsioni_rolling(y, config.MESI_INIZIALI, config.OGNI_MESI, config.P_MAX, config.Q_MAX)
    date_oos = rm.index[config.MESI_INIZIALI:]
    n = len(reale)
    pd.DataFrame({"mese": date_oos.astype(str), "reale": reale, "arima": f_mod, "media_storica": f_med}).to_csv(
        config.RISULTATI / "previsioni.csv", index=False, float_format="%.6f")
    e_m, e_b = reale - f_mod, reale - f_med
    r2o = fx.r2_fuori_campione(reale, f_med, f_mod)
    r2z = float(1 - np.sum(e_m ** 2) / np.sum(reale ** 2))
    t_cw, p_cw = fx.clark_west(reale, f_med, f_mod, config.LAG_TEST)
    reg("n_oos", n, "int", "Previsioni fuori campione (mesi)", "previsioni.csv")
    reg("mese_oos_primo", nome_mese(date_oos[0]), "testo", "Primo mese previsto fuori campione", "previsioni.csv")
    reg("n_blocchi", len(ordini), "int", "Volte in cui il modello è stato riscelto e ristimato", "previsioni_rolling")
    cnt = Counter(ordini)
    top, k = cnt.most_common(1)[0]
    reg("ord_top_p", top[0], "int", "Ordine AR più frequente tra le riscelte", "previsioni_rolling")
    reg("ord_top_q", top[1], "int", "Ordine MA più frequente tra le riscelte", "previsioni_rolling")
    reg("ord_top_quota", k / len(ordini), "pct0", "Quota di riscelte con l'ordine più frequente", "previsioni_rolling")
    reg("ord_n_distinti", len(cnt), "int", "Ordini diversi scelti nelle riscelte", "previsioni_rolling")
    reg("rmse_mod", float(np.sqrt(np.mean(e_m ** 2))), "pct2", "Radice dell'errore quadratico medio mensile del modello", "previsioni.csv")
    reg("rmse_med", float(np.sqrt(np.mean(e_b ** 2))), "pct2", "Radice dell'errore quadratico medio mensile della media storica", "previsioni.csv")
    reg("r2_oos", r2o, "pct2", "R quadro fuori campione del modello rispetto alla media storica (uno meno rapporto tra errori quadratici)", "previsioni.csv")
    reg("r2_oos_zero", r2z, "pct2", "R quadro fuori campione rispetto alla previsione «zero»", "previsioni.csv")
    reg("cw_t", t_cw, "num2", "Statistica di Clark-West (Newey-West a 12 ritardi)", "funzioni.clark_west")
    reg("cw_p", p_cw, "pval", "P-value di Clark-West a una coda: il modello batte la media storica", "funzioni.clark_west")
    # intervallo bootstrap dell'R quadro fuori campione
    boot = np.empty(config.N_BOOT)
    for i, idx in enumerate(fx.bootstrap_stazionario(rng, n, config.BLOCCO_MEDIO, config.N_BOOT)):
        boot[i] = 1 - np.sum(e_m[idx] ** 2) / np.sum(e_b[idx] ** 2)
    pd.DataFrame({"r2_oos": boot}).to_csv(config.RISULTATI / "bootstrap_r2.csv", index=False, float_format="%.6f")
    lo, hi = np.quantile(boot, [(1 - config.LIVELLO_IC) / 2, 1 - (1 - config.LIVELLO_IC) / 2])
    reg("r2_oos_lo", float(lo), "pct2", "Estremo inferiore dell'intervallo bootstrap dell'R quadro fuori campione", "bootstrap stazionario")
    reg("r2_oos_hi", float(hi), "pct2", "Estremo superiore dell'intervallo bootstrap dell'R quadro fuori campione", "bootstrap stazionario")
    # segno
    hit_m = float(np.mean(np.sign(f_mod) == np.sign(reale)))
    hit_med = float(np.mean(np.sign(f_med) == np.sign(reale)))
    su = float(np.mean(reale > 0))
    reg("hit_mod", hit_m, "pct1", "Quota di mesi in cui il segno previsto dal modello è giusto", "previsioni.csv")
    reg("hit_med", hit_med, "pct1", "Quota di mesi in cui il segno della media storica è giusto", "previsioni.csv")
    reg("hit_su", su, "pct1", "Quota di mesi positivi nel periodo fuori campione (chi prevede sempre «sale»)", "previsioni.csv")
    reg("quota_prev_negative", float(np.mean(f_mod < 0)), "pct1", "Quota di mesi in cui il modello prevede un rendimento negativo", "previsioni.csv")
    reg("prev_min", float(f_mod.min()), "pct2", "Previsione più bassa del modello (rendimento mensile)", "previsioni.csv")
    reg("prev_max", float(f_mod.max()), "pct2", "Previsione più alta del modello (rendimento mensile)", "previsioni.csv")
    # due metà del periodo fuori campione
    m2 = n // 2
    reg("r2_oos_a", fx.r2_fuori_campione(reale[:m2], f_med[:m2], f_mod[:m2]), "pct2", "R quadro fuori campione nella prima metà", "previsioni.csv")
    reg("r2_oos_b", fx.r2_fuori_campione(reale[m2:], f_med[m2:], f_mod[m2:]), "pct2", "R quadro fuori campione nella seconda metà", "previsioni.csv")
    reg("anno_meta", int(date_oos[m2].year), "annonum", "Primo anno della seconda metà del periodo fuori campione", "previsioni.csv")

    # --- Verdetti ----------------------------------------------------------------------------------------------------------
    h = [p + q <= config.H1_P_PIU_Q_MAX, r2_in < config.H2_R2_MAX, r2o < config.H3_R2_OOS_MAX, lb2p < config.SOGLIA_FORTE, hit_m <= su, p_cw >= config.SOGLIA]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "statsmodels": statsmodels.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
