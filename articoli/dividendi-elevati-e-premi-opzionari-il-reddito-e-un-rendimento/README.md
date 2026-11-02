# Dividendi elevati e premi opzionari: il reddito è un rendimento?

**Domanda:** gli ETF che puntano su dividendi alti o su premi di opzioni distribuiti rendono di più dell'S&P 500? E chi vive di rendita sta meglio con la distribuzione o vendendo quote di un ETF normale?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** SPY, QQQ, quattro ETF a dividendo elevato (SCHD, VYM, HDV, SPYD) e due a premio opzionario (XYLD, QYLD), dal giorno in cui esistono tutti.
- **Reddito:** differenza tra il rendimento con distribuzioni reinvestite (Adj Close) e quello del solo prezzo (Close).
- **Prelievo:** 4% annuo del capitale iniziale, in rate mensili fisse; con e senza imposta del 26%.
- **Test:** confronto con SPY e bootstrap a blocchi della differenza di Sharpe.

## Cosa c'è in questa cartella

```
dividendi-elevati-e-premi-opzionari-il-reddito-e-un-rendimento/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica da Yahoo Finance gli otto ETF (Close e Adj Close)
    ├── 02_backtest_e_test.py  metriche, reddito, prelievo, bootstrap
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            reddito e prezzo mensili, simulazione del prelievo con e senza tasse
    ├── motore.py              rendimento, volatilità, Sharpe, perdita massima, bootstrap a blocchi
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/dividendi-elevati-e-premi-opzionari-il-reddito-e-un-rendimento
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
