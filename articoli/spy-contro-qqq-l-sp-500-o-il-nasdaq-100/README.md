# SPY contro QQQ: l'S&P 500 o il Nasdaq-100?

**Domanda:** dal 1999 conviene l'S&P 500 (SPY) o il Nasdaq 100 (QQQ), una volta contati rischio, perdite e crisi?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** SPY e QQQ, rendimenti giornalieri.
- **Misure:** CAGR, volatilità, Sharpe, perdita massima e recupero, finestre di 3, 5 e 10 anni, tre crisi.
- **Test:** bootstrap a blocchi della differenza di Sharpe, persistenza del vincitore, scimmie.

## Cosa c'è in questa cartella

```
spy-contro-qqq-l-sp-500-o-il-nasdaq-100/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i dati da Yahoo Finance
    ├── 02_backtest_e_test.py  calcoli e test statistici
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── motore.py
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/spy-contro-qqq-l-sp-500-o-il-nasdaq-100
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
