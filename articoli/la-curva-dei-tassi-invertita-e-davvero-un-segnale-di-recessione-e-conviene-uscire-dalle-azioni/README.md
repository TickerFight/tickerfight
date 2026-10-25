# La curva dei tassi invertita: è davvero un segnale di recessione, e conviene uscire dalle azioni?

**Domanda:** quando il rendimento a 10 anni scende sotto quello a 3 mesi, arriva davvero una recessione? E conviene uscire dalle azioni?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Segnale:** a fine mese, spread = rendimento a 10 anni meno rendimento a 3 mesi. Curva invertita se lo spread è sotto zero.
- **Episodio:** almeno 3 fine-mese invertiti; serie separate da meno di 6 mesi di curva normale sono un solo episodio.
- **Recessioni:** le otto dichiarate dal NBER dal 1969 (date in `config.py`).
- **Strategia:** il segnale di fine mese decide il mese successivo: curva invertita = liquidità al tasso a 3 mesi, altrimenti S&P 500 (indice di prezzo, senza dividendi). Confronto con il buy & hold.
- **Il caso:** 2.000 strategie con lo stesso segnale spostato circolarmente nel tempo (almeno 24 mesi).

## Cosa c'è in questa cartella

```
la-curva-dei-tassi-invertita-e-davvero-un-segnale-di-recessione-e-conviene-uscire-dalle-azioni/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica S&P 500, ^TNX (10 anni) e ^IRX (3 mesi)
    ├── 02_backtest_e_test.py  episodi, recessioni NBER, strategia, confronto con il caso
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            serie mensili, episodi di inversione, strategia, drawdown
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/la-curva-dei-tassi-invertita-e-davvero-un-segnale-di-recessione-e-conviene-uscire-dalle-azioni
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
