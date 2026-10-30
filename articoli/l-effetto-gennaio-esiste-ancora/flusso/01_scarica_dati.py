"""Passo 1 - Scarica da Yahoo Finance le chiusure giornaliere dell'S&P 500 e del Russell 2000 (indici di prezzo).

Salva dati/gspc_giornaliero.csv, dati/rut_giornaliero.csv e dati/gspc_metadati.json (fonte, data, versione, SHA-256).
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
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    meta = {"fonte": "Yahoo Finance", "libreria": f"yfinance {yf.__version__}",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "serie": {}}
    for t, f in ((config.TICKER, config.FILE_DATI), (config.TICKER_PICCOLE, config.FILE_PICCOLE)):
        g = yf.Ticker(t).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
        if g.empty:
            raise SystemExit(f"Nessun dato per {t}")
        df = g[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Close"])
        if (df["Close"] <= 0).any():
            raise SystemExit(f"Chiusure non positive in {t}")
        if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
            df = df.iloc[:-1]
        df.to_csv(f, float_format="%.6f")
        meta["serie"][t] = {"righe": len(df), "prima": str(df.index[0].date()), "ultima": str(df.index[-1].date()),
                            "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
        print(t, meta["serie"][t])
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
