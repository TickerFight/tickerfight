"""Passo 1 - Scarica da Yahoo Finance le chiusure giornaliere corrette (dividendi e frazionamenti) dell'universo e dello SPY.

Salva dati/prezzi.csv (una colonna per titolo, indice Date) e dati/metadati.json con la fonte, la data del download,
la versione di yfinance, l'esito per ogni titolo e l'impronta SHA-256 del file. Gli script successivi leggono SOLO i
file salvati: i risultati restano riproducibili anche se Yahoo corregge i dati in futuro.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str) -> pd.Series:
    for tentativo in range(3):
        try:
            grezzo = yf.Ticker(ticker).history(start=config.INIZIO, auto_adjust=True)
        except Exception as e:  # rete o limiti di Yahoo: si riprova
            print(f"{ticker}: errore {e!r} (tentativo {tentativo + 1})")
            grezzo = pd.DataFrame()
        if not grezzo.empty:
            s = grezzo["Close"].copy()
            s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
            s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
            return s[s > 0]
        time.sleep(8)
    return pd.Series(dtype=float)


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    tickers = [config.INDICE] + list(config.UNIVERSO)
    serie, esiti = {}, []
    for t in tickers:
        s = scarica(t)
        if s.empty:
            esiti.append({"ticker": t, "stato": "assente: nessun dato restituito da Yahoo Finance"})
            print(f"{t}: nessun dato")
            continue
        # seduta ancora in corso: barra incompleta, da scartare
        if s.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 18:
            s = s.iloc[:-1]
        serie[t] = s
        esiti.append({"ticker": t, "stato": "ok", "righe": len(s), "prima_data": str(s.index[0].date()),
                      "ultima_data": str(s.index[-1].date())})
        print(f"{t}: {len(s)} righe, dal {s.index[0].date()} al {s.index[-1].date()}")
    if config.INDICE not in serie or len(serie) < 0.8 * len(tickers):
        raise SystemExit("Download insufficiente: manca lo SPY o più del 20% dei titoli.")
    df = pd.DataFrame(serie).sort_index()
    df.index.name = "Date"
    df.to_csv(config.FILE_PREZZI, float_format="%.6f")
    meta = {"fonte": "Yahoo Finance", "url_fonte": config.URL_FONTE, "libreria": f"yfinance {yf.__version__}",
            "prezzi": "chiusure corrette per dividendi e frazionamenti (auto_adjust=True)",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "file": config.FILE_PREZZI.name, "sha256": hashlib.sha256(config.FILE_PREZZI.read_bytes()).hexdigest(),
            "titoli": esiti}
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Salvati {df.shape[1]} titoli, {len(df)} giorni.")


if __name__ == "__main__":
    main()
