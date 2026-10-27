"""Passo 1 - Scarica da Yahoo Finance le serie giornaliere degli strumenti e del cambio euro-dollaro.

Salva dati/<ticker>.csv (Date, Open, High, Low, Close, Volume) e dati/metadati.json con la fonte, la data del download,
la versione di yfinance e l'impronta SHA-256 di ogni file. Gli script successivi leggono SOLO i file salvati: i risultati
restano riproducibili anche se Yahoo corregge i dati in futuro.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str) -> pd.DataFrame:
    for tentativo in range(3):
        grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
        if not grezzo.empty:
            return grezzo
        print(f"{ticker}: nessun dato (tentativo {tentativo + 1})")
        time.sleep(10)
    return pd.DataFrame()


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    meta = {"fonte": "Yahoo Finance", "url_fonte": config.URL_FONTE, "libreria": f"yfinance {yf.__version__}",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "strumenti": []}
    elenco = [(t, n, v) for t, n, v in config.STRUMENTI] + [(config.TICKER_CAMBIO, "cambio euro-dollaro", "USD")]
    for ticker, nome, valuta in elenco:
        riga = {"ticker": ticker, "nome": nome, "valuta": valuta}
        grezzo = scarica(ticker)
        if grezzo.empty:
            riga["stato"] = "scartato: nessun dato restituito da Yahoo Finance"
            meta["strumenti"].append(riga)
            continue
        df = grezzo[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Close"])
        df = df[df["Close"] > 0]
        if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 18:       # seduta in corso: barra incompleta
            df = df.iloc[:-1]
        salti = (df["Close"].pct_change().abs() > 0.25).sum()
        file = config.file_dati(ticker)
        df.to_csv(file, float_format="%.6f")
        riga.update({"stato": "ok", "file": file.name, "righe": len(df), "prima_data": str(df.index[0].date()),
                     "ultima_data": str(df.index[-1].date()), "variazioni_giornaliere_oltre_25_per_cento": int(salti),
                     "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
        meta["strumenti"].append(riga)
        print(f"{ticker}: {len(df)} righe, dal {riga['prima_data']} al {riga['ultima_data']}, salti oltre il 25%: {salti}")
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = {r["ticker"] for r in meta["strumenti"] if r["stato"] == "ok"}
    if config.TICKER_CAMBIO not in ok and any(v == "USD" for _, _, v in config.STRUMENTI):
        print("Attenzione: cambio non scaricato, gli strumenti in dollari verranno scartati.")
    if sum(1 for t, _, _ in config.STRUMENTI if t in ok) < 1:
        raise SystemExit("Nessuno strumento scaricato.")


if __name__ == "__main__":
    main()
