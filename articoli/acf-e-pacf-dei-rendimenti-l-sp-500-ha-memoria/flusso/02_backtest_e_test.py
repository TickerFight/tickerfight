"""Passo 2 - ACF e PACF dei rendimenti dell'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  acf_intero.csv       per ogni ritardo: ACF e PACF dei rendimenti, ACF dei valori assoluti e dei quadrati, p-value, Holm
  acf_finestre.csv     per ogni finestra di dieci anni: ACF al primo ritardo di rendimenti e valori assoluti, R2 di un AR(1), Ljung-Box
  permutazioni.csv     ACF al primo ritardo di rendimenti e valori assoluti per ciascun rimescolamento
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
    if isinstance(valore, (np.floating, np.integer)):
        valore = valore.item()
    if isinstance(valore, float) and not np.isfinite(valore):
        raise SystemExit(f"Numero non finito per {chiave}")
    RIS[chiave] = {"valore": valore, "formato": formato, "descrizione": descrizione, "origine": origine}


def main() -> None:
    config.RISULTATI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(config.FILE_DATI, parse_dates=["Date"], index_col="Date").sort_index()
    close = df["Close"].astype(float)
    if (close <= 0).any() or close.isna().any():
        raise SystemExit("Chiusure mancanti o non positive.")
    date = close.index
    r = fx.log_rendimenti(close)
    x = r.to_numpy()
    N = len(x)
    L = config.NLAG
    rng = np.random.default_rng(config.SEME)

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_sedute", len(close), "int", "Sedute (chiusure giornaliere) nei dati", "dati/")
    reg("n_rend", N, "int", "Rendimenti giornalieri usati (sedute meno una)", "dati/")
    reg("anni_totali", len(close) / config.SEDUTE_ANNO, "num1", "Anni di borsa nei dati (sedute diviso 252)", "dati/")
    reg("anni_finestra", config.SEDUTE_FINESTRA / config.SEDUTE_ANNO, "annonum", "Anni di ciascuna finestra", "config.py, SEDUTE_FINESTRA")
    reg("nlag", L, "int", "Ritardi guardati", "config.py, NLAG")
    reg("nlag_lungo", config.NLAG_LUNGO, "int", "Ritardi guardati per la persistenza dei movimenti", "config.py, NLAG_LUNGO")
    reg("soglia", config.SOGLIA, "pct0", "Livello di significatività dei test", "config.py")
    reg("soglia_forte", config.SOGLIA_FORTE, "pct0", "Livello di significatività forte", "config.py")
    reg("h1_max", config.H1_ACF_MAX, "num2", "Ipotesi 1: soglia di autocorrelazione in valore assoluto", "config.py")
    reg("h3_rapporto", config.H3_RAPPORTO, "int", "Ipotesi 3: rapporto minimo tra autocorrelazioni", "config.py")
    reg("h4_diff", config.H4_DIFFERENZA, "num2", "Ipotesi 4: differenza minima tra finestre", "config.py")
    reg("h5_r2", config.H5_R2_MAX, "pct0", "Ipotesi 5: quota massima di varianza spiegata", "config.py")
    reg("h5_quota", config.H5_QUOTA_FINESTRE, "pct0", "Ipotesi 5: quota minima di finestre", "config.py")
    reg("h6_max", config.H6_PACF_MAX, "num2", "Ipotesi 6: soglia di autocorrelazione parziale", "config.py")
    reg("livello_banda", 0.99, "pct0", "Livello della banda attorno allo zero e dell'intervallo dei rimescolamenti", "convenzione (99%)")
    reg("n_perm", config.N_PERM, "int", "Rimescolamenti dei rendimenti", "config.py, N_PERM")
    reg("media_rend", float(x.mean()), "pct2", "Rendimento logaritmico medio giornaliero", "dati/")
    reg("vol_giorn", float(x.std(ddof=1)), "pct2", "Deviazione standard dei rendimenti giornalieri", "dati/")

    # --- Intero periodo ---------------------------------------------------------------------------------------
    M = config.NLAG_LUNGO
    ar = fx.acf(x, M)
    aa = fx.acf(np.abs(x), M)
    aq = fx.acf(x ** 2, M)
    pr = fx.pacf_da_acf(ar[: L + 1])
    pa = fx.pacf_da_acf(aa[: L + 1])
    se = 1 / np.sqrt(N)
    z = ar[1: L + 1] / se
    p_r = np.array([fx.p_normale(v) for v in z])
    h_r = fx.holm(p_r)
    tab = pd.DataFrame({"ritardo": np.arange(1, L + 1), "acf_rend": ar[1: L + 1], "pacf_rend": pr[1:],
                        "acf_abs": aa[1: L + 1], "pacf_abs": pa[1:], "acf_quad": aq[1: L + 1],
                        "p_rend": p_r, "p_rend_holm": h_r})
    tab.to_csv(config.RISULTATI / "acf_intero.csv", index=False)
    pd.DataFrame({"ritardo": np.arange(1, M + 1), "acf_rend": ar[1:], "acf_abs": aa[1:], "acf_quad": aq[1:]}) \
        .to_csv(config.RISULTATI / "acf_lunga.csv", index=False)

    reg("se", se, "num3", "Errore standard dell'autocorrelazione di una serie senza memoria (1 diviso radice di N)", "formula di Bartlett")
    reg("banda99", 2.5758 * se, "num3", "Ampiezza della banda al 99% attorno allo zero", "2,5758 per l'errore standard")
    reg("acf1", ar[1], "num3", "Autocorrelazione dei rendimenti al ritardo 1, intero periodo", "funzioni.acf")
    reg("acf2", ar[2], "num3", "Autocorrelazione dei rendimenti al ritardo 2", "funzioni.acf")
    reg("acf_max_ass", float(np.abs(ar[1: L + 1]).max()), "num3", "Autocorrelazione massima in valore assoluto tra i ritardi 1-20 dei rendimenti", "funzioni.acf")
    reg("acf_max_rit", int(np.abs(ar[1: L + 1]).argmax() + 1), "int", "Ritardo in cui l'autocorrelazione dei rendimenti è massima in valore assoluto", "funzioni.acf")
    reg("n_sign_nom", int((p_r < config.SOGLIA).sum()), "int", "Ritardi (su 20) con autocorrelazione dei rendimenti oltre il 5% senza correzione", "z-test, 5%")
    reg("n_sign_holm", int((h_r < config.SOGLIA).sum()), "int", "Ritardi (su 20) significativi al 5% dopo la correzione di Holm", "Holm")
    reg("n_neg", int((ar[1: L + 1] < 0).sum()), "int", "Ritardi (su 20) con autocorrelazione dei rendimenti negativa", "funzioni.acf")
    qr, pq = fx.ljung_box(ar, N, L)
    reg("lb_stat", qr, "num1", "Statistica di Ljung-Box sui rendimenti (20 ritardi)", "funzioni.ljung_box")
    reg("lb_p", pq, "pval", "P-value di Ljung-Box sui rendimenti (20 ritardi)", "chi quadro con 20 gradi di libertà")
    qa, pqa = fx.ljung_box(aa, N, L)
    reg("lb_abs_stat", qa, "num1", "Statistica di Ljung-Box sui valori assoluti (20 ritardi)", "funzioni.ljung_box")
    reg("lb_abs_p", pqa, "pval", "P-value di Ljung-Box sui valori assoluti (20 ritardi)", "chi quadro con 20 gradi di libertà")
    reg("r2_ar1", ar[1] ** 2, "pct2", "Quota di varianza dei rendimenti spiegata da un AR(1) (ACF1 al quadrato), intero periodo", "ACF1 al quadrato")

    # PACF
    reg("pacf1", pr[1], "num3", "Autocorrelazione parziale al ritardo 1", "Durbin-Levinson")
    reg("pacf2", pr[2], "num3", "Autocorrelazione parziale al ritardo 2", "Durbin-Levinson")
    reg("pacf_max_ass", float(np.abs(pr[2:]).max()), "num3", "Autocorrelazione parziale massima in valore assoluto tra i ritardi 2-20", "Durbin-Levinson")
    reg("pacf_max_rit", int(np.abs(pr[2:]).argmax() + 2), "int", "Ritardo in cui l'autocorrelazione parziale (da 2) è massima in valore assoluto", "Durbin-Levinson")

    # Valori assoluti e quadrati
    reg("acf1_abs", aa[1], "num3", "Autocorrelazione dei valori assoluti al ritardo 1", "funzioni.acf")
    reg("acf10_abs", aa[10], "num3", "Autocorrelazione dei valori assoluti al ritardo 10", "funzioni.acf")
    reg("acf20_abs", aa[20], "num3", "Autocorrelazione dei valori assoluti al ritardo 20", "funzioni.acf")
    reg("acf100_abs", aa[100], "num3", "Autocorrelazione dei valori assoluti al ritardo 100", "funzioni.acf")
    reg("acf1_quad", aq[1], "num3", "Autocorrelazione dei quadrati al ritardo 1", "funzioni.acf")
    reg("n_pos_abs", int((aa[1: L + 1] > 0).sum()), "int", "Ritardi (su 20) con autocorrelazione dei valori assoluti positiva", "funzioni.acf")
    reg("n_oltre_banda_abs", int((np.abs(aa[1:]) > 2.5758 * se).sum()), "int", "Ritardi (su 100) dei valori assoluti oltre la banda al 99%", "funzioni.acf")
    reg("rapporto_abs_rend", abs(aa[1]) / abs(ar[1]), "num1", "Autocorrelazione dei valori assoluti diviso quella dei rendimenti, ritardo 1 (valori assoluti)", "rapporto")
    reg("lb_abs_stat_rapp", qa / qr, "num1", "Statistica di Ljung-Box dei valori assoluti diviso quella dei rendimenti", "rapporto")
    reg("pacf1_abs", pa[1], "num3", "Autocorrelazione parziale dei valori assoluti al ritardo 1", "Durbin-Levinson")
    reg("pacf_abs_n_pos", int((pa[1:] > 0).sum()), "int", "Ritardi (su 20) con autocorrelazione parziale dei valori assoluti positiva", "Durbin-Levinson")

    # --- Rimescolamenti --------------------------------------------------------------------------------------
    a1 = np.empty(config.N_PERM)
    a1a = np.empty(config.N_PERM)
    for i in range(config.N_PERM):
        s = rng.permutation(x)
        a1[i] = fx.acf(s, 1)[1]
        a1a[i] = fx.acf(np.abs(s), 1)[1]
    pd.DataFrame({"acf1_rend": a1, "acf1_abs": a1a}).to_csv(config.RISULTATI / "permutazioni.csv", index=False)
    lo, hi = np.percentile(a1, [0.5, 99.5])
    reg("perm_lo", lo, "num3", "Estremo inferiore del 99% delle ACF1 dei rendimenti rimescolati (percentile 0,5)", "numpy.percentile")
    reg("perm_hi", hi, "num3", "Estremo superiore del 99% delle ACF1 dei rendimenti rimescolati (percentile 99,5)", "numpy.percentile")
    reg("perm_max_ass", float(np.abs(a1).max()), "num3", "ACF1 massima in valore assoluto tra i rimescolamenti dei rendimenti", "numpy")
    reg("perm_fuori", bool(ar[1] < lo or ar[1] > hi) and 1 or 0, "int", "1 se l'ACF1 reale dei rendimenti cade fuori dal 99% dei rimescolamenti, 0 altrimenti", "confronto")
    reg("perm_p", float((np.sum(np.abs(a1) >= abs(ar[1])) + 1) / (config.N_PERM + 1)), "pval", "P-value del rimescolamento per l'ACF1 dei rendimenti (con correzione +1)", "permutazioni")
    reg("perm_abs_max", float(a1a.max()), "num3", "ACF1 massima dei valori assoluti rimescolati", "numpy")
    reg("perm_abs_n_oltre", int((a1a >= aa[1]).sum()), "int", "Rimescolamenti con ACF1 dei valori assoluti pari o superiore a quella reale", "permutazioni")

    # --- Finestre di dieci anni -------------------------------------------------------------------------------
    righe = []
    for a, b in fx.finestre(N, config.SEDUTE_FINESTRA):
        w = x[a:b]
        rw = fx.acf(w, L)
        aw = fx.acf(np.abs(w), 1)
        q, p = fx.ljung_box(rw, len(w), L)
        righe.append({"inizio": r.index[a], "fine": r.index[b - 1], "acf1_rend": rw[1], "acf1_abs": aw[1],
                      "r2_ar1": rw[1] ** 2, "lb_p": p})
    W = pd.DataFrame(righe)
    W.to_csv(config.RISULTATI / "acf_finestre.csv", index=False)
    k = len(W)
    iM, im = int(W["acf1_rend"].idxmax()), int(W["acf1_rend"].idxmin())
    reg("n_fin", k, "int", "Finestre di dieci anni non sovrapposte", "funzioni.finestre")
    reg("fin_max", W.loc[iM, "acf1_rend"], "num3", "ACF1 dei rendimenti più alta tra le finestre", "acf_finestre.csv")
    reg("fin_max_anno", str(W.loc[iM, "inizio"].date()), "anno", "Anno di inizio della finestra con l'ACF1 più alta", "acf_finestre.csv")
    reg("fin_min", W.loc[im, "acf1_rend"], "num3", "ACF1 dei rendimenti più bassa tra le finestre", "acf_finestre.csv")
    reg("fin_min_anno", str(W.loc[im, "inizio"].date()), "anno", "Anno di inizio della finestra con l'ACF1 più bassa", "acf_finestre.csv")
    reg("fin_diff", W["acf1_rend"].max() - W["acf1_rend"].min(), "num3", "Differenza tra l'ACF1 più alta e la più bassa tra le finestre", "acf_finestre.csv")
    reg("fin_n_pos", int((W["acf1_rend"] > 0).sum()), "int", "Finestre con ACF1 dei rendimenti positiva", "acf_finestre.csv")
    reg("fin_n_neg", int((W["acf1_rend"] < 0).sum()), "int", "Finestre con ACF1 dei rendimenti negativa", "acf_finestre.csv")
    reg("fin_n_lb", int((W["lb_p"] < config.SOGLIA).sum()), "int", "Finestre in cui Ljung-Box (20 ritardi) rifiuta al 5%", "acf_finestre.csv")
    reg("fin_r2_max", W["r2_ar1"].max(), "pct2", "Quota di varianza spiegata da un AR(1) nella finestra migliore", "acf_finestre.csv")
    reg("fin_r2_n_sotto", int((W["r2_ar1"] < config.H5_R2_MAX).sum()), "int", "Finestre in cui l'AR(1) spiega meno dell'1% della varianza", "acf_finestre.csv")
    reg("fin_abs_min", W["acf1_abs"].min(), "num3", "ACF1 dei valori assoluti più bassa tra le finestre", "acf_finestre.csv")
    reg("fin_abs_max", W["acf1_abs"].max(), "num3", "ACF1 dei valori assoluti più alta tra le finestre", "acf_finestre.csv")
    reg("fin_abs_n_pos", int((W["acf1_abs"] > 0).sum()), "int", "Finestre con ACF1 dei valori assoluti positiva", "acf_finestre.csv")

    # --- Verdetti sulle ipotesi -------------------------------------------------------------------------------
    h1 = np.abs(ar[1: L + 1]).max() <= config.H1_ACF_MAX
    h2 = (pq < config.SOGLIA_FORTE) and (ar[1] < lo or ar[1] > hi)
    h3 = (abs(aa[1]) >= config.H3_RAPPORTO * abs(ar[1])) and bool((aa[1: L + 1] > 0).all())
    h4 = (W["acf1_rend"].max() - W["acf1_rend"].min()) >= config.H4_DIFFERENZA
    h5 = (ar[1] ** 2 < config.H5_R2_MAX) and ((W["r2_ar1"] < config.H5_R2_MAX).mean() >= config.H5_QUOTA_FINESTRE)
    h6 = np.abs(pr[2:]).max() <= config.H6_PACF_MAX
    for i, v in enumerate([h1, h2, h3, h4, h5, h6], 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in [h1, h2, h3, h4, h5, h6])), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
