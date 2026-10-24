"""Passo 2 - Stazionarietà e test ADF sull'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json        ogni numero dell'articolo, con descrizione e origine
  adf_finestre.csv     per ogni finestra di dieci anni: p-value e statistica ADF su log-prezzo e rendimenti, volatilità annualizzata
  simulazioni.csv      statistiche ADF di random walk e di serie stazionarie lente simulate
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
    logp = np.log(close).to_numpy()
    rend = fx.log_rendimenti(close).to_numpy()          # rend[i] = rendimento della seduta i+1
    n = len(close)
    rng = np.random.default_rng(config.SEME)

    reg("prima_data", str(date[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(date[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_sedute", n, "int", "Sedute (chiusure giornaliere) nei dati", "dati/")
    reg("anni_totali", n / config.SEDUTE_ANNO, "num1", "Anni di borsa nei dati (sedute diviso 252)", "dati/")
    reg("anni_finestra", config.SEDUTE_FINESTRA / config.SEDUTE_ANNO, "annonum", "Anni di ciascuna finestra", "config.py, SEDUTE_FINESTRA")
    reg("soglia", config.SOGLIA, "pct0", "Livello di significatività dei test", "config.py")
    reg("soglia_forte", config.SOGLIA_FORTE, "pct0", "Livello di significatività forte", "config.py")
    reg("maxlag", config.MAXLAG_AIC, "int", "Ritardi massimi ammessi nell'ADF sui dati reali (scelta con AIC)", "config.py, MAXLAG_AIC")
    reg("h3_liv", config.H3_QUOTA_LIV, "pct0", "Ipotesi 3: quota minima di finestre in cui il prezzo non rifiuta", "config.py")
    reg("h3_rend", config.H3_QUOTA_REND, "pct0", "Ipotesi 3: quota minima di finestre in cui i rendimenti rifiutano", "config.py")
    reg("h5_pot", config.H5_POTENZA_MAX, "pct0", "Ipotesi 5: potenza massima attesa", "config.py")
    reg("h5_dim_min", config.H5_DIM_MIN, "pct0", "Ipotesi 5: dimensione minima attesa", "config.py")
    reg("h5_dim_max", config.H5_DIM_MAX, "pct0", "Ipotesi 5: dimensione massima attesa", "config.py")
    reg("n_sim", config.N_SIM, "int", "Serie simulate per tipo", "config.py, N_SIM")

    # --- Intero periodo ---------------------------------------------------------------------------------------
    s, p, lag = fx.adf(logp, config.REGR_LIVELLI, config.MAXLAG_AIC)
    reg("adf_liv_stat", s, "num2", "Statistica ADF sul logaritmo del prezzo, intero periodo (costante e trend)", "adfuller")
    reg("adf_liv_p", p, "pval", "P-value ADF sul logaritmo del prezzo, intero periodo (ipotesi nulla: radice unitaria)", "adfuller (MacKinnon)")
    reg("adf_liv_lag", lag, "int", "Ritardi scelti con AIC, log-prezzo", "adfuller")
    s2, p2, _ = fx.adf(logp, config.REGR_LIVELLI_ALT, config.MAXLAG_AIC)
    reg("adf_liv_alt_p", p2, "pval", "P-value ADF sul logaritmo del prezzo, intero periodo, solo costante", "adfuller")
    s3, p3, lag3 = fx.adf(rend, config.REGR_RENDIMENTI, config.MAXLAG_AIC)
    reg("adf_rend_stat", s3, "num2", "Statistica ADF sui rendimenti logaritmici giornalieri, intero periodo (solo costante)", "adfuller")
    reg("adf_rend_p", p3, "pval", "P-value ADF sui rendimenti giornalieri, intero periodo", "adfuller (MacKinnon)")
    reg("adf_rend_lag", lag3, "int", "Ritardi scelti con AIC, rendimenti", "adfuller")
    reg("h1_ok", int(p > config.SOGLIA), "int", "1 se l'ADF sul log-prezzo non rifiuta la radice unitaria (p sopra la soglia)", "adfuller")
    reg("h2_ok", int(p3 < config.SOGLIA_FORTE), "int", "1 se l'ADF sui rendimenti rifiuta con p sotto la soglia forte", "adfuller")
    reg("rend_medio_ann", float(np.exp(rend.mean() * config.SEDUTE_ANNO) - 1), "pct1", "Rendimento annuo composto dell'indice di prezzo (media dei log-rendimenti per 252, esponenziale)", "dati/")
    reg("vol_tot", float(rend.std(ddof=1) * np.sqrt(config.SEDUTE_ANNO)), "pct1", "Volatilità annualizzata di tutto il periodo", "dati/")

    # --- Finestre -----------------------------------------------------------------------------------------------
    righe = []
    for k, (a, b) in enumerate(fx.finestre(n, config.SEDUTE_FINESTRA), 1):
        lp = logp[a:b]
        r = np.diff(lp)
        sl, pl, _ = fx.adf(lp, config.REGR_LIVELLI, config.MAXLAG_AIC)
        sr, pr, _ = fx.adf(r, config.REGR_RENDIMENTI, config.MAXLAG_AIC)
        righe.append({"finestra": k, "inizio": date[a].date(), "fine": date[b - 1].date(), "stat_liv": sl, "p_liv": pl,
                      "stat_rend": sr, "p_rend": pr, "vol_ann": r.std(ddof=1) * np.sqrt(config.SEDUTE_ANNO)})
    W = pd.DataFrame(righe)
    nf = len(W)
    if nf < 5:
        raise SystemExit("Troppo poche finestre.")
    n_liv_non_rif = int((W["p_liv"] > config.SOGLIA).sum())
    n_rend_rif = int((W["p_rend"] < config.SOGLIA).sum())
    reg("n_finestre", nf, "int", "Finestre di dieci anni non sovrapposte", "adf_finestre.csv")
    reg("n_liv_non_rif", n_liv_non_rif, "int", "Finestre in cui l'ADF sul log-prezzo NON rifiuta la radice unitaria", "adf_finestre.csv")
    reg("n_liv_rif", nf - n_liv_non_rif, "int", "Finestre in cui l'ADF sul log-prezzo rifiuta la radice unitaria", "adf_finestre.csv")
    reg("quota_liv_non_rif", n_liv_non_rif / nf, "pct0", "Quota di finestre in cui l'ADF sul log-prezzo non rifiuta", "adf_finestre.csv")
    reg("n_rend_rif", n_rend_rif, "int", "Finestre in cui l'ADF sui rendimenti rifiuta la radice unitaria (p sotto 5%)", "adf_finestre.csv")
    reg("quota_rend_rif", n_rend_rif / nf, "pct0", "Quota di finestre in cui l'ADF sui rendimenti rifiuta", "adf_finestre.csv")
    reg("p_rend_max", float(W["p_rend"].max()), "pval", "Il p-value più alto sui rendimenti tra le finestre", "adf_finestre.csv")
    reg("p_liv_min", float(W["p_liv"].min()), "pval", "Il p-value più basso sul log-prezzo tra le finestre", "adf_finestre.csv")
    reg("p_liv_mediano", float(W["p_liv"].median()), "pval", "P-value mediano sul log-prezzo tra le finestre", "adf_finestre.csv")
    reg("h3_ok", int(n_liv_non_rif / nf >= config.H3_QUOTA_LIV and n_rend_rif / nf >= config.H3_QUOTA_REND), "int", "1 se l'ipotesi 3 è rispettata (80% e 95%)", "adf_finestre.csv")
    i_max, i_min = int(W["vol_ann"].idxmax()), int(W["vol_ann"].idxmin())
    reg("vol_max", float(W["vol_ann"].max()), "pct1", "Volatilità annualizzata della finestra più turbolenta", "adf_finestre.csv")
    reg("vol_min", float(W["vol_ann"].min()), "pct1", "Volatilità annualizzata della finestra più calma", "adf_finestre.csv")
    reg("vol_rapporto", float(W["vol_ann"].max() / W["vol_ann"].min()), "num1", "Rapporto tra volatilità massima e minima tra le finestre", "adf_finestre.csv")
    reg("vol_max_inizio", str(W["inizio"][i_max]), "data_lunga", "Inizio della finestra più turbolenta", "adf_finestre.csv")
    reg("vol_max_fine", str(W["fine"][i_max]), "data_lunga", "Fine della finestra più turbolenta", "adf_finestre.csv")
    reg("vol_min_inizio", str(W["inizio"][i_min]), "data_lunga", "Inizio della finestra più calma", "adf_finestre.csv")
    reg("vol_min_fine", str(W["fine"][i_min]), "data_lunga", "Fine della finestra più calma", "adf_finestre.csv")
    reg("h4_ok", int(W["vol_ann"].max() / W["vol_ann"].min() >= 2), "int", "1 se il rapporto di volatilità è almeno 2", "adf_finestre.csv")

    # --- Simulazioni: dimensione e potenza ------------------------------------------------------------------------
    sigma = float(rend.std(ddof=1))
    phi = 0.5 ** (1 / (config.EMIVITA_ANNI * config.SEDUTE_ANNO))
    L = config.SEDUTE_FINESTRA
    st_rw, p_rw, st_ar, p_ar = [], [], [], []
    for _ in range(config.N_SIM):
        s_, p_, _ = fx.adf(fx.random_walk(rng, L, sigma), config.REGR_LIVELLI, config.MAXLAG_SIM, autolag=None)
        st_rw.append(s_); p_rw.append(p_)
        s_, p_, _ = fx.adf(fx.ar1(rng, L, phi, sigma), config.REGR_LIVELLI, config.MAXLAG_SIM, autolag=None)
        st_ar.append(s_); p_ar.append(p_)
    pd.DataFrame({"stat_rw": st_rw, "p_rw": p_rw, "stat_ar": st_ar, "p_ar": p_ar}).to_csv(
        config.RISULTATI / "simulazioni.csv", index=False, float_format="%.6f")
    dim = float(np.mean(np.array(p_rw) < config.SOGLIA))
    pot = float(np.mean(np.array(p_ar) < config.SOGLIA))
    reg("emivita", config.EMIVITA_ANNI, "annonum", "Mezza vita (anni) della serie stazionaria simulata", "config.py, EMIVITA_ANNI")
    reg("phi_ar", phi, "num3", "Coefficiente autoregressivo giornaliero della serie stazionaria simulata", "config.py")
    reg("sim_dimensione", dim, "pct1", "Quota di random walk simulati in cui l'ADF rifiuta (p sotto 5%): dovrebbe stare vicino al 5%", "simulazioni.csv")
    reg("sim_potenza", pot, "pct1", "Quota di serie stazionarie lente simulate in cui l'ADF rifiuta la radice unitaria", "simulazioni.csv")
    reg("stat_critica", float(np.quantile(st_rw, config.SOGLIA)), "num2", "Quinto percentile della statistica ADF sui random walk simulati (soglia empirica)", "simulazioni.csv")
    reg("h5_ok", int(pot < config.H5_POTENZA_MAX and config.H5_DIM_MIN <= dim <= config.H5_DIM_MAX), "int", "1 se l'ipotesi 5 è rispettata", "simulazioni.csv")
    reg("sigma_sim", sigma, "num3", "Deviazione standard giornaliera dei log-rendimenti usata nelle simulazioni (in unità, non percentuale)", "dati/")

    W.to_csv(config.RISULTATI / "adf_finestre.csv", index=False, float_format="%.6f")
    out = {"generato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
           "pandas": pd.__version__, "numpy": np.__version__, "valori": RIS}
    (config.RISULTATI / "metriche.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Registrati {len(RIS)} numeri; {nf} finestre")
    print(f"ADF log-prezzo p={p:.3f}; rendimenti p={p3:.2g}; finestre: livelli non rifiutati {n_liv_non_rif}/{nf}, rendimenti rifiutati {n_rend_rif}/{nf}")
    print(f"vol rapporto {W['vol_ann'].max() / W['vol_ann'].min():.2f}; dimensione {dim:.1%}; potenza {pot:.1%}")


if __name__ == "__main__":
    main()
