"""Passo 1 - Scarica da Yahoo Finance Apple (AAPL) e il cambio euro/dollaro.

Salva:
  dati/aapl_giornaliero.csv      Date, Open, High, Low, Close, Volume
  dati/eurusd_giornaliero.csv    idem, in dollari per un euro
  dati/metadati.json             fonte, data del download, versione di yfinance, impronta SHA-256 dei file

Gli script successivi leggono SOLO i file salvati: i risultati sono riproducibili anche se Yahoo
corregge i dati in futuro.
"""
import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str) -> pd.DataFrame:
    grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
    if grezzo.empty:
        raise SystemExit(f"Yahoo Finance non ha restituito dati per {ticker}.")
    df = grezzo[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df.index.name = "Date"
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["Open", "Close"])
    if (df[["Open", "Close"]] <= 0).any().any():
        raise SystemExit(f"{ticker}: trovati prezzi non positivi.")
    return df


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)

    titolo = scarica(config.TICKER)
    cambio = scarica(config.TICKER_CAMBIO)

    # Se lo script gira durante la seduta, l'ultima barra di Apple è incompleta: la scartiamo.
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    barra_scartata = None
    if titolo.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
        barra_scartata = str(titolo.index[-1].date())
        titolo = titolo.iloc[:-1]

    titolo.to_csv(config.FILE_DATI, float_format="%.6f")
    cambio.to_csv(config.FILE_CAMBIO, float_format="%.6f")

    def impronta(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    metadati = {
        "ticker": config.TICKER,
        "ticker_cambio": config.TICKER_CAMBIO,
        "descrizione": config.DESCRIZIONE_DATI,
        "fonte": "Yahoo Finance",
        "url_fonte": config.URL_FONTE,
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "righe_titolo": len(titolo),
        "righe_cambio": len(cambio),
        "prima_data_titolo": str(titolo.index[0].date()),
        "ultima_data_titolo": str(titolo.index[-1].date()),
        "prima_data_cambio": str(cambio.index[0].date()),
        "ultima_data_cambio": str(cambio.index[-1].date()),
        "barra_incompleta_scartata": barra_scartata,
        "colonne_usate": config.NOTA_COLONNA,
        "sha256_titolo": impronta(config.FILE_DATI),
        "sha256_cambio": impronta(config.FILE_CAMBIO),
    }
    config.FILE_METADATI.write_text(json.dumps(metadati, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metadati, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
