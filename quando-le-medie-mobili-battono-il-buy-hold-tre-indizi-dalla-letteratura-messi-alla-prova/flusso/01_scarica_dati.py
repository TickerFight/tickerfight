"""Passo 1 - Scarica da Yahoo Finance i titoli di validazione.

I 50 titoli di sviluppo sono già in dati/titoli_sviluppo/ (copiati dall'articolo precedente, stessi file).
Qui si ripete lo stesso sorteggio (stesso elenco, stesso seme, stesso ordine) e, saltando i titoli già
provati nell'articolo precedente, si prendono i primi N_VALIDAZIONE con dati completi.

Salva:
  dati/titoli_validazione/<TICKER>.csv   Date, Open, High, Low, Close, Volume
  dati/selezione_validazione.csv         ordine del sorteggio, esito per ogni titolo provato
  dati/metadati.json                     fonte, data del download, versione di yfinance, impronte SHA-256
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


def main() -> None:
    config.DATI_VAL.mkdir(parents=True, exist_ok=True)
    comp = pd.read_csv(config.FILE_COMPOSIZIONE)
    gia_provati = set(pd.read_csv(config.FILE_SELEZIONE_SVIL)["ticker"])
    meta_svil = json.loads(config.FILE_META_SVIL.read_text(encoding="utf-8"))
    ultima_svil = pd.Timestamp(meta_svil["ultima_data_titoli"])

    ordine = np.random.default_rng(config.SEME).permutation(len(comp))
    ora_borsa = datetime.now(ZoneInfo(config.FUSO_BORSA))
    prese, righe = [], []
    for pos, k in enumerate(ordine, 1):
        if len(prese) >= config.N_VALIDAZIONE:
            break
        r = comp.iloc[k]
        t = r["ticker_yahoo"]
        if t in gia_provati:
            continue
        df = scarica(t)
        esito = "preso"
        if df is None:
            esito = "scartato: dati non disponibili"
        else:
            if df.index[-1].date() == ora_borsa.date() and ora_borsa.hour < 16:
                df = df.iloc[:-1]
            df = df[df.index <= ultima_svil]      # stesso ultimo giorno dei titoli di sviluppo: periodi confrontabili
            if df.empty:
                esito = "scartato: dati non disponibili"
                righe.append({"ordine_sorteggio": pos, "ticker": t, "nome": r["nome"], "settore": r["settore"], "esito": esito})
                continue
            fine = df.index[-1]
            i0 = int(df.index.searchsorted(fine - pd.DateOffset(years=config.ANNI_TEST)))
            if i0 < config.SEDUTE_MINIME_PRIMA:
                esito = f"scartato: storia troppo corta ({i0} sedute prima dell'inizio del test)"
            elif (ultima_svil - fine).days > 5 or (fine - ultima_svil).days > 5:
                esito = "scartato: periodo diverso da quello dei titoli di sviluppo"
        if esito == "preso":
            df.to_csv(config.DATI_VAL / f"{t}.csv", float_format="%.6f")
            prese.append(t)
        righe.append({"ordine_sorteggio": pos, "ticker": t, "nome": r["nome"], "settore": r["settore"], "esito": esito})
        print(f"{pos:3d} {t:8s} {esito}")
    if len(prese) < config.N_VALIDAZIONE:
        raise SystemExit(f"Solo {len(prese)} titoli validi su {config.N_VALIDAZIONE} richiesti.")
    pd.DataFrame(righe).to_csv(config.FILE_SELEZIONE_VAL, index=False)

    def impronta(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    metadati = {
        "descrizione": config.DESCRIZIONE_DATI,
        "fonte": "Yahoo Finance",
        "libreria": f"yfinance {yf.__version__}",
        "scaricato_il_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seme": config.SEME,
        "titoli_sviluppo": meta_svil["titoli"],
        "titoli_validazione": prese,
        "titoli_validazione_provati": len(righe),
        "titoli_validazione_scartati": len(righe) - len(prese),
        "ultima_data_titoli": str(ultima_svil.date()),
        "colonne_usate": config.NOTA_COLONNA,
        "sha256_validazione": {t: impronta(config.DATI_VAL / f"{t}.csv") for t in prese},
    }
    config.FILE_METADATI.write_text(json.dumps(metadati, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nScaricati {len(prese)} titoli di validazione, {len(righe) - len(prese)} scartati.")


if __name__ == "__main__":
    main()
