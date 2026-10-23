"""Passo 1 - Sceglie 50 titoli dell'S&P 500 con un sorteggio a seme fisso e scarica i loro prezzi da Yahoo Finance.

Salva:
  dati/sp500_composizione.csv   elenco dei componenti dell'indice al momento del download
  dati/selezione.csv            ordine del sorteggio, esito per ogni titolo provato (preso o scartato, e perché)
  dati/titoli/<TICKER>.csv      Date, Open, High, Low, Close, Volume dei 50 titoli scelti
  dati/eurusd_giornaliero.csv   cambio, in dollari per un euro
  dati/metadati.json            fonte, data del download, versione di yfinance, impronta SHA-256 dei file

Gli script successivi leggono SOLO i file salvati: i risultati sono riproducibili anche se Yahoo
corregge i dati in futuro.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str, tentativi: int = 3) -> pd.DataFrame | None:
    for t in range(tentativi):
        try:
            grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, auto_adjust=False)
        except Exception as e:  # noqa: BLE001 - errori di rete: si riprova
            print(f"  {ticker}: errore {type(e).__name__}, tentativo {t + 1}")
            grezzo = None
        if grezzo is not None and not grezzo.empty:
            break
        time.sleep(3)
    else:
        return None
    df = grezzo[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df.index.name = "Date"
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["Open", "Close"])
    if df.empty or (df[["Open", "Close"]] <= 0).any().any():
        return None
    return df


def leggi_composizione() -> pd.DataFrame:
    grezzo = pd.read_csv(config.URL_COMPOSIZIONE)
    colonne = {"Symbol": "simbolo", "Security": "nome", "Name": "nome", "GICS Sector": "settore"}
    df = grezzo.rename(columns=colonne)[["simbolo", "nome", "settore"]].copy()
    df["simbolo"] = df["simbolo"].astype(str).str.strip()
    df["ticker_yahoo"] = df["simbolo"].str.replace(".", "-", regex=False)   # BRK.B -> BRK-B
    df = df.drop_duplicates("ticker_yahoo").sort_values("ticker_yahoo").reset_index(drop=True)
    if len(df) < 400:
        raise SystemExit(f"Elenco dei componenti troppo corto ({len(df)} righe): scarico non valido.")
    return df


def main() -> None:
    config.DATI_TITOLI.mkdir(parents=True, exist_ok=True)
    comp = leggi_composizione()
    comp.to_csv(config.FILE_COMPOSIZIONE, index=False)

    cambio = scarica(config.TICKER_CAMBIO)
    if cambio is None:
        raise SystemExit("Yahoo Finance non ha restituito il cambio euro/dollaro.")
    cambio.to_csv(config.FILE_CAMBIO, float_format="%.6f")

    ordine = np.random.default_rng(config.SEME).permutation(len(comp))
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    prese, righe = [], []
    ultima_data = None
    for pos, k in enumerate(ordine, 1):
        if len(prese) >= config.N_TITOLI:
            break
        r = comp.iloc[k]
        t = r["ticker_yahoo"]
        df = scarica(t)
        esito = "preso"
        if df is None:
            esito = "scartato: dati non disponibili"
        else:
            # Se lo script gira durante la seduta l'ultima barra è incompleta: la scartiamo.
            if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
                df = df.iloc[:-1]
            fine = df.index[-1]
            i0 = int(df.index.searchsorted(fine - pd.DateOffset(years=config.ANNI_TEST)))
            if i0 < config.SEDUTE_MINIME_PRIMA:
                esito = f"scartato: storia troppo corta ({i0} sedute prima dell'inizio del test)"
            elif ultima_data is not None and (ultima_data - fine).days > 5:
                esito = "scartato: dati non aggiornati"
        if esito == "preso":
            ultima_data = df.index[-1] if ultima_data is None else max(ultima_data, df.index[-1])
            df.to_csv(config.DATI_TITOLI / f"{t}.csv", float_format="%.6f")
            prese.append(t)
        righe.append({"ordine_sorteggio": pos, "ticker": t, "nome": r["nome"], "settore": r["settore"], "esito": esito})
        print(f"{pos:3d} {t:8s} {esito}")
    if len(prese) < config.N_TITOLI:
        raise SystemExit(f"Solo {len(prese)} titoli validi su {config.N_TITOLI} richiesti.")
    pd.DataFrame(righe).to_csv(config.DATI / "selezione.csv", index=False)

    def impronta(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    metadati = {
        "descrizione": config.DESCRIZIONE_DATI,
        "fonte": "Yahoo Finance",
        "fonte_composizione": config.URL_COMPOSIZIONE,
        "url_fonte": config.URL_FONTE,
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seme": config.SEME,
        "componenti_nell_elenco": len(comp),
        "titoli_provati": len(righe),
        "titoli_scartati": len(righe) - len(prese),
        "titoli": prese,
        "ultima_data_titoli": str(ultima_data.date()),
        "prima_data_cambio": str(cambio.index[0].date()),
        "ultima_data_cambio": str(cambio.index[-1].date()),
        "colonne_usate": config.NOTA_COLONNA,
        "sha256_composizione": impronta(config.FILE_COMPOSIZIONE),
        "sha256_cambio": impronta(config.FILE_CAMBIO),
        "sha256_titoli": {t: impronta(config.DATI_TITOLI / f"{t}.csv") for t in prese},
    }
    config.FILE_METADATI.write_text(json.dumps(metadati, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nScaricati {len(prese)} titoli, {len(righe) - len(prese)} scartati. Ultima seduta: {ultima_data.date()}")


if __name__ == "__main__":
    main()
