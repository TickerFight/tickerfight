"""Motore di simulazione in euro di una regola di ingresso sul trend su un singolo strumento, con tre uscite possibili.

Regole (da dichiarare nell'articolo):
  - segnale: investito se la chiusura sta sopra la media mobile semplice (calcolata sulle chiusure);
  - il segnale a fine seduta t decide l'ordine della seduta t+1, eseguito alla chiusura di t+1 (nessun look-ahead),
    con il cambio della stessa seduta;
  - uscita di trend (regola "tr"): si vende quando il segnale diventa falso;
  - trailing stop (`trail`): si segue il massimo delle chiusure dall'acquisto (nella valuta dello strumento); se alla
    chiusura di t la chiusura sta a `trail` o più sotto quel massimo, si vende alla chiusura di t+1;
  - uscita a tempo (`tempo`): se alla chiusura di t sono passate `tempo` sedute dall'acquisto, si vende alla chiusura di t+1;
  - con trailing stop o uscita a tempo si entra sul segnale di trend e non si guarda più il segnale per uscire; dopo
    l'uscita si rientra solo dopo che il segnale è tornato falso e poi vero (se il segnale è già falso al momento
    dell'uscita, il rientro è libero alla prima risalita);
  - azioni frazionate, si investe tutta la cassa; commissione per ogni ordine = parte fissa + parte proporzionale
    all'importo investito o incassato;
  - la cassa non rende nulla; i dividendi non sono considerati;
  - tassa sulle plusvalenze calcolate in euro (cambio incluso), pagata a ogni vendita come nel regime amministrato;
    la commissione si somma al costo di acquisto e si sottrae dall'incasso; le minusvalenze compensano le plusvalenze
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


def prepara(titolo: pd.DataFrame, cambio: pd.DataFrame | None, media: int) -> pd.DataFrame:
    """Chiusure, cambio (dollari per euro; 1 per gli strumenti in euro), media mobile e segnale di trend."""
    df = titolo[["Close"]].astype(float).copy()
    if cambio is None:
        df["fx"] = 1.0
    else:
        fx = cambio["Close"].astype(float)
        df["fx"] = fx.reindex(df.index.union(fx.index)).ffill().reindex(df.index)
        df = df.dropna(subset=["fx"])
    df["sma"] = df["Close"].rolling(media).mean()
    df["segnale"] = (df["Close"] > df["sma"]) & df["sma"].notna()
    return df


def primo_indice(df: pd.DataFrame) -> int:
    """Prima seduta il cui segnale precedente è calcolabile con la media completa."""
    return int(np.flatnonzero(df["sma"].notna().to_numpy())[0]) + 1


def _compra_importo(cassa: float, fissa: float, perc: float) -> tuple[float, float]:
    """Dalla cassa all'importo investito e alla commissione pagata: cassa = investito + fissa + perc*investito."""
    investito = (cassa - fissa) / (1.0 + perc)
    return investito, fissa + perc * investito


def valuta_blocchi(C: np.ndarray, FX: np.ndarray, anni: np.ndarray, acquisti, vendite, capitale: float,
                   fissa: float, perc: float, aliquota: float) -> tuple[float, float, float]:
    """Valore finale, commissioni e tasse di una sequenza di blocchi (acquisto alla chiusura a[j], vendita alla chiusura
    b[j]). È la stessa contabilità di `simula`, senza il registro: serve alle scimmie."""
    cassa = capitale
    zaino = Zaino(aliquota)
    comm_tot = tasse_tot = 0.0
    for a, b in zip(acquisti, vendite):
        investito, comm = _compra_importo(cassa, fissa, perc)
        if investito <= 0:
            continue
        base = cassa
        azioni = investito / (C[a] / FX[a])
        lordo = azioni * C[b] / FX[b]
        comm_v = fissa + perc * lordo
        netto = lordo - comm_v
        tassa = zaino.tassa(int(anni[b]), netto - base)
        comm_tot += comm + comm_v
        tasse_tot += tassa
        cassa = netto - tassa
    return cassa, comm_tot, tasse_tot


def simula(df: pd.DataFrame, i0: int, capitale: float, fissa: float, perc: float, aliquota: float,
           strategia: bool, trail: float | None = None, tempo: int | None = None) -> dict:
    """strategia=True: regola di trend (uscita di trend; oppure trailing stop se `trail` è un numero; oppure uscita a tempo
    se `tempo` è un numero di sedute); False: buy & hold (compra a i0, vende alla fine)."""
    C, FX = (df[c].to_numpy(float) for c in ("Close", "fx"))
    SEG = df["segnale"].to_numpy(bool)
    date = df.index
    n = len(df)
    cassa, azioni, base = float(capitale), 0.0, 0.0
    massimo_locale = 0.0
    i_acq = 0
    bloccato = False
    zaino = Zaino(aliquota)
    log: list[dict] = []
    tot = {"commissioni": 0.0, "tasse": 0.0}
    equity = np.empty(n - i0)
    in_posizione = np.zeros(n - i0, dtype=bool)

    def compra(i, motivo):
        nonlocal cassa, azioni, base, massimo_locale, i_acq
        investito, comm = _compra_importo(cassa, fissa, perc)
        if investito <= 0:
            return
        px_eur = C[i] / FX[i]
        azioni = investito / px_eur
        base = cassa
        massimo_locale = C[i]
        i_acq = i
        tot["commissioni"] += comm
        log.append(dict(i=i, data=str(date[i].date()), lato="acquisto", motivo=motivo, prezzo=C[i], cambio=FX[i],
                        prezzo_eur=px_eur, azioni=azioni, commissione=comm, spesa_eur=cassa,
                        incasso_netto_eur=0.0, plusvalenza_eur=0.0, tassa_eur=0.0))
        cassa = 0.0

    def vendi(i, motivo):
        nonlocal cassa, azioni, base
        px_eur = C[i] / FX[i]
        lordo = azioni * px_eur
        comm = fissa + perc * lordo
        netto = lordo - comm
        guadagno = netto - base
        tassa = zaino.tassa(int(date[i].year), guadagno)
        tot["commissioni"] += comm
        tot["tasse"] += tassa
        log.append(dict(i=i, data=str(date[i].date()), lato="vendita", motivo=motivo, prezzo=C[i], cambio=FX[i],
                        prezzo_eur=px_eur, azioni=azioni, commissione=comm, spesa_eur=0.0,
                        incasso_netto_eur=netto, plusvalenza_eur=guadagno, tassa_eur=tassa))
        cassa = netto - tassa
        azioni, base = 0.0, 0.0

    for i in range(i0, n):
        if strategia:
            sig = bool(SEG[i - 1])
            if trail is None and tempo is None:
                if sig and azioni == 0.0:
                    compra(i, "segnale")
                elif (not sig) and azioni > 0.0:
                    vendi(i, "segnale")
            else:
                if bloccato and not sig:
                    bloccato = False
                if azioni > 0.0:
                    massimo_locale = max(massimo_locale, C[i - 1])
                    if trail is not None and C[i - 1] <= massimo_locale * (1.0 - trail):
                        vendi(i, "trailing stop")
                        bloccato = sig
                    elif tempo is not None and (i - 1) - i_acq >= tempo:
                        vendi(i, "uscita a tempo")
                        bloccato = sig
                elif sig and not bloccato:
                    compra(i, "segnale")
        elif i == i0:
            compra(i, "acquisto iniziale")
        equity[i - i0] = cassa + azioni * C[i] / FX[i]
        in_posizione[i - i0] = azioni > 0.0
    if azioni > 0.0:
        vendi(n - 1, "liquidazione finale")

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
        "n_uscite_regola": sum(1 for r in log if r["motivo"] in ("trailing stop", "uscita a tempo")),
        "commissioni_eur": tot["commissioni"],
        "tasse_eur": tot["tasse"],
        "quota_giorni_investito": float(in_posizione.mean()),
        "giorni_investito": int(in_posizione.sum()),
        "perdita_massima": float((equity / picco - 1).min()),
        "operazioni": log,
        "equity": equity,
        "in_posizione": in_posizione,
    }


def blocchi(res: dict) -> tuple[np.ndarray, np.ndarray]:
    """Indici di acquisto e di vendita (nelle sedute del dataframe) dei periodi investiti di una simulazione."""
    a = np.array([r["i"] for r in res["operazioni"] if r["lato"] == "acquisto"], dtype=int)
    b = np.array([r["i"] for r in res["operazioni"] if r["lato"] == "vendita"], dtype=int)
    return a, b


def scimmia(k: int, durata_totale: int, n_sedute: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Una scimmia: k periodi investiti, la cui durata totale (sedute tra acquisto e vendita) è `durata_totale`, piazzati
    a caso nelle `n_sedute` sedute disponibili, senza sovrapposizioni. Restituisce gli indici relativi di acquisto e vendita."""
    if k == 1:
        durate = np.array([durata_totale])
    else:
        tagli = np.sort(rng.choice(durata_totale - 1, size=k - 1, replace=False)) + 1
        durate = np.diff(np.r_[0, tagli, durata_totale])               # k durate, ciascuna almeno 1
    libere = n_sedute - durata_totale - k                              # sedute rimaste fuori dai blocchi (b - a + 1 sedute l'uno)
    if libere < 0:
        raise ValueError("blocchi troppo lunghi per le sedute disponibili")
    tagli_l = np.sort(rng.choice(libere + k, size=k, replace=False)) - np.arange(k)    # k+1 vuoti non negativi
    vuoti = np.diff(np.r_[0, tagli_l, libere])
    inizi = np.cumsum(np.r_[vuoti[0], vuoti[1:k] + durate[:-1] + 1])
    return inizi, inizi + durate
