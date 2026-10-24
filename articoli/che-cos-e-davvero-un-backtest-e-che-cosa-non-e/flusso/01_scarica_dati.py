"""Passo 1 - Scarica da Yahoo Finance la serie giornaliera dello SPY (ETF sull'S&P 500).

Salva:
  dati/spy_giornaliero.csv    la serie (Date, Open, High, Low, Close, AdjClose, Volume)
  dati/spy_metadati.json      da dove arrivano i dati, quando, con quale
                              versione di yfinance, e l'impronta SHA-256 del file

Gli script successivi leggono SOLO il file salvato: i risultati sono quindi
riproducibili anche se Yahoo corregge i dati in futuro.
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

    ticker = yf.Ticker(config.TICKER)
    grezzo = ticker.history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
    if grezzo.empty:
        raise SystemExit("Yahoo Finance non ha restituito dati.")

    df = grezzo[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].rename(columns={"Adj Close": "AdjClose"})
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df.index.name = "Date"
    righe_scaricate = len(df)

    # Controlli di qualità di base
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["Close", "AdjClose"])
    if ((df["Close"] <= 0).any() or (df["AdjClose"] <= 0).any()):
        raise SystemExit("Trovati prezzi di chiusura non positivi.")

    # Se lo script gira durante la seduta, l'ultima barra è incompleta: la scartiamo.
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    barra_scartata = None
    if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
        barra_scartata = str(df.index[-1].date())
        df = df.iloc[:-1]

    df.to_csv(config.FILE_DATI, float_format="%.6f")

    sha = hashlib.sha256(config.FILE_DATI.read_bytes()).hexdigest()
    metadati = {
        "ticker": config.TICKER,
        "descrizione": "SPY, ETF sull'S&P 500",
        "fonte": "Yahoo Finance",
        "url_fonte": config.URL_FONTE,
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "righe_scaricate": righe_scaricate,
        "righe_salvate": len(df),
        "prima_data": str(df.index[0].date()),
        "ultima_data": str(df.index[-1].date()),
        "barra_incompleta_scartata": barra_scartata,
        "colonna_usata": "Close (non corretta) per il segnale; AdjClose (corretta per dividendi) per i rendimenti",
        "sha256_file": sha,
    }
    config.FILE_METADATI.write_text(
        json.dumps(metadati, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(metadati, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
