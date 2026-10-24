"""Passo 1 - Scarica da Yahoo Finance le serie giornaliere (fondo azionario, fondo obbligazionario, tassi a 10 anni e a 13 settimane).

Salva dati/<ticker>.csv (Date, Close) e dati/metadati.json con fonte, data del download, versione di yfinance e impronta SHA-256.
Per i fondi Close è il prezzo corretto per dividendi (rendimento totale). Gli script successivi leggono SOLO i file salvati.
"""
import hashlib
import json
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str) -> pd.DataFrame:
    for tentativo in range(3):
        grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=True)
        if not grezzo.empty:
            return grezzo
        print(f"{ticker}: nessun dato (tentativo {tentativo + 1})")
        time.sleep(10)
    return pd.DataFrame()


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    meta = {"fonte": "Yahoo Finance", "url_fonte": config.URL_FONTE, "libreria": f"yfinance {yf.__version__}",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "serie": []}
    for ticker, nome, ruolo in config.SERIE:
        riga = {"ticker": ticker, "nome": nome, "ruolo": ruolo}
        grezzo = scarica(ticker)
        if grezzo.empty:
            riga["stato"] = "scartato: nessun dato restituito da Yahoo Finance"
            meta["serie"].append(riga)
            continue
        df = grezzo[["Close"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Close"])
        file = config.file_dati(ticker)
        df.to_csv(file, float_format="%.6f")
        riga.update({"stato": "ok", "file": file.name, "righe": len(df), "prima_data": str(df.index[0].date()),
                     "ultima_data": str(df.index[-1].date()), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
        meta["serie"].append(riga)
        print(f"{ticker}: {len(df)} righe, dal {riga['prima_data']} al {riga['ultima_data']}")
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    if sum(1 for r in meta["serie"] if r["stato"] == "ok") < len(config.SERIE):
        raise SystemExit("Non tutte le serie sono state scaricate.")


if __name__ == "__main__":
    main()
