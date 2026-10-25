"""Passo 1 - Scarica da Yahoo Finance S&P 500, rendimento a 10 anni (^TNX) e rendimento a 3 mesi (^IRX).

Salva:
  dati/serie_giornaliere.csv   colonne Date, GSPC (chiusura), TNX (% annuo), IRX (% annuo)
  dati/serie_metadati.json     fonte, data del download, versione di yfinance, impronta SHA-256
Gli script successivi leggono SOLO il file salvato.
"""
import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str) -> pd.Series:
    grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
    if grezzo.empty:
        raise SystemExit(f"Yahoo Finance non ha restituito dati per {ticker}.")
    s = grezzo["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
    return s


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    gspc = scarica(config.TICKER_AZIONI)
    tnx = scarica(config.TICKER_10A)
    irx = scarica(config.TICKER_3M)
    for nome, s in (("TNX", tnx), ("IRX", irx)):
        if not (-1 < s.median() < 25):
            raise SystemExit(f"{nome}: scala dei tassi inattesa (mediana {s.median():.2f}); attesi valori in % annuo.")
    df = pd.concat({"GSPC": gspc, "TNX": tnx, "IRX": irx}, axis=1).sort_index()
    df = df.dropna(subset=["GSPC"])
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    barra_scartata = None
    if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
        barra_scartata = str(df.index[-1].date())
        df = df.iloc[:-1]
    df.index.name = "Date"
    df.to_csv(config.FILE_DATI, float_format="%.6f")
    sha = hashlib.sha256(config.FILE_DATI.read_bytes()).hexdigest()
    meta = {
        "ticker": {"azioni": config.TICKER_AZIONI, "10_anni": config.TICKER_10A, "3_mesi": config.TICKER_3M},
        "fonte": "Yahoo Finance",
        "url_fonte": config.URL_FONTE,
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "righe_salvate": len(df),
        "prima_data": str(df.index[0].date()),
        "ultima_data": str(df.index[-1].date()),
        "barra_incompleta_scartata": barra_scartata,
        "colonne": "GSPC = chiusura dell'indice (senza dividendi); TNX e IRX = rendimento annuo in %",
        "sha256_file": sha,
    }
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
