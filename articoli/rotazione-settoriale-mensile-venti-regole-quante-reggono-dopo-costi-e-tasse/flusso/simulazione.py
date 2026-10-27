"""Motore di simulazione in euro di una rotazione mensile tra più ETF (o di un buy & hold), con costi e tasse.

Regole (da dichiarare nell'articolo):
  - le chiusure sono in dollari; il valore in euro di una posizione è azioni * chiusura / cambio (dollari per euro) della stessa seduta;
  - il segnale alla chiusura dell'ultima seduta del mese decide l'ordine della prima seduta del mese dopo, eseguito alla
    chiusura di quella seduta (nessun look-ahead);
  - a ogni ribilanciamento si vendono le posizioni uscite dal gruppo scelto e con la cassa disponibile si comprano, in parti
    uguali, quelle entrate; le posizioni che restano non si toccano;
  - azioni frazionate; commissione per ogni ordine = parte fissa + parte proporzionale all'importo investito o incassato;
  - la cassa non rende nulla; i dividendi non sono considerati (si usano le chiusure non corrette);
  - tassa sulle plusvalenze calcolate in euro (cambio incluso), pagata a ogni vendita come nel regime amministrato; la
    commissione si somma al costo di acquisto e si sottrae dall'incasso; le minusvalenze compensano le plusvalenze
    successive fino al quarto anno seguente;
  - a fine periodo si vende tutto, con commissione e tassa, per confrontare cifre nette.
Non modellati: imposta di bollo, tassa sulle transazioni finanziarie, spread di cambio, scarto tra denaro e lettera.
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


def prepara(chiusure: dict[str, pd.DataFrame], cambio: pd.DataFrame) -> tuple[pd.DatetimeIndex, list[str], np.ndarray, np.ndarray]:
    """Allinea le chiusure di tutti gli strumenti sulle sedute comuni (con cambio disponibile).
    Restituisce date, elenco dei ticker, matrice delle chiusure (sedute x strumenti) e vettore del cambio."""
    nomi = list(chiusure)
    tab = pd.concat({k: chiusure[k]["Close"].astype(float) for k in nomi}, axis=1).dropna()
    fx = cambio["Close"].astype(float)
    tab["__fx"] = fx.reindex(tab.index.union(fx.index)).ffill().reindex(tab.index)
    tab = tab.dropna()
    return tab.index, nomi, tab[nomi].to_numpy(float), tab["__fx"].to_numpy(float)


def fine_mese(date: pd.DatetimeIndex) -> np.ndarray:
    """Indici delle sedute che sono l'ultima del loro mese di calendario (l'ultima riga dei dati è esclusa)."""
    mese = date.year.to_numpy() * 12 + date.month.to_numpy()
    return np.flatnonzero(mese[1:] != mese[:-1])


def piano_rotazione(C: np.ndarray, date: pd.DatetimeIndex, lookback: int, k: int, t_min: int, colonne: list[int]) -> dict[int, tuple[int, ...]]:
    """Per ogni fine mese t >= t_min: i k strumenti (tra `colonne`) con il rendimento di prezzo più alto nelle ultime
    `lookback` sedute. Restituisce {indice della seduta di esecuzione (t+1): colonne scelte, in ordine di classifica}."""
    piano = {}
    for t in fine_mese(date):
        if t < t_min or t < lookback:
            continue
        rend = C[t, colonne] / C[t - lookback, colonne] - 1.0
        ordine = np.argsort(-rend, kind="stable")[:k]
        piano[int(t) + 1] = tuple(int(colonne[j]) for j in ordine)
    return piano


def _compra_importo(cassa: float, fissa: float, perc: float) -> tuple[float, float]:
    """Dalla cassa all'importo investito e alla commissione pagata: cassa = investito + fissa + perc*investito."""
    investito = (cassa - fissa) / (1.0 + perc)
    return investito, fissa + perc * investito


def simula(C: np.ndarray, FX: np.ndarray, anni: np.ndarray, piano: dict[int, tuple[int, ...]], i0: int, capitale: float,
           fissa: float, perc: float, aliquota: float, serie: bool = True) -> dict:
    """Esegue il piano {seduta: strumenti da tenere}. Alla prima seduta del piano si investe tutta la cassa."""
    n = C.shape[0]
    cassa = float(capitale)
    pos: dict[int, list[float]] = {}          # colonna -> [azioni, costo di acquisto in euro]
    zaino = Zaino(aliquota)
    comm_tot = tasse_tot = 0.0
    n_acq = n_ven = 0
    log: list[dict] = []
    storia: list[tuple[int, float, dict[int, float]]] = []

    def vendi(i, c, motivo):
        nonlocal cassa, comm_tot, tasse_tot, n_ven
        az, base = pos.pop(c)
        lordo = az * C[i, c] / FX[i]
        comm = fissa + perc * lordo
        netto = lordo - comm
        guadagno = netto - base
        tassa = zaino.tassa(int(anni[i]), guadagno)
        comm_tot += comm
        tasse_tot += tassa
        cassa += netto - tassa
        n_ven += 1
        if serie:
            log.append(dict(i=i, lato="vendita", col=c, motivo=motivo, azioni=az, commissione=comm,
                            incasso_netto_eur=netto, plusvalenza_eur=guadagno, tassa_eur=tassa))

    for i in sorted(piano):
        if i < i0:
            continue
        bersaglio = piano[i]
        for c in [c for c in pos if c not in bersaglio]:
            vendi(i, c, "rotazione")
        entranti = [c for c in bersaglio if c not in pos]
        if entranti and cassa > 0:
            quota = cassa / len(entranti)
            for c in entranti:
                investito, comm = _compra_importo(quota, fissa, perc)
                if investito <= 0:
                    continue
                az = investito / (C[i, c] / FX[i])
                pos[c] = [az, quota]
                comm_tot += comm
                n_acq += 1
                cassa -= quota
                if serie:
                    log.append(dict(i=i, lato="acquisto", col=c, motivo="rotazione", azioni=az, commissione=comm,
                                    spesa_eur=quota))
        if serie:
            storia.append((i, cassa, {c: v[0] for c, v in pos.items()}))
    ultimo = n - 1
    for c in list(pos):
        vendi(ultimo, c, "liquidazione finale")
    finale = cassa

    out = {"valore_finale_eur": finale, "rendimento_totale": finale / capitale - 1,
           "n_acquisti": n_acq, "n_vendite": n_ven, "commissioni_eur": comm_tot, "tasse_eur": tasse_tot}
    anni_tot = (ultimo - i0) / 252.0
    out["anni"] = anni_tot
    if not serie:
        return out
    equity = np.empty(n - i0)
    for j, (i, cs, az) in enumerate(storia):
        fine = storia[j + 1][0] if j + 1 < len(storia) else n
        val = np.full(fine - i, cs)
        for c, a in az.items():
            val = val + a * C[i:fine, c] / FX[i:fine]
        equity[i - i0:fine - i0] = val
    in_pos = np.array([bool(az) for (_, _, az) in storia])
    giorni_inv = 0
    for j, (i, cs, az) in enumerate(storia):
        fine = storia[j + 1][0] if j + 1 < len(storia) else n
        if az:
            giorni_inv += fine - i
    picco = np.maximum.accumulate(equity)
    out.update({"equity": equity, "operazioni": log, "perdita_massima": float((equity / picco - 1).min()),
                "quota_giorni_investito": giorni_inv / (n - i0)})
    return out


def cagr(finale: float, capitale: float, date: pd.DatetimeIndex, i0: int) -> float:
    anni = (date[-1] - date[i0]).days / 365.25
    return (finale / capitale) ** (1 / anni) - 1 if finale > 0 else float("nan")


def scimmia_piano(piano: dict[int, tuple[int, ...]], colonne: list[int], rng) -> dict[int, tuple[int, ...]]:
    """Una scimmia: stessi giorni di ordine e stesso numero di strumenti che entrano e escono a ogni ribilanciamento
    della regola, ma strumenti scelti a caso. Così il numero di ordini è identico a quello della regola."""
    out = {}
    prev_reale: set[int] = set()
    prev_m: list[int] = []
    for i in sorted(piano):
        T = set(piano[i])
        c = len(T - prev_reale)
        if not prev_m:
            nuovo = [int(x) for x in rng.choice(colonne, size=len(T), replace=False)]
        else:
            restano = len(prev_m) - c
            tieni = [int(x) for x in rng.choice(prev_m, size=restano, replace=False)] if restano > 0 else []
            altri = [x for x in colonne if x not in prev_m]
            entra = [int(x) for x in rng.choice(altri, size=c, replace=False)] if c > 0 else []
            nuovo = tieni + entra
        out[i] = tuple(nuovo)
        prev_m = nuovo
        prev_reale = T
    return out
