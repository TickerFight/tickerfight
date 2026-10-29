"""Passo 2 - L'intervallo di confidenza del CAGR dell'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  intervalli.csv    per ogni finestra: CAGR e tre intervalli (formula, bootstrap sui giorni, bootstrap a blocchi)
  copertura.csv     per ogni lunghezza di finestra: quota di intervalli che contengono il CAGR dell'intero periodo
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
GA = config.GIORNI_ANNO


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
    x = np.log(close).diff().dropna().to_numpy()
    date = close.index[1:]
    n = len(x)
    rng = np.random.default_rng(config.SEME)

    reg("prima_data", str(close.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_rend", n, "int", "Rendimenti giornalieri usati", "dati/")
    reg("anni_tot", n / GA, "num1", "Anni di borsa nei dati (sedute diviso 252)", "dati/")
    reg("vol_ann", float(x.std(ddof=1) * np.sqrt(GA)), "pct1", "Volatilità annua dei rendimenti logaritmici giornalieri", "dati/")
    reg("livello_ic", config.LIVELLO_IC, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("n_boot", config.N_BOOT, "int", "Ricampionamenti bootstrap", "config.py, N_BOOT")
    reg("blocco", config.BLOCCO, "int", "Sedute per blocco del bootstrap a blocchi", "config.py, BLOCCO")
    reg("h1_amp", config.H1_AMPIEZZA, "pp1", "Ipotesi 1: ampiezza minima dell'intervallo, in punti", "config.py")
    reg("h2_amp", config.H2_AMPIEZZA, "pp1", "Ipotesi 2: ampiezza minima dell'intervallo a dieci anni, in punti", "config.py")
    reg("h3_min", config.H3_RAPPORTO_MIN, "num1", "Ipotesi 3: rapporto minimo tra le ampiezze", "config.py")
    reg("h3_max", config.H3_RAPPORTO_MAX, "num1", "Ipotesi 3: rapporto massimo tra le ampiezze", "config.py")
    reg("h4_anni", config.H4_ANNI, "int", "Ipotesi 4: anni minimi per un intervallo di più o meno un punto", "config.py")
    reg("h5_cop", config.H5_COPERTURA, "pct0", "Ipotesi 5: copertura nominale", "config.py")

    righe, finestre = [], [(a, n - a * GA) for a in config.FINESTRE_ANNI if a * GA <= n] + [("tot", 0)]
    for a, inizio in finestre:
        w = x[inizio:]
        c, lo, hi = fx.intervallo_formula(w, GA, config.Z95)
        bi = fx.bootstrap_giorni(w, config.N_BOOT, GA, config.LIVELLO_IC, rng)
        bb = fx.bootstrap_blocchi(w, config.N_BOOT, config.BLOCCO, GA, config.LIVELLO_IC, rng)
        k = f"w{a}"
        righe.append({"finestra": str(a), "anni": len(w) / GA, "cagr": c, "formula_lo": lo, "formula_hi": hi,
                      "giorni_lo": bi[0], "giorni_hi": bi[1], "blocchi_lo": bb[0], "blocchi_hi": bb[1]})
        reg(f"{k}_anni", len(w) / GA, "num1", f"Anni della finestra {a}", "dati/")
        reg(f"{k}_cagr", c, "pct1", f"CAGR della finestra {a}", "funzioni.intervallo_formula")
        reg(f"{k}_an_lo", lo, "pct1", f"Estremo basso dell'intervallo (formula), finestra {a}", "funzioni.intervallo_formula")
        reg(f"{k}_an_hi", hi, "pct1", f"Estremo alto dell'intervallo (formula), finestra {a}", "funzioni.intervallo_formula")
        reg(f"{k}_bi_lo", bi[0], "pct1", f"Estremo basso dell'intervallo (bootstrap sui giorni), finestra {a}", "funzioni.bootstrap_giorni")
        reg(f"{k}_bi_hi", bi[1], "pct1", f"Estremo alto dell'intervallo (bootstrap sui giorni), finestra {a}", "funzioni.bootstrap_giorni")
        reg(f"{k}_bb_lo", bb[0], "pct1", f"Estremo basso dell'intervallo (bootstrap a blocchi), finestra {a}", "funzioni.bootstrap_blocchi")
        reg(f"{k}_bb_hi", bb[1], "pct1", f"Estremo alto dell'intervallo (bootstrap a blocchi), finestra {a}", "funzioni.bootstrap_blocchi")
        reg(f"{k}_amp_an", hi - lo, "pp1", f"Ampiezza dell'intervallo (formula), finestra {a}, in punti", "funzioni.intervallo_formula")
        reg(f"{k}_amp_bi", bi[1] - bi[0], "pp1", f"Ampiezza dell'intervallo (bootstrap sui giorni), finestra {a}, in punti", "funzioni.bootstrap_giorni")
        reg(f"{k}_amp_bb", bb[1] - bb[0], "pp1", f"Ampiezza dell'intervallo (bootstrap a blocchi), finestra {a}, in punti", "funzioni.bootstrap_blocchi")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "intervalli.csv", index=False, float_format="%.5f")
    reg("rapporto_bb_bi", RIS["wtot_amp_bb"]["valore"] / RIS["wtot_amp_bi"]["valore"], "num2", "Ampiezza a blocchi diviso ampiezza sui giorni, intero periodo", "rapporto")
    reg("se_tot", float(x.std(ddof=1) * np.sqrt(GA) / np.sqrt(n / GA)), "pp1", "Errore standard del rendimento logaritmico annuo medio, intero periodo, in punti", "sigma diviso radice degli anni")

    # --- Anni necessari -----------------------------------------------------------------------------------------------
    sigma = float(x.std(ddof=1) * np.sqrt(GA))
    for h, nome in ((0.02, "2pp"), (0.01, "1pp"), (0.005, "05pp")):
        reg(f"anni_{nome}", fx.anni_necessari(sigma, h, config.Z95), "int", f"Anni per un intervallo di più o meno {h * 100:g} punti", "funzioni.anni_necessari")

    # --- Copertura ----------------------------------------------------------------------------------------------------
    vero = float(x.mean() * GA)
    inizi = fx.inizi_mese(date)
    cop = []
    for a in config.COPERTURA_ANNI:
        q, k = fx.copertura(x, a * GA, inizi, vero, GA, config.Z95)
        cop.append({"anni": a, "copertura": q, "finestre": k})
        reg(f"cop{a}", q, "pct0", f"Quota di finestre di {a} anni il cui intervallo contiene il CAGR dell'intero periodo", "funzioni.copertura")
        reg(f"cop{a}_n", k, "int", f"Finestre di {a} anni (una per mese)", "funzioni.copertura")
    # Controllo aggiunto dopo aver visto la copertura (ipotesi 5) vicina al cento per cento: il riferimento contiene la finestra stessa.
    # Copertura onesta: il riferimento è la media di tutte le ALTRE sedute.
    for riga in cop:
        a = riga["anni"]
        q, k = fx.copertura_fuori(x, a * GA, inizi, GA, config.Z95)
        riga["copertura_fuori"] = q
        reg(f"cof{a}", q, "pct0", f"Copertura onesta, finestre di {a} anni: quota di intervalli che contengono il CAGR delle altre sedute", "funzioni.copertura_fuori")
    pd.DataFrame(cop).to_csv(config.RISULTATI / "copertura.csv", index=False, float_format="%.5f")
    reg("cagr_tot_riferimento", float(np.exp(vero) - 1), "pct1", "CAGR dell'intero periodo usato come riferimento della copertura", "dati/")

    # --- Verdetti ---------------------------------------------------------------------------------------------------------
    c30 = RIS["w30_cagr"]["valore"]
    h = [RIS["wtot_amp_bi"]["valore"] > config.H1_AMPIEZZA,
         RIS["w10_amp_an"]["valore"] > config.H2_AMPIEZZA,
         config.H3_RAPPORTO_MIN <= RIS["rapporto_bb_bi"]["valore"] <= config.H3_RAPPORTO_MAX,
         RIS["anni_1pp"]["valore"] > config.H4_ANNI,
         RIS["cop20"]["valore"] < config.H5_COPERTURA,
         RIS["wtot_bb_lo"]["valore"] <= c30 <= RIS["wtot_bb_hi"]["valore"]]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
