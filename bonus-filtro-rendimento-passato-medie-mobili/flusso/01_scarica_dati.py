"""Passo 1 - Scarica da Yahoo Finance i titoli nuovi per il test fuori campione.

Si ripete il sorteggio degli articoli precedenti (stesso elenco, stesso seme, stesso ordine) saltando i titoli
già usati, e si prendono i primi N_TITOLI con dati completi. I prezzi sono tagliati a FINE_TEST.

Salva:
  dati/titoli/<TICKER>.csv   Date, Open, High, Low, Close, Volume
  dati/eurusd_giornaliero.csv   cambio, in dollari per un euro, dal 2015
  dati/selezione.csv         ordine del sorteggio, esito per ogni titolo provato
  dati/metadati.json         fonte, data del download, versione di yfinance, impronte SHA-256
"""
import hashlib
import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

import config


def scarica(ticker: str, tentativi: int = 3) -> pd.DataFrame | None:
    for t in range(tentativi):
        try:
            grezzo = yf.Ticker(ticker).history(start=config.INIZIO_DOWNLOAD, end="2021-11-10", auto_adjust=False)
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
    df = df[df.index <= pd.Timestamp(config.FINE_TEST)].dropna(subset=["Open", "Close"])
    if df.empty or (df[["Open", "Close"]] <= 0).any().any():
        return None
    return df


def main() -> None:
    config.DATI_TITOLI.mkdir(parents=True, exist_ok=True)
    comp = pd.read_csv(config.FILE_COMPOSIZIONE)
    usati = set()
    for f in (config.FILE_SELEZ_SVIL, config.FILE_SELEZ_VAL):
        s = pd.read_csv(f)
        usati |= set(s.loc[s["esito"] == "preso", "ticker"])
    cambio = scarica(config.TICKER_CAMBIO)
    if cambio is None:
        raise SystemExit("Yahoo Finance non ha restituito il cambio euro/dollaro.")
    cambio.to_csv(config.FILE_CAMBIO, float_format="%.6f")
    ordine = np.random.default_rng(config.SEME).permutation(len(comp))
    prese, righe = [], []
    for pos, k in enumerate(ordine, 1):
        if len(prese) >= config.N_TITOLI:
            break
        r = comp.iloc[k]
        t = r["ticker_yahoo"]
        if t in usati:
            continue
        df = scarica(t)
        esito = "preso"
        if df is None:
            esito = "scartato: dati non disponibili"
        else:
            fine = df.index[-1]
            i0 = int(df.index.searchsorted(fine - pd.DateOffset(years=config.ANNI_TEST)))
            if (pd.Timestamp(config.FINE_TEST) - fine).days > 5:
                esito = "scartato: nessun dato vicino alla fine del test"
            elif i0 < config.SEDUTE_MINIME_PRIMA:
                esito = f"scartato: storia troppo corta ({i0} sedute prima dell'inizio del test)"
        if esito == "preso":
            df.to_csv(config.DATI_TITOLI / f"{t}.csv", float_format="%.6f")
            prese.append(t)
        righe.append({"ordine_sorteggio": pos, "ticker": t, "nome": r["nome"], "settore": r["settore"], "esito": esito})
        print(f"{pos:3d} {t:8s} {esito}")
    if len(prese) < config.N_TITOLI:
        raise SystemExit(f"Solo {len(prese)} titoli validi su {config.N_TITOLI} richiesti.")
    pd.DataFrame(righe).to_csv(config.FILE_SELEZIONE, index=False)

    def impronta(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    metadati = {
        "descrizione": config.DESCRIZIONE_DATI,
        "fonte": "Yahoo Finance",
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seme": config.SEME,
        "titoli_gia_usati": len(usati),
        "titoli_provati": len(righe),
        "titoli_scartati": len(righe) - len(prese),
        "titoli": prese,
        "fine_test": config.FINE_TEST,
        "colonne_usate": config.NOTA_COLONNA,
        "sha256_titoli": {t: impronta(config.DATI_TITOLI / f"{t}.csv") for t in prese},
        "sha256_cambio": impronta(config.FILE_CAMBIO),
    }
    config.FILE_METADATI.write_text(json.dumps(metadati, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nScaricati {len(prese)} titoli, {len(righe) - len(prese)} scartati.")


if __name__ == "__main__":
    main()
