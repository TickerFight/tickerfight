"""Passo 2 - Stima dello spread dai prezzi (Corwin-Schultz e Roll) su sette ETF.

Legge SOLO dati/<ticker>.csv e produce in risultati/: metriche.json, per_etf.csv, mensile_spy.csv.
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
    righe, serie = [], {}
    for t in config.TICKERS:
        df = pd.read_csv(config.file_dati(t), parse_dates=["Date"], index_col="Date").sort_index()
        df = df[(df["High"] >= df["Low"]) & (df["Low"] > 0)]
        raw = pd.Series(fx.cs_grezzo(df["High"].to_numpy(), df["Low"].to_numpy()), index=df.index).dropna()
        cs = raw.clip(lower=0)
        tick = (config.TICK / df["Close"]).mean()
        roll = fx.roll_mensile(df["Close"])
        k = t.lower()
        serie[t] = (df, raw, cs)
        reg(f"{k}_prima", str(df.index[0].date()), "data_lunga", f"Prima seduta di {t}", "dati/")
        reg(f"{k}_n", len(raw), "int", f"Coppie di giorni usate per {t}", "dati/")
        reg(f"{k}_cs", cs.mean(), "pct3", f"Stima media di Corwin-Schultz per {t} (negativi posti a zero)", "funzioni.cs_grezzo")
        reg(f"{k}_cs_med", cs.median(), "pct3", f"Stima mediana di Corwin-Schultz per {t}", "funzioni.cs_grezzo")
        reg(f"{k}_neg", float((raw < 0).mean()), "pct0", f"Quota di stime grezze negative per {t}", "funzioni.cs_grezzo")
        reg(f"{k}_tick", tick, "pct3", f"Minimo teorico dello spread per {t}: un centesimo diviso la chiusura, in media", "config.TICK / Close")
        reg(f"{k}_mult", cs.mean() / tick, "num1", f"Stima media diviso minimo teorico per {t}", "rapporto")
        reg(f"{k}_roll_nan", float(roll.isna().mean()), "pct0", f"Quota di mesi in cui Roll non è definito per {t}", "funzioni.roll_mensile")
        reg(f"{k}_roll_med", float(roll.median()), "pct3", f"Stima mediana di Roll sui mesi in cui è definita, {t}", "funzioni.roll_mensile")
        righe.append({"etf": t, "cs": cs.mean(), "cs_mediana": cs.median(), "neg": (raw < 0).mean(), "tick": tick,
                      "roll_nan": roll.isna().mean(), "roll_mediana": roll.median()})
    pd.DataFrame(righe).to_csv(config.RISULTATI / "per_etf.csv", index=False, float_format="%.6f")

    reg("n_etf", len(config.TICKERS), "int", "ETF analizzati", "config.py")
    df, raw, cs = serie["SPY"]
    reg("data_ultima", str(df.index[-1].date()), "data_lunga", "Ultima seduta dei dati", "dati/")
    reg("tick_dollari", config.TICK, "num2", "Tick minimo in dollari", "config.py")

    # Stima mensile di SPY contro la volatilità del mese
    m_cs = fx.media_mensile(cs)
    m_vol = fx.vol_mensile(df["Close"])
    mm = pd.concat([m_cs.rename("cs"), m_vol.rename("vol")], axis=1).dropna()
    mm.to_csv(config.RISULTATI / "mensile_spy.csv", float_format="%.6f")
    corr = float(mm["cs"].corr(mm["vol"]))
    reg("corr_vol", corr, "num2", "Correlazione mensile tra la stima di SPY e la volatilità giornaliera del mese", "pandas corr")
    reg("n_mesi", len(mm), "int", "Mesi usati per la correlazione", "dati/")
    mediana_mesi = float(m_cs.median())
    mar = float(m_cs[pd.Period(config.MESE_CRISI)])
    reg("mese_crisi", config.MESE_CRISI + "-01", "data_lunga", "Mese del crollo del Covid", "config.py")
    reg("cs_crisi", mar, "pct3", "Stima media di SPY nel mese del crollo", "funzioni")
    reg("cs_med_mesi", mediana_mesi, "pct3", "Mediana delle stime mensili di SPY", "funzioni")
    reg("mult_crisi", mar / mediana_mesi, "num1", "Stima del mese del crollo diviso la mediana dei mesi, SPY", "rapporto")
    prima = cs[cs.index < config.SOGLIA_PRIMA_ANNO].mean()
    seconda = cs[cs.index >= config.SOGLIA_PRIMA_ANNO].mean()
    reg("cs_prima", prima, "pct3", "Stima media di SPY prima del 2013", "funzioni")
    reg("cs_seconda", seconda, "pct3", "Stima media di SPY dal 2013", "funzioni")
    reg("costo_giro", RIS["spy_cs"]["valore"], "pct3", "Costo di un acquisto e una vendita di SPY se si pagasse l'intera stima (un giro completo)", "funzioni")

    # Costanti di soglia
    reg("h1_mult", config.H1_MULTIPLO, "int", "Ipotesi 1: multiplo minimo", "config.py")
    reg("h2_quota", config.H2_QUOTA_NEG, "pct0", "Ipotesi 2: quota minima di stime negative", "config.py")
    reg("h3_corr", config.H3_CORR, "num1", "Ipotesi 3: correlazione minima", "config.py")
    reg("h5_mult", config.H5_MULTIPLO, "int", "Ipotesi 5: multiplo minimo", "config.py")
    reg("h6_quota", config.H6_QUOTA_ROLL, "pct0", "Ipotesi 6: quota minima di mesi con Roll non definito", "config.py")

    h = [RIS["spy_mult"]["valore"] >= config.H1_MULTIPLO,
         RIS["spy_neg"]["valore"] > config.H2_QUOTA_NEG,
         corr > config.H3_CORR,
         RIS["eem_cs"]["valore"] > RIS["spy_cs"]["valore"] and RIS["iwm_cs"]["valore"] > RIS["spy_cs"]["valore"],
         mar / mediana_mesi >= config.H5_MULTIPLO,
         RIS["spy_roll_nan"]["valore"] > config.H6_QUOTA_ROLL]
    for i, v in enumerate(h, 1):
        reg(f"h{i}_esito", int(bool(v)), "int", f"Ipotesi {i}: 1 se confermata, 0 se smentita", "confronto con config.py")
    reg("n_conf", int(sum(bool(v) for v in h)), "int", "Ipotesi confermate (su 6)", "confronto con config.py")

    meta = {"generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "ipotesi": config.IPOTESI}
    (config.RISULTATI / "metriche.json").write_text(json.dumps({"meta": meta, "valori": RIS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Scritte {len(RIS)} metriche.")


if __name__ == "__main__":
    main()
