# La scimmia con il dardo batte la media mobile? Mille scimmie contro la regola più famosa della Borsa

**Domanda:** una regola a media mobile semplice (investiti quando la chiusura di ieri è sopra la media) batte migliaia di scimmie che stanno nel mercato per la stessa quota di tempo e con lo stesso numero di operazioni?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** investiti se la chiusura di ieri è sopra la media a n sedute (n = 50, 100, 150, 200, 250; la principale è 200), altrimenti liquidità senza interessi. Nessun look-ahead.
- **Indici:** S&P 500, DAX, FTSE 100, Nikkei 225 (prezzo, senza dividendi, valuta locale). Stesso giorno di partenza per regola, buy & hold e scimmie.
- **Scimmie a blocchi:** stesse durate dentro/fuori della regola, in ordine casuale (stessa quota, stesso numero di operazioni). **Scimmie a moneta:** ogni seduta investita con probabilità pari alla quota.
- **Metriche:** rendimento annuo composto, rapporto di Sharpe, perdita massima; con e senza costo di 0,1% per operazione.
- **Test multipli:** 20 confronti (4 indici per 5 lunghezze) per ciascuna misura, p corretti con Holm.

## Cosa c'è in questa cartella

```
la-scimmia-con-il-dardo-batte-la-media-mobile-mille-scimmie-contro-la-regola-piu-famosa-della-borsa/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py
    ├── 02_backtest_e_test.py
    ├── 03_grafici.py
    ├── config.py
    ├── funzioni.py
    └── verifica_motore.py
```

## Come si rifà

```bash
cd articoli/la-scimmia-con-il-dardo-batte-la-media-mobile-mille-scimmie-contro-la-regola-piu-famosa-della-borsa
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
