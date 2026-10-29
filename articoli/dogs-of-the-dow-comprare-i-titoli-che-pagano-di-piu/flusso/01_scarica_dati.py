"""Passo 1 - Scarica da Yahoo Finance prezzi e dividendi dei titoli del Dow Jones e dello SPY.

Salva dati/adj.csv (chiusure corrette per dividendi, per il rendimento totale), dati/close.csv (chiusure senza correzione per i dividendi,
corrette solo per i frazionamenti: servono per il rendimento da dividendo), dati/div.csv (dividendi pagati per azione, una riga per data
di stacco) e dati/metadati.json. Gli script successivi leggono SOLO i file salvati.
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
        try:
            g = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
        except Exception as e:
            print(f"{ticker}: errore {e!r} (tentativo {tentativo + 1})")
            g = pd.DataFrame()
        if not g.empty and "Adj Close" in g.columns:
            g.index = pd.to_datetime(g.index).tz_localize(None).normalize()
            g = g[~g.index.duplicated(keep="last")].sort_index()
            return g
        time.sleep(8)
    return pd.DataFrame()


def main() -> None:
    config.DATI.mkdir(parents=True, exist_ok=True)
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    adj, close, div, esiti = {}, {}, {}, []
    tickers = [config.INDICE] + list(config.UNIVERSO)
    for t in tickers:
        g = scarica(t)
        if g.empty:
            esiti.append({"ticker": t, "stato": "assente: nessun dato restituito da Yahoo Finance"})
            print(f"{t}: nessun dato")
            continue
        if g.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 18:
            g = g.iloc[:-1]
        g = g[(g["Adj Close"] > 0) & (g["Close"] > 0)].dropna(subset=["Adj Close", "Close"])
        adj[t], close[t] = g["Adj Close"], g["Close"]
        div[t] = g["Dividends"][g["Dividends"] > 0] if "Dividends" in g.columns else pd.Series(dtype=float)
        esiti.append({"ticker": t, "stato": "ok", "righe": len(g), "prima_data": str(g.index[0].date()),
                      "ultima_data": str(g.index[-1].date()), "n_dividendi": int(len(div[t]))})
        print(f"{t}: {len(g)} righe, {len(div[t])} dividendi, dal {g.index[0].date()} al {g.index[-1].date()}")
    if config.INDICE not in adj or len(adj) < 0.9 * len(tickers):
        raise SystemExit("Download insufficiente: manca lo SPY o più del 10% dei titoli.")
    for nome, d in (("adj", adj), ("close", close)):
        df = pd.DataFrame(d).sort_index()
        df.index.name = "Date"
        df.to_csv(config.DATI / f"{nome}.csv", float_format="%.6f")
    dv = pd.DataFrame(div).sort_index()
    dv.index.name = "Date"
    dv.to_csv(config.FILE_DIV, float_format="%.6f")
    meta = {"fonte": "Yahoo Finance", "url_fonte": config.URL_FONTE, "libreria": f"yfinance {yf.__version__}",
            "prezzi": "Adj Close = corretto per dividendi e frazionamenti; Close = corretto solo per frazionamenti",
            "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "titoli": esiti,
            "sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (config.FILE_ADJ, config.FILE_CLOSE, config.FILE_DIV)}}
    config.FILE_METADATI.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
