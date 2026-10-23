"""Motore di simulazione in euro di una regola a medie mobili su un singolo titolo.

Regole (da dichiarare nell'articolo):
  - segnale: investito se la media mobile veloce è sopra la lenta, calcolate sulle chiusure;
  - il segnale a fine seduta t decide l'operazione della seduta t+1 (nessun look-ahead);
  - esecuzione "apertura": prezzo di apertura di t+1, cambio dell'ultima chiusura nota (t);
    esecuzione "chiusura": prezzo di chiusura di t+1, cambio di t+1 (controllo di robustezza);
  - azioni frazionate, si investe tutta la cassa; commissione fissa per ogni ordine, acquisto o vendita;
  - la cassa non rende nulla; i dividendi non sono considerati;
  - tassa sulle plusvalenze calcolate in euro (cambio incluso), pagata a ogni vendita come nel regime
    amministrato; la commissione si somma al costo di acquisto e si sottrae dall'incasso; le minusvalenze
    compensano le plusvalenze successive fino al quarto anno seguente;
  - a fine periodo si vende tutto, con commissione e tassa, per confrontare cifre nette.
Non modellati: imposta di bollo, ritenuta sui dividendi, spread di cambio.
"""
from pathlib import Path

import numpy as np
import pandas as pd


class Zaino:
    """Minusvalenze compensabili con le plusvalenze successive, fino al 4° anno seguente."""

    def __init__(self, aliquota: float):
        self.aliquota = aliquota
        self.voci: list[list[float]] = []   # [ultimo anno utilizzabile, importo residuo]

    def tassa(self, anno: int, guadagno: float) -> float:
        if guadagno < 0:
            self.voci.append([anno + 4, -guadagno])
            return 0.0
        residuo = guadagno
        for voce in sorted(self.voci, key=lambda v: v[0]):      # prima le più vecchie
            if voce[0] < anno or voce[1] <= 0:
                continue
            usa = min(voce[1], residuo)
            voce[1] -= usa
            residuo -= usa
            if residuo <= 0:
                break
        return self.aliquota * residuo


def carica_csv(percorso: Path) -> pd.DataFrame:
    df = pd.read_csv(percorso, parse_dates=["Date"], index_col="Date").sort_index()
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated(keep="last")]
    if (df["Close"] <= 0).any() or df["Close"].isna().any():
        raise SystemExit(f"{percorso}: chiusure mancanti o non positive.")
    return df


def prepara(titolo: pd.DataFrame, cambio: pd.DataFrame, veloce: int, lenta: int) -> pd.DataFrame:
    df = titolo[["Open", "Close"]].astype(float).copy()
    fx = cambio["Close"].astype(float)
    df["fx"] = fx.reindex(df.index.union(fx.index)).ffill().reindex(df.index)
    df["sma_v"] = df["Close"].rolling(veloce).mean()
    df["sma_l"] = df["Close"].rolling(lenta).mean()
    df["segnale"] = (df["sma_v"] > df["sma_l"]) & df["sma_l"].notna()
    return df


def indice_data(df: pd.DataFrame, data) -> int:
    """Posizione della prima seduta con data uguale o successiva a quella indicata."""
    return int(np.searchsorted(df.index.values, np.datetime64(data)))


def simula(df: pd.DataFrame, i0: int, capitale: float, commissione: float, aliquota: float,
           modo: str, strategia: bool) -> dict:
    """strategia=True: regola a medie mobili; False: buy & hold (compra a i0, vende alla fine)."""
    O, C, FX = (df[c].to_numpy(float) for c in ("Open", "Close", "fx"))
    SEG = df["segnale"].to_numpy(bool)
    date = df.index
    n = len(df)
    cassa, azioni, base = float(capitale), 0.0, 0.0
    zaino = Zaino(aliquota)
    log: list[dict] = []
    tot = {"commissioni": 0.0, "tasse": 0.0}
    equity = np.empty(n - i0)
    in_posizione = np.zeros(n - i0, dtype=bool)

    def compra(i, px_usd, fx, etichetta):
        nonlocal cassa, azioni, base
        investito = cassa - commissione
        if investito <= 0:
            return
        px_eur = px_usd / fx
        spesa = cassa
        azioni = investito / px_eur
        base = spesa
        tot["commissioni"] += commissione
        log.append(dict(data=str(date[i].date()), lato="acquisto", motivo=etichetta, prezzo_usd=px_usd, cambio=fx,
                        prezzo_eur=px_eur, azioni=azioni, commissione=commissione, spesa_eur=spesa,
                        incasso_netto_eur=0.0, plusvalenza_eur=0.0, tassa_eur=0.0))
        cassa = 0.0

    def vendi(i, px_usd, fx, etichetta):
        nonlocal cassa, azioni, base
        px_eur = px_usd / fx
        lordo = azioni * px_eur
        netto = lordo - commissione
        guadagno = netto - base
        tassa = zaino.tassa(int(date[i].year), guadagno)
        tot["commissioni"] += commissione
        tot["tasse"] += tassa
        log.append(dict(data=str(date[i].date()), lato="vendita", motivo=etichetta, prezzo_usd=px_usd, cambio=fx,
                        prezzo_eur=px_eur, azioni=azioni, commissione=commissione, spesa_eur=0.0,
                        incasso_netto_eur=netto, plusvalenza_eur=guadagno, tassa_eur=tassa))
        cassa = netto - tassa
        azioni, base = 0.0, 0.0

    for i in range(i0, n):
        voglio = bool(SEG[i - 1]) if strategia else True
        px, fx = (O[i], FX[i - 1]) if modo == "apertura" else (C[i], FX[i])
        if voglio and azioni == 0.0:
            compra(i, px, fx, "segnale" if strategia else "acquisto iniziale")
        elif (not voglio) and azioni > 0.0:
            vendi(i, px, fx, "segnale")
        equity[i - i0] = cassa + azioni * C[i] / FX[i]
        in_posizione[i - i0] = azioni > 0.0
    if azioni > 0.0:
        vendi(n - 1, C[n - 1], FX[n - 1], "liquidazione finale")

    picco = np.maximum.accumulate(equity)
    anni = (date[-1] - date[i0]).days / 365.25
    finale = cassa
    return {
        "valore_finale_eur": finale,
        "rendimento_totale": finale / capitale - 1,
        "cagr": (finale / capitale) ** (1 / anni) - 1 if finale > 0 else float("nan"),
        "anni": anni,
        "n_acquisti": sum(1 for r in log if r["lato"] == "acquisto"),
        "n_vendite": sum(1 for r in log if r["lato"] == "vendita"),
        "commissioni_eur": tot["commissioni"],
        "tasse_eur": tot["tasse"],
        "quota_giorni_investito": float(in_posizione.mean()),
        "perdita_massima": float((equity / picco - 1).min()),
        "operazioni": log,
        "equity": equity,
        "in_posizione": in_posizione,
    }
