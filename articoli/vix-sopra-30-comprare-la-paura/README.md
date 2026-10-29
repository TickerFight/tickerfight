# VIX sopra 30: comprare la paura?

**Domanda:** dopo che il VIX chiude sopra 30, l'S&P 500 rende di più del solito nei mesi successivi? Si può comprare la paura?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Evento:** prima chiusura del VIX sopra la soglia dopo almeno 63 sedute sotto; acquisto alla chiusura successiva.
- **Misure:** rendimento a 21, 63, 126 e 252 sedute, quota di episodi positivi, peggiore chiusura nelle 63 sedute dopo l'acquisto, soglie 25, 30, 35 e 40.
- **Test:** scimmie (stesso numero di acquisti a date casuali) e confronto con una seduta qualunque.

## Cosa c'è in questa cartella

```
vix-sopra-30-comprare-la-paura/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica i dati da Yahoo Finance
    ├── 02_backtest_e_test.py  calcoli e test statistici
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/vix-sopra-30-comprare-la-paura
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
