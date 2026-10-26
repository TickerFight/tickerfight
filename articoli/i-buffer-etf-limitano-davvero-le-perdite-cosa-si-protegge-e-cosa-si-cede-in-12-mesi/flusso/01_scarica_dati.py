"""Passo 1 - Scarica da Yahoo Finance i dodici buffer ETF, SPY (S&P 500 total return) e il tasso a 3 mesi (^IRX).

Salva:
  dati/serie_giornaliere.csv   colonne Date, un prezzo di chiusura aggiustato per fondo, SPY, IRX (% annuo)
  dati/serie_metadati.json     fonte, data del download, versione di yfinance, righe per serie, impronta SHA-256
Gli script successivi leggono SOLO il file salvato. I fondi senza dati su Yahoo Finance sono segnalati e saltati.
"""
import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str, aggiustato: bool) -> pd.Series:
    try:
        grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=aggiustato)
    except Exception as e:  # noqa: BLE001
        print(f"{ticker}: errore {e}")
        return pd.Series(dtype=float)
    if grezzo.empty:
        print(f"{ticker}: nessun dato")
        return pd.Series(dtype=float)
    s = grezzo["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
    print(f"{ticker}: {len(s)} righe, da {s.index[0].date()} a {s.index[-1].date()}")
    return s


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    spy = scarica(config.TICKER_INDICE, True)
    irx = scarica(config.TICKER_3M, False)
    if len(spy) < 1000 or len(irx) < 1000:
        raise SystemExit("SPY o ^IRX senza storia sufficiente su Yahoo Finance.")
    if not (-1 < irx.median() < 25):
        raise SystemExit(f"IRX: scala dei tassi inattesa (mediana {irx.median():.2f}); attesi valori in % annuo.")
    colonne = {"SPY": spy}
    for tk in config.FONDI:
        s = scarica(tk, True)
        if len(s) >= 250:
            colonne[tk] = s
    if len(colonne) - 1 < 6:
        raise SystemExit(f"Solo {len(colonne) - 1} fondi con almeno un anno di storia: troppo pochi per l'articolo.")
    colonne["IRX"] = irx
    df = pd.concat(colonne, axis=1).sort_index()
    df["IRX"] = df["IRX"].ffill()
    df = df.dropna(subset=["SPY"])
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    barra_scartata = None
    if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
        barra_scartata = str(df.index[-1].date())
        df = df.iloc[:-1]
    df.index.name = "Date"
    df.to_csv(config.FILE_DATI, float_format="%.6f")
    sha = hashlib.sha256(config.FILE_DATI.read_bytes()).hexdigest()
    meta = {
        "ticker": {"indice": config.TICKER_INDICE, "3_mesi": config.TICKER_3M, "fondi": [c for c in df.columns if c in config.FONDI]},
        "fonte": "Yahoo Finance",
        "url_fonte": config.URL_FONTE,
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "righe_salvate": len(df),
        "prima_data": str(df.index[0].date()),
        "ultima_data": str(df.index[-1].date()),
        "righe_per_serie": {c: int(df[c].notna().sum()) for c in df.columns},
        "barra_incompleta_scartata": barra_scartata,
        "colonne": "prezzi di chiusura aggiustati (SPY comprende i dividendi); IRX = rendimento annuo in %",
        "sha256_file": sha,
    }
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
