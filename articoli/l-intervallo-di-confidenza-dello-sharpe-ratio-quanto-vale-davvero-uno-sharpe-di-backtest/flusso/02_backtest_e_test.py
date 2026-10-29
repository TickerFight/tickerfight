"""Passo 2 - L'intervallo di confidenza dello Sharpe ratio dell'S&P 500.

Legge SOLO dati/gspc_giornaliero.csv e produce in risultati/:
  metriche.json     ogni numero dell'articolo, con descrizione e origine
  intervalli.csv    per ogni finestra: Sharpe e quattro intervalli (Lo, Mertens, bootstrap sui giorni, bootstrap a blocchi)
  copertura.csv     per ogni lunghezza di finestra: copertura onesta della formula di Lo
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
    c = close.to_numpy()
    x = c[1:] / c[:-1] - 1.0
    date = close.index[1:]
    n = len(x)
    rng = np.random.default_rng(config.SEME)

    reg("prima_data", str(close.index[0].date()), "data_lunga", "Prima seduta dei dati", "dati/")
    reg("data_ultima", str(close.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("n_rend", n, "int", "Rendimenti giornalieri usati", "dati/")
    reg("anni_tot", n / GA, "num1", "Anni di borsa nei dati (sedute diviso 252)", "dati/")
    reg("livello_ic", config.LIVELLO_IC, "pct0", "Livello degli intervalli di confidenza", "config.py")
    reg("n_boot", config.N_BOOT, "int", "Ricampionamenti bootstrap", "config.py, N_BOOT")
    reg("blocco", config.BLOCCO, "int", "Sedute per blocco del bootstrap a blocchi", "config.py, BLOCCO")
    reg("h1_amp", config.H1_AMPIEZZA, "num2", "Ipotesi 1: ampiezza massima dell'intervallo di Lo sull'intero periodo", "config.py")
    reg("h2_amp", config.H2_AMPIEZZA, "num1", "Ipotesi 2: ampiezza minima dell'intervallo di Lo a dieci anni", "config.py")
    reg("h3_diff", config.H3_DIFF, "pct0", "Ipotesi 3: differenza massima di ampiezza tra Mertens e Lo", "config.py")
    reg("h5_cop", config.H5_COPERTURA, "pct0", "Ipotesi 5: copertura onesta minima a dieci anni", "config.py")
    z0 = (x - x.mean()) / x.std(ddof=0)
    reg("asimmetria", float(np.mean(z0 ** 3)), "num2", "Asimmetria dei rendimenti giornalieri", "dati/")
    reg("curtosi", float(np.mean(z0 ** 4)), "num1", "Curtosi (non in eccesso) dei rendimenti giornalieri; 3 per una distribuzione normale", "dati/")

    righe, finestre = [], [(a, n - a * GA) for a in config.FINESTRE_ANNI if a * GA <= n] + [("tot", 0)]
    for a, inizio in finestre:
        w = x[inizio:]
        sr = fx.sharpe(w, GA)
        lo_ = fx.intervallo(sr, fx.se_lo(w, GA), config.Z95)
        me_ = fx.intervallo(sr, fx.se_mertens(w, GA), config.Z95)
        bi = fx.bootstrap_sharpe(w, config.N_BOOT, 1, GA, config.LIVELLO_IC, rng)
        bb = fx.bootstrap_sharpe(w, config.N_BOOT, config.BLOCCO, GA, config.LIVELLO_IC, rng)
        k = f"w{a}"
        righe.append({"finestra": str(a), "anni": len(w) / GA, "sharpe": sr, "lo_lo": lo_[0], "lo_hi": lo_[1], "me_lo": me_[0], "me_hi": me_[1],
                      "bi_lo": bi[0], "bi_hi": bi[1], "bb_lo": bb[0], "bb_hi": bb[1]})
        reg(f"{k}_sr", sr, "num2", f"Sharpe annualizzato, finestra {a}", "funzioni.sharpe")
        for nome, (l, h), f_ in (("lo", lo_, "Lo"), ("me", me_, "Mertens"), ("bi", bi, "bootstrap sui giorni"), ("bb", bb, "bootstrap a blocchi")):
            reg(f"{k}_{nome}_lo", l, "num2", f"Estremo basso dell'intervallo ({f_}), finestra {a}", "funzioni")
            reg(f"{k}_{nome}_hi", h, "num2", f"Estremo alto dell'intervallo ({f_}), finestra {a}", "funzioni")
            reg(f"{k}_amp_{nome}", h - l, "num2", f"Ampiezza dell'intervallo ({f_}), finestra {a}", "funzioni")
    pd.DataFrame(righe).to_csv(config.RISULTATI / "intervalli.csv", index=False, float_format="%.5f")
    reg("se_tot", fx.se_lo(x, GA), "num3", "Errore standard di Lo dello Sharpe sull'intero periodo", "funzioni.se_lo")
    reg("rapporto_me_lo", RIS["wtot_amp_me"]["valore"] / RIS["wtot_amp_lo"]["valore"], "num3", "Ampiezza di Mertens diviso ampiezza di Lo, intero periodo", "rapporto")
    reg("diff_me_lo", abs(RIS["wtot_amp_me"]["valore"] / RIS["wtot_amp_lo"]["valore"] - 1), "pct1", "Differenza relativa di ampiezza tra Mertens e Lo, intero periodo", "rapporto")
    reg("rapporto_bb_bi", RIS["wtot_amp_bb"]["valore"] / RIS["wtot_amp_bi"]["valore"], "num2", "Ampiezza a blocchi diviso ampiezza sui giorni, intero periodo", "rapporto")

    # --- Anni necessari ------------------------------------------------------------------------------------------------
    sr_t = RIS["wtot_sr"]["valore"]
    for h, nome in ((0.2, "02"), (0.1, "01"), (0.05, "005")):
        reg(f"anni_{nome}", fx.anni_necessari(sr_t, h, config.Z95, GA), "int", f"Anni per un intervallo di più o meno {h} sullo Sharpe", "funzioni.anni_necessari")

    # --- Copertura onesta ------------------------------------------------------------------------------------------------
    inizi = fx.inizi_mese(date)
    cop = []
    for a in config.COPERTURA_ANNI:
        q, kk = fx.copertura_fuori(x, a * GA, inizi, GA, config.Z95)
        cop.append({"anni": a, "copertura": q, "finestre": kk})
        reg(f"cop{a}", q, "pct0", f"Copertura onesta della formula di Lo, finestre di {a} anni", "funzioni.copertura_fuori")
        reg(f"cop{a}_n", kk, "int", f"Finestre di {a} anni (una per mese)", "funzioni.copertura_fuori")
    pd.DataFrame(cop).to_csv(config.RISULTATI / "copertura.csv", index=False, float_format="%.5f")

    # --- La regola a media mobile contro il buy & hold ----------------------------------------------------------------------
    rr, bh = fx.regola_sma(c, config.MEDIA_REGOLA)
    sr_r, sr_b = fx.sharpe(rr, GA), fx.sharpe(bh, GA)
    lo_d, hi_d = fx.differenza_sharpe_bootstrap(rr, bh, config.N_BOOT, config.BLOCCO, GA, config.LIVELLO_IC, rng)
    reg("media_regola", config.MEDIA_REGOLA, "int", "Lunghezza della media mobile della regola", "config.py")
    reg("reg_n", len(rr), "int", "Sedute del campione comune regola e buy & hold", "dati/")
    reg("reg_sr", sr_r, "num2", "Sharpe della regola a media mobile", "funzioni.sharpe")
    reg("reg_bh_sr", sr_b, "num2", "Sharpe del buy & hold sulle stesse date", "funzioni.sharpe")
    reg("reg_diff", sr_r - sr_b, "num2", "Sharpe della regola meno Sharpe del buy & hold", "funzioni.sharpe")
    reg("reg_lo", lo_d, "num2", "Estremo inferiore dell'intervallo bootstrap a blocchi della differenza", "funzioni.differenza_sharpe_bootstrap")
    reg("reg_hi", hi_d, "num2", "Estremo superiore dell'intervallo bootstrap a blocchi della differenza", "funzioni.differenza_sharpe_bootstrap")
    reg("reg_quota_inv", float(np.mean(rr != 0)), "pct0", "Quota di giorni in cui la regola è investita (giorni con rendimento diverso da zero)", "dati/")

    # --- Verdetti ---------------------------------------------------------------------------------------------------------------
    h = [RIS["wtot_amp_lo"]["valore"] < config.H1_AMPIEZZA,
         RIS["w10_amp_lo"]["valore"] > config.H2_AMPIEZZA,
         RIS["diff_me_lo"]["valore"] < config.H3_DIFF,
         RIS["wtot_amp_bb"]["valore"] > RIS["wtot_amp_bi"]["valore"],
         RIS["cop10"]["valore"] >= config.H5_COPERTURA,
         lo_d <= 0 <= hi_d]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "seme": config.SEME, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
