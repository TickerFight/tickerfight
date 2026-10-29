"""Passo 1 - Scarica da Yahoo Finance prezzi, dividendi e split dei sei strumenti.

Salva in dati/ un file per strumento (<ticker>.csv con Close, Adj Close, Dividends, Stock Splits) e dati/metadati.json
con da dove arrivano i dati, quando, con quale versione di yfinance e l'impronta SHA-256 di ogni file.
Gli script successivi leggono SOLO i file salvati.
"""
import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    meta = {"fonte": "Yahoo Finance", "url_fonte": config.URL_FONTE, "libreria": f"yfinance {yf.__version__}",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "strumenti": {}}
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    for chiave, ticker, _ in config.STRUMENTI:
        g = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False, actions=True)
        if g.empty:
            raise SystemExit(f"Nessun dato per {ticker}")
        for col in ("Dividends", "Stock Splits"):
            if col not in g:
                g[col] = 0.0
        df = g[["Close", "Adj Close", "Dividends", "Stock Splits"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Close", "Adj Close"])
        if (df[["Close", "Adj Close"]] <= 0).any().any():
            raise SystemExit(f"Prezzi non positivi per {ticker}")
        scartata = None
        if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
            scartata = str(df.index[-1].date())
            df = df.iloc[:-1]
        percorso = config.DATI / f"{ticker}.csv"
        df.to_csv(percorso, float_format="%.8f")
        meta["strumenti"][ticker] = {
            "prima_data": str(df.index[0].date()), "ultima_data": str(df.index[-1].date()), "righe": len(df),
            "dividendi": int((df["Dividends"] > 0).sum()), "split": int((df["Stock Splits"] > 0).sum()),
            "barra_incompleta_scartata": scartata, "sha256_file": hashlib.sha256(percorso.read_bytes()).hexdigest()}
        print(ticker, meta["strumenti"][ticker])
    (config.DATI / "metadati.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
