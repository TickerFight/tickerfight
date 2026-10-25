"""Passo 1 - Scarica da Yahoo Finance la serie giornaliera di cinque ETF (SPY, VGK, EEM, VTI, VWO).

Salva, per ogni ETF, dati/<ticker>.csv (Date, Close, Adj Close, Volume) e dati/metadati.json con la fonte,
la data del download, la versione di yfinance e l'impronta SHA-256 di ogni file. Gli script successivi leggono SOLO
i file salvati: i risultati restano riproducibili anche se Yahoo corregge i dati in futuro.
"Adj Close" è il prezzo con i dividendi reinvestiti: è quello che si usa per i rendimenti.
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
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "etf": []}
    nomi = {t: (n, a) for t, n, a in config.ETF + config.ETF_ALT}
    for ticker in config.TUTTI_I_TICKER:
        riga = {"ticker": ticker, "nome": nomi[ticker][0], "area": nomi[ticker][1]}
        grezzo = scarica(ticker)
        if grezzo.empty or "Adj Close" not in grezzo.columns:
            riga["stato"] = "scartato: nessun dato restituito da Yahoo Finance"
            meta["etf"].append(riga)
            continue
        df = grezzo[["Close", "Adj Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["Adj Close"])
        df = df[df["Adj Close"] > 0]
        # seduta ancora in corso: barra incompleta, da scartare
        if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 18:
            df = df.iloc[:-1]
        file = config.file_dati(ticker)
        df.to_csv(file, float_format="%.6f")
        riga.update({"stato": "ok", "file": file.name, "righe": len(df), "prima_data": str(df.index[0].date()),
                     "ultima_data": str(df.index[-1].date()), "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
        meta["etf"].append(riga)
        print(f"{ticker}: {len(df)} righe, dal {riga['prima_data']} al {riga['ultima_data']}")
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    principali = {t for t, _, _ in config.ETF}
    ok = {r["ticker"] for r in meta["etf"] if r["stato"] == "ok"}
    if not principali <= ok:
        raise SystemExit(f"Mancano ETF principali: {sorted(principali - ok)}")


if __name__ == "__main__":
    main()
