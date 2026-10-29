# Tech contro il resto: la tecnologia batte tutti gli altri settori?

**Domanda:** il settore tecnologico (XLK) batte davvero tutti gli altri otto settori messi insieme, e a quale prezzo in perdite?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Dati:** i nove settori S&P 500 (ETF Select Sector).
- **Confronto:** XLK contro gli altri otto in pari peso con ribilanciamento giornaliero.
- **Test:** bootstrap a blocchi della differenza di Sharpe, finestre di 5 anni, crisi, scimmie.

## Cosa c'è in questa cartella

```
tech-contro-il-resto-la-tecnologia-batte-tutti-gli-altri-settori/
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
cd articoli/tech-contro-il-resto-la-tecnologia-batte-tutti-gli-altri-settori
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
